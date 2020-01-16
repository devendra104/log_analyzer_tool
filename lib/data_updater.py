from lib.utils import Utils
from lib.xlsDataParser import *

SHEET_NAME = {'Searching_Pattern': 0, 'Messages_for_Pattern': 0}


class DataUpdater(object):
    @staticmethod
    def test_result_update(sheet_number, row_number, data_list,
                           analysis_file_update=False):
        if analysis_file_update:
            result_file_path = os.path.abspath('.') + "/config/" + \
                               Utils.get_config_value("analysis_input_file")
        else:
            result_file_path = os.path.abspath('.') + "/report/" + \
                               Utils.get_config_value("analysis_output_file")

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
                           component_not_check=None, component_version=None,
                           snap_number=None):
        data_list = ["{}".format(build_job_name), "{}".format(validation_type),
                     "{}".format(job_number), "{}".format(component_not_check),
                     "{}".format(component_version), "{}".format(snap_number)
                     ]
        row_number = 1
        sheet_number = 0
        DataUpdater.test_result_update(sheet_number, row_number, data_list,
                                       analysis_file_update=True)

    @staticmethod
    def pattern_collection():
        searching_pattern = DataUpdater.reading_message(
            SHEET_NAME["Messages_for_Pattern"], "{}/config/{}".
            format(Utils.get_config_value("source_file_path"),
                   Utils.get_config_value("pattern_data")))
        return searching_pattern

    @staticmethod
    def message_population():
        error_mapping_messages = \
            DataUpdater.reading_message(SHEET_NAME["Searching_Pattern"], "{}/config/{}".
                                 format(Utils.get_config_value("source_file_path"),
                                        Utils.get_config_value("message_data")))
        return error_mapping_messages

    @staticmethod
    def reading_message(sheet_no, configFile):
        with XlsDataParser(configFile) as xslParserObj:
            configData = xslParserObj.readPartialSheet(sheet_no, 1, 1, None, 1)
        message_collection = {}
        for element in configData:
            message_collection["{}".format(element[0])] = "{}".format(element[1])
        return message_collection
