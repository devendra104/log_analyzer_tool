import ast
import re
from flask import Flask, request, render_template, session, Response
from lib.forms import JobSearchForm, ValidatorName, ReportForm, ObservationUpdate
from lib.data_updater import DataUpdater
from lib.data_processing import extracting_build_info, regex_data_retrieval, \
    accessing_data_via_id, delete_record, update_record
from lib.utils import Utils
from threading import Thread
from lib.controller import Controller


app = Flask(__name__)
app.secret_key = 'super secret key'
app.config['SESSION_TYPE'] = 'filesystem1'


@app.route('/log_analysis_dashboard')
def menu():
    return render_template("menu.html")


@app.route('/historical_data_dashboard')
def historical_data_menu():
    job_list = Utils.validation_param_detail("validation_parameter.sample",
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

    fs = regex_data_retrieval(job_name=job_name)
    try:
        pattern_type = re.search(r'\w*-\w*', job_name).group()
    except AttributeError:
        pattern_type = job_name

    page_list, data_list, per_page = Utils.page_common_logic(fs, id)
    return render_template("index_pagination.html", List=data_list,
                           pages=page_list,
                           pattern_type=pattern_type,
                           job_name=job_name,
                           index=Utils.index_list((per_page * (id - 1)),
                                                  (per_page * (id - 1)) + per_page),
                           )


@app.route('/update/<data>')
def update_build_details(data):
    if request.method == "PUT":
        pass


@app.route('/delete/<build_id>')
def delete_build_data(build_id):
    if request.method == "DELETE":
        pass


@app.route('/Build_Search', methods=['GET', 'POST'])
def index():
    search_form = JobSearchForm(request.form)
    if request.method == 'POST':
        job_name = search_form.data['job_name'].strip()
        build_number = search_form.data['build_number']
        component_version = search_form.data["component_version"]

        fs = extracting_build_info(job_name=job_name, build_number=build_number,
                                   component_version=component_version)
        data_list = Utils.collection_creation(fs)
        return render_template("search_results.html", List=data_list)

    return render_template('search.html', form=search_form)


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
        Utils.report_preparation(common_report)
        return render_template('data_processing.html', job_type=job_type)
    return render_template('report_mail.html', form=form)


@app.route('/edit_observation/<pattern_type>/<id>', methods=['GET', 'POST'])
def edit_observation(pattern_type, id):
    fs = accessing_data_via_id(build_id="{}".format(id))
    record = Utils.collection_creation(fs)[0]
    form = ObservationUpdate(request.form)
    if request.method == 'POST':
        try:
            observations = ast.literal_eval(form.data["observation_data"])
            if type(observations) is dict:
                for observation in observations:
                    Utils.db_update(observation_record_key="{}".format(observation),
                                    observation_record_value="{}".
                                    format(observations[observation]))
            record["Validation"]["All_Commands_Execution_status"] = \
                Utils.record_updater(record["Validation"]["All_Commands_Execution_status"],
                                     observations)
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
        Utils.version_update(component_version)
        DataUpdater.build_sheet_update(job_type, job_number,
                                       component_not_check, component_version,
                                       snap_number)
        return render_template('data_processing.html', form=form,
                               job_processing_type=job_processing_type)
    return render_template('analyser_input.html', form=form)


@app.route('/Systemlog/<int:job_number>')
def system_log(job_number):
    build_data = extracting_build_info("Build-Number", job_number)
    build_information = Utils.collection_creation(build_data)
    return render_template('SystemLog.html',
                           build_information=build_information[-1]["SystemLog"],
                           system_log_separation=Utils.system_log_separation)


@app.route('/progress/<string:job_type>')
def progress(job_type):
    if job_type == "log_analysis":
        obj = Controller()
        th1 = Thread(target=obj.run)
    else:
        th1 = Thread(target=Utils.copy_report(session['recipient']))
    th1.start()
    return Response(Utils.generate(th1), mimetype='text/event-stream')


@app.route('/search_helper')
def search_helper():
    return render_template('build_search_helper.html')


@app.route('/analysis_helper')
def analysis_helper():
    return render_template('log_analysis_help.html')


@app.route('/report_helper')
def report_helper():
    return render_template('upgrade_report_preparation_helper.html')


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template("500.html"), 500
