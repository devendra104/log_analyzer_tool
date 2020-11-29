import ast
import os
import re
import secrets
from threading import Thread

from flask import flash
from flask import Flask
from flask import render_template
from flask import request
from flask import Response
from flask_paginate import get_page_args
from flask_paginate import Pagination
from utils.common import Common
from utils.controller import Controller
from utils.data_updater import DataUpdater
from utils.db import accessing_all_data
from utils.db import accessing_data_via_id
from utils.db import accessing_observation_db
from utils.db import db_update
from utils.db import delete_record
from utils.db import extracting_build_info
from utils.db import extracting_data_by_field
from utils.db import extracting_job_status
from utils.db import regex_data_retrieval
from utils.db import update_record
from views.build import JobSearchForm
from views.build import ObservationUpdate
from views.build import ReportForm
from views.build import SearchByField
from views.build import ValidatorName


app = Flask(
    __name__,
    template_folder="../templates",
    static_url_path="",
    static_folder="../static",
)
app.secret_key = secrets.token_hex(16)
app.config["SESSION_TYPE"] = "log_analysis"


@app.route("/")
def menu():
    """
    This API module is used to list all the operation supported by this tool.
    :return: Redirect the main menu page
    """
    available_job = accessing_all_data()
    all_available_job = []
    job_url = {}
    for job in available_job:
        if job["Job-Name"] not in all_available_job:
            all_available_job.append(job["Job-Name"])
    Common.logger.info(f"Available job is {all_available_job}")

    for job in all_available_job:
        common_db_status = extracting_job_status(job_name=job)
        common_status = [
            common_db_status["PASSED"],
            common_db_status["FAILED"],
            common_db_status["UNSTABLE"],
        ]
        color = ["green", "red", "yellow"]
        overall = [{"data": common_status, "backgroundColor": color}]
        status_url = (
            "https://quickchart.io/chart?c={'type':'pie',data:{'labels':"
            "['PASS', 'FAIL', 'UNSTABLE']," + f"datasets:{overall}" + "}}"
        )
        job_url[job] = status_url
    Common.logger.info(f"All urls {job_url}")
    return render_template("menu.html", job_url=job_url)


def page_list(fs, per_page, offset=0):
    """
    This function is used to calculate the current offset value
    :param fs:
    :param per_page:
    :param offset:
    :return: offset number
    """
    Common.logger.info(f"Collecting the requested record by the pagination module {fs}")
    requested_record = Common.collection_creation(fs)
    return requested_record[offset : offset + per_page]


@app.route("/evaluated_data_history/Job-Name/<job_name>")
def index_pagination(job_name):
    """
    This API  is used to list the job based on their job name
    :param str job_name: Name of the Jenkins job
    :return: redirect the build history page
    """
    fs = regex_data_retrieval(job_name=job_name)
    if fs.count() == 0:
        return render_template("404.html", title="404"), 404
    try:
        pattern_type = re.search(r"\w*-\w*", job_name).group()
    except AttributeError:
        Common.logger.warn(
            f"index_pagination:failed to search the job name: {job_name}"
        )
        pattern_type = job_name
    offset = {"page": 1, "per_page": Common.get_config_value("per_page")}
    page, per_page, offset = get_page_args(
        page_parameter="page", per_page_parameter="per_page", **offset
    )
    pagination_items = page_list(fs, per_page=per_page, offset=offset)
    pagination = Pagination(
        page=page, per_page=per_page, total=fs.count(), css_framework="bootstrap4"
    )
    return render_template(
        "index_pagination.html",
        List=pagination_items,
        page=page,
        per_page=per_page,
        pagination=pagination,
        pattern_type=pattern_type,
        job_name=job_name,
    )


@app.route("/build_filter")
def job_filter_menu():
    """
    This API is used to list the menu options fo search the job based on their type
    :return: redirect the search menu option page
    """
    return render_template("search_menu.html")


@app.route("/historical_data_dashboard")
def historical_data_menu():
    """
    This API
    :return:
    """
    list_of_jobs = Common.validation_param_detail(
        "validation_parameter.sample", "jenkins_job_details"
    )
    job_collection = list()
    actual_jobs = list()
    for job in list_of_jobs:
        actual_jobs.append(
            list_of_jobs[job]["job_name"].replace("-<component-version>", "")
        )
        job_collection.append(
            list_of_jobs[job]["job_name"].replace("<component-version>", "[0-9].[0-9]")
        )
    return render_template(
        "build_history_menu.html",
        job_collection=job_collection,
        actual_jobs=actual_jobs,
    )


@app.route("/build_search/<job_name>/<build_number>/<component_version>")
@app.route("/build_search", methods=["GET", "POST"])
def index(job_name=None, build_number=None, component_version=None):
    """
    This API is used to search the result based on the selected filtered options.
    :param str job_name:
    :param int build_number:
    :param str component_version:
    :return: Searched results and search job menu
    """
    search_form = JobSearchForm(request.form)
    if request.method == "POST":
        job_name = search_form.data["job_name"].strip()
        try:
            pattern_type = re.search(r"\w*-\w*", job_name).group()
        except AttributeError:
            Common.logger.warn(f"index:failed to search the job name: {job_name}")
            pattern_type = job_name
        build_number = search_form.data["build_number"]
        component_version = search_form.data["component_version"]

        fs = extracting_build_info(
            job_name=job_name,
            build_number=build_number,
            component_version=component_version,
        )
        if fs.count() == 0:
            return render_template("404.html", title="404"), 404
        data_list = Common.collection_creation(fs)
        return render_template(
            "search_results.html",
            List=data_list,
            pattern_type=pattern_type,
            data_display="True",
        )
    if job_name and build_number and component_version:
        fs = extracting_build_info(
            job_name=job_name,
            build_number=build_number,
            component_version=component_version,
        )
        if fs.count() == 0:
            return render_template("404.html", title="404"), 404
        data_list = Common.collection_creation(fs)
        test_data_map = Common.test_map_details(data_list)
        try:
            pattern_type = re.search(r"\w*-\w*", data_list[0]["Job-Name"]).group()
        except AttributeError:
            Common.logger.warn(
                f"index:failed to search the job: {data_list[0]['Job-Name']}"
            )
            pattern_type = job_name

        return render_template(
            "search_results.html",
            List=data_list,
            pattern_type=pattern_type,
            data_display="False",
            test_data_map=test_data_map,
        )
    return render_template("search.html", form=search_form)


@app.route("/search_by_component", methods=["GET", "POST"])
def search_by_component():
    """
    This API is used to search the job based on the their component
    :return:
    """
    search_form = SearchByField(request.form)
    if request.method == "POST":
        Common.logger.info("search_by_component:Post API called")
        field_name = search_form.select.data
        field_value = search_form.data["search"].strip()
        fs = extracting_data_by_field(field_name=field_name, field_value=field_value)
        if fs.count() == 0:
            return render_template("404.html", title="404"), 404

        data_list = Common.collection_creation(fs)
        test_data_map = Common.test_map_details(data_list)
        if test_data_map == 500:
            Common.logger.warn(
                f"search_by_component:Internal server error comes while listing "
                f"the data_list={data_list}"
            )
            return render_template("500.html", title="500"), 500
        return render_template(
            "search_results.html", List=data_list, test_data_map=test_data_map
        )
    return render_template("component_search_by_field.html", search_form=search_form)


@app.route("/report_preparation", methods=["GET", "POST"])
def upgrade_report():
    """
    This API is used to pass the parameter tat helps to prepare the report and send it to
    recipient user.
    """
    form = ReportForm(request.form)
    if request.method == "POST":
        Common.logger.info("upgrade_report:Post API called")
        job_type = "mail_report"
        job_category = (form.data["job_category"].strip()).split(",")
        job_name = (form.data["job_name"].strip()).split(",")
        build_number = (form.data["build_number"].strip()).split(",")
        bugzilla = (form.data["bugzilla"].strip()).split(",")
        recipient_list = form.data["recipient_list"].strip()
        component_version = form.data["component_version"].strip()
        message_body = form.data["message_details"]
        subject = form.data["subject_details"]
        bugzilla = list() if bugzilla == [""] else bugzilla
        common_report = Common.data_preparation_for_report(
            job_category, job_name, bugzilla, build_number
        )

        for data in common_report:
            try:
                job_details = extracting_build_info(
                    job_name=common_report[data]["job_name"],
                    build_number=int(common_report[data]["build_number"]),
                    component_version=component_version,
                )
            except ValueError:
                Common.logger.warn(
                    f"upgrade_report:Value error happened while extracting the "
                    f"build information for job:{common_report[data]['job_name']}"
                    f" build number ={int(common_report[data]['build_number'])} "
                    f"and component_version= {component_version}"
                )
                return render_template("500.html", title="500"), 500
            if job_details.count() == 0:
                Common.logger.warn(
                    f"upgrade_report: the value for the job "
                    f"{common_report[data]['job_name']}"
                )
                return render_template("404.html", title="404"), 404

            for job_detail in job_details:
                common_report[data]["Build_Status"] = job_detail["Build-Status"]
                common_report[data]["Build Url"] = (
                    job_detail["Job Url"] if "Job Url" in job_detail else "unavailable"
                )
                common_report[data]["Snap No"] = (
                    job_detail["Snap-Version"]
                    if "Snap-Version" in job_detail
                    else "unavailable"
                )
                try:
                    pattern_type = re.search(r"\w*-\w*", job_detail["Job-Name"]).group()
                except AttributeError:
                    pattern_type = job_detail["Job-Name"]

                if pattern_type in Common.get_config_value("test_map"):
                    highlighted_data = job_detail["Validation"][
                        "Pre_Upgrade_test_Failure"
                    ]
                    common_report[data]["highlighted_information"] = highlighted_data
                else:
                    highlighted_data = job_detail["Validation"][
                        "All_Commands_Execution_status"
                    ]
                    common_report[data]["highlighted_information"] = (
                        highlighted_data["highlighted_content"]
                        if "highlighted_content" in highlighted_data
                        else "unavailable"
                    )

                common_report[data]["component_version"] = component_version
        if not message_body:
            common_report["body"] = "Please find the job execution details below"
        else:
            common_report["body"] = message_body
        common_report["subject"] = subject
        common_report["recipient"] = recipient_list
        Common.report_preparation(common_report)
        return render_template("data_processing.html", job_type=job_type)
    return render_template("report_mail.html", form=form)


@app.route("/edit_observation/<pattern_type>/<count>/<id>", methods=["GET", "POST"])
def edit_observation(pattern_type, id):
    """
    This API is used to edit the observation based on the available record.
    :param pattern_type:
    :param id:
    """
    fs = accessing_data_via_id(build_id=f"{id}")
    if fs.count() == 0:
        return render_template("404.html", title="404"), 404
    record = Common.collection_creation(fs)[0]
    form = ObservationUpdate(request.form)
    if request.method == "POST":
        Common.logger.info(
            f"edit_observation: Post API called against id {id} and pattern type"
            f" {pattern_type}"
        )
        observations = ast.literal_eval(form.data["observation_data"])
        try:
            Common.logger.info(
                f"edit_observation: The provided observation is {observations}"
                f" {pattern_type}"
            )
            if pattern_type not in Common.get_config_value("test_map"):
                if type(observations) is dict:
                    for observation in observations:
                        db_update(
                            observation_record_key=f"{observation}",
                            observation_record_value="{}".format(
                                observations[observation]
                            ),
                        )
                record["Validation"] = Common.record_updater(
                    record["Validation"], observations
                )
                update_record(f"{id}", old_record=record)
            else:
                os.popen("touch problem_in_before_update")
                failed_test_details = {
                    "test_details": record["Validation"]["Pre_Upgrade_test_Failure"]
                }
                updated_data = Common.record_updater(failed_test_details, observations)
                record["Validation"]["Pre_Upgrade_test_Failure"] = updated_data[
                    "test_details"
                ]
                update_record(f"{id}", old_record=record)
        except Exception as ex:
            Common.logger.warn(
                f"edit_observation: The provided dictionary is not in correct "
                f"format {ex}"
            )
            flash(
                "Please provide the proper dictionary format {} of pattern {}".format(
                    observations, pattern_type
                )
            )
            return render_template(
                "observation.html", form=form, pattern_type=pattern_type, record=record
            )
        flash("Data Submitted Successfully")
    return render_template(
        "observation.html", form=form, pattern_type=pattern_type, record=record
    )


@app.route("/input", methods=["GET", "POST"])
def job_process():
    """
    This API is used to download the logs and analyze it based on the provided details
    """
    form = ValidatorName(request.form)
    if request.method == "POST":
        Common.logger.info(f"job_process: Post method called")
        job_processing_type = "log_analysis"
        job_type = form.data["job_type"].strip()
        job_number = form.data["job_number"]
        component_not_check = form.data["skip_selection"]
        component_version = form.data["component_version"]
        snap_number = form.data["snap_number"]
        Common.version_update(component_version, job_type)
        DataUpdater.build_sheet_update(
            job_type, job_number, component_not_check, component_version, snap_number
        )
        return render_template(
            "data_processing.html", form=form, job_processing_type=job_processing_type
        )
    return render_template("analyser_input.html", form=form)


@app.route("/job_list")
def job_list():
    """
    This api help us to get the details of job name, build number and component version.
    """
    fs = accessing_all_data()
    if fs.count() == 0:
        Common.logger.info(f"job_list: there is no details available in the database")
        return render_template("404.html", title="404"), 404
    records = Common.collection_creation(fs)
    job_records = dict()
    for job in records:
        if job["Job-Name"] not in job_records and (
            "Build-Number" in job and "Build-Version" in job
        ):

            job_records[job["Job-Name"]] = {
                "Build-Number": [job["Build-Number"]],
                "Build-Version": [job["Build-Version"]],
            }
        elif "Build-Number" in job and "Build-Version" in job:
            job_records[job["Job-Name"]]["Build-Number"].append(job["Build-Number"])
            job_records[job["Job-Name"]]["Build-Version"].append(job["Build-Version"])
    if job_records == dict():
        return render_template("404.html", title="404"), 404
    return render_template("job_name.html", job_records=job_records)


@app.route("/list_of_error")
def list_of_error():
    """
    This API is used to list down the errors and observations
    """
    fs = accessing_observation_db()
    Common.logger.info(
        "list_of_error: GET method call for the list of the observations "
    )
    offset = {"page": 1, "per_page": Common.get_config_value("per_page")}
    page, per_page, offset = get_page_args(
        page_parameter="page", per_page_parameter="per_page", **offset
    )
    pagination_items = page_list(fs, per_page=per_page, offset=offset)
    pagination = Pagination(
        page=page, per_page=per_page, total=fs.count(), css_framework="bootstrap4"
    )
    return render_template(
        "observation_error.html",
        List=pagination_items,
        page=page,
        per_page=per_page,
        pagination=pagination,
    )


@app.route("/system_log/<id>")
def system_log(id):
    """
    This API is used to extract the system log based on their unique job id
    :param id:
    """
    Common.logger.info("system_log: system log API called")
    fs = accessing_data_via_id(build_id=f"{id}")
    record = Common.collection_creation(fs)[0]
    return render_template(
        "system_log.html",
        record=record["SystemLog"],
        system_log_separation=Common.system_log_separation,
    )


@app.route("/progress/<string:job_type>")
def progress(job_type):
    """
    This API is used to call the action based on the provided job type
    :param job_type:
    """
    if job_type == "log_analysis":
        Common.logger.info("progress: log analysis called")
        obj = Controller()
        th1 = Thread(target=obj.run)
    else:
        Common.logger.info("progress: mail send report called")
        th1 = Thread(target=Common.mail_send())
    th1.start()
    return Response(Common.generate(th1), mimetype="text/event-stream")


@app.route("/delete", methods=["GET", "POST"])
def delete_build_data():
    """
    This API is used to delete the job based
    """
    search_form = JobSearchForm(request.form)
    if request.method == "POST":
        job_name = search_form.data["job_name"].strip()
        build_number = search_form.data["build_number"]
        component_version = search_form.data["component_version"]
        fs = extracting_build_info(
            job_name=job_name,
            build_number=build_number,
            component_version=component_version,
        )
        if fs.count() == 0:
            return render_template("404.html", title="404"), 404

        record = Common.collection_creation(fs)[0]
        response_json = delete_record(build_id=record["_id"])
        if response_json.acknowledged:
            flash(
                "Build No {} of Job {} having version {} deleted successfully".format(
                    job_name, build_number, component_version
                )
            )
        else:
            flash("Failed to delete content")
    return render_template("delete_build.html", form=search_form)


@app.errorhandler(404)
def page_not_found(error):
    """
    Page not found
    :param error:
    :return:
    """
    return render_template("404.html"), 404


@app.errorhandler(503)
def service_not_available(error):
    """
    Service Unavailable server error response code
    :param error:
    :return:
    """
    return render_template("503.html"), 503


@app.errorhandler(403)
def forbidden_service_not_available(error):
    """
    Forbidden client error status response code
    :param error:
    :return:
    """
    return render_template("403.html"), 404


@app.errorhandler(500)
def internal_server_error(error):
    """
    Internal Server Error server error response code
    :param error:
    :return:
    """
    return render_template("500.html"), 500


@app.errorhandler(412)
def internal_server_error(error):
    """
    Precondition Failed client error response code
    :param error:
    :return:
    """
    return render_template("412.html"), 500
