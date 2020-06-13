
from odoo import models, fields, api,_
from datetime import datetime
from odoo.exceptions import UserError, AccessError ,ValidationError
from dateutil import relativedelta
from odoo.tools import float_compare


class contract_wizard(models.Model):
    _name='contract.wizard'

    start_date=fields.Date('Start Date',required=True)
    end_date=fields.Date('End Date', required=True,
                          default=str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10],
                          )
    product_id = fields.Many2one('product.template', 'Product')
    vendor_id = fields.Many2one('res.partner', 'Vendor')
    state = fields.Selection([
        ('open', 'Running'),
        ('close', 'Expired'),
    ], string='Status', track_visibility='onchange', help='Status of the contract')


    @api.multi
    def print_report(self):
        data = {}
        vehicles = []

        if self.start_date and self.end_date and self.product_id.id:
            records = self.env['purchase.contract.line'].search(
                [('line_id.date', '>=', self.start_date), ('line_id.date', '<=', self.end_date), ('product_id', '=', self.product_id.id)
                 ])

            data['records'] = records.ids
            data['start_date'] = self.start_date
            data['end_date'] = self.end_date
        if self.start_date and self.end_date and  self.vendor_id.id:
            records = self.env['purchase.contract.line'].search(
                [('line_id.date', '>=', self.start_date), ('line_id.date', '<=', self.end_date),
                 ('line_id.vendor_id', '=', self.vendor_id.id)
                 ])

            data['records'] = records.ids
            data['start_date'] = self.start_date
            data['end_date'] = self.end_date
        if self.start_date and self.end_date and self.state == False and self.product_id.id == False and self.vendor_id.id == False:
            records = self.env['purchase.contract.line'].search(
                [('line_id.date', '>=', self.start_date), ('line_id.date', '<=', self.end_date),
                 ])

            data['records'] = records.ids
            data['start_date'] = self.start_date
            data['end_date'] = self.end_date
        if self.start_date and self.end_date and self.state :
            records = self.env['purchase.contract.line'].search(
                [('line_id.date', '>=', self.start_date), ('line_id.date', '<=', self.end_date),
                 ('line_id.state', '=', self.state)
                 ])

            data['records'] = records.ids
            data['start_date'] = self.start_date
            data['end_date'] = self.end_date
        if self.start_date and self.end_date and self.product_id.id and self.vendor_id.id:
            records = self.env['purchase.contract.line'].search(
                [('line_id.date', '>=', self.start_date), ('line_id.date', '<=', self.end_date),
                 ('product_id', '=', self.product_id.id) , ('line_id.vendor_id', '=', self.vendor_id.id)
                 ])

            data['records'] = records.ids
            data['start_date'] = self.start_date
            data['end_date'] = self.end_date
        return self.env['report'].get_action(self, 'is_purchase_10.is_purchase_contract_template', data=data)


class is_contract_wazirds(models.AbstractModel):
    _name = 'report.is_purchase_10.is_purchase_contract_template'

    @api.model
    def render_html(self, docids,data):
        data['records']=self.env['purchase.contract.line'].browse(data['records'])
        docs=data['records']
        docargs = {

            'data': data,
            'docs': docs,
        }
        return self.env['report'].render('is_purchase_10.is_purchase_contract_template', docargs)
