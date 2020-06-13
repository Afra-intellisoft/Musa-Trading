
from odoo import models, fields, api,_
from datetime import datetime
from odoo.exceptions import UserError, AccessError ,ValidationError
from dateutil import relativedelta
from odoo.tools import float_compare


class clearance_wizard(models.Model):
    _name='clearance.wizard'

    start_date=fields.Date('Start Date',required=True)
    end_date=fields.Date('End Date', required=True,
                          default=str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10],
                          )
    state = fields.Selection([
        ('open', 'Running'),
        ('done', 'Done'),
    ], string='Status', track_visibility='onchange', help='Status of the contract')
    number = fields.Many2one('customs.clearance',string="No C/C")
    partner_id = fields.Many2one('res.partner',string="Vendor")


    @api.multi
    def print_report(self):
        data = {}
        vehicles = []
        if self.start_date and self.end_date:
            records = self.env['customs.clearance'].search(
                [('date_order', '>=', self.start_date), ('date_order', '<=', self.end_date)
                 ])

            data['records'] = records.ids
            data['start_date'] = self.start_date
            data['end_date'] = self.end_date
            data['partner'] = self.partner_id.name
        if self.start_date and self.end_date and self.state:
            records = self.env['customs.clearance'].search(
                [('date_order', '>=', self.start_date), ('date_order', '<=', self.end_date), ('state', '=', self.state)
                 ])

            data['records'] = records.ids
            data['start_date'] = self.start_date
            data['end_date'] = self.end_date
            data['partner'] = self.partner_id.name
        if self.start_date and self.end_date and self.partner_id.id:
            records = self.env['customs.clearance'].search(
                [('date_order', '>=', self.start_date), ('date_order', '<=', self.end_date), ('partner_id', '=', self.partner_id.id),
                 ])

            data['records'] = records.ids
            data['start_date'] = self.start_date
            data['end_date'] = self.end_date
            data['partner'] = self.partner_id.name
        if self.start_date and self.end_date and self.number.id:
            records = self.env['customs.clearance'].search(
                [('date_order', '>=', self.start_date), ('date_order', '<=', self.end_date),
                 ('id', '=', self.number.id)
                 ])
            data['records'] = records.ids
            data['start_date'] = self.start_date
            data['end_date'] = self.end_date
        return self.env['report'].get_action(self, 'is_purchase_10.is_purchase_customs_clearance_template', data=data)


class is_clearance_wazirds(models.AbstractModel):
    _name = 'report.is_purchase_10.is_purchase_customs_clearance_template'

    @api.model
    def render_html(self, docids,data):
        data['records']=self.env['customs.clearance'].browse(data['records'])
        docs=data['records']
        docargs = {

            'data': data,
            'docs': docs,
        }
        return self.env['report'].render('is_purchase_10.is_purchase_customs_clearance_template', docargs)
