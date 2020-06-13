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


class WizardMaintenanceVehicle(models.Model):
    _name = 'wizard.maintenance.vehicle'
    _description = 'Print Maintenance Vehicle'
    from_date = fields.Date(string='Date From', required=True)
    to_date = fields.Date(string='Date To', required=True,
                          default=str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10],
                          )
    name = fields.Char(string="Maintenance Vehicle")
    @api.multi
    def print_report(self):
        for report in self:
            vehicle_ids = False
            from_date = report.from_date
            to_date = report.to_date
            if self.from_date > self.to_date:
                raise UserError(_("You must be enter start date less than end date !"))
            file_name = _('Maintenance Vehicle.xlsx')
            fp = BytesIO()
            workbook = xlsxwriter.Workbook(fp)
            excel_sheet = workbook.add_worksheet('Maintenance Vehicle')
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
            excel_sheet.write(row, col, 'Vehicle', header_format)
            col += 1
            excel_sheet.write(row, col, 'Product', header_format)
            col += 1
            excel_sheet.write(row, col, 'Service', header_format)
            col += 1
            excel_sheet.write(row, col, 'Quantity', header_format)
            col += 1
            excel_sheet.write(row, col, 'Price', header_format)
            col += 1
            excel_sheet.set_column(0, 4, 20)
            excel_sheet.set_row(5, 20)
            excel_sheet.merge_range(1, 0, 2, 3, '', format)
            am_lst = []
            rs_lst = []
            sl_lst = []

            excel_sheet.cols_left_to_right = 1
            main_vehicle_ids = report.env['fleet.vehicle.log.services'].search(
                [('date', '<=', to_date), ('date', '>=', from_date), ('state', '=', 'purchases')])
            for vehicle in main_vehicle_ids:
                vehicle_id = vehicle.vehicle_id.name
                order = vehicle.cost_ids
                for main in order:
                    col = 0
                    row += 1
                    sequence_id += 1
                    product_id = main.product_id
                    price = main.amount
                    cost_subtype_id = main.cost_subtype_id
                    quantity = main.quantity
                    excel_sheet.write(row, col, sequence_id, header_format_sequence)
                    col += 1
                    if vehicle_id:
                        excel_sheet.write(row, col, vehicle_id, format)
                    else:
                        excel_sheet.write(row, col, '', format)
                    col += 1
                    if product_id:
                        excel_sheet.write(row, col, product_id.name, format)
                    else:
                        excel_sheet.write(row, col, '', format)
                    col += 1
                    if cost_subtype_id:
                        excel_sheet.write(row, col, cost_subtype_id.name, format)
                    else:
                        excel_sheet.write(row, col, '', format)
                    col += 1
                    if quantity:
                        excel_sheet.write(row, col, quantity, format)
                    else:
                        excel_sheet.write(row, col, '', format)
                    col += 1
                    if price:
                        excel_sheet.write(row, col, price, format)
                    else:
                        excel_sheet.write(row, col, '', format)
                    col += 1
                    col = 0
                row += 1
            # excel_sheet.merge_range(row, col, row, col + 4, 'Total', header_format)
            # excel_sheet.write_formula(row, 5, 'SUM(F' + str(first_row) + ':F' + str(row) + ')',header_format)
            workbook.close()
            file_download = base64.b64encode(fp.getvalue())
            fp.close()
            wizardmodel = self.env['vehicle.maintenance.excel']
            res_id = wizardmodel.create({'name': file_name, 'file_download': file_download})
            return {
                'name': 'Files to Download',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'vehicle.maintenance.excel',
                'type': 'ir.actions.act_window',
                'target': 'new',
                'res_id': res_id.id,
            }


############################################
class vehicle_maintenance_report_excel(models.TransientModel):
    _name = 'vehicle.maintenance.excel'

    name = fields.Char('File Name', size=256, readonly=True)
    file_download = fields.Binary('File to Download', readonly=True)
