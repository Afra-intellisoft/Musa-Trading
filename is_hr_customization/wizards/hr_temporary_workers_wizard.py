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


class WizardTemporaryWorkers(models.Model):
    _name = 'wizard.temporary.workers'
    _description = 'Print Temporary Workers'
    from_date = fields.Date(string='Date From', required=True)
    to_date = fields.Date(string='Date To', required=True,
                          default=str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10],
                          )
    name = fields.Char(string=" Payment to Temporary Workers")

    @api.multi
    def print_report(self):
        for report in self:
            from_date = report.from_date
            to_date = report.to_date
            if self.from_date > self.to_date:
                raise UserError(_("You must be enter start date less than end date !"))
            report.name = ('Temporary Workers From ' + from_date + ' To ' + to_date)
            report_title = ('Temporary Workers From ' + from_date + ' To ' + to_date)
            file_name = _('Temporary Workers.xlsx')
            fp = BytesIO()
            workbook = xlsxwriter.Workbook(fp)
            excel_sheet = workbook.add_worksheet('Temporary Workers')
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
            excel_sheet.write(row, col, 'Amount', header_format)
            col += 1

            excel_sheet.set_column(0, 4, 25)
            excel_sheet.set_row(1, 25)
            excel_sheet.merge_range(0, 0, 1, 10, '', title_format)
            excel_sheet.merge_range(0, 0, 1, 10, report_title)
            excel_sheet.merge_range(3, 0, 4, 10, '', title_format)
            transport_lta_ids = report.env['hr.temporary.worker.paysheet'].search(
                [('date', '<=', to_date), ('date', '>=', from_date),])
            for payslip_period in transport_lta_ids:
                temporary = payslip_period.lta_temporary_ids
                for temp in temporary:
                    name = temp.name
                    amount = temp.amount
                    col = 0
                    row += 1
                    sequence_id += 1
                    excel_sheet.write(row, col, sequence_id, header_format_sequence)
                    col += 1
                    if name:
                        excel_sheet.write(row, col, name, format)
                    else:
                        excel_sheet.write(row, col, '', format)
                    col += 1
                    if amount:
                        excel_sheet.write(row, col, amount, format)
                    else:
                        excel_sheet.write(row, col, '', format)


        workbook.close()
        file_download = base64.b64encode(fp.getvalue())
        fp.close()
        wizardmodel = self.env['temporary.workers.excel']
        res_id = wizardmodel.create({'name': file_name, 'file_download': file_download})
        return {
            'name': 'Files to Download',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'temporary.workers.excel',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': res_id.id,
        }

    ############################################
    class temporary_workers_excel(models.TransientModel):
        _name = 'temporary.workers.excel'

        name = fields.Char('File Name', size=256, readonly=True)
        file_download = fields.Binary('File to Download', readonly=True)