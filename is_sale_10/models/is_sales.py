#-*- coding: utf-8 -*-
import datetime
import logging
import re
import uuid
from collections import Counter, OrderedDict
from itertools import product
from werkzeug import urls
from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import except_orm, Warning, RedirectWarning
from odoo.tools.float_utils import float_is_zero, float_compare
import odoo.addons.decimal_precision as dp
from odoo.tools import amount_to_text_en, float_round
from odoo.tools import amount_to_text_en
import math


class SaleOrder(models.Model):
    _inherit = 'sale.order'


    @api.onchange('order_line')
    def request_new_price(self):
        for line in self.order_line:
            price = line.new_price
            if price > 0:
                self.price = True





    grade = fields.Many2one('product.grade',string="Grade")
    sale_type = fields.Selection([('internal', 'Internal Sale') ,('external', 'External Sale')], string='Sale Type',default='internal')
    net_kgs = fields.Char('Net Kgs')
    price = fields.Boolean('Price')
    total_kgs = fields.Char('Pkgs')
    other = fields.Char('Other')
    customs_id = fields.Many2one('customs.clearance.export', string="Reference")
    contract = fields.Boolean('Contract Request')
    check_amount_in_words = fields.Char(string="Amount in Words")
    packaging_details = fields.Char(string="Packaging Details")
    per_item = fields.Char(string=" Promotional Item")
    mark_number = fields.Char(string=" Marks Of Number")
    shipment_duration = fields.Char(string="Shipment Duration")
    production_date = fields.Date(string=" Production Date")
    expiration_date = fields.Date(string=" Expiration Date")
    bank_details = fields.Char(string=" Bank Details")
    other_condition = fields.Char(string="Other Condition")
    other_signature = fields.Char(string="Signature")
    other_stamp = fields.Char(string=" Stamp")
    signal_consign_id = fields.Many2one('final.consign',string=" Final Consign")
    destination_id = fields.Many2one('destination',string="Destination")
    notify_party_id = fields.Many2one('notify.party',string="Notify Party")
    ship_to = fields.Char(string="Ship To")
    note = fields.Text(string="NOTES")
    to_text = fields.Char('Amount in Words:', compute='_compute_text')
    get_total_special = fields.Float('aMOUNT', compute='get_special_price',store = True)
    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('sale', 'Sales Order'),
        ('mg', 'Manger Approval'),
        ('contract', 'Contract'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')

    @api.one
    @api.depends('get_total_special')
    def _compute_text(self):
        self.to_text =amount_to_text_en.amount_to_text(math.floor(self.get_total_special), lang='en', currency='')

    # @api.one
    # def manger_approve(self):
    #     self.state = 'sale'

    @api.one
    def Need_approval(self):
        self.state = 'mg'

    @api.constrains('partner_id')
    def spicify_ammount(self):
        total = 0.0
        if self.partner_id:
            check_amount = self.env['check_followups.check_followups'].search(
                [('account_holder', '=', self.partner_id.id)])
            for rec in check_amount:
                if rec.state == 'under_collection':
                    total += rec.amount
        if total > self.partner_id.amount and self.partner_id.amount != 0.0:
            raise Warning(_("This Customer Has Unpaid Checks .!"))



    @api.constrains('order_line')
    def specify_amount(self):
          for x in self :
              for rec in x.order_line:
                 gg = rec.price_unit
                 if rec.price_unit == 0.0:
                     raise ValueError(_('You Can Not Sell This Product Because It Does Not Have A Price.'))

    @api.depends('order_line.special_price')
    def get_special_price(self):
        total = 0.0
        for rec in self.order_line:
            total += rec.special_price
        self.get_total_special =  total

    @api.depends('get_total_special')
    def compute_text(self,get_total_special,currency):
        convert_amount_in_words = amount_to_text_en(get_total_special,lang='en',currency='')
        convert_amount_in_words = convert_amount_in_words.replace(' and Zero Cent','only')
        return convert_amount_in_words

    @api.one
    def contract_request(self):
        import_obj = self.env['sale.contract']
        self.contract = True
        contract_vals = {
            'state': 'draft',
            'reference': self.id,
            'date': self.confirmation_date,
            'vendor_id': self.partner_id.id,
            'pricelist_id': self.pricelist_id.id,
            'payment_term_id': self.payment_term_id.id,
            'delivery_location ': self.ship_to,
        }

        request_id = import_obj.create(contract_vals)
        for service in self.order_line:
            order_lines_vals = {'line_id': request_id.id,
                                'product_id': service.product_id.id,
                                # 'weight': service.weight,
                                'product_qty': service.product_uom_qty,
                                'product_uom_qty': service.product_uom.id,
                                'price': service.price_unit,
                                'discount': service.discount,
                                'name': service.name,
                                }
            line = self.env['sale.contract.line']
            line.create(order_lines_vals)
            # self.state = 'contract'




class Respartner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'
    amount= fields.Float('Amount')

class NotifyParty(models.Model):
    _name = 'notify.party'
    name = fields.Char('Name')

class Destination(models.Model):
    _name = 'destination'
    name = fields.Char('Name')

class FinalConsign(models.Model):
    _name = 'final.consign'
    name = fields.Char('Name')

class SalePersonBonus(models.Model):
    _name= 'sale.person.bonus'
    _inherit = ['mail.thread']

    name = fields.Char('Bonus No')
    notes = fields.Text('Note')
    request = fields.Boolean('Request')
    order_request = fields.Boolean('Request')
    # name = fields.Char('Bonus No')
    date = fields.Date('Date',default=fields.Date.today(), readonly=True)
    product_qty = fields.Float('Quantity')
    employee_id = fields.Many2one('hr.employee',string="Employee")
    partner_id = fields.Many2one('res.partner',string="Partner")
    invoice_id = fields.Many2one('account.invoice','Invoice')
    bonus_type = fields.Selection([('cash', 'Cash'), ('product', 'Product')],
                             string='Bonus Type', default='cash')
    request_amount = fields.Float('Bonus Amount', required=True)
    exp_account = fields.Many2one('account.account', string="Expense Account")
    journal_id = fields.Many2one('account.journal', 'Bank/Cash Journal',
                                 help='Payment journal.',
                                 domain=[('type', 'in', ['bank', 'cash'])])
    product_id = fields.Many2one('product.product','Product')

    move_id = fields.Many2one('account.move', 'Journal Entry', readonly=True)
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm')],
                             string='Bounce', default='draft')
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.user.company_id)
    request_currency = fields.Many2one('res.currency', 'Currency',
                                       default=lambda self: self.env.user.company_id.currency_id)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('done', 'Done'),
        ('refuse', 'Refused'),
        ('auditor', 'Auditor')
    ], string="State", default='draft', track_visibility='onchange', copy=False, )


    @api.one
    def order_stock(self):
        material_obj = self.env['material.request']
        material_vals = {
            'state': 'draft',
            'ordering_date': self.date,
            'applicant_name': self.employee_id.id,

        }
        request_id = material_obj.create(material_vals)
        material_order_lines_vals = {'request_id': request_id.id,
                                     'product_id': self.product_id.id,
                                     'description': self.product_id.name,
                                     'ordered_qty': self.product_qty,
                                     }
        line = self.env['material.request.line']
        line.create(material_order_lines_vals)
        self.request = True
        self.state = 'confirm'

    @api.one
    def order_hr_bonus(self):
        bonus_obj = self.env['hr.bonus.month']
        bonus_vals = {
            'state': 'draft',
            'name': self.name,
            'applicant_name': self.employee_id.id,

        }
        request_id = bonus_obj.create(bonus_vals)
        bonus_order_lines_vals = {'bonus_id': request_id.id,
                                     'employee_id': self.employee_id.id,
                                         'amount': self.request_amount,
                                     'invoice_id': self.invoice_id.id,
                                     'date_bonus': self.date,
                                     }
        line = self.env['hr.bonus.line']
        line.create(bonus_order_lines_vals)
        self.order_request = True
        self.state = 'done'


    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('sale.person.bonus') or '/'
        return super(SalePersonBonus, self).create(vals)

    def make_payment(self):
        self.validate_move()
        self.state = 'done'
        return True

    def cancel(self):
        self.move_id.button_cancel()
        self.move_id.unlink()
        self.state='cancel'

    @api.one
    def validate_move(self):
        dictionary = {
            'name': self.name,
            'account_holder': self.company_id.id,
            'check_amount': self.request_amount,

        }

        if not self.exp_account:
            raise Warning(_("Expense or debit account must be selected!"))

        if not self.journal_id:
            raise Warning(_("Journal must be selected!"))

        if self.request_currency == self.env.user.company_id.currency_id:
            line_ids = []
            untaxed_credit = (0, 0, {'move_id': self.move_id.id,
                                         'name': self.name,
                                         #'partner_id': self.beneficiary.id,
                                         'account_id': self.journal_id.default_debit_account_id.id,
                                         # 'analytic_account_id': self.analytic_account.id,
                                         'credit': self.request_amount,
                                         'currency_id': self.request_currency.id,
                                         #'amount_currency': -self.request_amount,
                                         'company_id': self.company_id.id,
                                         })
            line_ids.append(untaxed_credit)
            debit_val = (0, 0, {'move_id': self.move_id.id,
                                'name': self.name,
                                #'partner_id': self.beneficiary.id,
                                'account_id': self.exp_account.id,
                                'debit': self.request_amount,
                                'currency_id': self.request_currency.id,
                               # 'amount_currency': self.request_amount,
                                'company_id': self.company_id.id,
                                })

            line_ids.append(debit_val)
            vals = {
                'journal_id': self.journal_id.id,
                #'date': datetime.today(),
                'ref': self.name,
               # 'CS': self.beneficiary.id,
                'company_id': self.company_id.id,
                'line_ids': line_ids
            }
            # add lines
            self.move_id = self.env['account.move'].create(vals)

        elif self.request_currency != self.env.user.company_id.currency_id :
            line_ids = []
            credit_val = (0, 0, {'move_id': self.move_id.id,
                                     'name': self.name,
                                     #'partner_id': self.beneficiary.id,
                                     'account_id': self.journal_id.default_debit_account_id.id,
                                     # 'analytic_account_id': self.analytic_account.id,
                                     'credit': self.request_amount / self.request_currency.rate,
                                     'currency_id': self.request_currency.id,
                                     'amount_currency': -self.request_amount,
                                     'company_id': self.company_id.id,
                                     })
            line_ids.append(credit_val)

            debit_val = (0, 0, {'move_id': self.move_id.id,
                                'name': self.name,
                              #  'partner_id': self.beneficiary.id,
                                'account_id': self.exp_account.id,
                                'debit': self.request_amount / self.request_currency.rate,
                                'currency_id': self.request_currency.id,
                                'amount_currency': self.request_amount,
                                'company_id': self.company_id.id,
                                })
            line_ids.append(debit_val)
            vals = {
                'journal_id': self.journal_id.id,
                'date': datetime.today(),
                'ref': self.name,
                'CS': self.beneficiary.id,
                'company_id': self.company_id.id,
                'line_ids': line_ids
            }
            # add lines
            self.move_id = self.env['account.move'].create(vals)


        else:
            raise Warning(_("An issue was faced when validating!"))




class invoicecustom(models.Model):
    _inherit = 'account.invoice'

    policyholder= fields.Char('policyholder')
    contract_no = fields.Char('contract No')
    custom_no = fields.Char('customs NO')
    port_city = fields.Char('Port')
    payment_type = fields.Char('payment type')
    product_production = fields.Char('production Date')
    product_expiration = fields.Char('Expiration Dates ')
    sale_type = fields.Selection([('local', 'local sale'), ('external', 'external sale')],
                             srtring='Sale Type', default='local')


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    grade = fields.Many2one('product.grade',string=" STD Grade")
    net_kgs = fields.Float('Net Kgs',compute="amount_of_kgs",store = True)
    total_kgs = fields.Float('Pkgs')
    new_price = fields.Float('New Price',store=True, default=0.0)
    unit_in_page = fields.Char('Unit In One Page')
    std= fields.Char('STD')
    special_price= fields.Float('Price')
    price_unit = fields.Float('Unit Price',related="product_id.list_price", readonly=True,store=True, default=0.0)

    @api.depends('total_kgs','product_uom_qty')
    def amount_of_kgs(self):
       for x in self:
           x.net_kgs = x.product_uom_qty * x.total_kgs

    @api.multi
    def _prepare_invoice_line(self,qty):
        res = super(SaleOrderLine, self)._prepare_invoice_line(qty)
        res.update({
            'grade': self.grade.id,
            'net_kgs': self.net_kgs,
            'total_kgs': self.total_kgs
        })
        return res


    @api.onchange('product_id')
    def _onchange_product_id(self):
        self.total_kgs = self.product_id.weight

class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    grade = fields.Many2one('product.grade',string="Grade")
    net_kgs = fields.Char('Net Kgs')
    total_kgs = fields.Char('Pkgs')



class SaleContract(models.Model):
    _name = 'sale.contract'


    @api.multi
    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise Warning(
                    _("Warning! You cannot delete a Sale Contract which is in %s state.") % (rec.state))
            return super(SaleContract, self).unlink()

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('sale.contract') or '/'
        return super(SaleContract, self).create(vals)

    @api.constrains('line_ids')
    def request_price_validation(self):
        for line in self.line_ids:
            price = line.price
            product_qty = line.product_qty
            if price <= 0:
                raise Warning(_("Price Must be greater than zero!"))
            if product_qty <= 0:
                raise Warning(_("Quantity Must be greater than zero!"))

    @api.onchange('vendor_id')
    def _onchange_vendor_id(self):
        self.payment_term_id = self.vendor_id.property_payment_term_id.id

    name = fields.Char('Contract', readonly=True)
    sale_count = fields.Integer(compute='_compute_orders_number', string='Count', default=0, store=True,)
    invoice = fields.Char('Invoice Reference')
    reference = fields.Many2one('sale.order','Reference',readonly=True)
    note = fields.Text('Note')
    date_invoice = fields.Date('Date Invoice')
    delivery_location = fields.Char('Delivery Location')
    beneficiary = fields.Many2one('res.partner','Beneficiary')
    city = fields.Char('City')
    date = fields.Date('Date' ,default=fields.Date.today(), readonly=True)
    vendor_id = fields.Many2one('res.partner', string='Customer')
    currency_id = fields.Many2one('res.currency', string='Currency')
    date_from = fields.Date('Date From')
    date_to = fields.Date('Date To')
    line_ids = fields.One2many('sale.contract.line','line_id',string='Contract')
    request_ids = fields.One2many('customs.clearance.export','request_id',string='Contract')
    clearance = fields.Boolean('Clearance Request')
    state = fields.Selection([
            ('draft', 'New'),
            ('open', 'Running'),
            ('start_clearance', 'Start Clearance'),
            ('close', 'Close'),
        ], string='Status', track_visibility='onchange', help='Status of the contract', default='draft')

    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist',
                                   help="Pricelist for current sales order.")
    payment_term_id = fields.Many2one('account.payment.term', string='Payment Terms', oldname='payment_term')
    # invoiced = fields.Boolean(string='Invoiced', compute='_action_view_quotation', store=True)


    # @api.depends('line_ids')
    # def _action_view_quotation(self):
    #     for requisition in self:
    #         for invo in requisition.line_ids:
    #             if invo != 'no':
    #                 # raise UserError(_('In order to delete a purchase Request, you must cancel it first.'))
    #                 requisition.invoiced = True




    @api.depends('request_ids')
    def _compute_orders_number(self):
        for rec in self:
            rec.sale_count = len(rec.request_ids)
    @api.one
    def open_request(self):
        self.state = 'open'

    @api.one
    def clearance_request(self):
        import_obj = self.env['customs.clearance.export']
        self.clearance = True
        contract_vals = {
            'state': 'draft',
            'contract_id': self.id,
            'date': self.date,
            'vendor_id': self.vendor_id.id,
            # 'cultivate_id': self.cultivate_id.id,
            # 'contract_id': self.name,
        }
        request_id = import_obj.create(contract_vals)
        for service in self.line_ids:
            order_lines_vals = {'export_id': request_id.id,
                                'product_id': service.product_id.id,
                                'weight': service.weight,
                                'value_weight': service.value_weight,
                                'product_qty': service.qty_consumed,
                                'product_uom_qty': service.product_uom_qty.id,
                                'price': service.price,
                                # 'cultivate_id': self.cultivate_id.id,
                                }
            line = self.env['sale.contract.line']
            line.create(order_lines_vals)
            self.state = 'start_clearance'

class SaleContractLine(models.Model):
    _name = 'sale.contract.line'


    @api.onchange('product_id')
    def _onchange_product_id(self):
        self.weight = self.product_id.weight
        self.price = self.product_id.lst_price
        self.product_uom_qty = self.product_id.uom_id.id


    @api.multi
    @api.depends('weight','product_qty')
    def compute_weight(self):
        for rec in self:
            rec.value_weight = rec.weight * rec.product_qty

    @api.multi
    @api.depends('value_weight', 'price')
    def compute_total_qty(self):
        for rec in self:
            rec.total_qty = rec.price * rec.value_weight

    @api.multi
    @api.depends('product_qty', 'qty_remaining')
    def compute_count_quantity(self):
        for rec in self:
            rec.quantity = rec.product_qty - rec.qty_remaining

    name = fields.Char('Description')
    note = fields.Text('Note')
    request_id = fields.Many2one('sale.contract', string='Sale Agreement', ondelete='cascade',translate=True)
    container_number = fields.Char('Container No')
    code_number = fields.Char('Code No')
    path_number = fields.Char('Batch No')
    product_id = fields.Many2one('product.product', 'Product')
    total_qty = fields.Float('Total' ,compute="compute_total_qty", store=True)
    product_qty = fields.Float('Quantity')
    quantity = fields.Float('Quantity',compute="compute_count_quantity", store=True)
    weight = fields.Float('Weight')
    value_weight = fields.Float('Total Weight', compute="compute_weight")
    qty_consumed = fields.Float('Qty Consumed')
    qty_remaining = fields.Float('Qty Remaining')
    product_uom_qty = fields.Many2one('product.uom', string='Unit of measure')
    line_id = fields.Many2one('sale.contract', string='Contract')
    export_id = fields.Many2one('customs.clearance.export', string='Export')
    price = fields.Float('Price')
    discount = fields.Float('Discount (%)')
    expired = fields.Boolean('Expired', compute='compute_expired', store=True)


    @api.depends('product_qty', 'qty_remaining')
    def compute_expired(self):
        for rec in self:
            if rec.product_qty == rec.qty_remaining:
                rec.expired = True


    def _prepare_sale_order_line(self, name, product_qty=0.0, price_unit=0.0, taxes_ids=False):
        self.ensure_one()
        requisition = self.request_id
        qty = self.product_qty
        unit_of_measure = self.product_id.uom_po_id

        return {
            'name': name,
            'product_id': self.product_id.id,
            'product_uom_qty': self.product_id.uom_po_id.id,
            'product_qty': self.quantity,
            'price': price_unit,
            'weight': self.product_id.weight,
            'taxes_id': [(6, 0, taxes_ids)],
        }


    @api.multi
    @api.depends('product_qty', 'qty_consumed', 'qty_remaining')
    def compute_qty_remaining(self):
        for rec in self:
            rec.qty_remaining += rec.qty_consumed


class CustodyClearance(models.Model):
	_inherit = 'custody.clearance'

	export_id = fields.Many2one('customs.clearance.export', string="Customs Clearance")

class CustomsClearanceExport(models.Model):
    _inherit = ['ir.needaction_mixin', 'mail.thread']
    _name = 'customs.clearance.export'

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise Warning(
                    _("Warning! You cannot delete a Customs Clearance Export which is in %s state.") % (rec.state))
            return super(CustomsClearanceExport, self).unlink()

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('customs.clearance.export') or '/'
        return super(CustomsClearanceExport, self).create(vals)

    @api.multi
    @api.depends('bank_commission')
    def compute_total_bank(self):
        for rec in self:
            rec.total_bank =  rec.bank_commission

    @api.onchange('request_id')
    def _onchange_request_id(self):
        if not self.request_id:
            return

        requisition = self.request_id
        if self.vendor_id:
            partner = self.vendor_id
        else:
            partner = requisition.vendor_id
        payment_term =  partner.property_supplier_payment_term_id
        FiscalPosition = self.env['account.fiscal.position']
        fpos = FiscalPosition.get_fiscal_position(partner.id)
        fpos = FiscalPosition.browse(fpos)
        self.vendor_id = partner.id
        self.fiscal_position_id = fpos.id
        self.payment_term_id = payment_term.id,
        self.partner_ref = requisition.name
        self.pricelist_id = requisition.pricelist_id.id
        self.payment_term_id = requisition.payment_term_id.id
        self.date = self.date
        order_lines = []
        for line in requisition.line_ids:
            product_lang = line.product_id.with_context({
                'lang': partner.lang,
                'vendor_id': partner.id,
            })
            name = product_lang.display_name
            if product_lang.description_sale:
                name += '\n' + product_lang.description_sale
            if line.product_uom_qty != line.product_id.uom_po_id:
                product_qty = line.product_uom_qty._compute_quantity(line.qty_consumed, line.product_id.uom_po_id)
                price_unit = line.price_unit
            else:
                product_qty = line.qty_consumed
                price_unit = line.price
            order_line_values = line._prepare_sale_order_line(
                name=name, product_qty=product_qty, price_unit=price_unit,
                )
            order_lines.append((0, 0, order_line_values))
        self.export_ids = order_lines

    @api.one
    def approve_open(self):

        import_obj = self.env['sale.order']
        contract_vals = {
            'state': 'sale',
            'customs_id': self.id,
            'partner_id': self.vendor_id.id,
            # 'pricelist_id': self.pricelist_id.id,
            'payment_term_id': self.payment_term_id.id,
            'sale_type': 'external',
        }
        request_id = import_obj.create(contract_vals)
        export_ids = self.export_ids
        for service in export_ids:
            order_lines_vals = {'order_id': request_id.id,
                                'product_id': service.product_id.id,
                                'name': service.product_id.name,
                                'product_uom_qty': service.product_qty,
                                'product_uom': service.product_uom_qty.id,
                                'new_price': service.price,
                                'price_unit': service.price,
                                'net_kgs': service.value_weight,
                                'total_kgs': service.product_id.weight,
                                'price_subtotal': service.total_qty,
                                }
            line = self.env['sale.order.line']
            line.create(order_lines_vals)
            product_qty = service.product_qty
            form_ids = self.env['sale.contract.line'].search(
                [('line_id.name', '=', self.request_id.name), ('product_id', '=', service.product_id.id),
                 ('expired', '=', False),])
            if not form_ids:
                raise Warning(
                    _("This Product Has not available in Contract%s") % service.product_id.name)

            for line in form_ids:
                line.qty_remaining += product_qty
                if line.qty_remaining > line.product_qty:
                    raise UserError(_("The Qty consumed greater than qty approved"))
            self.state = 'open'
        xyz = form_ids[-1].line_id
        if any(form.expired == True for form in form_ids):
            xyz.state = 'close'

    name = fields.Char('Serial No', readonly=True)
    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist',
                                   help="Pricelist for current sales order.")
    payment_term_id = fields.Many2one('account.payment.term', string='Payment Terms', oldname='payment_term')
    contract_id = fields.Many2one('sale.contract','Reference', readonly=True)
    request_id = fields.Many2one('sale.contract','Reference')
    certificate_number = fields.Integer('Certificate No')
    clearance_amount = fields.Float('Custody Amount', compute="_compute_contracts_count")
    contracts_count = fields.Integer(string='Contracts', compute="_compute_contracts_count", store=True)
    export_custody_ids = fields.One2many('custody.clearance', 'export_id', string='Contract')
    invoice_no = fields.Char('Invoice No')
    order_id = fields.Many2one('sale.order', string='Order')
    bl_no = fields.Char('B/L No')
    done = fields.Boolean('Done')
    date_bl_no = fields.Date('Date B/L No')
    note_bl_no = fields.Text('Note')
    attach = fields.Binary(string="Upload File")
    journal_id = fields.Many2one('account.journal', 'Bank/Cash Journal',
                                 help='Payment journal.',
                                 domain=[('type', 'in', ['bank', 'cash'])])
    account_invoice_id = fields.Many2one('account.dollar', string='Count Rate')
    date = fields.Date('Date', default=fields.Date.today(), readonly=True)
    vendor_id = fields.Many2one('res.partner', string='Customer')
    export_ids = fields.One2many('sale.contract.line', 'export_id', string='Contract')
    bank_id = fields.Many2one('account.journal', 'Bank')
    bank_commission = fields.Float('Bank Commission')
    value_goods = fields.Float('Value Goods')
    currency_id = fields.Many2one('res.currency', string='Currency')
    account_debit_id = fields.Many2one('account.account', string='Account Debit')
    account_credit_id = fields.Many2one('account.account', string='Account Credit')
    move_id = fields.Many2one('account.move', string='Journal Entry', readonly=True)
    total_bank = fields.Float('Total', compute="compute_total_bank", store=True)
    docs_bank = fields.Boolean('Docs Bank')
    date_bank = fields.Date('Date')
    note_bank = fields.Text('Note')
    idbc = fields.Boolean('IDBC')
    date_idbc = fields.Date('Date')
    note_idbc = fields.Text('Note')
    note_docs = fields.Text('Note')
    shipping_time = fields.Boolean('Shipping Time')
    date_shipping_time = fields.Date('Date')
    note_shipping_time = fields.Text('Note')
    attach_shipping = fields.Binary(string="Upload File")
    appeal_signed = fields.Boolean('Appeal Signed')
    date_appeal_signed = fields.Date('Date')
    note_appeal_signed = fields.Text('Note')
    # contract_id = fields.Many2one('sale.contract', string='Contract')
    clearance = fields.Boolean('Clearance Request')
    shipment_arrive = fields.Boolean('Shipment Arrived')
    done_shipment_arrive = fields.Boolean('Done')
    date_arrive = fields.Date('Date')
    note_arrive = fields.Text('Note')
    eta = fields.Boolean('ETA')
    date_eta = fields.Date('Date')
    note_eta = fields.Text('Note')
    health = fields.Boolean('Health')
    date_health = fields.Date('Date')
    note_health = fields.Text('Note')
    health_no = fields.Char('Number')
    attach_health = fields.Binary(string="Upload File")
    inspector = fields.Boolean('Inspector')
    date_inspector = fields.Date('Date')
    note_inspector = fields.Text('Note')
    inspector_no = fields.Char('Number')
    attach_inspector = fields.Binary(string="Upload File")
    ssmo = fields.Boolean('SSMO')
    date_ssmo = fields.Date('Date')
    note_ssmo = fields.Text('Note')
    ssmo_no = fields.Char('Number')
    attach_ssmo = fields.Binary(string="Upload File")
    docs = fields.Boolean('Docs')
    done_docs = fields.Boolean('Done')
    docs_no = fields.Char('Number')
    date_docs = fields.Date('Date')
    note_docs = fields.Text('Note')
    attach_docs = fields.Binary(string="Upload File")
    other = fields.Boolean('Other')
    date_other = fields.Date('Date')
    note_other = fields.Text('Note')
    other_no = fields.Char('Number')
    attach_other= fields.Binary(string="Upload File")
    vassal_hooked = fields.Boolean('Vassal Hooked')
    date_vassal_hooked = fields.Date('Date')
    note_vassal_hooked = fields.Text('Note')
    moving_containers = fields.Boolean('Moving Containers')
    date_moving = fields.Date('Date')
    note_moving = fields.Text('Note')
    certificate_received = fields.Boolean('Certificate Received')
    date_certificate = fields.Date('Date')
    note_certificate = fields.Text('Note')
    done_clearance = fields.Boolean('Done')
    rent_car = fields.Boolean('Rent Car')
    amount_rent = fields.Float('Amount')
    date_rent = fields.Date('Date')
    note_rent = fields.Text('Note')
    examine_goods = fields.Boolean('Examine Goods')
    date_goods = fields.Date('Date')
    note_goods = fields.Text('Note')
    container_dispatch = fields.Boolean('Container Dispatch')
    date_container_dispatch = fields.Date('Date')
    note_container_dispatch = fields.Text('Note')
    total_amount_ex = fields.Float('Total Amount Clearance', compute="_compute_total_amount_ex",
                                          store=True)
    state = fields.Selection([
            ('draft', 'New'),
            ('open', 'Running'),
            ('done', 'Done'),
        ], string='Status', track_visibility='onchange', default='draft')


    @api.model
    def _needaction_domain_get(self):
        return [('state', '=', 'open')]

    @api.depends('export_custody_ids')
    def _compute_contracts_count(self):
        for rec in self:
            amount = 0.0
            customs = rec.export_custody_ids
            rec.contracts_count = len(rec.export_custody_ids)
            for obj in customs:
                amount += obj.custody_amount
            rec.clearance_amount = amount

    @api.multi
    @api.depends('amount_rent', 'bank_commission','clearance_amount')
    def _compute_total_amount_ex(self):
        for rec in self:
            rec.total_amount_ex = rec.bank_commission + rec.amount_rent + rec.clearance_amount

    @api.one
    def approve_done(self):
        self.done = True
        self.state = 'done'

    @api.onchange('container_dispatch')
    def _onchange_container_dispatch(self):
        if self.container_dispatch == True:
            self.date_container_dispatch = default = fields.Date.today()

    @api.onchange('examine_goods')
    def _onchange_examine_goods(self):
        if self.examine_goods == True:
            self.date_goods = default = fields.Date.today()

    @api.onchange('rent_car')
    def _onchange_rent_car(self):
        if self.rent_car == True:
            self.date_rent = default = fields.Date.today()

    @api.onchange('certificate_received')
    def _onchange_certificate_received(self):
        if self.certificate_received == True:
            self.date_certificate = default = fields.Date.today()
            self.done_clearance = True


    @api.onchange('vassal_hooked')
    def _onchange_vassal_hooked(self):
        if self.vassal_hooked == True:
            self.date_vassal_hooked = default = fields.Date.today()

    @api.onchange('moving_containers')
    def _onchange_moving_containers(self):
        if self.moving_containers == True:
            self.date_moving = default = fields.Date.today()

    @api.onchange('other')
    def _onchange_other(self):
        if self.other == True:
            self.date_other = default = fields.Date.today()

    @api.onchange('health')
    def _onchange_health(self):
        if self.health == True:
            self.date_health = default = fields.Date.today()

    @api.onchange('docs')
    def _onchange_docs(self):
        if self.docs == True:
            self.date_docs = default = fields.Date.today()
            self.done_docs = default = True

    @api.onchange('ssmo')
    def _onchange_ssmo(self):
        if self.ssmo == True:
            self.date_ssmo = default = fields.Date.today()

    @api.onchange('inspector')
    def _onchange_inspector(self):
        if self.inspector == True:
            self.date_inspector = default = fields.Date.today()

    @api.onchange('eta')
    def _onchange_eta(self):
        if self.eta == True:
            self.date_eta = default = fields.Date.today()

    @api.onchange('shipment_arrive')
    def _onchange_shipment_arrive(self):
        if self.shipment_arrive == True:
            self.date_arrive = default = fields.Date.today()
            self.done_shipment_arrive = True


    @api.onchange('docs_bank')
    def _onchange_docs_bank(self):
        if self.docs_bank == True:
            self.date_bank = default = fields.Date.today()


    @api.onchange('appeal_signed')
    def _onchange_appeal_signed(self):
        if self.appeal_signed == True:
            self.date_appeal_signed = default = fields.Date.today()


    @api.onchange('idbc')
    def _onchange_idbc(self):
        if self.idbc == True:
            self.date_idbc = default = fields.Date.today()

    @api.onchange('shipping_time')
    def _onchange_shipping_time(self):
        if self.shipping_time == True:
            self.date_shipping_time = default = fields.Date.today()


    @api.one
    def finance_approve(self):
        precision = self.env['decimal.precision'].precision_get('Clearance')
        self.env.cr.execute("""select current_date;""")
        xt = self.env.cr.fetchall()
        self.comment_date4 = xt[0][0]
        can_close = False
        move_obj = self.env['account.move']
        move_line_obj = self.env['account.move.line']
        currency_obj = self.env['res.currency']
        created_move_ids = []
        clearance_ids = []
        for clearance in self:
            line_ids = []
            debit_sum = 0.0
            credit_sum = 0.0
            clearance_request_date = clearance.date
            for obj in clearance:
                # amount = obj.total_amount_ex
                amount = obj.amount_rent
                reference = obj.journal_id.name
                journal_id = clearance.journal_id.id
                currency_id = clearance.currency_id.id
                move_dict = {
                    'narration': reference,
                    'ref': reference,
                    'journal_id': journal_id,
                    'currency_id': currency_id,
                    'date': clearance_request_date,
                }

                debit_line = (0, 0, {
                    'name': reference,
                    'partner_id': False,
                    'account_id': clearance.account_debit_id.id,
                    'journal_id': journal_id,
                    'currency_id': currency_id,
                    'date': clearance_request_date,
                    'debit': amount > 0.0 and amount or 0.0,
                    'credit': amount < 0.0 and -amount or 0.0,
                    'analytic_account_id': False,
                    'tax_line_id': 0.0,
                })
                line_ids.append(debit_line)
                debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']
                credit_line = (0, 0, {
                    'name': reference,
                    'partner_id': False,
                    'account_id': clearance.account_credit_id.id,
                    'journal_id': journal_id,
                    'currency_id': currency_id,
                    'date': clearance_request_date,
                    'debit': amount < 0.0 and -amount or 0.0,
                    'credit': amount > 0.0 and amount or 0.0,
                    'analytic_account_id': False,
                    'tax_line_id': 0.0,
                })
                line_ids.append(credit_line)
                credit_sum += credit_line[2]['credit'] - credit_line[2]['debit']
                if float_compare(credit_sum, debit_sum, precision_digits=precision) == -1:
                    acc_journal_credit = clearance.journal_id.default_credit_account_id.id
                    if not acc_journal_credit:
                        raise UserError(
                            _('The Expense Journal "%s" has not properly configured the Credit Account!') % (
                                clearance.journal_id.name))
                    adjust_credit = (0, 0, {
                        'name': _('Adjustment Entry'),
                        'partner_id': False,
                        'account_id': acc_journal_credit,
                        'journal_id': journal_id,
                        'currency_id': currency_id,
                        'date': clearance_request_date,
                        'debit': 0.0,
                        'credit': debit_sum - credit_sum,
                    })
                    line_ids.append(adjust_credit)

                elif float_compare(debit_sum, credit_sum, precision_digits=precision) == -1:
                    acc_journal_debit = clearance.journal_id.default_debit_account_id.id
                    if not acc_journal_debit:
                        raise UserError(_('The Expense Journal "%s" has not properly configured the Debit Account!') % (
                            clearance.journal_id.name))
                    adjust_debit = (0, 0, {
                        'name': _('Adjustment Entry'),
                        'partner_id': False,
                        'account_id': acc_journal_debit,
                        'journal_id': journal_id,
                        'currency_id': currency_id,
                        'date': clearance_request_date,
                        'debit': credit_sum - debit_sum,
                        'credit': 0.0,
                    })
                    line_ids.append(adjust_debit)

                move_dict['line_ids'] = line_ids
                move = self.env['account.move'].create(move_dict)
                clearance.write({'move_id': move.id, 'date': clearance_request_date})
                move.post()
            self.clearance = True

class ProductTemplate(models.Model):
    _inherit = 'product.template'
#
    @api.depends('qty_available')
    def compute_list_price(self):
        for rec in self:
            value_ids = self.env['stock.quant'].search([('product_id', '=', rec.id)])
            qty = 0.0
            qty_value = 0.0
            for value in value_ids:
                qty += value.qty
                qty_value += value.inventory_value
            if qty > 0.0:
                rec.average_price = qty_value / qty
                rec.average_price = qty_value / qty
                print( rec.average_price)

    average_price = fields.Float(string="Average Price", compute="compute_list_price")

class MarketValution(models.Model):
    _name = 'market.valuation'

    name = fields.Char('Name', required=True)
    valuation_date = fields.Date('Date', required=True)
    product_id = fields.Many2one('product.product', 'Product', required=True)
    note = fields.Text('Description', required=True)
