
from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import UserError, AccessError, ValidationError
from dateutil import relativedelta

class OvertimeWizard(models.Model):
    _name = 'overtime.wizard'

    date_from = fields.Date('Start Date', required=True)
    date_to = fields.Date('End Date', required=True,
                           default=str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[
                                   :10],
                           )

    @api.multi
    def print_report(self):
        data = {}
        vehicles = []
        if self.date_from and self.date_to:
            records = self.env['hr.overtime.month'].search(
                [('date_from', '>=', self.date_from), ('date_to', '<=', self.date_to),
                 ])

            data['records'] = records.ids
            data['date_from'] = self.date_from
            data['date_to'] = self.date_to
            return self.env['report'].get_action(self, 'is_hr_customization.hr_overtime_template', data=data)

class is_wizards(models.AbstractModel):
    _name = 'report.is_hr_customization.hr_overtime_template'

    @api.model
    def render_html(self, docids, data):
        # data['00000000'] = self.env['account.analytic.line'].browse(data['records'])
        data['records'] = self.env['hr.overtime.month'].browse(data['records'])
        docs = data['records']
        docargs = {

            'data': data,
            'docs': docs,
        }
        return self.env['report'].render('is_hr_customization.hr_overtime_template', docargs)
