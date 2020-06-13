# -*- coding: utf-8 -*-
from odoo import api, models, fields
from operator import itemgetter


#
# from openerp import api, models, fields
# from openerp.tools import float_round
# from openerp.exceptions import UserError, Warning

class state_report(models.AbstractModel):
    _name = 'report.is_sale_10.state_customer_template'

    def get_state(self):
        product_records = []
        all_records = []
        custmer = []
        active_ids = self._context.get('active_ids')
        states = self.env['state.report.wizard'].browse(active_ids)
        for obj in states:
            date_from = obj.date_from
            date_to = obj.date_to
            state = obj.state
            city_id = obj.city_id

        product_state =self.env['product.quantity.state'].search([('operation_id.min_date', '>=',date_from), ('operation_id.min_date', '<=', date_to),
             ('city', '=',city_id.id),('product_state', '=',state.id)])




        for state_order in product_state:
            if state_order.partner_id.id not in custmer :
                custmer.append(state_order.partner_id.id)

            if state_order.product_id.id not in product_records:
                product_records.append(state_order.product_id.id)
        for cstm in custmer:
            for product in product_records:
                product_ids = self.env['product.quantity.state'].search(
                    [('partner_id', '=', cstm), ('product_id', '=', product),])
                sum_qty = 0.0
                if product_ids:
                    for f in product_ids:
                        sum_qty += f.product_quantity

                    all_records.append({
                            'partner':f.partner_id.name,
                            'name':f.product_id.name,
                            'qty':sum_qty,
                        })
        sorted_lst = sorted(all_records, key=itemgetter('qty'), reverse=True)

        return sorted_lst


    @api.model
    def render_html(self, docids, data):
        self.model = self.env.context.get('active_model')
        docargs = {
            'doc_ids': self.ids,
            'doc_model': self,
            'docs': self,
            'data': data['form'],
            'state': data['form'][0]['state'],
            'city_id': data['form'][0]['city_id'],
            'date_from': data['form'][0]['date_from'],
            'date_to': data['form'][0]['date_to'], }
        if data['form'][0]['state'] :
            docargs['product_state'] = self.get_state()
        return self.env['report'].render('is_sale_10.state_customer_template', docargs)
