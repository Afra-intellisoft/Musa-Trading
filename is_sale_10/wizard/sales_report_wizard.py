
from odoo import models, fields, api,_
from datetime import datetime
from odoo.exceptions import UserError, AccessError ,ValidationError
from dateutil import relativedelta

class sales_report(models.Model):
    _name='sale.report.wizard'

    start_date=fields.Date('Start Date',required=True)
    end_date=fields.Date('End Date', required=True,
                          default=str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10],
                          )


    @api.multi
    def print_report(self):
        data = {}
        vehicles = []
        if self.start_date and self.end_date:
            records = self.env['sale.order'].search(
                [('date_order', '>=', self.start_date), ('date_order', '<=', self.end_date), ('state', '=', 'sale'),
                 ])


            data['records'] = records.ids
            data['start_date'] = self.start_date
            data['end_date'] = self.end_date
            # data['cost_subtype_id'] = cost_subtype_id
            # data['quantity'] = quantity
            return self.env['report'].get_action(self, 'is_sale_10.sales_template', data=data)


class is_sale(models.AbstractModel):
    _name = 'report.is_sale_10.sales_template'


    @api.model
    def render_html(self, docids,data):
        # data['records'] = self.env['account.analytic.line'].browse(data['records'])
        data['records']=self.env['sale.order'].browse(data['records'])
        docs=data['records']
        docargs = {

            'data': data,
            'docs': docs,
        }
        return self.env['report'].render('is_sale_10.sales_template', docargs)