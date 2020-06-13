# -*- coding: utf-8 -*-
from odoo import api, models, fields
from operator import itemgetter

#
# from openerp import api, models, fields
# from openerp.tools import float_round
# from openerp.exceptions import UserError, Warning

class all_check_report(models.AbstractModel):
    _name = 'report.is_sale_10.all_state_template'

    def get_details(self):
        res = []
        product_records = {}
        product_list = []
        records = False
        active_ids = self._context.get('active_ids')
        type_state = self.env['all.state.wizard'].browse(active_ids)
        for rec in type_state:
            date_from = rec.date_from
            date_to = rec.date_to
            all_type = rec.all_type

        custmer = []
        city = []
        state = []
        product = []
        sum_qty = 0.0
        qty = 0.0
        if all_type == 'all_state':

            pqs_ids = self.env['product.quantity.state'].search(
                [('operation_id.min_date', '>=', date_from), ('operation_id.min_date', '<=', date_to)
                 ])

            for part in pqs_ids :
                qty += part.product_quantity
                if part.partner_id.id not in custmer :
                    custmer.append(part.partner_id.id)
                if part.city.id not in city:
                    city.append(part.city.id)
                if part.product_state.id not in state :
                    state.append(part.product_state.id)
                if part.product_id.id not in product :
                    product.append(part.product_id.id)
            for cstm in custmer :
                for cit in city :
                    for sta in state :
                        for pro in product :
                            qty_ids = self.env['product.quantity.state'].search([('product_id', '=', pro)])
                            qty2 = 0.0
                            if qty_ids:
                                for rec in qty_ids:
                                    qty2 += rec.product_quantity
                            city_ids = self.env['product.quantity.state'].search([('partner_id', '=', cstm),('city', '=', cit),('product_state', '=', sta),('product_id', '=', pro)])
                            sum_qty = 0.0
                            if city_ids:
                                for f in city_ids:
                                    sum_qty += f.product_quantity
                                precentage = (sum_qty * 100.0) / qty2
                                product_list.append({
                                           'partner_id':f.partner_id.name,
                                           'product_id':f.product_id.name,
                                           'quantity':sum_qty,
                                           'precentage':precentage,
                                           'city':f.city.name,
                                           'state':f.product_state.name,

                                        })
        result = [dict(tupleized) for tupleized in set(tuple(item.items()) for item in product_list)]
        sorted_lst = sorted(result, key=itemgetter('state','quantity'), reverse=True)
        return sorted_lst

    @api.model
    def render_html(self, docids, data):
        self.model = self.env.context.get('active_model')
        docargs = {
            'doc_ids': self.ids,
            'doc_model': self,
            'docs': self,
            'data': data['form'],
            'all_type': data['form'][0]['all_type'],
            'date_from': data['form'][0]['date_from'],
            'date_to': data['form'][0]['date_to'], }
        if data['form'][0]['all_type']:
            docargs['pqs_ids'] = self.get_details()
        return self.env['report'].render('is_sale_10.all_state_template', docargs)
