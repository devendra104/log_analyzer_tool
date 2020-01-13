from lib.utils import Utils
from config import config
from lib.xlsDataParser import *

SHEET_NAME = {'Searching_Pattern': 0, 'Messages_for_Pattern': 0}


class DataUpdater(object):
    @staticmethod
    def test_result_update(sheet_number, row_number, data_list, file_name=None):
        if file_name:
            result_file_path = config.source_file_path + "/config/" + "Build-Job.xls"
        else:
            result_file_path = config.source_file_path + "/report/" + "report.xls"

        xlsObj, wb_copy = XlsDataParser.copy_xls(result_file_path, sheet_number)
        column_number = 0
        for content in data_list:
            xlsObj.write(row_number, column_number, "{}".format(content),
                         XlsDataParser.cell_styles())
            column_number += 1
        wb_copy.save(result_file_path)
        del xlsObj
        del wb_copy

    @staticmethod
    def build_sheet_update(build_job_name, validation_type, job_number=None,
                           component_not_check=None, component_version=None):
        data_list = ["{}".format(build_job_name), "{}".format(validation_type),
                     "{}".format(job_number), "{}".format(component_not_check),
                     "{}".format(component_version)
                     ]
        row_number = 1
        sheet_number = 0
        file_name = "Build-Job_78.xls"
        DataUpdater.test_result_update(sheet_number, row_number, data_list, file_name)

    @staticmethod
    def pattern_collection():
        searching_pattern = DataUpdater.reading_message(
            SHEET_NAME["Messages_for_Pattern"], "{}/config/{}".
            format(config.source_file_path, config.pattern_data))
        return searching_pattern

    @staticmethod
    def message_population():
        error_mapping_messages = \
            DataUpdater.reading_message(SHEET_NAME["Searching_Pattern"], "{}/config/{}".
                                 format(config.source_file_path, config.message_data))
        return error_mapping_messages

    @staticmethod
    def reading_message(sheet_no, configFile):
        with XlsDataParser(configFile) as xslParserObj:
            configData = xslParserObj.readPartialSheet(sheet_no, 1, 1, None, 1)
        message_collection = {}
        for element in configData:
            message_collection["{}".format(element[0])] = "{}".format(element[1])
        return message_collection
