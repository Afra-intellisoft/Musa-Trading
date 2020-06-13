from odoo import api, fields, models, _
from odoo.exceptions import UserError, Warning
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from odoo.tools import float_compare
import math
import babel
import time
from odoo import tools
import calendar
from odoo.exceptions import UserError, ValidationError



class request_taxes(models.Model):
    _name = 'request.taxes'
    _inherit = ['mail.thread']
    _description = "taxes Request"

    @api.model
    def create(self, vals):
        res = super(request_taxes, self).create(vals)
        next_seq = self.env['ir.sequence'].get('request.taxes.sequence')
        res.update({'tax_no': next_seq})
        return res

    name = fields.Char(string="Taxe Name" ,required=True)
    tax_no = fields.Char('Tax No')
    date = fields.Date(string="Date Request", default=fields.Date.today(), readonly=True)
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.user.company_id)
    debit_account = fields.Many2one('account.account', string="Debit Account")
    credit_account = fields.Many2one('account.account', string="Credit Account")
    journal_id = fields.Many2one('account.journal', string="Journal")
    tax_amount = fields.Float(string="Taxes Amount", required=True)
    attach = fields.Binary("Attachments", help="here you can attach a file or a document to the record !!")
    no_month = fields.Integer(string="No Of Month", default=1,required=True)
    payment_start_date = fields.Date(string="Start Date of Payment", required=True, default=fields.Date.today())
    tax_line_ids = fields.One2many('request.taxes.line', 'tax_id', string="tax Line")
    check_line_ids = fields.One2many('check.taxes.line', 'taxe_id', string="taxe Line")
    note = fields.Text(string=' Note')
    emp_note = fields.Text(string=' Note')
    rmain_amount = fields.Float(string="Rmaining Amount", compute="compute_rmaining_amount")
    state = fields.Selection(
        [('draft', 'To Submit'),
         ('finish', 'Finished')],
        'Status', readonly=True, track_visibility='onchange', copy=False, default='draft')

    @api.one
    def confirm(self):
        for x in self:
            x.state = 'finish'

    @api.one
    @api.constrains('tax_amount')
    def _check_amount(self):
        if self.tax_amount <= 0.0:
            raise ValidationError(_('The Tax Amount Must be Strictly positive.'))

    @api.depends('tax_line_ids.paid')
    def compute_rmaining_amount(self):
        for x in self:
            for y in x.tax_line_ids:
                if y.paid == True:
                     x.rmain_amount = x.tax_amount - y.paid_amount


    @api.multi
    def unlink(self):
        if any(bool(rec.tax_line_ids) for rec in self):
            raise UserError(_("You can not delete a payment that is already posted"))
        return super(request_taxes, self).unlink()





class tax_line(models.Model):
    _name = "request.taxes.line"
    _description = "taxes Request Line"

    name = fields.Char("name")
    paid_date = fields.Date(string="Payment Date", required=True)
    paid_amount = fields.Float(string="Paid Amount", required=True)
    paid = fields.Boolean(string="Paid")
    note = fields.Text(string="Notes")
    partner_id = fields.Many2one('res.partner', string="Customer")
    debit_account = fields.Many2one('account.account', string="Debit Account", required=True)
    # credit_account = fields.Many2one('account.account', string="Credit Account", required=True)
    journal_id = fields.Many2one('account.journal', string="Journal", required=True)
    move_id = fields.Many2one('account.move', string="Journal Entry", readonly=True)
    paid = fields.Boolean(string="Paid")
    check_no = fields.Integer('Check No.')
    tax_id = fields.Many2one('request.taxes', string="Loan Ref.", ondelete='cascade')

    @api.one
    def validate(self):
        if not self.debit_account or not self.credit_account or not self.journal_id:
            raise Warning(_("You Must Enter  &  Account and Journal to Create Entries "))
        can_close = False
        loan_obj = self.env['account.dollar.line']
        move_obj = self.env['account.move']
        move_line_obj = self.env['account.move.line']
        currency_obj = self.env['res.currency']
        created_move_ids = []
        line_ids = []
        for tax in self:
            dollar_ids = []
            debit_sum = 0.0
            credit_sum = 0.0
            tax_request_date = tax.paid_date
            reference = tax.tax_id.name
            journal_id = tax.journal_id.id
            paid_amount = tax.paid_amount
            partner_id = tax.partner_id.id
            company_id=tax.tax_id.company_id.id

            move_dict = {
                'name': reference,
                'narration': reference,
                'ref': reference,
                'journal_id': journal_id,
                'date': tax_request_date,
                'company_id':company_id,

            }

            if tax.paid == False:
                debit_line = (0, 0, {
                    'name': reference,
                    'partner_id': partner_id,
                    'account_id': tax.debit_account.id,
                    'journal_id': journal_id,
                    'date': tax_request_date,
                    'debit': paid_amount > 0.0 and paid_amount or 0.0,
                    'credit': paid_amount < 0.0 and -paid_amount or 0.0,
                    'analytic_account_id': False,
                })
                line_ids.append(debit_line)
                credit_line = (0, 0, {
                    'name': reference,
                    'partner_id': partner_id,
                    'account_id': self.journal_id.default_credit_account_id.id,
                    'journal_id': journal_id,
                    'date': tax_request_date,
                    'debit': paid_amount < 0.0 and -paid_amount or 0.0,
                    'credit': paid_amount > 0.0 and paid_amount or 0.0,
                    'analytic_account_id': False,
                })
                line_ids.append(credit_line)

        move_dict['line_ids'] = line_ids
        move = self.env['account.move'].create(move_dict)
        tax.write({'move_id': move.id, 'date': tax_request_date})
        move.post()
        tax.paid = True

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.move_id:
                raise Warning(_("Warning! You cannot delete a Taxes which paid") )
        return super(tax_line, self).unlink()

class check_tax_line(models.Model):
    _name = "check.taxes.line"
    _description = "Check Request Line"

    name = fields.Char("name")
    date = fields.Date(string="Payment Date", required=True)
    amount = fields.Float(string="Paid Amount", required=True)
    paid = fields.Boolean(string="Paid")
    note = fields.Text(string="Notes")
    bank_id = fields.Many2one('res.bank')
    account_holder = fields.Many2one('res.partner', string="Account Holder")
    check_no = fields.Char('Check No.')
    journal_id = fields.Many2one('account.journal', string='Payment Journal', required=True, domain=[('type', 'in', ('bank', 'cash'))])
    currency_id = fields.Many2one('res.currency', string='Currency',  default=lambda self: self.env.user.company_id.currency_id)
    taxe_id = fields.Many2one('request.taxes', string="Check Ref.")

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.paid == True:
                raise Warning(_("Warning! You  Cannot Delete A Check "))
        return super(check_tax_line, self).unlink()

    def create_check(self):
            inbound_manual = self.env.ref('check_followups.account_payment_method_check_outBound')
            for x in self:
                payment_dict = {
                    'amount': x.amount,
                    'journal_id': x.journal_id.id,
                    'currency_id': x.currency_id.id,
                    'payment_date': x.date,
                    'payment_method_id': inbound_manual.id,
                    'payment_type': 'outbound',
                    'partner_type': 'supplier',
                    'partner_id': x.account_holder.id,
                    'Check_no': x.check_no,
                    'Bank_id': x.bank_id.id,
                    'check_date': x.date,
                    'Account_No': x.check_no,
                }
            self.env['account.payment'].create(payment_dict).post()
            self.paid = True



