import os
import random
import ssl
import subprocess

import jenkinsapi
import requests
import urllib3
from jenkinsapi.jenkins import Jenkins
from utils.common import Common


class JenkinsJob:
    def __init__(self):
        requests.packages.urllib3.disable_warnings()
        context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
        context.verify_mode = ssl.CERT_NONE
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def __enter__(self):
        self.jenkinsObj = Jenkins(
            Common.get_config_value("jenkins_base_url"),
            Common.decrypt(Common.get_config_value("jenkins_username")),
            Common.decrypt(Common.get_config_value("jenkins_password")),
            ssl_verify=False,
        )
        return self.jenkinsObj

    @staticmethod
    def env_setup():
        if not os.path.isfile(
            os.path.join(os.path.abspath("."), Common.get_config_value("data_location"))
        ):
            os.mkdir(
                os.path.join(
                    os.path.abspath("."), Common.get_config_value("data_location")
                )
            )
        return 0

    def get_job_info(self, jobName):
        job = self.jenkinsObj[jobName]
        try:
            lgj = job.get_last_good_build().get_number()
        except jenkinsapi.custom_exceptions.NoBuildData:
            lgj = 0
        try:
            lbj = job.get_last_failed_buildnumber()
        except jenkinsapi.custom_exceptions.NoBuildData:
            lbj = 0
        if lbj and lgj:
            job_number = lbj if int(lbj) > int(lgj) else lgj
            time_stamp = self.build_execution_time(jobName, job_number)
            return int(job_number), time_stamp
        else:
            time_stamp = self.build_execution_time(jobName, int(lbj) + int(lgj))
            return int(lbj) + int(lgj), time_stamp

    @staticmethod
    def download_the_logs(downloadlink, job_name):
        status = subprocess.call(
            [
                "wget {} -P {}/{} --no-check-certificate".format(
                    downloadlink,
                    os.path.abspath("."),
                    Common.get_config_value("data_location"),
                )
            ],
            shell=True,
        )
        if status == 0:
            rename_file_name = "{}_{}".format(job_name, random.randint(1, 10000))
            os.rename(
                f"{os.path.abspath('.')}/{Common.get_config_value('data_location')}"
                "/consoleFull",
                f"{os.path.abspath('.')}/{Common.get_config_value('data_location')}/"
                f"{rename_file_name}",
            ) if os.path.isfile(
                f"{os.path.abspath('.')}/{Common.get_config_value('data_location')}"
                f"/consoleFull"
            ) else "Nothing"
            Common.logger.info(f"[download_the_logs] Downloaded logs renamed")
            return rename_file_name
        else:
            Common.logger.warn(
                f"[download_the_logs]: The job does not exist {job_name} "
                f"and downloadable link {downloadlink}"
            )
            return False

    @staticmethod
    def build_execution_time(job_name, build_no):
        job_url = (
            Common.get_config_value("jenkins_base_url")
            + f"/job/{job_name}/{build_no}/api/python?tree=timestamp"
        )
        timestamp_response = requests.get(url=job_url, verify=False)
        if timestamp_response.status_code == 200:
            Common.logger.info(
                f"[build_execution_time] Build Execution time has collected "
                f"{timestamp_response.json()['timestamp']}"
            )
            return timestamp_response.json()["timestamp"]
        else:
            Common.logger.warn(
                f"[build_execution_time]: Build execution time identification "
                f"failed get response {timestamp_response.status_code}"
            )
            return timestamp_response.status_code

    def __exit__(self, exc_type, exc_val, exc_tb):
        del self.jenkinsObj

    @staticmethod
    def jenkins_data_collection(job_name, job_number):
        """
        This method use to prepare the environment to download the requested log from
        jenkins job.
        :param str job_name: name of the requested job
        :param int job_number: build number of the requested job
        :return: file_name, download_console_log_url
        """
        try:
            if type(job_number) is int:
                download_console_log_url = (
                    f"{Common.get_config_value('jenkins_base_url')}"
                    f"/job/{job_name}/{job_number}/consoleFull"
                )
                file_name = JenkinsJob().download_the_logs(
                    download_console_log_url, job_name
                )
                if file_name:
                    return file_name, download_console_log_url
                else:
                    return False
        except Exception as err:
            Common.logger.warn(
                f"[jenkins_data_collection] Jenkins data collection failed {err}"
            )
