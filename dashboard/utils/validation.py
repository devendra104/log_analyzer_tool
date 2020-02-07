import os
import paramiko
from utils.common import Common
from utils.logparser import LogAnalyser


class Validation:

    @staticmethod
    def ssh_object(machine_name):
        """
        This method is used to create an ssh object and the machine status(ping or not)
        :param str machine_name: machine hostname.

        :return: ssh_object
        """
        if os.system("ping -c1 {} 2>/dev/null 1>/dev/null".format(machine_name)) != 0:
            return False
        ssh_object = paramiko.SSHClient()
        ssh_object.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        for password in Common.get_config_value("build_machine_password"):
            ssh_object = Common.ssh_connection_handling(ssh_object, machine_name,
                                                       Common.get_config_value("build_machine_username"),
                                                       password)
            if not ssh_object:
                continue
            else:
                break
        return ssh_object

    @staticmethod
    def command_execution_on_build_machine(validation_command, machine_name):
        """
        This method is used to collect the commands output, the output mapped with
        their keys
        :param dict validation_command:
        :param str machine_name: machine hostname.
        :return: command_output
        """
        if machine_name:
            ssh_object = Validation.ssh_object(machine_name)
            ssh_object = [ssh_object if ssh_object else False][0]
            if ssh_object:
                command_output = Validation.data_validation_over_test_machine(
                    validation_command, ssh_object)
                ssh_object.close()
            else:
                command_output = {"Machine Status": "Machine is not pingable, Kindly "
                                                    "check the status on upsift/RHEV"}
        else:
            command_output = "Check on Build machine status was un-checked"
        return command_output

    @staticmethod
    def data_validation_over_test_machine(validation_command, ssh_object):
        """
        This method use to trigger the users validation request on Build machine and
        collect their output which maps with user request.
        :param dict validation_command: collection of all the requested command which
        will be executed over target machine.
        :param obj ssh_object: build machines connection object.

        :return: validation_output
        """
        validation_output = {}
        for validation in validation_command:
            stdin, stdout, stderr = ssh_object.\
                exec_command("{}".format(validation_command[validation]))
            data = stdout.readlines()

            # To Handle mongo db issue
            # bson.errors.InvalidDocument: key 'foreman-maintain upgrade check
            # --target-version 6.6 -y' must not contain '.'
            temp_key = "{}".format(validation).replace(".", "  ")
            validation_output[temp_key] = \
                data[-1].strip() if stderr.readlines and data else "Fail"
        return validation_output

    @staticmethod
    def job_analysis(validation_data, job_file_name, machine_name, skip_check=False):
        job_result = dict()
        job_result["All_Commands_Execution_status"] = LogAnalyser. \
            suspicious_message_extractor(job_file_name)

        if validation_data["keyword_availability"]:
            job_result["keyword_availability"] = LogAnalyser.keyword_validation\
                (validation_data["keyword_availability"], job_file_name)
        else:
            job_result["keyword_availability"] = " "

        if validation_data["test_execution_record"]:
            total_test_failure = LogAnalyser.regex_information_extractor(
                job_file_name, validation_data["test_failure"])
            total_test = LogAnalyser.regex_information_extractor(
                job_file_name, validation_data["total_test_executed"])
            job_result["Pre_Upgrade_test_Failure"] = total_test_failure
            job_result["Total Test Executed"] = total_test
        else:
            job_result["Pre_Upgrade_test_Failure"] = []
            job_result["Total Test Executed"] = []

        if skip_check[0] == "no_checks_on_build_machine":
            job_result["on_machine_output"] = ""
        else:
            job_result["on_machine_output"] = Validation.\
                command_execution_on_build_machine(
                validation_data["check_on_build_environement"], machine_name)
        if validation_data["pattern_to_pattern_filter"]:
            pattern1 = validation_data["pattern_to_pattern_filter"]["pattern1"]
            pattern2 = validation_data["pattern_to_pattern_filter"]["pattern2"]
            err_warn_in_between_pat = LogAnalyser.pattern_to_pattern_match(pattern1,
                                                                           pattern2,
                                                                           job_file_name)
            job_result["All_Commands_Execution_status"]["Pattern_Pattern_match"] = \
                err_warn_in_between_pat
        else:
            job_result["All_Commands_Execution_status"]["Pattern_Pattern_match"] = []

        job_result["System_Log"] = LogAnalyser. \
            system_log_analysis(job_file_name)

        return job_result

    @staticmethod
    def unknown_type():
        return {"validation_type": "!!!!!!!!!!Validation Type should not be empty"
                                   "!!!!!!!!!!"}
