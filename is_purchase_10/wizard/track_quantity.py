
from odoo import models, fields, api,_
from datetime import datetime
from odoo.exceptions import UserError, AccessError ,ValidationError
from dateutil import relativedelta
from odoo.tools import float_compare


class track_wizard(models.Model):
    _name='track.wizard'

    start_date=fields.Date('Start Date',required=True)
    end_date=fields.Date('End Date', required=True,
                          default=str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10],
                          )
    product_id = fields.Many2one('product.template', string='Stander')
    ref_id = fields.Many2one('purchase.track.quantity', string='Reference No')


    @api.multi
    def print_report(self):
        data = {}
        vehicles = []

        if self.start_date and self.end_date and self.product_id.name:
            records = self.env['purchase.track.quantity'].search(
                [('date', '>=', self.start_date), ('date', '<=', self.end_date), ('stander_id', '=', self.product_id.name),
                 ])
            data['records'] = records.ids
            data['start_date'] = self.start_date
            data['end_date'] = self.end_date
            data['product_id'] = self.product_id.name
        if self.start_date and self.end_date and self.ref_id.id:
            records = self.env['purchase.track.quantity'].search(
                [('date', '>=', self.start_date), ('date', '<=', self.end_date),
                 ('id', '=', self.ref_id.id),
                 ])
        #
            data['records'] = records.ids
            data['start_date'] = self.start_date
            data['end_date'] = self.end_date

        if self.start_date and self.end_date and self.product_id.id == False and self.ref_id.id == False:
            records = self.env['purchase.track.quantity'].search(
                [('date', '>=', self.start_date), ('date', '<=', self.end_date),
                 ])

            data['records'] = records.ids
            data['start_date'] = self.start_date
            data['end_date'] = self.end_date
        return self.env['report'].get_action(self, 'is_purchase_10.is_purchase_track_template', data=data)


class is_track_wazirds(models.AbstractModel):
    _name = 'report.is_purchase_10.is_purchase_track_template'

    @api.model
    def render_html(self, docids,data):
        data['records']=self.env['purchase.track.quantity'].browse(data['records'])
        docs=data['records']
        docargs = {

            'data': data,
            'docs': docs,
        }
        return self.env['report'].render('is_purchase_10.is_purchase_track_template', docargs)
