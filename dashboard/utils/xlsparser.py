###########################
# Description: The Purpose of this library to read
# the data from xls sheet and upate the result into xls sheet
#
#############################
import io
import os

import xlrd
import xlwt
from xlutils.copy import copy


class Xlsparser:

    MODEREAD = "read"
    MODEWRITE = "write"

    def __init__(self, file_loc, mode=MODEREAD):
        if (mode == self.MODEREAD) and (not os.path.isfile(file_loc)):
            raise RuntimeError(f"Failed to open xls file [{file_loc}]")
        self.mode, self.file_loc = mode, file_loc
        self.workbook, self.sheets, self.sheet = None, None, None

    def __enter__(self):
        self.open_work_book()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_work_book()

    def open_work_book(self, result_file=None):
        if self.mode == self.MODEREAD:
            self.workbook = xlrd.open_workbook(self.file_loc)
            self.sheets = self.workbook.sheets()
        elif self.mode == self.MODEWRITE:
            self.workbook = xlwt.Workbook()
            self.sheet = self.workbook.add_sheet("Sheet 1")
            self.workbook.save(f"{result_file}")

    def close_work_book(self):
        if self.mode == self.MODEREAD:
            pass
        if self.mode == self.MODEWRITE:
            with open(self.file_loc, "wb") as file:
                self.workbook.save(file)

    def read_partial_sheet(
        self, sheet_number, from_row=None, from_column=None, n_rows=None, n_columns=None
    ):

        to_row = (
            from_row + n_rows
            if n_rows and (from_row + n_rows) <= self.sheets[sheet_number].nrows
            else self.sheets[sheet_number].nrows
        )
        to_col = (
            from_column + n_columns
            if n_columns
            and (from_column + n_columns) <= self.sheets[sheet_number].ncols
            else self.sheets[sheet_number].ncols
        )

        if from_row > to_row or from_column > to_col:
            raise RuntimeError(
                f"Invalid column [{from_row}] or row [{from_column}] number."
            )

        data = [
            [
                self.sheets[sheet_number].cell(row_no, column).value
                for column in range(to_col)
            ]
            for row_no in range(from_row, to_row)
        ]
        return data

    def read_sheet(self, sheet_number):
        return self.read_partial_sheet(sheet_number)

    def write_cell(self, row_no, col_no, value, style=None):
        self.sheet.write(row_no, col_no, value, style)

    def write_row(self, row_no, from_column, value_list, style):
        col_no = from_column
        if type(value_list) == list:
            for value in value_list:
                self.sheet.write(row_no, col_no, value, style)
                col_no += 1
        else:
            self.sheet.write(row_no, col_no, value_list)

    def write_column(self, from_row, col_no, value_list, style=None):
        row_no = from_row
        for value in value_list:
            self.sheet.write(row_no, col_no, value, style)
            row_no += 1

    @staticmethod
    def copy_xls(xlssheet, sheet_no):
        wb = xlrd.open_workbook(xlssheet, formatting_info=True)
        wb_copy = copy(wb)
        sheet_obj = wb_copy.get_sheet(sheet_no)
        return sheet_obj, wb_copy

    @staticmethod
    def font(bold=None):
        style = xlwt.XFStyle()
        if bold:
            style.font.bold = True
            pattern = xlwt.Pattern()
            pattern.pattern = xlwt.Pattern.SOLID_PATTERN
            pattern.pattern_back_colour = xlwt.Style.colour_map["ocean_blue"]
            style.pattern = pattern
        style.alignment.WRAP_AT_RIGHT = True
        style.alignment.VERT_TOP = True

        return style

    @staticmethod
    def cell_styles():
        style = Xlsparser.font()
        style.font.height = 220
        style.borders.MEDIUM = True
        return style
