import os
import requests
import ssl
import subprocess
import urllib3
import random
import jenkinsapi
from jenkinsapi.jenkins import Jenkins
from config import config
from lib.log_exception import LogException


class JenkinsJob:
    def __init__(self):
        requests.packages.urllib3.disable_warnings()
        context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
        context.verify_mode = ssl.CERT_NONE
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def __enter__(self):
        self.jenkinsObj = Jenkins(config.url, config.username,
                                  config.password, ssl_verify=False)
        return self.jenkinsObj

    @staticmethod
    def env_setup():
        if not os.path.isfile(config.data_location):
            os.mkdir(config.data_location)
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
            ["wget {} -P {}".format(downloadlink, config.data_location)], shell=True)
        if status == 0:
            rename_file_name = "{}_{}".format(job_name, random.randint(1, 10000))
            os.rename("{}/consoleFull".format(config.data_location), "{}/{}"
                      .format(config.data_location, rename_file_name))\
                if os.path.isfile("{}/consoleFull".format(config.data_location)) \
                else "Nothing"
            return rename_file_name
        else:
            LogException.JOB_DOES_NOT_EXIST(job_name)
            return False

    @staticmethod
    def build_execution_time(job_name, build_no):
        job_url = config.url +"/job/{}/{}/api/python?tree=timestamp".\
            format(job_name,build_no)
        timestamp_response = requests.get(url=job_url, verify=False)
        if timestamp_response.status_code == 200:
            print(timestamp_response.json()["timestamp"])
            return timestamp_response.json()["timestamp"]
        else:
            return timestamp_response.status_code

    def __exit__(self, exc_type, exc_val, exc_tb):
        del self.jenkinsObj
