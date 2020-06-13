
from odoo import models, fields, api,_
from datetime import datetime
from odoo.exceptions import UserError, AccessError ,ValidationError
from dateutil import relativedelta

class sales_product_report(models.Model):
    _name='sale.product.wizard'

    start_date=fields.Date('Start Date',required=True)
    end_date=fields.Date('End Date', required=True,
                          default=str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10],
                          )
    product_id = fields.Many2one('product.product','Product', required=True)


    @api.multi
    def print_report(self):
        data = {}
        vehicles = []
        if self.start_date and self.end_date:
            records = self.env['sale.order.line'].search(
                [('product_id', '=',self.product_id.id)
                ,('order_id.date_order', '>=', self.start_date),('order_id.date_order', '<=', self.end_date),('order_id.state', '=','sale')  ])

            data['records'] = records.ids
            data['start_date'] = self.start_date
            data['end_date'] = self.end_date
            # data['product_id'] = self.product_id.id
            # data['quantity'] = quantity
        return self.env['report'].get_action(self, 'is_sale_10.sales_product_template', data=data)


class is_fleet(models.AbstractModel):
    _name = 'report.is_sale_10.sales_product_template'


    @api.model
    def render_html(self, docids,data):
        # data['records'] = self.env['account.analytic.line'].browse(data['records'])
        data['records']=self.env['sale.order.line'].browse(data['records'])
        docs=data['records']
        docargs = {

            'data': data,
            'docs': docs,
        }
        return self.env['report'].render('is_sale_10.sales_product_template', docargs)