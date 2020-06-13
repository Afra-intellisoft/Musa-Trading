
from odoo import models, fields, api,_
from datetime import datetime
from odoo.exceptions import UserError, AccessError ,ValidationError
from dateutil import relativedelta
from odoo.tools import float_compare


class cultivate_wizard(models.Model):
    _name='cultivate.wizard'

    start_date=fields.Date('Start Date',required=True)
    end_date=fields.Date('End Date', required=True,
                          default=str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10],
                          )
    product_id = fields.Many2one('product.agriculture', 'Category')
    qty_remaining = fields.Boolean('Qty Remaining')
    qty_consumed = fields.Boolean('Qty Consumed')


    @api.multi
    def print_report(self):
        data = {}
        vehicles = []
        if self.start_date and self.end_date and self.product_id  and self.qty_remaining == False and self.qty_consumed == False:
            records = self.env['purchase.contract.line'].search(
                [('cultivate_id.date', '>=', self.start_date), ('cultivate_id.date', '<=', self.end_date), ('product_id.agriculture_id', '=', self.product_id.id)
                 ])
            data['records'] = records.ids
            data['start_date'] = self.start_date
            data['end_date'] = self.end_date
            data['agriculture'] = self.product_id.name
        if self.start_date and self.end_date and self.product_id and self.qty_remaining == True  and self.qty_consumed == False :
            records = self.env['purchase.contract.line'].search(
                [('cultivate_id.date', '>=', self.start_date), ('cultivate_id.date', '<=', self.end_date),
                 ('product_id.agriculture_id', '=', self.product_id.id),('expired_agricultural', '=', True),
                 ])
            data['records'] = records.ids
            data['start_date'] = self.start_date
            data['end_date'] = self.end_date
            data['agriculture'] = self.product_id.name
        if self.start_date and self.end_date and self.product_id and self.qty_remaining == False and self.qty_consumed == True:
            records = self.env['purchase.contract.line'].search(
                [('cultivate_id.date', '>=', self.start_date), ('cultivate_id.date', '<=', self.end_date),
                 ('product_id.agriculture_id', '=', self.product_id.id), ('expired_agricultural', '=', False),
                 ])
            data['records'] = records.ids
            data['start_date'] = self.start_date
            data['end_date'] = self.end_date
            data['agriculture'] = self.product_id.name

        return self.env['report'].get_action(self, 'is_purchase_10.is_purchase_cultivate_template', data=data)


class is_cultivate_wazirds(models.AbstractModel):
    _name = 'report.is_purchase_10.is_purchase_cultivate_template'

    @api.model
    def render_html(self, docids,data):
        data['records']=self.env['purchase.contract.line'].browse(data['records'])
        docs=data['records']
        docargs = {

            'data': data,
            'docs': docs,
        }
        return self.env['report'].render('is_purchase_10.is_purchase_cultivate_template', docargs)
