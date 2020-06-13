from odoo import models, fields, api,_
from datetime import datetime
from odoo.exceptions import UserError, AccessError ,ValidationError
from dateutil import relativedelta

class sales_bonus_report(models.Model):

    _name='sale.bonus.wizard'

    start_date=fields.Date('Start Date',required=True)
    end_date=fields.Date('End Date', required=True,
                          default=str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10],
                          )


    @api.multi
    def print_report(self):
        data = {}
        vehicles = []
        if self.start_date and self.end_date:
            records = self.env['sale.person.bonus'].search(
                [('date', '>=', self.start_date), ('date', '<=', self.end_date),
                 ])


            data['records'] = records.ids
            data['start_date'] = self.start_date
            data['end_date'] = self.end_date
            return self.env['report'].get_action(self, 'is_sale_10.is_sales_bonus_template', data=data)

            # return self.env['report'].get_action(self, 'is_sale_10.is_sales_bonus_template', data=data)


class is_bonus(models.AbstractModel):
    _name = 'report.is_sale_10.is_sales_bonus_template'


    @api.model
    def render_html(self, docids,data):
        data['records']=self.env['sale.person.bonus'].browse(data['records'])
        docs=data['records']
        docargs = {

            'data': data,
            'docs': docs,
        }
        return self.env['report'].render('is_sale_10.is_sales_bonus_template', docargs)