# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
import math


class state_report_wizard(models.TransientModel):
    _name = 'state.report.wizard'
    date_from = fields.Date('From Date', required="True")
    date_to = fields.Date('To Date', required="True")
    state = fields.Many2one('res.country.state','State',required="True")
    city_id = fields.Many2one('city.state', string='City',required="True",domain="[('state_id','=',state)]")

    @api.multi
    def create_report(self, data):
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['date_from', 'date_to', 'state','city_id'])
        print("iAM IN WIZARD....................", data['form'])
        return self.env['report'].get_action(self,'is_sale_10.state_customer_template', data=data)


