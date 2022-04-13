import os
import re

from utils.common import Common


class LogAnalyser:
    """
    The purpose of this class to extract the information from the logger file as per
    users request.
    """

    @staticmethod
    def machine_details(job_file_name):
        """
        This function uses to collect the build machine details from the logger file
        :param job_file_name: Uses the passed file to extract the build machine detail.
        :return:
        """
        build_detail = Common.validation_param_detail(
            "machine_detail.yaml", "machine_detail"
        )
        machine_name = [
            build_detail[content]
            for content in build_detail
            if re.search(rf"{content}", f"{job_file_name}")
        ]

        Common.logger.info(f"[machine name] Build machine: {machine_name}")
        return machine_name

    @staticmethod
    def ran_job_status(job_file_name):
        """
        This function uses to check the ran status of build job
        :param str job_file_name: Uses the passed file to collect the all failed test
        cases information from the logger file
        :return: ran_status
        """
        try:
            ran_status = (
                os.popen(
                    f"zless {Common.get_config_value('data_location')}/"
                    f"{job_file_name}|grep -w Finished: "
                )
                .readlines()[0]
                .split(":")[-1]
                .strip()
            )
            Common.logger.info(
                f"[]: Successfully collected the status of build job name:"
                f" {job_file_name}"
            )

            return ran_status
        except Exception as ex:
            Common.logger.warning(
                f"[ran_job_status]: Failed to match the pattern of ran job: " f"{ex}"
            )

    @staticmethod
    def keyword_validation(keywords, job_file_name):
        """
        This function uses to validate the keyword whether it available in the logger or
        not
        :param list keywords: collection of keywords which uses to check , it available
        or not in logger file.
        :param str job_file_name: Uses the passed file to collect the all failed test
        cases information from the logger file
        :return: status
        """
        match = 0
        try:
            for keyword in keywords:
                keyword = os.popen(
                    'grep -w "{}" {}/{}'.format(
                        keyword, Common.get_config_value("data_location"), job_file_name
                    )
                ).readlines()
                match = match if keyword else match + 1
            status = (
                "All Keyword matched" if match == 0 else "Keyword Validation Failed"
            )
            return status
        except Exception as ex:
            Common.logger.warning(
                f"[keyword_validation]: Failed to match the keyword: "
                f"{keywords} in the logs {ex}"
            )

    @staticmethod
    def regex_information_extractor(job_file_name, command):
        """
        This function uses to collect the information(test cases failed, passed,
        highlited part etc) from the log file on the basis of requested regex expression
        :param str job_file_name:  Uses the passed file to collect the all failed test
        cases information from the logger file
        :param command: Uses the logic to extract the failed test cases information
        :return: failed_test_cases_information
        """
        failed_test_cases_information = os.popen(
            "zless {}/{}|{}".format(
                Common.get_config_value("data_location"), job_file_name, command
            )
        ).readlines()
        return failed_test_cases_information

    @staticmethod
    def suspicious_message_extractor(job_file_name):
        """
        This function uses to collect the error, warning, and other suspicious message
        from the log file
        :param str job_file_name: Uses the passed file to collect the all suspicious
        messages from the logger file.
        :return: suspicious_messages
        """
        suspicious_messages = {}
        filename = "{}/{}".format(
            Common.get_config_value("data_location"), job_file_name
        )
        regex_logic = (
            "awk -F';' '/run: /{print $1}'|"
            "awk -F'run:' '{print $2}'| sed -e 's/^[ \t]*//'|"
            r"awk -F'/' '{print $1}'|awk 'NF>0'|grep -v '^mkdir\|"
            r"^sed\|^rm\|^echo\|^ping\|^cp\|^wget\|^cd\|^/\|^du\|^mktemp\|"
            r"^firewall-cmd\|^scp\|^which\|^df\|grep\|^\[\|^/\|^/\|^[1-9]'"
        )
        messages = os.popen(f"cat {filename}|{regex_logic}").readlines()
        for message in messages:
            temp_key = f"{message}".replace(".", "  ").strip()
            suspicious_messages[temp_key] = list()
            message = message.strip().replace("'", "")
            if message:
                try:
                    command1 = (
                        'flag{ if (/run: /){print buf; flag="";} '
                        "else buf = buf $0 ORS};" + f"/ run: {message}/"
                    )
                    command2 = "{flag=1}"
                    pattern = os.popen(
                        f"awk '{command1} {command2}' {filename} 2>/dev/null"
                    ).readlines()
                    for pat in pattern:
                        data_mod = pat.strip()
                        if not len(data_mod) == 0:
                            try:
                                if re.search(
                                    f"(Warning)|(Error)|(Failed)|"
                                    f"(FAIL)|(Fail)|(ERROR)|(WARNING)",
                                    f"{data_mod}",
                                ):
                                    # To Handle mongo db issue .(dot) as a
                                    # key store issue

                                    suspicious_messages[temp_key].append(
                                        data_mod[0:190].strip()
                                    )
                            except Exception as ex:
                                Common.logger.warn(
                                    f"[suspicious_message_extractor]: Exception "
                                    f"throws while extracting the suspicious "
                                    f"message {ex}"
                                )
                except Exception as ex:
                    Common.logger.warn(
                        f"[suspicious_message_extractor]: Failed to "
                        f"extract the suspicious message from the logs"
                        f" {ex}"
                    )
        return suspicious_messages

    @staticmethod
    def pattern_to_pattern_match(pattern1, pattern2, file_name):
        """
        This function uses to collect the all suspicious error warning messages from
        in between passed pattern.
        :param str pattern1: The first pattern
        :param str pattern2: The last pattern
        :param str file_name: Uses the passed file to collect the all suspicious error
        warning messages from in between passed pattern.
        :return: warning_error_collection
        """
        key1 = pattern1.replace(".", "-")
        warning_error_collection = {key1: []}
        filename = "{}/{}".format(Common.get_config_value("data_location"), file_name)
        co1 = f"{pattern1}"
        co2 = f"^{pattern2}"
        command = " /" + co1 + "/ {flag=1;next} /" + co2 + "/{flag=0} flag { print }"
        datas = os.popen(f"cat {filename}| awk '{command}'")
        for data in datas:
            data = Common.decoding_strings(data)
            if data:
                data = data.strip().replace("'", "")
                if data:
                    if re.search(
                        f"(Warning)|(Error)|(Failed)|(FAIL)|(Fail)|(ERROR)|(WARNING)",
                        f"{data}",
                    ):
                        warning_error_collection[key1].append(data.strip())
            else:
                warning_error_collection[key1].append("Data is not in correct format")
        Common.logger.info(
            "[pattern_to_pattern_match]: Successfully Collected the error and"
            " other warning messages from in-between pattern"
        )
        return warning_error_collection

    @staticmethod
    def system_log_analysis(file_name):
        """
        This function uses to collect the all suspicious system logs from logger file
        :param str file_name: Uses the passed file to collect the all failed test
        cases information from the logger file
        :return: system_log
        """
        system_log = {}
        log_types = [
            "foreman-installer/satellite.log",
            "satellite-installer/satellite-installer.log",
            "capsule-installer/capsule-installer.log",
            "foreman-installer/capsule.log",
            "foreman/production.log",
            "foreman-proxy/proxy.log",
            "candlepin/candlepin.log",
            "messages",
            "mongodb/mongodb.log",
            "tomcat/catalina.out",
        ]
        filename = f"{Common.get_config_value('data_location')}/{file_name}"
        system_log_path = "/var/log"
        for log_type in log_types:
            datas = os.popen(
                f"cat {filename}|grep -A4 '{system_log_path}/{log_type}:'"
                f"|grep -A1 'Errors found:'"
            )
            if datas:
                for data in datas:
                    data = Common.decoding_strings(data)
                    if True:
                        if not re.search(r"Errors found:", data):
                            system_log[
                                log_type.split("/")[-1].replace(".", "-")
                            ] = data[0:5000]
                        else:
                            system_log[
                                log_type.split("/")[-1].replace(".", "-")
                            ] = "String format is not correct"
        Common.logger.info(
            f"[system_log_analysis]: Successfully collected the systems log of"
            f" {file_name}"
        )
        return system_log
