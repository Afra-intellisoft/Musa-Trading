# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from dateutil import relativedelta
import datetime



class OverTimeWizard(models.TransientModel):
    _name = 'overtime.wizard'

    date_from = fields.Date('From Date')
    date_to = fields.Date('To Date')




    @api.multi
    def print_report(self):
        # raise UserError('------------------')
        records = False
        data = {}
        if self.date_from and self.date_to:
            records = self.env['hr.overtime.month'].search([('date_from', '>=', self.date_from), ('date_to', '<=', self.date_to)])
            # print (customers_ids)
        data['records'] = records
        data['date_from'] = self.date_from
        data['date_to'] = self.date_to
        return self.env['report'].render('is_hr_customization.action_hr_overtime_template_report', records)
        # return self.env.ref('is_hr_customization.action_hr_overtime_template_report').report_action([], data=data)