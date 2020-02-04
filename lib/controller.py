#########################################
#  Purpose:
#  The Purpose of this tool to analyse the jenkins log and update
#  their results in xls file as well as mongoDB database
#
#
#########################################


import ast
import time
from lib.xlsDataParser import *
from lib.jenkinsjob import *
from lib.logparser import LogAnalyser
from lib.data_updater import DataUpdater
from lib.validation import Validation
from lib.utils import Utils
from lib.system_properties import SystemProperties


class Controller:
    def __init__(self):
        self.prop_obj = SystemProperties()

    def run(self):
        """
        This method is used to trigger the main method and perform the cleanup of all
        properties
        :return:
        """
        sheet_number = {"Sheet_1": 0}
        Utils.environment_preparation()
        for sheet in sheet_number.keys():
            row_no = 0
            self.prop_obj.sheets_number = sheet_number
            self.prop_obj.rows_no = row_no
            self.prop_obj.sheets = sheet
            self.mapper_builder()
            del self.prop_obj.rows_no
            del self.prop_obj.job_mapper
            del self.prop_obj.jobs_list
            del self.prop_obj.sheets_number
            del self.prop_obj.sheets

    def mapper_builder(self):
        """
        This function is used to build the job mapper object and trigger the
        log analysis module to analyse the data on the basis of downloaded logs.
        :return:
        """
        job_list = Controller.reading_input_data_from_xls(
            self.prop_obj.sheets_number[self.prop_obj.sheets],
            "{}/config/{}".format(os.path.abspath('.'),
                                  Utils.get_config_value("analysis_input_file")))
        [self.prop_obj.jobs_list.append(job) for job in job_list]
        jenkins_obj = JenkinsJob()
        for job_attributes in self.prop_obj.jobs_list:
            validation_data = Utils.validation_param_detail\
            ("validation_parameter.yaml", "jenkins_job_details")[job_attributes[0]]
            if job_attributes[1]:
                build_numbers = job_attributes[1].split(',')
                for build_number in build_numbers:
                    with jenkins_obj:
                        time_stamp = jenkins_obj.build_execution_time(validation_data["job_name"], build_number)
                        self.prop_obj.job_mapper[build_number] = {}
                        self.prop_obj.job_mapper[build_number]["time_stamp"] = time_stamp
                        self.prop_obj.job_mapper[build_number][
                            "skip_check"] = ast.literal_eval(job_attributes[2])
                        self.prop_obj.job_mapper[build_number]["build_version"] = job_attributes[3]
                        self.prop_obj.job_mapper[build_number]["snap_no"] = job_attributes[4]
            else:
                with jenkins_obj:
                    build_number, time_stamp = jenkins_obj.get_job_info("{}".format(validation_data["job_name"]))
                    self.prop_obj.job_mapper[build_number] = {}
                    self.prop_obj.job_mapper[build_number]["time_stamp"] = time_stamp
                    self.prop_obj.job_mapper[build_number]["skip_check"] = ast.literal_eval(
                        job_attributes[3])
                    self.prop_obj.job_mapper[build_number]["build_version"] = \
                        job_attributes[4]
                    self.prop_obj.job_mapper[build_number]["snap_no"] = job_attributes[5]

            for build_number in self.prop_obj.job_mapper:
                build_file, build_url = JenkinsJob.jenkins_data_collection(
                    validation_data["job_name"], int(build_number))
                self.prop_obj.job_mapper[build_number]["build_file_name"] = build_file
                self.prop_obj.job_mapper[build_number]["build_url"] = build_url

            for build_number in self.prop_obj.job_mapper:
                self.log_analysis(build_number, validation_data)
                self.prop_obj.rows_no += 1

    @staticmethod
    def reading_input_data_from_xls(sheet_no, conf_data):
        """
        This method use to read the data from xls file updated by users.
        :param int sheet_no:
        :param str conf_data:
        :return:
        """

        with XlsDataParser(conf_data) as xslParserObj:
            conf_data = xslParserObj.readPartialSheet(sheet_no, 1, 0, None)
        return conf_data

    def header_of_table(self):
        """
        This method use to create the header data in report file.
        """
        style = XlsDataParser.font(True)
        result_file_path = os.path.abspath('.') + "/report/" + \
                           Utils.get_config_value("analysis_output_file")

        if self.prop_obj.rows_no == 0:
            xls_report = XlsDataParser(result_file_path, XlsDataParser.modeWrite)
            xls_report.open_work_book(result_file_path)
            xls_report.writeRow(0, 0, ["Job-Name", "Build Number"
                                       "Build Status", "Validation",
                                       "Build Time"], style)
            xls_report.close_work_book()
            self.prop_obj.rows_no = self.prop_obj.rows_no + 1

    def log_analysis(self, build_number, validation_data):
        """
        This method is used to analyse the logs based on users request, and upload their
        results in mongodb database as well as xls file in report folder.
        :param int build_number:
        :param dict validation_data:
        """
        self.header_of_table()
        job_file_name = self.prop_obj.job_mapper[build_number]["build_file_name"]
        build_status = LogAnalyser.ran_job_status(job_file_name)
        machine_address = LogAnalyser.machine_details(job_file_name)

        upgrade_validation_result = Validation.job_analysis(validation_data, job_file_name, machine_address,
                                    self.prop_obj.job_mapper[build_number]["skip_check"])

        job_time_stamp = time.ctime(self.prop_obj.job_mapper[build_number]["time_stamp"])
        xls_report_content = [validation_data["job_name"], build_number,
                              build_status, upgrade_validation_result,
                              self.prop_obj.job_mapper[build_number]["time_stamp"]]

        analysis_result = {"Job-Name": validation_data["job_name"],
                           "Build-Number": build_number,
                           "Build-Status": build_status,
                           "Validation": upgrade_validation_result,
                           "Job-Time-Stamp": job_time_stamp,
                           "Build-Version" : self.prop_obj.job_mapper[build_number]["build_version"],
                           "Snap-Version" : self.prop_obj.job_mapper[build_number]["snap_no"],
                           "SystemLog": upgrade_validation_result["System_Log"]
                           if "System_Log" in upgrade_validation_result else None,
                           "Job Url": self.prop_obj.job_mapper[build_number]["build_url"]}
        Utils.db_update(analysis_result)
        DataUpdater.test_result_update(self.prop_obj.sheets_number[self.prop_obj.sheets],
                                       self.prop_obj.rows_no, xls_report_content)
