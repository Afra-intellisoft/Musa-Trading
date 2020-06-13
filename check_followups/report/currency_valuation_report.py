# -*- coding: utf-8 -*-
from odoo import api, models, fields
from operator import itemgetter


#
# from openerp import api, models, fields
# from openerp.tools import float_round
# from openerp.exceptions import UserError, Warning

class all_check_report(models.AbstractModel):
    _name = 'report.is_sale_10.valuation_template'

    def get_sales(self):
        product_records = {}
        all_records = []
        active_ids = self._context.get('active_ids')
        customer = self.env['valution.report.wizard'].browse(active_ids)
        for ch in customer:
            date_from=ch.date_from
            date_to=ch.date_to


        market =self.env['market.valuation'].search([('valution_date', '>=',date_from), ('valution_date', '<=', date_to)])
        for valution in market:
          name = valution.name
          date = valution.valution_date
          text = valution.note

          all_records.append({
                    'name':name,
                    'date':date,
                    'text':text,
          })
        print all_records
        return all_records



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
            docargs['market'] = self.get_sales()
        return self.env['report'].render('is_sale_10.valuation_template', docargs)
