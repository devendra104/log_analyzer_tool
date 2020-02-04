import re
import os
from lib.log_exception import LogException
from lib.utils import Utils


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
        machine_data = Utils.validation_param_detail("machine_detail.yaml",
                                                     "machine_detail")
        pattern_data = [machine_data[content] for content in machine_data if
                        re.search(r'{}'.format(content), "{}".format(job_file_name))]
        if pattern_data:
            machine_detal = os.popen("{} {}/{}".format(pattern_data[0], Utils.\
                                                       get_config_value("data_location"),
                                                       job_file_name)).readlines()[0].strip()
            return machine_detal
        else:
            return None

    @staticmethod
    def ran_job_status(job_file_name):
        """
        This function uses to check the ran status of build job
        :param str job_file_name: Uses the passed file to collect the all failed test
        cases information from the logger file
        :return: ran_status
        """
        try:
            ran_status = os.popen("zless {}/{}|grep -w Finished: ".format
                                  (Utils.get_config_value("data_location"),
                                   job_file_name)).readlines()[0].split(":")[-1].strip()

            return ran_status
        except Exception:
            raise LogException.PATTERN_MATCH_EXCEPTION("buid_status")

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
                keyword = os.popen('grep -w "{}" {}/{}'.
                                   format(keyword, Utils.
                                          get_config_value("data_location"),
                                          job_file_name)).readlines()
                match = match if keyword else match + 1
            status = "All Keyword matched" if match == 0 else \
                "Keyword Validation Failed"
            return status
        except Exception:
            raise LogException.PATTERN_MATCH_EXCEPTION("build_status")

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
        failed_test_cases_information = os.popen('zless {}/{}|{}'.format(
            Utils.get_config_value("data_location"), job_file_name, command)).readlines()
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
        filename = "{}/{}".format(Utils.get_config_value("data_location"), job_file_name)
        regex_logic = "awk -F';' '/run: /{print $1}'|" \
                      "awk -F'run:' '{print $2}'| sed -e 's/^[ \t]*//'|" \
                      "awk -F'/' '{print $1}'|awk 'NF>0'|grep -v '^mkdir\|" \
                      "^sed\|^rm\|^echo\|^ping\|^cp\|^wget\|^cd\|^/\|^du\|^mktemp\|" \
                      "^firewall-cmd\|^scp\|^which\|^df\|grep\|^\[\|^/\|^/\|^[1-9]'"
        messages = os.popen("cat {}|{}".format(filename, regex_logic)).readlines()
        for message in messages:
            temp_key = "{}".format(message).replace(".", "  ").strip()
            suspicious_messages[temp_key] = list()
            message = message.strip().replace("'", "")
            if message:
                try:
                    command1 = 'flag{ if (/run: /){print buf; flag="";} ' \
                               'else buf = buf $0 ORS};' + "/ run: {}/".format(message)
                    command2 = "{flag=1}"
                    pattern = os.popen(
                        "awk '{} {}' {} 2>/dev/null".format(command1, command2,
                                                            filename)).readlines()
                    for pat in pattern:
                        data_mod = pat.strip()
                        if not len(data_mod) == 0:
                            try:
                                if re.search('(Warning)|(Error)|(Failed)|'
                                             '(FAIL)|(Fail)|(ERROR)|(WARNING)',
                                             "{}".format(data_mod)):
                                    # To Handle mongo db issue .(dot) as a
                                    # key store issue

                                    suspicious_messages[temp_key]\
                                        .append(data_mod[0:190].strip())
                            except Exception:
                                pass
                except Exception:
                    pass
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
        filename = "{}/{}".format(Utils.get_config_value("data_location"), file_name)
        co1 = "{}".format(pattern1)
        co2 = "^{}".format(pattern2)
        command = ' /' + co1 + '/ {flag=1;next} /' + co2 + '/{flag=0} flag { print }'
        datas = os.popen(("cat {}| awk '{}'".format(filename, command)))
        for data in datas:
            data = data.strip().replace("'", "")
            if data:
                if re.search('(Warning)|(Error)|(Failed)|(FAIL)|(Fail)|(ERROR)|(WARNING)',
                             "{}".format(data)):
                    warning_error_collection[key1].append(data.strip())
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
        log_types = ['foreman-installer/satellite.log',
                     'satellite-installer/satellite-installer.log',
                     'capsule-installer/capsule-installer.log',
                     'foreman-installer/capsule.log', 'foreman/production.log',
                     'foreman-proxy/proxy.log', 'candlepin/candlepin.log', 'messages',
                     'mongodb/mongodb.log', 'tomcat/catalina.out']
        filename = "{}/{}".format(Utils.get_config_value("data_location"), file_name)
        system_log_path = "/var/log"
        for log_type in log_types:
            datas = os.popen(
                "cat {}|grep -A4 '{}/{}:'"
                "|grep -A1 'Errors found:'".format(
                    filename, system_log_path, log_type))
            if datas:
                for data in datas:
                    if not re.search(r"Errors found:", data):
                        system_log[log_type.split("/")[-1].replace(".", "-")] = \
                            data[0:5000]
        return system_log
