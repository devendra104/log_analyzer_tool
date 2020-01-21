import ast
import re
from flask import Flask, request, render_template, session, Response
from lib.forms import JobSearchForm, ValidatorName, ReportForm, ObservationUpdate
from lib.data_updater import DataUpdater
from lib.data_processing import extracting_build_info
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
    return render_template("build_history_menu.html")


@app.route('/evaluated_data_history/Job-Name/satellite_and_capsule_upgrade')
def upgrade_data_menu():
    return render_template('upgrade_data.html')


@app.route('/evaluated_data_history/<search_type>/<search_from>/<int:id>')
def pagination(id, search_type, search_from):
    fs = extracting_build_info(search_type, search_from)
    try:
        pattern_type = re.search(r'\w*-\w*', search_from).group()
    except AttributeError:
        pattern_type = search_from
    page_list, data_list, per_page = Utils.page_common_logic(fs, id)
    return render_template("index_pagination.html", List=data_list,
                           pages=page_list,
                           pattern_type=pattern_type,
                           search_type=search_type,
                           search_from=search_from,
                           index=Utils.index_list((per_page * (id - 1)),
                                                  (per_page * (id - 1)) + per_page))


@app.route('/search/<int:id>/<data_selection>/<search_string>')
def search_results(id, data_selection, search_string):
    if data_selection == "Build-Number":
        fs = extracting_build_info(search_type=data_selection,
                                   data_selection=int(search_string))
    else:
        fs = extracting_build_info(search_type=data_selection,
                                   data_selection=search_string)

    page_list, data_list, per_page = Utils.page_common_logic(fs, id)
    return render_template("search_results.html", List=data_list,
                           pages=page_list,
                           index=Utils.index_list((per_page * (id - 1)),
                                            (per_page * (id - 1)) + per_page),
                           data_selection=data_selection,
                           search_string=search_string)


@app.route('/Build_Search', methods=['GET', 'POST'])
def index():
    search = JobSearchForm(request.form)
    if request.method == 'POST':
        search_string = search.data['search'].strip()
        session["data_selection"] = search_string
        session["search_type"] = search.select.data
        search_string = int(search_string) if search_string.isdigit() \
            else search_string
        fs = extracting_build_info(search_type=search.select.data,
                                   data_selection=search_string)
        page_list, data_list, per_page = Utils.page_common_logic(fs)
        return render_template("search_results.html", List=data_list,
                               pages=page_list,
                               index=Utils.index_list((per_page * (1 - 1)),
                                                      (per_page * (1 - 1)) + per_page),
                               search_string=search_string,
                               data_selection=search.select.data)

    return render_template('search.html', form=search)


@app.route('/report_preparation', methods=['GET', 'POST'])
def upgrade_report():
    common_report = {}
    report_form = ReportForm(request.form)
    if request.method == 'POST':
        job_type = "mail_report"
        customer_name = report_form.customer.data.split(',')
        build_no = report_form.build_no.data.split(',')
        snap = report_form.snap_no.data.split(',')
        bug = report_form.bugzilla.data.split(',')
        recipient_name = report_form.recipient.data.split(',')
        session["recipient"] = recipient_name
        for j in range(len(customer_name)):
            common_report[customer_name[j]] = {'Build': build_no[j],
                                               'Bugzilla': bug[j], 'Snap_No': snap[j]}
        for data in common_report:
            data1 = extracting_build_info('Build-Number',
                                          int(common_report[data]["Build"]))
            for i in data1:
                common_report[data]["Build_Status"] = i["Build-Status"]
                common_report[data]["Build Url"] = i["Job Url"] if "Job Url"\
                                                                   in i else "unavailable"
                print(common_report[data]["Build Url"])
        Utils.report_preparation(common_report)
        return render_template('data_processing.html', job_type=job_type)
    return render_template('report_mail.html', report_form=report_form)


@app.route('/edit_observation/<pattern_type>/<id>', methods=['GET', 'POST'])
def edit_observation(pattern_type, id):
    fs = extracting_build_info(search_type="_id", data_selection="{}".format(id))
    record = Utils.collection_creation(fs)
    form = ObservationUpdate(request.form)
    if request.method == 'POST':
        try:
            observations = ast.literal_eval(form.data["observation_data"])
            if type(observations) is dict:
                for observation in observations:
                    Utils.db_update(observation_record_key="{}".format(observation),
                                    observation_record_value="{}".
                                    format(observations[observation]))
                    print(observation)
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
        job_type = "log_analysis"
        job_name = form.data['job_name'].strip()
        validation_type = form.data['validator_selection'].strip()
        job_number = form.data['job_number']
        component_not_check = form.data["skip_selection"]
        component_version = form.data["component_version"]
        snap_number = form.data["snap_number"]
        Utils.version_update(component_version)
        DataUpdater.build_sheet_update(job_name, validation_type, job_number,
                                       component_not_check, component_version,
                                       snap_number)
        return render_template('data_processing.html', form=form, job_type=job_type)
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
