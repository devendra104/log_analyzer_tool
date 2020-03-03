import os
import ast
import re
import json
import pickle
import xlwt
import time
import yaml
import paramiko
from functools import reduce


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
        report_file_path = '{}/{}'.format(os.path.abspath('.'),
                                          Common.get_config_value("report_location"))
        fd = open("{}/mail_report.html".format(report_file_path), "w")
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
                    ''')
        fd.write('''
            <p><font color="black">{}
                </font></p>
                    <table>
                        <thead>
                            <tr>
                                <th> Job Category </th>
                                <th> Job Status </th>
                                <th> Highlighted information/Test Failure</th>
                                <th> Job URL </th>
                                <th> Bugzilla </th>
                                <th> Snap No </th>
                                <th> Component Version </th>
                                <th> Warning And Alert Details </th>
                                </tr></thead> '''.format(data["body"]))
        data.pop('body')
        report_file_path = '{}/{}'.format(os.path.abspath('.'),
                                          Common.get_config_value("report_location"))

        if os.path.isfile("{}/{}".format(report_file_path, "subject")):
            os.remove("{}/{}".format(report_file_path, "subject"))
        if os.path.isfile("{}/{}".format(report_file_path, "recipient")):
            os.remove("{}/{}".format(report_file_path, "recipient"))
        with open("{}/{}".format(report_file_path, "subject"), "wb") as handler:
            pickle.dump(data["subject"], handler)
        data.pop("subject")

        with open("{}/{}".format(report_file_path, "recipient"), "wb") as handler:
            pickle.dump(data["recipient"], handler)
        data.pop('recipient')

        for _ in data:
            fd.write('<tr><td>{}</td><td>{}</td>'.format(_, data[_]['Build_Status']))
            fd.write("<td>")
            for content in data[_]["highlighted_information"]:
                if (content.lstrip()).rstrip():
                    fd.write("<li align=\"left\">{}</li>".format((content.lstrip()).rstrip()))
            fd.write("</td>")
            fd.write("<td><a href={}>Job Link</a></td>".format(data[_]['Build Url']))
            if data[_]['bugzilla'].lstrip().rstrip():
                fd.write("<td><a href=https://bugzilla.redhat.com/show_bug.cgi?id={}>Bugzilla_link</a></td>".format(data[_]['bugzilla']))
            else:
                fd.write("<td>{}</a></td>".format(data[_]['bugzilla']))

            fd.write("<td>{}</td><td>{}</td>".format(data[_]['Snap No'],
                                                          data[_]['component_version']))
            fd.write("<td><a href=http://{}:5001/build_search/{}/{}/{}>Other details</a></td></tr>"
                     .format(Common.get_config_value("build_server_hostname"), data[_]['job_name'],
                             data[_]['build_number'], data[_]['component_version']))

        fd.write('''<tfoot> 
                            <tr> 
                                <th colspan="10"> redhat.com </th> 
                            </tr> 
                    </tfoot>
                </table>
                
            </body>
            <p><font color="black">Note: For more details</font></p>
            <form action="https://mojo.redhat.com/docs/DOC-1207508"><input type="submit" value="Mojo Page" /></form>
            <p><font color="black">Thanks</font></p>
            <font color="black">Upgrade Team</font>
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
    def mail_send():
        """
        This method use to copy the report to the mail server.
        """
        report_file_path = '{}/{}'.format(os.path.abspath('.'),
                                          Common.get_config_value("report_location"))
        with open("{}/{}".format(report_file_path, "subject"), "rb") as subject_handler:
            subject = pickle.load(subject_handler)
        with open("{}/{}".format(report_file_path, "recipient"), "rb") as recipient_handler:
            recipient = pickle.load(recipient_handler)
        report_file_path = '{}/{}'.format(os.path.abspath('.'),
                                          Common.get_config_value("report_location"))
        if os.path.isfile("{}/mail_report.html".format(report_file_path)):
            os.popen("ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@{} {}/{} {} {}".\
                     format(Common.get_config_value("build_server_hostname"),
                            Common.get_config_value("mail_script_location"),
                            Common.get_config_value("mail_script_name"),
                            subject, recipient))

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
            if os.path.isdir("{}".format(report_file_path)):
                for data_path, directory_list, file_list in \
                        os.walk("{}".format(report_file_path)):
                    [os.remove("{}/{}".format(report_file_path, file))
                     for file in file_list]
            else:
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
        version_update_list = {"validation_parameter.sample": "validation_parameter.yaml"
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
            try:
                record = ast.literal_eval(records[record])
            except Exception:
                record = record
            if type(records[record]) is dict:
                records[record] = Common.record_updater(records[record], observations)

            elif type(records[record]) is list:
                list_records = []
                for list_record in records[record]:
                    for observation in observations:
                        if observation != "_id":
                            if re.search(observation, "{}".format(list_record)):
                                if not re.search(observations[observation],
                                                 "{}".format(records[record])):
                                    list_records.append("{}".format(list_record) + " --> " +
                                                        observations[observation])
                                else:
                                    list_records.append(list_record)
                            else:
                                list_records.append(list_record)
                records[record] = list_records
            else:
                for observation in observations:
                    if observation != "_id":
                        if re.search(observation, "{}".format(records[record])):
                            if not re.search(observations[observation], "{}".format(records[record])):
                                records[record] = "{}".format(records[record]) + " --> " + \
                                                observations[observation]
        return records

    @staticmethod
    def json_validator(form_object):
        """
        :param form_object:
        :return:
        """
        try:
            if ast.literal_eval(form_object.data["observation_data"]):
                return True
        except Exception:
            return False

    @staticmethod
    def data_preparation_for_report(job_category, job_name, bugzilla, build_number):
        common_report = dict()
        if len(job_category) == len(job_name) == len(bugzilla):
            for job_no in range(len(job_category)):
                common_report[job_category[job_no]] = {"job_name": job_name[job_no],
                                                       "build_number": build_number[job_no],
                                                       "bugzilla": bugzilla[job_no]}
        elif len(bugzilla) == 0 and (len(job_category) == len(job_name)):
            for job_no in range(len(job_category)):
                common_report[job_category[job_no]] = {"job_name": job_name[job_no],
                                                       "build_number": build_number[job_no],
                                                       "bugzilla": ""}
        else:
            for job_no in range(len(job_category)):
                try:
                    common_report[job_category[job_no]] = {"job_name": job_name[job_no]}
                    temp = job_no
                except IndexError:
                    common_report[job_category[job_no]] = {"job_name": job_name[temp]}

            for job_no in range(len(job_category)):
                try:
                    common_report[job_category[job_no]]["build_number"] = build_number[job_no]
                    temp = job_no
                except IndexError:
                    common_report[job_category[job_no]]["build_number"] = build_number[temp]

            for job_no in range(len(job_category)):
                try:
                    common_report[job_category[job_no]]["bugzilla"] = bugzilla[job_no]
                    temp = job_no
                except IndexError:
                    common_report[job_category[job_no]]["bugzilla"] = bugzilla[temp]
        return common_report

    @staticmethod
    def test_map_details(data_list):
        test_data_map = list()
        test_map = Common.get_config_value("test_map")
        for job_name in data_list:
            try:
                job_prefix = re.search(r'\w*-\w*', job_name["Job-Name"]).group()
            except Exception:
                job_prefix = job_name["Job-Name"]
            if job_prefix in test_map:
                test_data_map.append(job_name["Job-Name"])
        return test_data_map
