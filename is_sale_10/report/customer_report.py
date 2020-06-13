# -*- coding: utf-8 -*-
from odoo import api, models, fields
from operator import itemgetter


#
# from openerp import api, models, fields
# from openerp.tools import float_round
# from openerp.exceptions import UserError, Warning

class all_check_report(models.AbstractModel):
    _name = 'report.is_sale_10.sales_customer_template'

    def get_sales(self):
        product_records = {}
        all_records = []
        active_ids = self._context.get('active_ids')
        customer = self.env['customer.report.wizard'].browse(active_ids)
        for ch in customer:
            date_from=ch.date_from
            date_to=ch.date_to
            partner_id=ch.partner_id

        sales =self.env['sale.order'].search([('date_order', '>=',date_from), ('date_order', '<=', date_to),
             ('state', '=','sale'),('partner_id', '=',partner_id.id)])
        for sale_order in sales:
            for sale in sale_order.order_line:
                if sale.product_id not in product_records:
                    product_records.update({sale.product_id.id: 0})

        for product in product_records:

            partner_sales = self.env['sale.order.line'].search([
                ('order_id.date_order', '>=', date_from), ('order_id.date_order', '<=', date_to),
                ('order_id.state', '=', 'sale'), ('order_id.partner_id', '=', partner_id.id),('product_id', '=', product)])
            sum_partner_sales = sum(partner_sales.mapped('product_uom_qty'))

            all_sales = self.env['sale.order.line'].search([
                ('order_id.date_order', '>=', date_from), ('order_id.date_order', '<=', date_to),
                ('order_id.state', '=', 'sale'),
                ('product_id', '=', product)])
            sum_all_sales = sum(all_sales.mapped('product_uom_qty'))
            product = self.env['product.product'].search([('id','=' , product)])
            precentage = ( sum_partner_sales * 100.0) / sum_all_sales
            print(precentage,'jh')

            all_records.append({
                    'partner':partner_id.name,
                    'name':product.name,
                    'qty':sum_partner_sales,
                    'precentage':precentage
                })
        print all_records
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
            'partner_id': data['form'][0]['partner_id'],
            'date_from': data['form'][0]['date_from'],
            'date_to': data['form'][0]['date_to'], }
        if data['form'][0]['partner_id']:
            docargs['sales'] = self.get_sales()
        return self.env['report'].render('is_sale_10.sales_customer_template', docargs)
