#########################################
#  Purpose:
#  The Purpose of this tool to analyse the jenkins log and update
#  their results in xls file as well as mongoDB database
#
#
#########################################


import ast
import re
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
        sheet_number = {"Satellite6.4": 0}
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
            "{}/config/{}".format(config.source_file_path, config.build_data_file))

        [self.prop_obj.jobs_list.append(job) for job in job_list]
        jenkins_obj = JenkinsJob()
        for job_attributes in self.prop_obj.jobs_list:
            job_collection = Utils.sub_job_detail()[job_attributes[0]]
            if job_attributes[2]:
                buld_number_collection = job_attributes[2].split(",") \
                    if re.search(r",", str(job_attributes[2])) else [int(job_attributes[2])]
                for build_number, job_name in zip(buld_number_collection, job_collection):
                    self.prop_obj.job_mapper[job_name] = {"build_number": build_number}
                    with jenkins_obj:
                        time_stamp = jenkins_obj.build_execution_time(job_name, build_number)
                        self.prop_obj.job_mapper[job_name]["time_stamp"] = time_stamp
                    self.prop_obj.job_mapper[job_name]["validation_type"] = job_attributes[1]
                    self.prop_obj.job_mapper[job_name]["skip_check"] = ast.literal_eval(job_attributes[3])

            else:
                with jenkins_obj:
                    for job_name in job_collection:
                        build_number, time_stamp = jenkins_obj.get_job_info("{}".format(job_name))
                        self.prop_obj.job_mapper[job_name] = {"build_number": build_number}
                        self.prop_obj.job_mapper[job_name]["time_stamp"] = time_stamp
                        self.prop_obj.job_mapper[job_name]["validation_type"] = job_attributes[1]
                        self.prop_obj.job_mapper[job_name]["skip_check"] = ast.literal_eval(
                            job_attributes[3])
            for job_name in self.prop_obj.job_mapper:
                build_file, build_url = Utils.jenkins_data_collection(
                    job_name, int(self.prop_obj.job_mapper[job_name]["build_number"]))
                self.prop_obj.job_mapper[job_name]["build_file_name"] = build_file
                self.prop_obj.job_mapper[job_name]["build_url"] = build_url

            for job_name in self.prop_obj.job_mapper:
                self.log_analysis(job_name)
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
        result_file_path = config.source_file_path + "/report/" + "report.xls"

        if self.prop_obj.rows_no == 0:
            xls_report = XlsDataParser(result_file_path, XlsDataParser.modeWrite)
            xls_report.open_work_book(result_file_path)
            xls_report.writeRow(0, 0, ["Job-Name", "Build Number", "Failure Message",
                                       "Analysis", "Build Status", "Validation",
                                       "Job Url"], style)
            xls_report.close_work_book()
            self.prop_obj.rows_no = self.prop_obj.rows_no + 1

    def log_analysis(self, job_name):
        """
        This method is used to analyse the logs based on users request, and upload their
        results in mongodb database as well as xls file in report folder.
        :param job_name: name of the job, job_name should be available in
        sub_job.yaml file.

        """
        self.header_of_table()
        build_status = LogAnalyser.ran_job_status(self.prop_obj.job_mapper[job_name]["build_file_name"])
        machine_address = LogAnalyser.machine_details(self.prop_obj.job_mapper[job_name]["build_file_name"])
        upgrade_validation_result = getattr(Validation, '{}'.format(
            self.prop_obj.job_mapper[job_name]["validation_type"]))\
            (machine_address, self.prop_obj.job_mapper[job_name]["build_file_name"],
             self.prop_obj.job_mapper[job_name]["skip_check"]) \
            if self.prop_obj.job_mapper[job_name]["validation_type"] in config.\
            validation_type else Validation.unknown_type()

        upgrade_validation_result.pop("job_name")
        upgrade_validation_result.pop("sub_job")
        job_time_stamp = time.ctime(self.prop_obj.job_mapper[job_name]["time_stamp"])
        xls_report_content = [job_name, self.prop_obj.job_mapper[job_name]["build_number"],
                              build_status, upgrade_validation_result,
                              self.prop_obj.job_mapper[job_name]["time_stamp"]]

        analysis_result = {"Job-Name": job_name,
                           "Build-Number": self.prop_obj.job_mapper[job_name]["build_number"],
                           "Build-Status": build_status,
                           "Validation": upgrade_validation_result,
                           "Job-Time-Stamp": job_time_stamp,
                           "SystemLog": upgrade_validation_result["System_Log"]
                           if "System_Log" in upgrade_validation_result else None,
                           "Job Url": self.prop_obj.job_mapper[job_name]["build_url"]}
        Utils.db_update(analysis_result)
        DataUpdater.test_result_update(self.prop_obj.sheets_number[self.prop_obj.sheets],
                                       self.prop_obj.rows_no, xls_report_content)
