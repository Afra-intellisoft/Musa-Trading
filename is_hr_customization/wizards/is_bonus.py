
from odoo import models, fields, api,_
from datetime import datetime
from odoo.exceptions import UserError, AccessError ,ValidationError
from dateutil import relativedelta

class IsBonusWizard(models.Model):
    _name='is.bonus.wizard'

    start_date=fields.Date('Start Date',required=True)
    end_date=fields.Date('End Date', required=True,
                          default=str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10],
                          )


    @api.multi
    def print_report(self):
        data = {}
        vehicles = []
        if self.start_date and self.end_date:
            records = self.env['hr.bonus.month'].search(
                [('date', '>=', self.start_date), ('date', '<=', self.end_date),
                 ])

            data['records'] = records.ids
            data['start_date'] = self.start_date
            data['end_date'] = self.end_date
            return self.env['report'].get_action(self, 'is_hr_customization.hr_bonus_template', data=data)


class is_wizards(models.AbstractModel):
    _name = 'report.is_hr_customization.hr_bonus_template'

    @api.model
    def render_html(self, docids,data):
        # data['00000000'] = self.env['account.analytic.line'].browse(data['records'])
        data['records']=self.env['hr.bonus.month'].browse(data['records'])
        docs=data['records']
        docargs = {

            'data': data,
            'docs': docs,
        }
        return self.env['report'].render('is_hr_customization.hr_bonus_template', docargs)
