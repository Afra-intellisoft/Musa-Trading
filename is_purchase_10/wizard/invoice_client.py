
from odoo import models, fields, api,_
from datetime import datetime
from odoo.exceptions import UserError, AccessError ,ValidationError
from dateutil import relativedelta
from odoo.tools import float_compare


class client_wizard(models.Model):
    _name='client.wizard'

    start_date=fields.Date('Start Date',required=True)
    end_date=fields.Date('End Date', required=True,
                          default=str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10],
                          )
    vendor_id = fields.Many2one('res.partner', string='Supplier')
    grade_id = fields.Many2one('product.grade', string='Grade')
    lot_number = fields.Char('Lot No')
    auction_no = fields.Char('Auction NO')
    qty_remaining = fields.Boolean('Qty Remaining')


    @api.multi
    def print_report(self):
        data = {}
        vehicles = []
        if self.start_date and self.end_date and self.vendor_id.id :
            records = self.env['purchase.contract.line'].search(
                [('invoice_id.date', '>=', self.start_date), ('invoice_id.date', '<=', self.end_date),
                 ('invoice_id.partner_id', '=', self.vendor_id.id)
                 ])

            data['records'] = records.ids
            data['start_date'] = self.start_date
            data['end_date'] = self.end_date
            data['vendor'] = self.vendor_id.name
        if self.start_date and self.end_date and self.vendor_id.id and self.grade_id.id:
            records = self.env['purchase.contract.line'].search(
                [('invoice_id.date', '>=', self.start_date), ('invoice_id.date', '<=', self.end_date),
                 ('invoice_id.partner_id', '=', self.vendor_id.id), ('grade_id', '=', self.grade_id.id)
                 ])

            data['records'] = records.ids
            data['start_date'] = self.start_date
            data['end_date'] = self.end_date
            data['vendor'] = self.vendor_id.name
        if self.start_date and self.end_date and self.vendor_id.id and self.auction_no:
            records = self.env['purchase.contract.line'].search(
                [('invoice_id.date', '>=', self.start_date), ('invoice_id.date', '<=', self.end_date),
                 ('invoice_id.partner_id', '=', self.vendor_id.id), ('invoice_id.auction_no', '=', self.auction_no)
                 ])

            data['records'] = records.ids
            data['start_date'] = self.start_date
            data['end_date'] = self.end_date
            data['vendor'] = self.vendor_id.name
        if self.start_date and self.end_date and self.vendor_id.id and self.lot_number:
            records = self.env['purchase.contract.line'].search(
                [('invoice_id.date', '>=', self.start_date), ('invoice_id.date', '<=', self.end_date),
                 ('invoice_id.partner_id', '=', self.vendor_id.id), ('lot_number', '=', self.lot_number)
                 ])

            data['records'] = records.ids
            data['start_date'] = self.start_date
            data['end_date'] = self.end_date
            data['vendor'] = self.vendor_id.name
        if self.start_date and self.end_date and self.vendor_id.id and self.qty_remaining == True:
            records = self.env['purchase.contract.line'].search(
                [('invoice_id.date', '>=', self.start_date), ('invoice_id.date', '<=', self.end_date),
                 ('invoice_id.partner_id', '=', self.vendor_id.id), ('expired_order', '=', True)
                 ])

            data['records'] = records.ids
            data['start_date'] = self.start_date
            data['end_date'] = self.end_date
            data['vendor'] = self.vendor_id.name
        return self.env['report'].get_action(self, 'is_purchase_10.is_purchase_client_template', data=data)


class is_client_wazirds(models.AbstractModel):
    _name = 'report.is_purchase_10.is_purchase_client_template'

    @api.model
    def render_html(self, docids,data):
        data['records']=self.env['purchase.contract.line'].browse(data['records'])
        docs=data['records']
        docargs = {

            'data': data,
            'docs': docs,
        }
        return self.env['report'].render('is_purchase_10.is_purchase_client_template', docargs)
