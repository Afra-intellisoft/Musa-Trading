# -*- coding: utf-8 -*-
from odoo import api, models, fields
from operator import itemgetter

#
# from openerp import api, models, fields
# from openerp.tools import float_round
# from openerp.exceptions import UserError, Warning

class all_check_report(models.AbstractModel):
    _name = 'report.is_sale_10.product_state_template'

    def get_details(self):
        res = []
        product_records = {}
        product_list = []
        records = False
        active_ids = self._context.get('active_ids')
        product = self.env['product.state.wizard'].browse(active_ids)
        for rec in product:
            date_from = rec.date_from
            date_to = rec.date_to
            product_id = rec.product_id

        partner_ids = self.env['res.partner'].search([])
        custmer = []
        city = []
        state = []
        product = []
        sum_qty = 0.0
        qty = 0.0
        pqs_ids = self.env['product.quantity.state'].search(
            [('operation_id.min_date', '>=', date_from), ('operation_id.min_date', '<=', date_to),
             ('product_id','=',product_id.id),
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
                        city_ids = self.env['product.quantity.state'].search([('partner_id', '=', cstm),('city', '=', cit),('product_state', '=', sta),('product_id', '=', pro)])
                        sum_qty = 0.0
                        if city_ids:
                            for f in city_ids:
                                sum_qty += f.product_quantity
                            precentage = (sum_qty * 100.0) / qty
                            product_list.append({
                                       'partner_id':f.partner_id.name,
                                       'quantity':sum_qty,
                                       'precentage':precentage,
                                       'city':f.city.name,
                                       'state':f.product_state.name,

                                    })
        result = [dict(tupleized) for tupleized in set(tuple(item.items()) for item in product_list)]
        sorted_lst = sorted(result, key=itemgetter('quantity'), reverse=True)
        return sorted_lst

    @api.model
    def render_html(self, docids, data):
        self.model = self.env.context.get('active_model')
        docargs = {
            'doc_ids': self.ids,
            'doc_model': self,
            'docs': self,
            'data': data['form'],
            'product_id': data['form'][0]['product_id'],
            'date_from': data['form'][0]['date_from'],
            'date_to': data['form'][0]['date_to'], }
        if data['form'][0]['product_id']:
            docargs['pqs_ids'] = self.get_details()
        return self.env['report'].render('is_sale_10.product_state_template', docargs)
