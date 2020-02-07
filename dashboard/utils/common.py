import os
import ast
import re
import json
import xlwt
import time
import yaml
import paramiko
from functools import reduce
from pymongo import MongoClient


class Common:
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
                                       format(Common.config_path, yaml_file_name)),
                                  Loader=yaml.FullLoader)[file_header]))
        return validation_param

    @staticmethod
    def get_config_value(key):
        cfg = Common.validation_param_detail("environment_setup.yaml", "config")
        return reduce(lambda c, k: c[k], key.split('.'), cfg)

    @staticmethod
    def page_common_logic(fs, per_page, id=1):
        """
        This method use by rest service's to publish the record in page wise.
        :param object fs:
        :param int id:
        :return: page_list, data_list, per_page
        """
        requested_record = Common.collection_creation(fs)
        pages = int(len(requested_record) / per_page)
        quot = int(len(requested_record) % per_page)
        if quot != 0:
            pages = pages + 1
        if id == 1:
            page_list = Common.index_list(0, pages)
            data_list = requested_record[0:per_page]
        else:
            page_list = Common.index_list(0, pages)
            data_list = requested_record[
                        (per_page * (id - 1)):(per_page * (id - 1)) + per_page]
        return page_list, data_list

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
        log = Common.combining_alternate_element(satellite_log)
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
                                <th> Job Category </th>
                                <th> Job Name  </th>
                                <th> Job Status </th>
                                <th> Highlighted information</th>
                                <th> Job URL </th>
                                <th> Bugzilla </th>
                                <th> Snap No </th>
                                <th> Component Version </th>
                            </tr>
                        </thead> ''')
        for _ in data:
            fd.write('<tr><td>{}</td><td>{}</td><td>{}</td><td>{}'
                     '</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>'
                     .format(_, data[_]['job_name'], data[_]['Build_Status'],
                             data[_]["highlighted_information"],
                             data[_]['Build Url'], data[_]['bugzilla'],
                             data[_]['Snap No'], data[_]['component_version']))

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
    def db_update(test_data=None, observation_record_key=None, observation_record_value=None):
        """
        This method use to update the log analysis database whenever new record come
        :param dict test_data:
        :param str observation_record_key:
        :param str observation_record_value:
        """
        client = MongoClient()
        if observation_record_key and observation_record_value:
                data_status = Common.check_before_insertion(
                    client, observation_record_key=observation_record_key,
                    observation_record_value=observation_record_value)
        else:
            data_status = Common.check_before_insertion(
                client, build_no=test_data["Build-Number"], job_name=test_data["Job-Name"])
        status = True if data_status else False
        if status:
            return
        if observation_record_key and observation_record_value:
            db = client.observation_record_db
        else:
            db = client.test_database1
        collections = db.files
        if observation_record_key and observation_record_value:
            collections.insert({"{}".format(
                observation_record_key): "{}".format(observation_record_value)})
        else:
            collections.insert(test_data)
        client.close()

    @staticmethod
    def check_before_insertion(mongo_obj, observation_record_key=None,
                               observation_record_value=None, build_no=None, job_name=None):
        """
        This method use to check whether the record present or not and return their
        status.
        :param int build_no:
        :param string job_name:
        :param obj mongo_obj:
        :param str observation_record_key:
        :param str observation_record_value:
        :return: status
        """
        if observation_record_key and observation_record_value:
            db = mongo_obj.observation_record_db
        else:
            db = mongo_obj.test_database1
        collections = db.files
        if observation_record_key and observation_record_value:
            fs = collections.find({"{}".format(observation_record_key):
                                       "{}".format(observation_record_value)})
        else:
            fs = collections.find(
                {'Build-Number': build_no, 'Job-Name': '{}'.format(job_name)})
        status = True if fs.count() > 0 else False
        return status

    @staticmethod
    def environment_preparation():
        """
        This method use to prepare the environment and check the data path exist or not.
        """
        report_file_path = '{}/{}'.format(os.path.abspath('.'),
                                          Common.get_config_value("report_location"))
        data_location_path = '{}/{}'.format(os.path.abspath('.'),
                                            Common.get_config_value("data_location"))

        if '{}'.format(Common.get_config_value("report_location")):
            os.mkdir("{}".format(report_file_path))
            workbook = xlwt.Workbook()
            workbook.add_sheet('test1')
            workbook.save("{}/report.xls".format(report_file_path))
        if '{}'.format(Common.get_config_value("data_location"))\
                not in Common.get_config_value("unsupported_path"):
            try:
                if os.path.isdir("{}".format(data_location_path)):
                    for data_path, directory_list, file_list in \
                            os.walk("{}".format(data_location_path)):
                        [os.remove("{}/{}".format(data_path, file)) for file in file_list]
                else:
                    os.mkdir("{}".format(data_location_path))
            except OSError:
                raise LogException.PATH_NOT_FOUND("FAIL:")
        else:
            raise LogException.PATH_NOT_FOUND("PATH NOT FOUND")


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
            if os.path.isfile("{}/{}".format(Common.config_path, version_update_list[tmp_file])):
                os.remove("{}/{}".format(Common.config_path, version_update_list[tmp_file]))
            status = os.popen("cp {}/{} {}/{}".format(Common.config_path, tmp_file,
                                                      Common.config_path,
                                                      version_update_list[tmp_file]))
            status.close()
            file_name = "{}/{}".format(Common.config_path, version_update_list[tmp_file])
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
            ssh_object.connect("{}".format(hostname), username=username, password=password)
            return ssh_object
        except paramiko.ssh_exception.AuthenticationException:
            return False

    @staticmethod
    def record_updater(records, observations):
        """

        :param records:
        :param observations:
        :return:
        """
        for record in records:
            for observation in observations:
                if observation != "_id":
                    if re.search(observation, "{}".format(records[record])):
                        records[record] = "{}".format(records[record]) + " --> " + \
                                         observations[observation]
        return records
