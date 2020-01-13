class SystemProperties(object):
    def __init__(self):
        self.job_map = {}
        self.row_no = 0
        self.job_list = []
        self.sheet_number = ""
        self.row_no = ""
        self.sheet = ""

    @property
    def job_mapper(self):
        return self.job_map

    @job_mapper.setter
    def job_mapper(self, job_map):
        self.job_map = job_map

    @job_mapper.deleter
    def job_mapper(self):
        del self.job_map

    @property
    def jobs_list(self):
        return self.job_list

    @jobs_list.setter
    def jobs_list(self, job_list):
        self.job_list = job_list

    @jobs_list.deleter
    def jobs_list(self):
        del self.job_list

    @property
    def jobs_type(self):
        return self.job_type

    @jobs_type.setter
    def jobs_type(self, job_type):
        self.job_type.append(job_type)

    @jobs_type.deleter
    def jobs_type(self):
        del self.job_type

    @property
    def sheets_number(self):
        return self.sheet_number

    @sheets_number.setter
    def sheets_number(self, sheet_number):
        self.sheet_number = sheet_number

    @sheets_number.deleter
    def sheets_number(self):
        del self.sheet_number

    @property
    def rows_no(self):
        return self.row_no

    @rows_no.setter
    def rows_no(self, row_no):
        self.row_no = row_no

    @rows_no.deleter
    def rows_no(self):
        del self.row_no

    @property
    def sheets(self):
        return self.sheet

    @sheets.setter
    def sheets(self, sheet):
        self.sheet = sheet

    @sheets.deleter
    def sheets(self):
        del self.sheet
