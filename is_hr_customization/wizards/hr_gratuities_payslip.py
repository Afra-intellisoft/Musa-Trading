# -*- coding: utf-8 -*-
###########
from openerp import fields, models, api, tools, _
from openerp.exceptions import ValidationError
import xlsxwriter
import base64
import datetime
#from cStringIO import StringIO
from io import StringIO, BytesIO
from datetime import *
from datetime import datetime, timedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
import os
from odoo.exceptions import UserError
from dateutil import relativedelta
from io import BytesIO


class Wizardgratuities(models.Model):
    _name = 'wizard.gratuities'
    _description = 'Print Gratuities'
    from_date = fields.Date(string='Date From', required=True)
    to_date = fields.Date(string='Date To', required=True,
                          default=str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10],
                          )
    name = fields.Char(string="Gratuities")
    @api.multi
    def print_report(self):
        for report in self:
            bonus_ids = False
            from_date = report.from_date
            to_date = report.to_date
            if self.from_date > self.to_date:
                raise UserError(_("You must be enter start date less than end date !"))
            report.name = 'Gratuities from ' + from_date + ' To ' + to_date
            report_title = 'Gratuities from ' + from_date + ' To ' + to_date
            file_name = _('Gratuities.xlsx')
            fp = BytesIO()
            workbook = xlsxwriter.Workbook(fp)
            excel_sheet = workbook.add_worksheet('Gratuities Payslip')
            # excel_sheet.right_to_left()
            excel_sheet.protect()
            header_format = workbook.add_format(
                {'bold': True, 'font_color': 'white', 'bg_color': '#808080', 'border': 1})
            header_format_sequence = workbook.add_format(
                {'bold': False, 'font_color': 'black', 'bg_color': 'white', 'border': 1})
            format = workbook.add_format({'bold': False, 'font_color': 'black', 'bg_color': 'white', 'border': 1})
            title_format = workbook.add_format({'bold': True, 'font_color': 'black', 'bg_color': 'white'})
            header_format.set_align('center')
            header_format.set_text_wrap()
            format = workbook.add_format({'bold': False, 'font_color': 'black','bg_color': 'white'})
            title_format = workbook.add_format({'bold': True, 'font_color': 'black','bg_color': 'white'})
            title_format.set_align('center')
            format.set_align('center')
            header_format_sequence.set_align('center')
            format.set_text_wrap()
            format.set_num_format('#,##0.00')
            format_details = workbook.add_format()
            format_details.set_num_format('#,##0.00')
            sequence_id = 0
            col = 0
            row = 8
            first_row = 10
            excel_sheet.set_column(0, 4, 25)
            excel_sheet.set_row(1, 25)
            excel_sheet.write(row, col, '#', header_format)
            col += 1
            excel_sheet.write(row, col, 'NAME EMPLOYEE', header_format)
            col += 1
            excel_sheet.write(row, col, 'Date', header_format)
            col += 1
            excel_sheet.write(row, col, 'AMOUNT', header_format)
            col += 1
            excel_sheet.set_column(0, 4, 20)
            excel_sheet.set_row(5, 20)
            excel_sheet.merge_range(0, 0, 1, 3, report_title, title_format)
            excel_sheet.merge_range(1, 0, 2, 3, '', format)
            am_lst = []
            rs_lst = []
            sl_lst = []

            excel_sheet.cols_left_to_right = 1
            gratuities_ids = report.env['hr.gratuities.paysheet'].search(
                [('date', '<=', to_date), ('date', '>=', from_date), ('state', '=', 'finance_approval')])
            for gratuities in gratuities_ids:
                emp = gratuities.employee_gratuities_ids
                employee_id = False
                amount = 0.0
                for line in emp:
                    col = 0
                    row += 1
                    sequence_id += 1
                    employee_id = line.employee_id
                    date = line.date
                    amount = line.amount
                    excel_sheet.write(row, col, sequence_id, header_format_sequence)
                    col += 1
                    if employee_id:
                        excel_sheet.write(row, col, employee_id.name, format)
                    else:
                        excel_sheet.write(row, col, '', format)
                    col += 1
                    if date:
                        excel_sheet.write(row, col, date, format)
                    else:
                        excel_sheet.write(row, col, '', format)
                    col += 1
                    if amount:
                        excel_sheet.write(row, col, amount, format)
                    else:
                        excel_sheet.write(row, col, '', format)
                    col += 1

            col = 0
            row += 1
            excel_sheet.merge_range(row, 0, row, 2, 'Total', header_format)
            excel_sheet.write_formula(row, 3, 'SUM(D' + str(first_row) + ':D' + str(row) + ')', header_format)
            workbook.close()
            file_download = base64.b64encode(fp.getvalue())
            fp.close()
            wizardmodel = self.env['gratuities.report.excel']
            res_id = wizardmodel.create({'name': file_name, 'file_download': file_download})
            return {
                'name': 'Files to Download',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'gratuities.report.excel',
                'type': 'ir.actions.act_window',
                'target': 'new',
                'res_id': res_id.id,
            }


############################################
class gratuities_report_excel(models.TransientModel):
    _name = 'gratuities.report.excel'

    name = fields.Char('File Name', size=256, readonly=True)
    file_download = fields.Binary('File to Download', readonly=True)
