###########################
# Description: The Purpose of this library to read
# the data from xls sheet and upate the result into xls sheet
#
#############################


import os
import xlrd
import xlwt
import io
from xlutils.copy import copy


class XlsDataParser:

    modeRead = "read"
    modeWrite = "write"

    def __init__(self, file_loc, mode=modeRead):
        if (mode == self.modeRead) and (not os.path.isfile(file_loc)):
            raise RuntimeError("Failed to open xls file [{}]".format(file_loc))
        self.mode, self.file_loc = mode, file_loc
        self.workbook, self.sheets, self.sheet = None, None, None

    def __enter__(self):
        self.open_work_book()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_work_book()

    def open_work_book(self, result_file=None):
        if self.mode == self.modeRead:
            self.workbook = xlrd.open_workbook(self.file_loc)
            self.sheets = self.workbook.sheets()
        elif self.mode == self.modeWrite:
            self.workbook = xlwt.Workbook()
            self.sheet = self.workbook.add_sheet('Sheet 1')
            self.workbook.save("{}".format(result_file))

    def close_work_book(self):
        if self.mode == self.modeRead:
            pass
        if self.mode == self.modeWrite:
            with io.open(self.file_loc, 'wb') as file:
                self.workbook.save(file)

    def readPartialSheet(self, sheet_number, from_row=None,
                         from_column=None, nrows=None, ncolumns=None):

        to_row = from_row + nrows if nrows and (from_row + nrows) <= \
            self.sheets[sheet_number].nrows else self.sheets[sheet_number].nrows
        to_col = from_column + ncolumns if ncolumns and (from_column + ncolumns) <= \
            self.sheets[sheet_number].ncols else self.sheets[sheet_number].ncols

        if from_row > to_row or from_column > to_col:
            raise RuntimeError("Invalid column [{}] or row [{}] number.".\
                               format(from_row, from_column))
        # data = []
        data = [[self.sheets[sheet_number].cell(row_no, column).value
                for column in range(to_col)]
                for row_no in range(from_row, to_row)]
        return data

    def readSheet(self, sheetNumber):
        return self.readPartialSheet(sheetNumber)

    def writeCell(self, rowNo, colNo, value, style=None):
        self.sheet.write(rowNo, colNo, value, style)

    def writeRow(self, rowNo, fromColumn, valueList, style):
        colNo = fromColumn
        if type(valueList)==list:
            for value in valueList:
                self.sheet.write(rowNo, colNo, value, style)
                colNo += 1
        else:
            self.sheet.write(rowNo, colNo, valueList)

    def writeColumn(self, fromRow, colNo, valueList, style=None):
        rowNo = fromRow
        for value in valueList:
            self.sheet.write(rowNo, colNo, value, style)
            rowNo += 1

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
            pattern.pattern_back_colour = xlwt.Style.colour_map['ocean_blue']
            style.pattern = pattern
        style.alignment.WRAP_AT_RIGHT = True
        style.alignment.VERT_TOP = True

        return style

    @staticmethod
    def cell_styles():
        style = XlsDataParser.font()
        style.font.height = 220
        style.borders.MEDIUM = True
        return style
