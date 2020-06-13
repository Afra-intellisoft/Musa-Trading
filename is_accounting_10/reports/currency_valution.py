# -*- coding: utf-8 -*-
from odoo import api, models, fields
from operator import itemgetter


#
# from openerp import api, models, fields
# from openerp.tools import float_round
# from openerp.exceptions import UserError, Warning

class all_check_report(models.AbstractModel):
    _name = 'report.is_accounting_10.currency_valuation'

    def get_currency_valution(self):
        product_records = {}
        all_records = []
        all_record = []
        active_ids = self._context.get('active_ids')
        customer = self.env['currency.report.wizard'].browse(active_ids)
        for ch in customer:
            date_from = ch.date_from
            date_to = ch.date_to




        currency_id =self.env['account.dollar.line'].search([('date', '>=',date_from), ('date', '<=', date_to)])



        for valution in currency_id:
            date = valution.date
            request_currency = valution.request_currency.name
            amount_usd = valution.amount_usd
            rate = valution.rate
            amount_sdg = valution.amount_sdg


            all_records.append({
                        'date':date,
                        'request_currency':request_currency,
                        'amount_usd':amount_usd,
                        'rate':rate,
                        'amount_sdg':amount_sdg,


              })


        return all_records


    @api.model
    def render_html(self, docids, data):
        currency_ids = self.env['collect.currency'].search([])
        for x in currency_ids:
            average = x.average_dollar
        self.model = self.env.context.get('active_model')
        docargs = {
            'doc_ids': self.ids,
            'doc_model': self,
            'docs': self,
            'data': data['form'],
            'average':average,
            'date_from': data['form'][0]['date_from'],
            'date_to': data['form'][0]['date_to'], }
        print(docargs,'docargs')
        if data['form']:
            docargs['currency_id'] = self.get_currency_valution()
        return self.env['report'].render('is_accounting_10.currency_valuation', docargs)


