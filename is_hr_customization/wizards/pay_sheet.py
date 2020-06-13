# -*- coding: utf-8 -*-
###########

from odoo import fields, models, api, tools, _
from odoo.exceptions import ValidationError
import xlsxwriter
import base64
import datetime
from io import StringIO
from datetime import *
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
import os
from odoo.exceptions import UserError
from dateutil import relativedelta
from io import BytesIO
from datetime import timedelta

class Wizard_paysheet_roll(models.Model):
    _name = 'wizard.paysheet.roll'
    _description = 'Print Payslip'

    from_date = fields.Date(string='Date From', required=True)
    to_date = fields.Date(string='Date To', required=True,
                          default=str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10],
                          )
    name = fields.Char(string="Payslip")

    @api.multi
    def print_report(self):
        for report in self:
            from_date = report.from_date
            to_date = report.to_date
            if self.from_date > self.to_date:
                raise UserError(_("You must be enter start date less than end date !"))
            report.name = ('Pay Sheet From ' + from_date + ' To ' + to_date)
            report_title = ('Salaries From ' + from_date + ' To ' + to_date)
            file_name = _('Pay Sheet.xlsx')
            fp = BytesIO()
            workbook = xlsxwriter.Workbook(fp)
            excel_sheet = workbook.add_worksheet('Pay Sheet')
            # excel_sheet.left_to_left()
            header_format = workbook.add_format({'bold': True, 'font_color': 'white', 'bg_color': '#808080', 'border': 1})
            header_format_sequence = workbook.add_format({'bold': False, 'font_color': 'black', 'bg_color': 'white','border': 1})
            format = workbook.add_format({'bold': False, 'font_color': 'black', 'bg_color': 'white', 'border': 1})
            title_format = workbook.add_format({'bold': True, 'font_color': 'black', 'bg_color': 'white'})
            title = workbook.add_format({'bold': True, 'font_color': 'white', 'bg_color': '#336699', 'border': 1 ,'align':'center'})
            title_payslip = workbook.add_format({'bold': True, 'font_color': 'white', 'bg_color': '#99bbff', 'border': 1 ,'align':'center'})
            title_header = workbook.add_format({'bold': True, 'font_color': 'white', 'bg_color': '#004de6', 'border': 1 ,'align':'center'})
            title_sequence = workbook.add_format({'bold': False, 'font_color': 'black', 'bg_color': 'white','border': 1})
            title_format.set_text_wrap()
            title_format.set_align('center')
            format.set_align('center')
            header_format_sequence.set_align('center')
            header_format.set_align('center')
            header_format.set_text_wrap()
            excel_sheet.set_row(5, 20)
            excel_sheet.set_column('F:U', 20,)
            format.set_text_wrap()
            format.set_num_format('#,##0.00')
            format_details = workbook.add_format()
            format_details.set_num_format('#,##0.00')
            sequence_id = 0
            col = 0
            row = 5
            first_row = 7
            excel_sheet.write(row, col, '#',  header_format)
            col += 1
            excel_sheet.write(row, col, 'Name', header_format)
            col += 1
            excel_sheet.write(row, col, 'Department', header_format)
            col += 1
            excel_sheet.write(row, col, 'Position', header_format)
            col += 1
            excel_sheet.write(row, col, 'Contract Start', header_format)
            col += 1
            # excel_sheet.write(row, col, 'Contract End', header_format)
            # col += 1
            excel_sheet.write(row, col, 'Basic Salary', header_format)
            col += 1
            excel_sheet.write(row, col, 'Gross', header_format)
            col += 1
            excel_sheet.write(row, col, 'Cloth', header_format)
            col += 1
            excel_sheet.write(row, col, 'Transportation', header_format)
            col += 1
            excel_sheet.write(row, col, 'Wear', header_format)
            col += 1
            excel_sheet.write(row, col, 'Meal', header_format)
            col += 1
            excel_sheet.write(row, col, 'Cola', header_format)
            col += 1
            # excel_sheet.write(row, col, 'Gratuities', header_format)
            # col += 1
            excel_sheet.write(row, col, 'Benefits', header_format)
            col += 1
            excel_sheet.write(row, col, 'Deductions Short Loan', header_format)
            col += 1
            excel_sheet.write(row, col, 'Deductions Long Loan', header_format)
            col += 1
            excel_sheet.write(row, col, 'Total deductions Benefits', header_format)
            col += 1
            excel_sheet.write(row, col, 'Total_Net_Salary', header_format)
            excel_sheet.set_column(0, 4, 25)
            excel_sheet.set_row(1, 25)
            excel_sheet.merge_range(0, 0, 1, 10, '', title_format)
            excel_sheet.merge_range(2, 0, 3, 10, report_title, title_format)
            excel_sheet.merge_range(3, 0, 4, 10, '', title_format)
            payslip_month_ids = report.env['hr.payslip'].search(
                [('date_to', '<=', to_date), ('date_from', '>=', from_date)])
            for payslip_period in payslip_month_ids:
                slip_id = payslip_period.id
                employee = payslip_period.employee_id.id
                employee_id = payslip_period.employee_id.name
                department_id = payslip_period.employee_id.department_id.name
                job_id = payslip_period.employee_id.job_id.name
                date_end = payslip_period.employee_id.contract_id.date_end
                date_start = payslip_period.employee_id.contract_id.date_start
                birthday = payslip_period.employee_id.birthday
                start_date = self.env['hr.contract'].search([('employee_id','=',payslip_period.employee_id.id)],limit = 1,order ='date_start desc').date_start
                col = 0
                row += 1
                sequence_id += 1
                excel_sheet.write(row, col, sequence_id, header_format_sequence)

                col += 1
                if employee_id:
                    excel_sheet.write(row, col, employee_id, format)
                else:
                    excel_sheet.write(row, col, '', format)
                col += 1
                if department_id:
                    excel_sheet.write(row, col, department_id, format)
                else:
                    excel_sheet.write(row, col, '', format)
                col += 1
                if job_id:
                    excel_sheet.write(row, col, job_id, format)
                else:
                    excel_sheet.write(row, col, '', format)
                col += 1
                if date_start:
                    excel_sheet.write(row, col, date_start, format)
                else:
                    excel_sheet.write(row, col, '', format)
                col += 1
                slip_ids = payslip_period.env['hr.payslip.line'].search([('slip_id', '=', slip_id),
                                                                         ('employee_id', '=', employee)])
                gross = 0.0
                basic_salary = 0.0
                cloth = 0.0
                meal = 0.0
                transportation = 0.0
                coal = 0.0
                wear = 0.0
                benefits = 0.0
                # gratuities = 0.0
                deductions_short_loan = 0.0
                deductions_long_loan = 0.0
                deductions = 0.0
                Total_Net_Salary = 0.0
                for slip_line in slip_ids:
                    category = slip_line.code
                    if category == 'BASIC':
                        basic_salary = slip_line.total
                    if category == 'GROSS':
                        gross = slip_line.total
                    if category == 'CLOTH':
                        cloth = slip_line.total
                    if category == 'Transportation':
                        transportation = slip_line.total
                    if category == 'Wear':
                        wear = slip_line.total
                    if category == 'MEAL':
                        meal = slip_line.total
                    if category == 'COLA':
                        coal = slip_line.total
                    # if category == 'Gratuities':
                    #     gratuities = slip_line.total
                    if category == 'Benefits':
                        benefits = slip_line.total
                    if category == 'Deductions_short_loan':
                        deductions_short_loan = slip_line.total
                    if category == 'Deductions_long_loan':
                        deductions_long_loan = slip_line.total
                    if category == 'Total_Ded_Benefits':
                        deductions = slip_line.total
                    if category == 'NET':
                        Total_Net_Salary = slip_line.total


                    col = 5
                    excel_sheet.write(row, col, basic_salary, format)
                    col += 1
                    excel_sheet.write(row, col, gross, format)
                    col += 1
                    excel_sheet.write(row, col, cloth, format)
                    col += 1
                    excel_sheet.write(row, col, transportation, format)
                    col += 1
                    excel_sheet.write(row, col, wear, format)
                    col += 1
                    excel_sheet.write(row, col,meal, format)
                    col += 1
                    excel_sheet.write(row, col, coal, format)
                    col += 1
                    # excel_sheet.write(row, col, gratuities, format)
                    # col += 1
                    excel_sheet.write(row, col, benefits, format)
                    col += 1
                    excel_sheet.write(row, col, deductions_short_loan, format)
                    col += 1
                    excel_sheet.write(row, col, deductions_long_loan, format)
                    col += 1
                    excel_sheet.write(row, col, deductions, format)
                    col += 1
                    excel_sheet.write(row, col, Total_Net_Salary, format)
                    col += 1






        workbook.close()
        file_download = base64.b64encode(fp.getvalue())
        fp.close()
        wizardmodel = self.env['payslip.report.excel']
        res_id = wizardmodel.create({'name': file_name, 'file_download': file_download})
        return {
            'name': 'Files to Download',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'payslip.report.excel',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': res_id.id,
        }

    ############################################
    class payslip_report_excel(models.TransientModel):
        _name = 'payslip.report.excel'

        name = fields.Char('File Name', size=256, readonly=True)
        file_download = fields.Binary('File to Download', readonly=True)