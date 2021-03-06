# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
import math


class product_state_wizard(models.TransientModel):
    _name = 'product.state.wizard'
    date_from = fields.Date('From Date', required="True")
    date_to = fields.Date('To Date', required="True")
    product_id = fields.Many2one('product.product','Product',required="True")




    @api.multi
    def create_report(self, data):
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['date_from', 'date_to', 'product_id'])
        print("iAM IN WIZARD....................", data['form'])
        return self.env['report'].get_action(self,'is_sale_10.product_state_template', data=data)


