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



class zaka_account(models.Model):
    _name = 'zaka.account'
    _inherit = ['mail.thread']
    _description = "zaka Request"


    @api.model
    def create(self, vals):
        res = super(zaka_account, self).create(vals)
        next_seq = self.env['ir.sequence'].get('zaka.account.sequence')
        res.update({'zaka_no': next_seq})
        return res

    name = fields.Char(string="Name",required=True)
    zaka_no = fields.Char('Zaka No')

    date = fields.Date(string="Date Request", default=fields.Date.today())

    # from_date = fields.Date('From Date',required=True)
    # to_date = fields.Date('To Date',required=True)
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.user.company_id,required=True)

    zakah_debit = fields.Many2one('account.account', string="Debit Account")
    zakah_credit = fields.Many2one('account.account', string="Credit Account")
    journal_id = fields.Many2one('account.journal', string="Journal")
    # zakah_amount = fields.Float(string="Zakah Amount", compute="compute_zakah",store=True)

    move_id = fields.Many2one('account.move', string="Journal Entry", readonly=True)
    refund_move_id = fields.Many2one('account.move', string="Journal Refund Entry", readonly=True)
    amount = fields.Float(string='Amount' ,required=True)
    zakah_note = fields.Text(string=' Note')
    note = fields.Text(string=' Note')
    state = fields.Selection(
        [('draft', 'To Submit'),
         ('finish', 'Finished')],
        'Status', readonly=True, track_visibility='onchange', copy=False, default='draft')
    zakah_line_ids = fields.One2many('zaka.account.line', 'zakah_id', string="zakah Line", index=True)
    check_line_ids = fields.One2many('check.zakat.line', 'zakat_check_id', string="zakah Line", index=True)
    rmain_amount = fields.Float(string="Rmaining Amount", compute="compute_rmaining_amount")

    @api.multi
    def unlink(self):
        if any(bool(rec.zakah_line_ids) for rec in self):
            raise UserError(_("You can not delete a payment that is already posted"))
        return super(zaka_account, self).unlink()

    @api.one
    def confirm(self):
        for x in self:
            x.state = 'finish'


    @api.depends('zakah_line_ids.paid')
    def compute_rmaining_amount(self):
        for x in self:
            for y in x.zakah_line_ids:
                if y.paid == True:
                    x.rmain_amount = x.amount - y.amount

    @api.one
    @api.constrains('tax_amount')
    def _check_amount(self):
        if self.amount <= 0.0:
            raise ValidationError(_('The Tax amount must be strictly positive.'))

    @api.multi
    def compute_zakah(self):
        initial_balance = 0.0
        total_debit_liability = 0.0
        total_credit_liability = 0.0
        total_balance_liability = 0.0
        liabilities_balance = 0.0
        zk = 0.0

        assets_accounts = self.env['account.account'].search([('user_type_id.name', '=', 'Current Assets')])
        for asset_account in assets_accounts:
            balance_debit = 0.0
            balance_credit = 0.0
            total_balance_assets = 0.0
            total_credit_assets = 0.0
            total_debit_assets = 0.0
            balance_amount =0.0
            curr_balance = 0.0
            payable_balance = 0.0

            asset_ids = False
            account_name = asset_account.code + ' ' + asset_account.name
            if self.to_date and self.from_date:
                asset_ids = self.env['account.move.line'].search([('account_id', '=', asset_account.id),
                                                                          ('move_id.state', '=', 'posted'),
                                                                          ('date', '>=', self.from_date),
                                                                          ('date', '<=', self.to_date)])

                if asset_ids:
                    for balance in asset_ids:
                        balance_debit += balance.debit
                        balance_credit += balance.credit
                    account_balance = balance_debit - balance_credit
                    # balance_amount += initial_balance
                    # total_debit_assets += balance_debit
                    # total_credit_assets += balance_credit
                    # total_balance_assets = account_balance
                    curr_balance = account_balance
                    print(curr_balance, 'ass')

        Ban_Cash_accounts = self.env['account.account'].search([('user_type_id.name', '=', 'Bank and Cash')])
        for account_bank in Ban_Cash_accounts:
            bank_debit = 0.0
            bank_credit = 0.0
            bank_balance = 0.0
            bank_amount = 0.0
            total_cash_balance = 0.0


            ban_cash_ids = False
            bank_name = account_bank.code + ' ' + account_bank.name
            if self.to_date and self.from_date:
                ban_cash_ids = self.env['account.move.line'].search([('account_id', '=', account_bank.id),
                                                                  ('move_id.state', '=', 'posted'),
                                                                  ('date', '>=', self.from_date),
                                                                  ('date', '<=', self.to_date)])

                if ban_cash_ids:
                    for bank in ban_cash_ids:
                        bank_debit += bank.debit
                        bank_credit += bank.credit
                    bank_balance = bank_debit - bank_credit
                    # total_debit_assets += bank_debit
                    # total_credit_assets += bank_credit
                    # total_balance_assets += bank_balance
                    # total_cash_balance += bank_balance
                    bank_amount = bank_balance
                    print(bank_amount, 'cas bank')

        Receivable_accounts = self.env['account.account'].search([('user_type_id.name', '=', 'Receivable')])
        for account_rec in Receivable_accounts:
            receivable_credit = 0.0
            receivable_debit = 0.0
            receivable_balance = 0.0
            total_rec_balance = 0.0


            Receivable_ids = False
            account_name = account_rec.code + ' ' + account_rec.name
            if self.to_date and self.from_date:
                    Receivable_ids = self.env['account.move.line'].search([('account_id', '=', account_rec.id),
                                                                         ('move_id.state', '=', 'posted'),
                                                                         ('date', '>=', self.from_date),
                                                                         ('date', '<=', self.to_date)])

                    if Receivable_ids:
                        for receivable in Receivable_ids:
                            receivable_debit += receivable.debit
                            receivable_credit += receivable.credit
                        receivable_balance = receivable_debit - receivable_credit
                        # total_debit_assets += receivable_debit
                        # total_credit_assets += receivable_credit
                        # total_balance_assets += receivable_balance
                        total_rec_balance = receivable_balance
                        # balance_amount += initial_balance
                    print(total_rec_balance,'rec')

        Payable_accounts = self.env['account.account'].search([('user_type_id.name', '=', '	Payable')])
        total_debit_liability = 0.0
        total_credit_liability = 0.0
        for payable_liability in Payable_accounts:
            payable_liability_debit = 0.0
            payable_liability_credit = 0.0
            payable_liability_balance = 0.0
            card_liability_amount = 0.0
            total_debit_liability = 0.0
            total_credit_liability = 0.0
            total_balance_liability = 0.0
            liabilities_balance = 0.0

            Payable_ids = False
            account_name = payable_liability.code + ' ' + payable_liability.name
            if self.to_date and self.from_date:
                Payable_ids = self.env['account.move.line'].search([('account_id', '=', payable_liability.id),
                                                                       ('move_id.state', '=', 'posted'),
                                                                       ('date', '>=', self.from_date),
                                                                       ('date', '<=', self.to_date)])

                if Payable_ids:

                    for payable_liability_id in Payable_ids:
                        payable_liability_debit += payable_liability_id.debit
                        payable_liability_credit += payable_liability_id.credit
                    payable_liability_balance = payable_liability_debit - payable_liability_credit
                    # total_debit_liability += payable_liability_debit
                    # total_credit_liability += payable_liability_credit
                    # total_balance_liability += payable_liability_balance
                    payable_balance = payable_liability_balance
                    print(payable_balance, 'pay')

        currnt_Liabilities_accounts = self.env['account.account'].search([('user_type_id.name', '=', 'Current Liabilities')])
        for current_liability_id in currnt_Liabilities_accounts:
            current_liability_debit = 0.0
            current_liability_credit = 0.0
            current_liability_balance = 0.0
            current_liability_amount = 0.0

            currnt_Liabilities_ids = False
            account_name = current_liability_id.code + ' ' + current_liability_id.name
            if self.to_date and self.from_date:
                currnt_Liabilities_ids = self.env['account.move.line'].search([('account_id', '=', current_liability_id.id),
                                                                    ('move_id.state', '=', 'posted'),
                                                                    ('date', '>=', self.from_date),
                                                                    ('date', '<=', self.to_date)])

                if currnt_Liabilities_ids:
                    for liability_id in currnt_Liabilities_ids:
                        current_liability_debit += liability_id.debit
                        current_liability_credit += liability_id.credit
                    current_liability_balance = current_liability_debit - current_liability_credit
                    # total_debit_liability += current_liability_debit
                    # total_credit_liability += current_liability_credit
                    # total_balance_liability += current_liability_balance
                    liabilities_balance = current_liability_balance
                    print(liabilities_balance, 'cuur l')

        non_currnt_Liabilities_accounts = self.env['account.account'].search([('user_type_id.name', '=', 'Non-current Liabilities')])
        for non_current in non_currnt_Liabilities_accounts:
            non_liability_debit = 0.0
            non_liability_credit = 0.0
            non_liability_balance = 0.0
            non_liability_amount = 0.0

            non_Liabilities_ids = False
            account_name = non_current.code + ' ' + non_current.name
            if self.to_date and self.from_date:
                non_Liabilities_ids = self.env['account.move.line'].search([('account_id', '=', non_current.id),
                                                                    ('move_id.state', '=', 'posted'),
                                                                    ('date', '>=',self. from_date),
                                                                    ('date', '<=',self. to_date)])

                if non_Liabilities_ids:
                    for non_liability_id in currnt_Liabilities_ids:
                        non_liability_debit += non_liability_id.debit
                        non_liability_credit += non_liability_id.credit
                        # non_liability_balance = non_liability_debit - non_liability_credit
                    # total_debit_liability = non_liability_debit
                    # total_credit_liability = non_liability_credit
                    total_balance_liability = total_debit_liability - total_credit_liability
                    # liabilities_balance += non_liability_balance
                    print(total_balance_liability, 'non cuur ')

        total = curr_balance +  bank_amount + total_rec_balance
        total2= liabilities_balance + total_balance_liability + payable_balance
        total3=  total2 - total
        zk = total3 / 40
        self.zakah_amount = zk
        self.state ='compute'

    @api.one
    def zakah_validate(self):
        for x in self:
            x.state ='confirm'

    @api.one
    def loan_refuse(self):
        for x in self:
            x.state = 'refuse'

class zaka_account_line(models.Model):
    _name = 'zaka.account.line'
    _inherit = ['mail.thread']
    _description = "zaka Request"


    name = fields.Char(string="Name")
    zaka_date = fields.Char('Zaka No')
    date = fields.Date(string="Date Request", default=fields.Date.today())
    request_currency = fields.Many2one('res.currency', 'Currency', )
    amount = fields.Float('Amount', store='True',required=True)
    partner_id = fields.Many2one('res.partner', string="Customer")
    check_no = fields.Integer('Check No.')
    debit_account = fields.Many2one('account.account', string="Debit Account",required=True)
    # credit_account = fields.Many2one('account.account', string="Credit Account",required=True)
    journal_id = fields.Many2one('account.journal', string="Journal",required=True)
    move_id = fields.Many2one('account.move', string="Journal Entry", readonly=True)
    paid = fields.Boolean(string="Paid")
    zakah_id = fields.Many2one('zaka.account', string="Zakah")
    note = fields.Text(string=' Note')

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
        for zakah in self:
            dollar_ids = []
            debit_sum = 0.0
            credit_sum = 0.0
            zaka_request_date = zakah.date
            # currency = zakah.request_currency.id
            reference = zakah.zakah_id.name
            journal_id = zakah.journal_id.id
            amount = zakah.amount
            partner_id =zakah.partner_id.id
            company_id=zakah.zakah_id.company_id.id

            move_dict = {
                'name': reference,
                'narration': reference,
                'ref': reference,
                'journal_id': journal_id,
                'date': zaka_request_date,
                'company_id': company_id,

            }

            if zakah.paid == False:
                debit_line = (0, 0, {
                    'name': reference,
                    'partner_id': partner_id,
                    'account_id': zakah.debit_account.id,
                    'journal_id': journal_id,
                    'date': zaka_request_date,
                    'debit': amount > 0.0 and amount or 0.0,
                    'credit': amount < 0.0 and -amount or 0.0,
                    'analytic_account_id': False,
                })
                line_ids.append(debit_line)
                credit_line = (0, 0, {
                    'name': reference,
                    'partner_id': partner_id,
                    'account_id': self.journal_id.default_credit_account_id.id,
                    'journal_id': journal_id,
                    'date': zaka_request_date,
                    'debit': amount < 0.0 and -amount or 0.0,
                    'credit': amount > 0.0 and amount or 0.0,
                    'analytic_account_id': False,
                })
                line_ids.append(credit_line)

        move_dict['line_ids'] = line_ids
        move = self.env['account.move'].create(move_dict)
        zakah.write({'move_id': move.id, 'date': zaka_request_date})
        move.post()
        zakah.paid = True

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.move_id:
                raise Warning(_("Warning! You cannot delete a Taxes which paid"))
        return super(zaka_account_line, self).unlink()


class check_tax_line(models.Model):
    _name = "check.zakat.line"
    _description = "Check Request Line"

    name = fields.Char("name")
    date = fields.Date(string="Payment Date", required=True)
    amount = fields.Float(string="Paid Amount", required=True)
    paid = fields.Boolean(string="Paid")
    note = fields.Text(string="Notes")
    bank_id = fields.Many2one('res.bank')
    account_holder = fields.Many2one('res.partner', string="Account Holder")
    check_no = fields.Char('Check No.')
    zakat_check_id = fields.Many2one('zaka.account', string="Check Ref.")
    journal_id = fields.Many2one('account.journal', string='Payment Journal', required=True,
                                 domain=[('type', 'in', ('bank', 'cash'))])
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self: self.env.user.company_id.currency_id)

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.paid == True:
                raise Warning(_("Warning! You Cannot Delete A Check "))
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
