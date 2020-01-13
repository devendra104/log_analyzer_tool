import os
import re
import paramiko
from config import config
from lib.utils import Utils
from lib.logparser import LogAnalyser


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
        for password in config.openshift_password:
            ssh_object = Utils.ssh_connection_handling(ssh_object, machine_name,
                                                       config.openshift_username,
                                                       password)
            if not ssh_object:
                continue
            else:
                break
        return ssh_object

    @staticmethod
    def command_execution_on_build_machine(validation_command, validation_job_name,
                                           machine_name, skip_check):
        """
        This method is used to collect the commands output, the output mapped with
        their keys
        :param dict validation_command:
        :param str validation_job_name:
        :param str machine_name: machine hostname.
        :param list skip_check:

        :return: command_output
        """
        if skip_check[0] == "checks_on_build_machine" and machine_name:
            ssh_object = Validation.ssh_object(machine_name)
            ssh_object = [ssh_object if ssh_object else False][0]
            if ssh_object:
                command_output = Validation.data_validation_over_test_machine(
                    validation_command[validation_job_name], ssh_object)
                ssh_object.close()
            else:
                command_output = {"Machine Status": "Machine is not pingable, Kindly "
                                                    "check the status on upsift/RHEV"}
        else:
            command_output = "Check on Build machine status was un-checked"
        return command_output

    @staticmethod
    def keyword_validation(keywords, job_file_name):
        """
        This method is used to collect the keyword status whether it is available or
        not in logger.
        :param list keywords: It contains the list of keys
        :param str job_file_name: Uses the passed file to collect the all failed test
        cases information from the logger file

        :return: validation_output
        """
        validation_output = LogAnalyser.keyword_validation(keywords, job_file_name)
        return validation_output

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
    def upgrade_validation(machine_name, job_file_name, skip_check):
        """
        This method use to collect the all analysis result and returns to the log_analyser.
        :param str machine_name: machine hostname.
        :param str job_file_name: Uses the passed file to collect the all suspicious
        messages from the logger file.
        :param list skip_check:

        :return: job_result
        """
        job_result = {}
        validation_output, validation_command, validation_job_name, sub_job = \
            Validation.common_validation(job_file_name, "db_upgrade_migrate")
        pat_to_pat_match = validation_command[validation_job_name]["pattern_to_pattern_filter"]
        pattern1 = pat_to_pat_match["pattern1"]
        pattern2 = pat_to_pat_match["pattern2"]
        err_warn_in_between_pat = LogAnalyser.pattern_to_pattern_match(pattern1, pattern2,
                                                                       job_file_name)
        validation_command[validation_job_name].pop("pattern_to_pattern_filter")
        job_result["on_machine_output"] = Validation.command_execution_on_build_machine(
            validation_command, validation_job_name, machine_name, skip_check)
        if re.search(r"satellite6_db_upgrade_migrate", "{}".format(job_file_name)):

            job_result["keyword_availability"] = validation_output
            job_result["sub_job"] = sub_job
            job_result["job_name"] = validation_job_name
            job_result["All_Commands_Execution_status"] = LogAnalyser. \
                suspicious_message_extractor(job_file_name)
            job_result["All_Commands_Execution_status"]["Pattern_Pattern_match"] = \
                err_warn_in_between_pat
            job_result["System_Log"] = LogAnalyser.\
                system_log_analysis(job_file_name)
            return job_result

    @staticmethod
    def pre_upgrade(machine_name, job_file_name, skip_check):
        """
        This method is used to collect the result of all upgrade  jobs which include sync,
        pre_upgrade, satellite/capsule upgrade & Post upgrade.
        :param str machine_name: machine hostname.
        :param str job_file_name: Uses the passed file to collect the all suspicious
        messages from the logger file.
        :param list skip_check:

        :return: job_result
        """
        validation_output, validation_command, validation_job_name, sub_job = \
            Validation.common_validation(job_file_name, "upgrade_phase")
        job_result = {}
        sub_job = True if validation_command["sub_job"] == "True" else False
        print(".............Sub job................", sub_job)
        if re.search(r"upgrade-to-", "{}".format(job_file_name)):
            job_result["keyword_availability"] = validation_output
            job_result["job_name"] = validation_job_name
            job_result["sub_job"] = sub_job
            job_result["System_Log"] = None
            job_result["All_Commands_Execution_status"] = LogAnalyser. \
                suspicious_message_extractor(job_file_name)
            job_result["All_Commands_Execution_status"]["highlited_information"] = \
                LogAnalyser.regex_information_extractor(job_file_name, validation_command[\
                    validation_job_name]["highlited_upgrade_content"])
            return job_result

        if re.search(r"^automation-preupgrade-|^automation-postupgrade-",
                     "{}".format(job_file_name)):
            total_test_failure = LogAnalyser.regex_information_extractor(
                job_file_name, validation_command[validation_job_name]["test_failure"])
            total_test = LogAnalyser.regex_information_extractor(
                job_file_name, validation_command[validation_job_name]["total_test_executed"])
            job_result["keyword_availability"] = validation_output
            job_result["Pre_Upgrade_test_Failure"] = total_test_failure
            job_result["Total Test Executed"] = total_test
            job_result["job_name"] = validation_job_name
            job_result["sub_job"] = sub_job
            job_result["System_Log"] = None
            job_result["All_Commands_Execution_status"] = LogAnalyser. \
                suspicious_message_extractor(job_file_name)
            return job_result

        if re.search(r"upgrade-phase", "{}".format(job_file_name)):
            job_result["on_machine_output"] = Validation.\
                command_execution_on_build_machine(validation_command,
                                                   validation_job_name, machine_name,
                                                   skip_check)
            job_result["keyword_availability"] = validation_output
            job_result["job_name"] = validation_job_name
            job_result["sub_job"] = sub_job
            job_result["System_Log"] = LogAnalyser. \
                system_log_analysis(job_file_name)
            job_result["All_Commands_Execution_status"] = LogAnalyser.\
                suspicious_message_extractor(job_file_name)
            return job_result

    @staticmethod
    def common_validation(job_name, job_type):
        """
        This method use by all the validation method to get the job name,
        commands, sub_job or not etc.
        :param str job_name: Uses the passed file to collect the all suspicious
        messages from the logger file.
        :param dict job_type: It contains all the information related to jobs in
        dictionary format.

        :return: validation_output, validation_command, validation_job_name, sub_job
        """
        validation_job_name = re.split(r"_\d*$", "{}".format(job_name))[0]
        validation_command = Utils.validation_param_detail()[job_type]
        validation_output = Validation.keyword_validation(
            validation_command[validation_job_name]["keyword_availability"], job_name)
        validation_command[validation_job_name].pop('keyword_availability')
        sub_job = True if validation_command["sub_job"] == "True" else False
        return validation_output, validation_command, validation_job_name, sub_job

    @staticmethod
    def unknown_type():
        return {"validation_type": "!!!!!!!!!!Validation Type should not be empty"
                                   "!!!!!!!!!!"}
