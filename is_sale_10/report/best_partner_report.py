# -*- coding: utf-8 -*-
from odoo import api, models, fields
from operator import itemgetter

#
# from openerp import api, models, fields
# from openerp.tools import float_round
# from openerp.exceptions import UserError, Warning

class best_partner_report(models.AbstractModel):
    _name = 'report.is_sale_10.best_partner_template'

    def get_details(self):
        res = []
        product_records = {}
        partner_list = []
        num_line = 0
        total_employee = 0
        records = False
        active_ids = self._context.get('active_ids')
        product = self.env['best.partner.wizard'].browse(active_ids)
        for rec in product:
            date_from = rec.date_from
            date_to = rec.date_to
            number = rec.no_of_partner

        custmer = []
        sum_total = 0.0
        pqs_ids = self.env['sale.order'].search(
            [('date_order', '>=', date_from), ('date_order', '<=', date_to),('state','=','sale')])
        for part in pqs_ids :
            if part.partner_id.id not in custmer :
                custmer.append(part.partner_id.id)
        for cstm in custmer :
            partner_id = self.env['sale.order'].search([('partner_id', '=', cstm)])
            sum_total = 0.0
            if partner_id:
               for f in partner_id:

                   sum_total += f.amount_total

               partner_list.append({
                   'partner_id':f.partner_id.name,
                   'amount_total':sum_total

                })

        result = [dict(tupleized) for tupleized in set(tuple(item.items()) for item in partner_list)]
        sorted_lst = sorted(result, key=itemgetter('amount_total'), reverse=True)[:number]
        return sorted_lst


    @api.model
    def render_html(self, docids, data):
        self.model = self.env.context.get('active_model')
        docargs = {
            'doc_ids': self.ids,
            'doc_model': self,
            'docs': self,
            'data': data['form'],
            'date_from': data['form'][0]['date_from'],
            'date_to': data['form'][0]['date_to'], }
        if data['form']:
            docargs['pqs_ids'] = self.get_details()
        return self.env['report'].render('is_sale_10.best_partner_template', docargs)
