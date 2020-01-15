import ast
import re
import json
import time
import yaml
import paramiko
from functools import reduce
from lib.jenkinsjob import *
from pymongo import MongoClient


class Utils:
    config_path = os.path.join(os.path.abspath("."), "config")
    if not os.path.exists(config_path):
        config_path = os.path.join(os.path.abspath("."), "config")

    @staticmethod
    def validation_param_detail(yaml_file_name, file_header):
        """
        This method use to convert the validation_parameter yaml file in to dictionary.
        :return: validation_param
        """
        validation_param = ast.literal_eval\
            (json.dumps(yaml.load(open("{}/{}".\
                                       format(Utils.config_path, yaml_file_name)),
                                  Loader=yaml.FullLoader)[file_header]))
        return validation_param

    @staticmethod
    def get_config_value(key):
        cfg = Utils.validation_param_detail("environment_setup.yaml", "config")
        return reduce(lambda c, k: c[k], key.split('.'), cfg)

    @staticmethod
    def page_common_logic(fs, id=1):
        """
        This method use by rest service's to publish the record in page wise.
        :param objetc fs:
        :param int id:
        :return: page_list, data_list, per_page
        """
        per_page = 5
        requested_record = Utils.collection_creation(fs)
        print(requested_record)
        pages = int(len(requested_record) / per_page)
        quot = int(len(requested_record) % per_page)
        if quot != 0:
            pages = pages + 1
        if id == 1:
            page_list = Utils.index_list(0, pages)
            data_list = requested_record[0:5]
        else:
            page_list = Utils.index_list(0, pages)
            data_list = requested_record[
                        (per_page * (id - 1)):(per_page * (id - 1)) + per_page]
        return page_list, data_list, per_page

    @staticmethod
    def collection_creation(record_object):
        """
        This method use to create the collection of user requested data(system log).
        :param obj record_object:
        :return:
        """
        record = [rec_ob for rec_ob in record_object]
        return record

    @staticmethod
    def index_list(page, per_page):
        """
        This method use by rest services to create the index list
        :param int page:
        :param int per_page:
        :return: page_index
        """
        page_index = []
        for i in range(page + 1, per_page + 1):
            page_index.append(i)
        return page_index

    @staticmethod
    def combining_alternate_element(log):
        """
        This method use to collect the record from the system logs,
        the odd selection help to remove the null after every time slots.
        example: [DEBUG 2019-08-25T15:19:18 main] Hook /usr/sh
        combine result.
        :param list log:

        :return:log_list
        """
        log_list = []
        count = 0
        temp = ""
        for content in log:
            if count % 2 == 0:
                temp = content
            else:
                temp = temp + content
                log_list.append(temp)
                temp = ""
            count += 1
        return log_list

    @staticmethod
    def system_log_separation(log_type, log):
        """
        This method use to divide the logs string by using some regex logic that helps
        to manage the logs with starting time stamp string.

        :param str log_type: System log type
        :param str log: huge log string.
        :return: log
        """
        satellite_log = []
        if log_type == "satellite-log":
            satellite_log = re.split(r'(\[DEBUG \d*-\d*-\d*\w\d*:\d*:\d* \w*\])', log)
        elif (log_type == "messages") or (log_type == "candelpin-log"):
            satellite_log = re.split(r'(\w{1,3} \d{1,2} \d{1,2}:\d{1,2}:\d{1,2})', log)
        if satellite_log:
            satellite_log.pop(0)
        log = Utils.combining_alternate_element(satellite_log)
        return log

    @staticmethod
    def report_preparation(data):
        """
        This method use to prepare the log based on users request.
        :param dict data:
        """
        fd = open("mail_report.html", "w")
        fd.write('''
            <html>
                <head>
                    <meta http-equiv="Content-Type" content="text/html charset=UTF-8" />
                        <style>
                            table {
                                font-family: arial, sans-serif;
                                border-collapse: collapse;
                                width: 100%;
                            }
        
                            th {
                                border: 1px solid #000000;
                                text-align: center;
                                padding: 8px;
                                background-color: #7598bf;
                                color:#000000
        
                            }
                            td {
                                border: 1px solid #000000;
                                text-align: center;
                                padding: 8px;
                                background-color: #dbe5f0;
                                color:#000000
        
                            }
                        </style>
                    </head>
        
                <body>
                    <p><font color="black"> Hi All </font></p>
                    <p><font color="black"> Installer succeeded while upgrading the 
                    following 6.5 DB's to 6.6 snap1. 
                    Please see the job links below for more details:
                    </font></p>
                    <table>
                        <thead>
                            <tr>
                                <th> Customer Name </th>
                                <th> Upgrade URL </th>
                                <th> Upgrade Status</th>
                                <th> Bugzilla </th>
                                <th> Snap No </th>
                            </tr>
                        </thead> ''')
        for _ in data:
            fd.write('<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>'
                     .format(_, data[_]['Build Url'], data[_]['Build_Status'],
                             data[_]['Bugzilla'], data[_]['Snap_No']))
        fd.write('''<tfoot> 
                            <tr> 
                                <th colspan="10"> redhat.com </th> 
                            </tr> 
                    </tfoot>
                </table>
            </body>
        </html>
        ''')
        fd.close()

    @staticmethod
    def generate(th1):
        """
        This method use to mange the progress of data by rest api.
        :param obj th1: thread object
        """
        pro = 1
        while True:
            if th1.is_alive() and pro < 99:
                pro = pro + 1
                time.sleep(1)
                yield "data:" + str(pro) + "\n\n"
            else:
                if not th1.is_alive():
                    yield "data:" + str(100) + "\n\n"

    @staticmethod
    def copy_report(recipients):
        """
        This method use to copy the report to the mail server.
        :param recipients:
        :return:
        """
        file_path = "mail_report.html"
        if os.path.isfile("{}".format(file_path)):
            commands = "scp -r {} root@zyz.com:~"\
                .format(file_path)
            result = os.popen("{}".format(commands))
            time.sleep(2)
            if result:
                for recipient in recipients:
                    os.popen("ssh root@xyz.com sh test.sh {}"
                             .format(recipient))

    @staticmethod
    def db_update(test_data):
        """
        This method use to update the log analysis database whenever new record come
        :param dict test_data:
        """
        client = MongoClient()
        data_status = Utils.check_before_insertion(test_data["Build-Number"],
                                                   test_data["Job-Name"], client)
        status = True if data_status else False
        if status:
            return
        db = client.test_database1
        collections = db.files
        collections.insert(test_data)
        client.close()

    @staticmethod
    def check_before_insertion(build_no, job_name, mongo_obj):
        """
        This method use to check whether the record present or not and return their
        status.
        :param int build_no:
        :param string job_name:
        :param obj mongo_obj:
        :return: status
        """
        db = mongo_obj.test_database1
        collections = db.files
        fs = collections.find(
            {'Build-Number': build_no, 'Job-Name': '{}'.format(job_name)})
        status = True if fs.count() > 0 else False
        return status

    @staticmethod
    def environment_preparation():
        """
        This method use to prepare the environment and check the data path exist or not.
        """
        if '{}'.format(Utils.get_config_value("data_location"))\
                not in Utils.get_config_value("unsupported_path"):
            try:
                if os.path.isdir('{}/{}'.format(os.path.abspath('.'),
                                                Utils.get_config_value("data_location"))):
                    for data_path, directory_list, file_list in \
                            os.walk("{}/{}".format(os.path.abspath('.'),
                                                   Utils.get_config_value("data_location"))):
                        [os.remove("{}/{}".format(data_path, file)) for file in file_list]
                else:
                    os.mkdir('{}/{}'.format(os.path.abspath('.'),
                                            Utils.get_config_value("data_location")))
            except OSError:
                raise LogException.PATH_NOT_FOUND("FAIL:")
        else:
            raise LogException.PATH_NOT_FOUND("PATH NOT FOUND")

    @staticmethod
    def jenkins_data_collection(job_name, job_number):
        """
        This method use to prepare the environment to download the requested log from
        jenkins job.
        :param str job_name: name of the requested job
        :param int job_number: build number of the requested job
        :return: file_name, download_console_log_url
        """
        try:
            jenkins_obj = JenkinsJob()
            if type(job_number) is int:
                download_console_log_url = "{}/job/{}/{}/consoleFull". \
                    format(Utils.get_config_value("jenkins_base_url"), job_name, job_number)
                file_name = jenkins_obj.download_the_logs(download_console_log_url,
                                                          job_name)
                if file_name:
                    return file_name, download_console_log_url
                else:
                    return False
        except Exception as err:
            print("Timeout error come: {}".format(err))

    @staticmethod
    def version_update(component_version):
        """
        This method use to build the sub_job and validation_parameter yaml file as per
         the version request.
        :param str component_version: version name of the build job,
        it would be like 6.0, 6.5 etc
        """
        version_update_list = {"sub_job.sample": "sub_job.yaml",
                               "validation_parameter.sample": "validation_parameter.yaml"
                               , "machine_detail.sample": "machine_detail.yaml"}
        command = "sed -i 's/<component-version>/{}/'".format(component_version)
        for tmp_file in version_update_list:
            if os.path.isfile("{}/{}".format(Utils.config_path, version_update_list[tmp_file])):
                os.remove("{}/{}".format(Utils.config_path, version_update_list[tmp_file]))
            status = os.popen("cp {}/{} {}/{}".format(Utils.config_path, tmp_file,
                                                      Utils.config_path,
                                                      version_update_list[tmp_file]))
            status.close()
            file_name = "{}/{}".format(Utils.config_path, version_update_list[tmp_file])
            status = os.popen("{} {}".format(command, file_name))
            status.close()

    @staticmethod
    def ssh_connection_handling(ssh_object, hostname, username, password):
        """
        This method use to create the connection object as per users request.
        :param obj ssh_object:
        :param str hostname: hostname of the build machine
        :param str username: username of the build machine
        :param str password: password of th build machine
        :return: ssh_object, bool value
        """
        try:
            ssh_object.connect("".format(hostname), username=username, password=password)
            return ssh_object
        except paramiko.ssh_exception.AuthenticationException:
            return False
