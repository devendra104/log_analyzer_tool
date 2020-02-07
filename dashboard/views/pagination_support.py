import ast
import re

from flask import Flask, request, render_template, session, Response
from views.build import JobSearchForm, ValidatorName, ReportForm, ObservationUpdate, SearchByField
from utils.data_updater import DataUpdater
from utils.db import extracting_build_info, regex_data_retrieval, \
    accessing_data_via_id, delete_record, update_record, extracting_data_by_field, accessing_observation_db
from utils.common import Common
from threading import Thread
from utils.controller import Controller


app = Flask(__name__, template_folder='../templates', static_url_path='',
            static_folder='/home/desingh/Satellite-QE/Log_Analyszer/app/dashboard/static')
app.secret_key = 'super secret key'
app.config['SESSION_TYPE'] = 'filesystem1'


@app.route('/log_analysis_dashboard')
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


@app.route('/Build_Search', methods=['GET', 'POST'])
def index():
    search_form = JobSearchForm(request.form)
    if request.method == 'POST':
        job_name = search_form.data['job_name'].strip()
        build_number = search_form.data['build_number']
        component_version = search_form.data["component_version"]

        fs = extracting_build_info(job_name=job_name, build_number=build_number,
                                   component_version=component_version)
        data_list = Common.collection_creation(fs)
        return render_template("search_results.html", List=data_list)

    return render_template('search.html', form=search_form)


@app.route('/search_by_component',  methods=['GET', 'POST'])
def search_by_component():
    search_form = SearchByField(request.form)
    if request.method == 'POST':
        field_name = search_form.select.data
        field_value = search_form.data['search'].strip()
        fs = extracting_data_by_field(field_name=field_name,
                                      field_value=field_value)
        data_list = Common.collection_creation(fs)
        return render_template("search_results.html", List=data_list)
    return render_template('component_search_by_field.html', search_form=search_form)


@app.route('/report_preparation', methods=['GET', 'POST'])
def upgrade_report():
    common_report = {}
    form = ReportForm(request.form)
    if request.method == 'POST':
        job_type = "mail_report"
        job_category = (form.data['job_category'].strip()).split(",")
        job_name = (form.data["job_name"].strip()).split(",")
        build_number = (form.data["build_number"].strip()).split(",")
        bugzilla = (form.data["bugzilla"].strip()).split(",")
        recipient_list = form.data["recipient_list"].strip()
        component_version = form.data["component_version"].strip()
        for job_no in range(len(job_category)):
            common_report[job_category[job_no]] = {"job_name": job_name[job_no],
                                                   "build_number": build_number[job_no],
                                                   "bugzilla": bugzilla[job_no]}

        for data in common_report:
            job_details = extracting_build_info(job_name=common_report[data]["job_name"],
                                                build_number=int(common_report[data]["build_number"]),
                                                component_version=component_version)
            for job_detail in job_details:
                common_report[data]["Build_Status"] = job_detail["Build-Status"]
                common_report[data]["Build Url"] = job_detail["Job Url"] if "Job Url"\
                                                                   in job_detail else "unavailable"
                common_report[data]["Snap No"] = job_detail["Snap-Version"] \
                    if "Snap-Version" in job_detail else "unavailable"
                common_report[data]["highlighted_information"] = job_detail["highlighted_information"]\
                    if "highlighted_information" in job_detail else "unavailable"

                common_report[data]["recipient_list"] = recipient_list
                common_report[data]["component_version"] = component_version
        Common.report_preparation(common_report)
        return render_template('data_processing.html', job_type=job_type)
    return render_template('report_mail.html', form=form)


@app.route('/edit_observation/<pattern_type>/<id>', methods=['GET', 'POST'])
def edit_observation(pattern_type, id):
    fs = accessing_data_via_id(build_id="{}".format(id))
    record = Common.collection_creation(fs)[0]
    form = ObservationUpdate(request.form)
    if request.method == 'POST':
        try:
            observations = ast.literal_eval(form.data["observation_data"])
            if type(observations) is dict:
                for observation in observations:
                    Common.db_update(observation_record_key="{}".format(observation),
                                     observation_record_value="{}".
                                     format(observations[observation]))
            record["Validation"]["All_Commands_Execution_status"] = \
                Common.record_updater(
                    record["Validation"]["All_Commands_Execution_status"], observations)
            update_record("{}".format(id), old_record=record)
        except UnboundLocalError:
            pass
    if pattern_type in ["automation-preupgrade", "automation-postupgrade"]:
        return render_template('observation.html', form=form,
                               pattern_type=pattern_type, record=record)
    else:
        return render_template('observation.html', form=form,
                               pattern_type=pattern_type, record=record)


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


@app.route('/list_of_error/<int:id>')
def list_of_error(id):
    per_page = 10
    fs = accessing_observation_db()
    page_list, record = Common.page_common_logic(fs, per_page, id)
    return render_template("observation_error.html", record=record, pages=page_list,
                           index=Common.index_list((per_page * (id - 1)),
                                                   (per_page * (id - 1)) + per_page))


@app.route('/system_log/<id>')
def system_log(id):
    fs = accessing_data_via_id(build_id="{}".format(id))
    record = Common.collection_creation(fs)[0]
    return render_template('system_log.html',
                           record=record["SystemLog"],
                           system_log_separation=Common.system_log_separation)


@app.route('/progress/<string:job_type>')
def progress(job_type):
    if job_type == "log_analysis":
        obj = Controller()
        th1 = Thread(target=obj.run)
    else:
        th1 = Thread(target=Common.copy_report(session['recipient']))
    th1.start()
    return Response(Common.generate(th1), mimetype='text/event-stream')


@app.route('/update/<data>')
def update_build_details(data):
    if request.method == "PUT":
        pass


@app.route('/delete/<build_id>')
def delete_build_data(build_id):
    if request.method == "DELETE":
        pass


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template("500.html"), 500
