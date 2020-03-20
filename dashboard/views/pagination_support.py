import ast
import os
import re

from flask import Flask, request, render_template, session, Response, flash
from views.build import JobSearchForm, ValidatorName, ReportForm, ObservationUpdate, SearchByField
from utils.data_updater import DataUpdater
from utils.db import extracting_build_info, regex_data_retrieval, \
    accessing_data_via_id, delete_record, update_record, extracting_data_by_field,\
    accessing_observation_db, accessing_all_data, db_update
from utils.common import Common
from threading import Thread
from utils.controller import Controller


app = Flask(__name__, template_folder='../templates', static_url_path='',
            static_folder='../static')
app.secret_key = 'super secret key'
app.config['SESSION_TYPE'] = 'filesystem1'


@app.route('/')
def menu():
    return render_template("menu.html")


@app.route('/build_filter')
def job_filter_menu():
    return render_template("search_menu.html")


@app.route('/historical_data_dashboard')
def historical_data_menu():
    job_list = Common.validation_param_detail("validation_parameter.sample",
                                              "jenkins_job_details")
    job_collection = list()
    actual_jobs = list()
    for job in job_list:
        actual_jobs.append(job_list[job]["job_name"].replace("-<component-version>", ''))
        job_collection.append(job_list[job]["job_name"].replace("<component-version>",
                                                                "[0-9].[0-9]"))
    return render_template("build_history_menu.html", job_collection=job_collection,
                           actual_jobs=actual_jobs)


@app.route('/evaluated_data_history/Job-Name/<job_name>/<int:id>')
def pagination(job_name, id):
    per_page = 5
    fs = regex_data_retrieval(job_name=job_name)
    if fs.count() == 0:
        return render_template('404.html', title='404'), 404
    try:
        pattern_type = re.search(r'\w*-\w*', job_name).group()
    except AttributeError:
        pattern_type = job_name

    page_list, data_list = Common.page_common_logic(fs, per_page, id)
    return render_template("index_pagination.html", List=data_list,
                           pages=page_list,
                           pattern_type=pattern_type,
                           job_name=job_name,
                           index=Common.index_list((per_page * (id - 1)),
                                                   (per_page * (id - 1)) + per_page))


@app.route('/build_search/<job_name>/<build_number>/<component_version>')
@app.route('/build_search', methods=['GET', 'POST'])
def index(job_name=None, build_number=None, component_version=None):
    search_form = JobSearchForm(request.form)
    if request.method == 'POST':
        job_name = search_form.data['job_name'].strip()
        try:
            pattern_type = re.search(r'\w*-\w*', job_name).group()
        except AttributeError:
            pattern_type = job_name
        build_number = search_form.data['build_number']
        component_version = search_form.data["component_version"]

        fs = extracting_build_info(job_name=job_name, build_number=build_number,
                                   component_version=component_version)
        if fs.count() == 0:
            return render_template('404.html', title='404'), 404
        data_list = Common.collection_creation(fs)
        return render_template("search_results.html", List=data_list,
                               pattern_type=pattern_type, data_display="True")
    if job_name and build_number and component_version:
        fs = extracting_build_info(job_name=job_name, build_number=build_number,
                                   component_version=component_version)
        if fs.count() == 0:
            return render_template('404.html', title='404'), 404
        data_list = Common.collection_creation(fs)
        test_data_map = Common.test_map_details(data_list)
        try:
            pattern_type = re.search(r'\w*-\w*', data_list[0]["Job-Name"]).group()
        except AttributeError:
            pattern_type = job_name

        return render_template("search_results.html", List=data_list,
                               pattern_type=pattern_type, data_display="False",
                               test_data_map=test_data_map)

    return render_template('search.html', form=search_form)


@app.route('/search_by_component',  methods=['GET', 'POST'])
def search_by_component():
    search_form = SearchByField(request.form)
    if request.method == 'POST':
        field_name = search_form.select.data
        field_value = search_form.data['search'].strip()
        fs = extracting_data_by_field(field_name=field_name,
                                      field_value=field_value)
        if fs.count() == 0:
            return render_template('404.html', title='404'), 404
        data_list = Common.collection_creation(fs)
        test_data_map = Common.test_map_details(data_list)
        if test_data_map == 500:
            return render_template('500.html', title='500'), 500
        return render_template("search_results.html", List=data_list,
                               test_data_map=test_data_map)
    return render_template('component_search_by_field.html', search_form=search_form)


@app.route('/report_preparation', methods=['GET', 'POST'])
def upgrade_report():
    form = ReportForm(request.form)
    if request.method == 'POST':
        job_type = "mail_report"
        job_category = (form.data['job_category'].strip()).split(",")
        job_name = (form.data["job_name"].strip()).split(",")
        build_number = (form.data["build_number"].strip()).split(",")
        bugzilla = (form.data["bugzilla"].strip()).split(",")
        recipient_list = form.data["recipient_list"].strip()
        component_version = form.data["component_version"].strip()
        message_body = form.data["message_details"]
        subject = form.data["subject_details"]
        bugzilla = list() if bugzilla == [''] else bugzilla
        common_report = Common.data_preparation_for_report(
            job_category, job_name, bugzilla, build_number)

        for data in common_report:
            try:
                job_details = extracting_build_info(job_name=common_report[data]["job_name"],
                                                    build_number=int(common_report[data]["build_number"]),
                                                    component_version=component_version)
            except ValueError:
                return render_template('500.html', title='500'), 500
            if job_details.count() == 0:
                return render_template('404.html', title='404'), 404

            for job_detail in job_details:
                common_report[data]["Build_Status"] = job_detail["Build-Status"]
                common_report[data]["Build Url"] = job_detail["Job Url"] if "Job Url"\
                                                                   in job_detail else "unavailable"
                common_report[data]["Snap No"] = job_detail["Snap-Version"] \
                    if "Snap-Version" in job_detail else "unavailable"
                try:
                    pattern_type = re.search(r'\w*-\w*', job_detail["Job-Name"]).group()
                except AttributeError:
                    pattern_type = job_detail["Job-Name"]

                if pattern_type in Common.get_config_value("test_map"):
                    highlighted_data = job_detail["Validation"]["Pre_Upgrade_test_Failure"]
                    common_report[data]["highlighted_information"] = highlighted_data
                else:
                    highlighted_data = job_detail["Validation"]["All_Commands_Execution_status"]
                    common_report[data]["highlighted_information"] = \
                        highlighted_data["highlighted_content"] \
                        if "highlighted_content" in \
                           highlighted_data else "unavailable"

                common_report[data]["component_version"] = component_version
        if not message_body:
            common_report["body"] = "Please find the job execution details below"
        else:
            common_report["body"] = message_body
        common_report["subject"] = subject
        common_report["recipient"] = recipient_list
        Common.report_preparation(common_report)
        return render_template('data_processing.html', job_type=job_type)
    return render_template('report_mail.html', form=form)


@app.route('/edit_observation/<pattern_type>/<count>/<id>', methods=['GET', 'POST'])
def edit_observation(pattern_type, id, count):
    fs = accessing_data_via_id(build_id="{}".format(id))
    if fs.count() == 0:
        return render_template('404.html', title='404'), 404
    record = Common.collection_creation(fs)[0]
    form = ObservationUpdate(request.form)
    if request.method == 'POST':
        observations = ast.literal_eval(form.data["observation_data"])
        try:
            if pattern_type not in Common.get_config_value("test_map"):
                if type(observations) is dict:
                    for observation in observations:
                        db_update(observation_record_key="{}".format(observation),
                                  observation_record_value="{}".format(observations[observation]))
                record["Validation"] = \
                    Common.record_updater(record["Validation"], observations)
                update_record("{}".format(id), old_record=record)
            else:
                failed_test_details = {"test_details": record["Validation"]["Pre_Upgrade_test_Failure"]}
                updated_data = Common.record_updater(failed_test_details, observations)
                record["Validation"]["Pre_Upgrade_test_Failure"] = updated_data["test_details"]
                update_record("{}".format(id), old_record=record)
        except Exception:
            flash("Please provide the proper dictionary format {} of pattern {}".
                  format(observations, pattern_type))
            return render_template('observation.html', form=form,
                                   pattern_type=pattern_type, record=record)
        flash("Data Submitted Successfully")
    if type(int(count)/5) is float:
        count = int(int(count)/5) + 1
    else:
        count = int(int(count) / 5)
    return render_template('observation.html', form=form,
                           pattern_type=pattern_type, record=record, count=count)


@app.route('/input', methods=['GET', 'POST'])
def job_process():
    form = ValidatorName(request.form)
    if request.method == 'POST':
        job_processing_type = "log_analysis"
        job_type = form.data['job_type'].strip()
        job_number = form.data['job_number']
        component_not_check = form.data["skip_selection"]
        component_version = form.data["component_version"]
        snap_number = form.data["snap_number"]
        Common.version_update(component_version)
        DataUpdater.build_sheet_update(job_type, job_number,
                                       component_not_check, component_version,
                                       snap_number)
        return render_template('data_processing.html', form=form,
                               job_processing_type=job_processing_type)
    return render_template('analyser_input.html', form=form)


@app.route('/job_list')
def job_list():
    """
    This api help us to get the details of job name, build number and component version.
    :return:
    """
    fs = accessing_all_data()
    if fs.count() == 0:
        return render_template('404.html', title='404'), 404
    records = Common.collection_creation(fs)
    job_records = dict()
    for job in records:
        if job["Job-Name"] not in job_records and ("Build-Number" in job
                                                   and "Build-Version" in job):

            job_records[job["Job-Name"]] = {"Build-Number": [job["Build-Number"]],
                                            "Build-Version": [job["Build-Version"]]}
        elif "Build-Number" in job and "Build-Version" in job:
            job_records[job["Job-Name"]]["Build-Number"].append(job["Build-Number"])
            job_records[job["Job-Name"]]["Build-Version"].append(job["Build-Version"])
    if job_records == dict():
        return render_template('404.html', title='404'), 404
    return render_template("job_name.html", job_records=job_records)


@app.route('/list_of_error/<int:id>')
def list_of_error(id):
    """
    :param id:
    :return:
    """
    per_page = 10
    fs = accessing_observation_db()
    page_list, record = Common.page_common_logic(fs, per_page, id)
    return render_template("observation_error.html", record=record, pages=page_list,
                           index=Common.index_list((per_page * (id - 1)),
                                                   (per_page * (id - 1)) + per_page))


@app.route('/system_log/<id>')
def system_log(id):
    """
    :param report:
    :return:
    """
    fs = accessing_data_via_id(build_id="{}".format(id))
    record = Common.collection_creation(fs)[0]
    return render_template('system_log.html',
                           record=record["SystemLog"],
                           system_log_separation=Common.system_log_separation)


@app.route('/progress/<string:job_type>')
def progress(job_type):
    """
    :param job_type:
    :return:
    """
    if job_type == "log_analysis":
        obj = Controller()
        th1 = Thread(target=obj.run)
    else:
        th1 = Thread(target=Common.mail_send())
    th1.start()
    return Response(Common.generate(th1), mimetype='text/event-stream')


@app.route('/update/<data>')
def update_build_details(data):
    """
    :param data:
    :return:
    """
    if request.method == "PUT":
        pass


@app.route('/delete', methods=["GET", "POST"])
def delete_build_data():
    """
    :param build_id:
    :return:
    """

    search_form = JobSearchForm(request.form)
    if request.method == 'POST':
        job_name = search_form.data['job_name'].strip()
        build_number = search_form.data['build_number']
        component_version = search_form.data["component_version"]
        fs = extracting_build_info(job_name=job_name, build_number=build_number,
                                   component_version=component_version)
        if fs.count() == 0:
            return render_template('404.html', title='404'), 404

        record = Common.collection_creation(fs)[0]
        response_json = delete_record(build_id=record["_id"])
        if response_json.acknowledged:
            flash("Build No {} of Job {} having version {} deleted successfully".
                  format(job_name, build_number, component_version))
        else:
            flash("Failed to delete content")
    return render_template("delete_build.html", form=search_form)


@app.errorhandler(404)
def page_not_found(error):
    """
    :param error:
    :return:
    """
    return render_template("404.html"), 404


@app.errorhandler(503)
def service_not_available(error):
    """

    :param error:
    :return:
    """
    return render_template("503.html"), 503


@app.errorhandler(403)
def service_not_available(error):
    """

    :param error:
    :return:
    """
    return render_template("403.html"), 404


@app.errorhandler(500)
def internal_server_error(error):
    """

    :param error:
    :return:
    """
    return render_template("500.html"), 500


@app.errorhandler(412)
def internal_server_error(error):
    """

    :param error:
    :return:
    """
    return render_template("412.html"), 500
