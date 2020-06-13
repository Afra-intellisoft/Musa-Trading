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



class account_payment(models.Model):
    _inherit = 'account.payment'
    _description = "payment"

    @api.one
    @api.depends('currency_id','journal_id')
    def agriculture_request(self):
        form_ids = self.env['account.move.line'].search(
            [('currency_id', '=', self.currency_id.id), ('move_id.journal_id', '=', self.journal_id.id),
             ('move_id.state', '=', 'posted'), ('account_id', '=', self.journal_id.default_debit_account_id.id)])
        if not form_ids:
            self.average = 0.0
        amount_currency = 0.0
        debit = 0.0
        credit = 0.0
        for form in form_ids:
            amount_currency += form.amount_currency
            debit += form.debit
            credit += form.credit
            xyz = credit - debit
            if xyz != 0.0 and amount_currency != 0.0:
                self.average = -(xyz / amount_currency)






    dollar_invoice = fields.Many2one('collect.currency', string='Dollar Rate')
    ave_dollar = fields.Float(string='Average Of Currency',compute="compute_avg_dollar",store=True)
    ave_dollar_id = fields.Many2one("account.dollar.line")
    notes = fields.Text('Note')
    average = fields.Float('Average',compute="agriculture_request", store=True)
    test = fields.Boolean('Test')
    currency_rate_id = fields.Many2one('res.currency.rate', string='Currency Rate')
    new_rate = fields.Float(string='Currency Rate', related='currency_rate_id.rate', digits=(12, 10), readonly=False)
    inv_rate = fields.Float(string='Rate ', related='currency_rate_id.inv_rate', readonly=False)

    @api.multi
    @api.depends('dollar_invoice')
    def compute_avg_dollar(self):
        for rec in self:
            avg = rec.dollar_invoice.amount
        rec.ave_dollar = avg

    # @api.model
    def get_rate(self):
        inv_rate = self.inv_rate
        currency_rate_id = self.currency_rate_id.id
        self.env.cr.execute(
            '''UPDATE res_currency_rate set inv_rate= %s where id =%s ''' % (inv_rate, currency_rate_id))
        return True

    @api.onchange('currency_id')
    def compute_rate_id(self):
        for rec in self:
            if rec.currency_id:
                currency = self.env['res.currency.rate'].search([('currency_id', '=', rec.currency_id.id)],
                                                                order='name desc', limit=1).id
                rec.currency_rate_id = currency


class account_dollar(models.Model):
    _name = 'collect.currency'
    _description = "Dollar"

    name = fields.Char('Name', required=True)
    customer_id = fields.Many2one('res.partner','Partner')
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.user.company_id)

    amount = fields.Float('Average')
    currency_id = fields.Many2one('res.currency', string='Currency')
    amount1  = fields.Float('Amount USD' )
    average_dollar = fields.Float(" Currency  Average", compute="compute_average_dollar",store=True)
    # average_dollar_id=fields.Float(" Currency  Average", compute="compute_average_id")
    state = fields.Selection(
        [('draft', 'To Submit'),('confirm', 'Confirmed'),
         ('done', 'Finished')],
        'Status', readonly=True, track_visibility='onchange', copy=False, default='draft')
    journal_id = fields.Many2one('account.journal', 'Journal',
                                )
    # domain = [('type', 'in', ['bank', 'cash'])]

    Dollar_line_ids = fields.One2many('account.dollar.line', 'dollar_id', string="Dollar Line", index=True)








    @api.one
    def confirm(self):
        for x in self:
            x.state = 'confirm'

    # @api.one
    # @api.constrains('amount')
    # def _check_amount(self):
    #     if self.amount <= 0.0:
    #         raise ValidationError(_('The SDG Amount Must be Strictly positive.'))

        # @api.one
        # @api.constrains('amount1')
        # def _check_amount(self):
        #     if self.amount1 <= 0.0:
        #         raise ValidationError(_('The USD  Amount Must be Strictly positive'))

    @api.multi
    def unlink(self):
        if any(bool(rec.Dollar_line_ids) for rec in self):
            raise UserError(_("You can not delete a payment that is already posted"))
        return super(account_dollar,self).unlink()

    @api.multi
    @api.depends('Dollar_line_ids')
    def compute_average_dollar(self):
        for rec in self:
            qty = 0.0
            total = 0.0
            qty_debit = 0.0
            total_debit = 0.0
            x = 0.0
            z = 0.0
            Dollar_line = rec.Dollar_line_ids
            for obj in Dollar_line:
                qty += obj.amount_credit_usd
                qty_debit += obj.amount_debit_usd
                total += obj.amount_credit_sdg
                total_debit += obj.amount_sdg
                x = qty - qty_debit
                z = total - total_debit
            if x > 0.0:
               rec.average_dollar = z / x

    @api.constrains('Dollar_line_ids')
    def compute_line_id(self):
        for x in self:
            Dollar_line = self.Dollar_line_ids
            total_debit = 0.0
            total = 0.0
            for obj in Dollar_line:
                total += obj.amount_credit_sdg
                total_debit += obj.amount_sdg
            if total_debit > 0.0 and total > 0.0:
                if total == total_debit:
                    self.state = 'done'

    # @api.onchange('Dollar_line_ids')
    # def compute_average_id(self):
    #     for x in self:
    #         dollar = self.env['account.dollar.line'].search([('dollar_id','=',self.id)])
    #         print(dollar)
    #         amount2 = 0.0
    #         amount1 = 0.0
    #         for y in dollar:
    #             amount2 += y.amount_usd
    #             amount1 += y.amount_sdg
    #             if amount2 > 0.0:
    #                 x.average_dollar_id=amount1 / amount2


class account_dollar_line(models.Model):
    _name = 'account.dollar.line'
    _description = "Dollar Line"

    name = fields.Char('name')
    date = fields.Date('Date' ,required=True)
    request_currency = fields.Many2one('res.currency', 'Currency',required=True)
    amount_sdg  = fields.Float('Total Debit SDG',compute="compute_dollar", store='True')
    amount_credit_sdg  = fields.Float('Total Credit SDG',compute="compute_dollar_credit", store='True')
    amount_credit_usd  = fields.Float('Credit',required=True )
    amount_debit_usd  = fields.Float('Debit',required=True)
    rate  = fields.Float('Rate',required=True)
    check_no = fields.Integer('Check No.')
    debit_account = fields.Many2one('account.account', string="Debit Account",required=True)
    # credit_account = fields.Many2one('account.account', string="Credit Account",required=True)
    journal_id = fields.Many2one('account.journal', string="Journal",required=True)
    move_id = fields.Many2one('account.move', string="Journal Entry", readonly=True)
    paid = fields.Boolean(string="Paid")
    dollar_id = fields.Many2one('collect.currency', string="Dollar")
    note = fields.Text(string="Note")

    @api.depends('rate','amount_credit_usd')
    def compute_dollar_credit(self):
        for line in self:
             amount_credit_usd = line.amount_credit_usd
             rate = line.rate
             line.amount_credit_sdg = amount_credit_usd * rate


    @api.depends('rate','amount_credit_sdg')
    def compute_dollar(self):
        amount_credit_sdg = 0.0
        rate = 0.0
        for line in self:
             amount_credit_sdg += line.amount_credit_sdg
             rate += line.rate
             if amount_credit_sdg > 0.0:
                self.amount_sdg = amount_credit_sdg / rate

    @api.one
    def validate(self):
        if not self.debit_account or not self.journal_id:
            raise Warning(_("You Must Enter  &  Account and Journal to Create Entries "))
        can_close = False
        loan_obj = self.env['account.dollar.line']
        move_obj = self.env['account.move']
        move_line_obj = self.env['account.move.line']
        currency_obj = self.env['res.currency']
        created_move_ids = []
        line_ids = []
        for dollar in self:
            dollar_ids = []
            debit_sum = 0.0
            credit_sum = 0.0
            dollar_request_date = dollar.date
            currency = dollar.request_currency.id
            reference = dollar.dollar_id.name
            journal_id = dollar.journal_id.id
            amount_credit_sdg = dollar.amount_credit_sdg
            amount_debit_sdg = dollar.amount_sdg
            amount_usd = dollar.amount_credit_usd
            amount_debit_usd = dollar.amount_debit_usd
            customer_id = dollar.dollar_id.customer_id.id
            company_id=dollar.dollar_id.company_id.id

            move_dict = {
                'name': reference,
                'narration': reference,
                'ref': reference,
                'journal_id': journal_id,
                'date': dollar_request_date,
                'company_id': company_id,

            }

            if dollar.paid == False:
                debit_line = (0, 0, {
                    'name': reference,
                    'partner_id': customer_id,
                    'account_id': dollar.debit_account.id,
                    'journal_id': journal_id,
                    'date': dollar_request_date,
                    'currency_id':currency,
                    'amount_currency': amount_usd or amount_debit_usd,
                    'debit': amount_credit_sdg > 0.0 and amount_credit_sdg or 0.0 or amount_debit_sdg > 0.0 and amount_debit_sdg or 0.0,
                    'credit': amount_credit_sdg < 0.0 and -amount_credit_sdg or 0.0 or  amount_debit_sdg < 0.0 and -amount_debit_sdg or 0.0,
                    'analytic_account_id': False,
                })
                line_ids.append(debit_line)
                credit_line = (0, 0, {
                    'name': reference,
                    'partner_id': customer_id,
                    'account_id': self.journal_id.default_credit_account_id.id,
                    'journal_id': journal_id,
                    'date': dollar_request_date,
                    'currency_id': currency,
                    'amount_currency': -amount_usd or -amount_debit_usd,
                    'debit': amount_credit_sdg < 0.0 and -amount_credit_sdg or 0.0 or amount_debit_sdg < 0.0 and -amount_debit_sdg or 0.0,
                    'credit': amount_credit_sdg > 0.0 and amount_credit_sdg or 0.0 or  amount_debit_sdg > 0.0 and amount_debit_sdg or 0.0,
                    'analytic_account_id': False,
                })
                line_ids.append(credit_line)

        move_dict['line_ids'] = line_ids
        move = self.env['account.move'].create(move_dict)
        dollar.write({'move_id': move.id, 'date': dollar_request_date})
        move.post()
        dollar.paid = True


    @api.multi
    def unlink(self):
        if any(bool(rec.paid==True) for rec in self):
            raise UserError(_("You can not delete a payment that is already posted"))
        return super(account_dollar_line, self).unlink()

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.one
    @api.depends('currency_id', 'journal_avg_id')
    def vendor_request(self):
        form_ids = self.env['account.move.line'].search(
            [('currency_id', '=', self.currency_id.id), ('move_id.journal_id', '=', self.journal_avg_id.id),
             ('move_id.state', '=', 'posted'), ('account_id', '=', self.journal_avg_id.default_debit_account_id.id)])
        if not form_ids:
            self.average = 0.0
        amount_currency = 0.0
        debit = 0.0
        credit = 0.0
        for form in form_ids:
            amount_currency += form.amount_currency
            debit += form.debit
            credit += form.credit
            xyz = credit - debit
            if xyz != 0.0 and amount_currency != 0.0:
                self.average = -(xyz / amount_currency)


    # dollar_invoice_id = fields.Many2one('collect.currency',string='Dollar Rate')
    journal_avg_id = fields.Many2one('account.journal', 'Journal',
                                 help='Payment journal.',
                                 )
    # domain = [('type', 'in', ['bank', 'cash'])]
    average = fields.Float(string='Average',compute="vendor_request", store=True)
    currency_rate_id = fields.Many2one('res.currency.rate', string='Currency Rate')
    new_rate = fields.Float(string='Currency Rate', digits=(12, 10))
    inv_rate = fields.Float(string='Rate', related='currency_rate_id.inv_rate',readonly = False, track_visibility='always')
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  required=True,
                                  track_visibility='always')
    @api.one
    def get_rate(self):
        inv_rate = self.inv_rate
        currency_rate_id = self.currency_rate_id.id
        self.env.cr.execute(
            '''UPDATE res_currency_rate set inv_rate= %s where id =%s ''' % (inv_rate, currency_rate_id))

    @api.multi
    @api.onchange('dollar_invoice_id')
    def compute_avg(self):
        for rec in self:
            avg = rec.dollar_invoice_id.amount
        rec.ave_dollar = avg

    @api.onchange('currency_id')
    def compute_rate_id(self):
        for rec in self:
            if rec.currency_id:
                currency = self.env['res.currency.rate'].search([('currency_id', '=', rec.currency_id.id)],
                                                                order='name desc', limit=1).id
            rec.currency_rate_id = currency

class res_currency_rate(models.Model):
    _inherit = "res.currency.rate"

    inv_rate = fields.Float("Inverse Rate", default="1")

    @api.one
    @api.depends('inv_rate')
    @api.constrains('inv_rate')
    def _get_rate(self):
        if self.inv_rate == 0 or self.inv_rate == 0.00:
            raise Warning(_("Can not divide by zero!"))
        else:
            self.rate = 1 / self.inv_rate
