
from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, Warning
from odoo.tools.float_utils import float_round
from datetime import datetime
from odoo import time
from dateutil import relativedelta
from odoo.tools.float_utils import float_compare, float_round, float_is_zero

class hr_bonus_month(models.Model):
    _name = 'hr.bonus.month'

    name = fields.Char(string='Bonus', required=True)
    date = fields.Date(string='Date',
                            default=time.strftime('%Y-%m-01'))

    bonus_ids = fields.One2many('hr.bonus.line', 'bonus_id', string='Bonus Month')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('done', 'Done'),
        ('refuse', 'Refused'),
        ('auditor', 'Auditor')
    ], string="State", default='draft', track_visibility='onchange', copy=False, )

    journal_id = fields.Many2one('account.journal', string="Journal")
    account_id = fields.Many2one('account.account', string="Credit Account")
    move_id = fields.Many2one('account.move', string="Journal Entry", readonly=True)
    finance_request = fields.Boolean('Finance Request')

    @api.one
    def bonus_auditor(self):
        for x in self:
            x.state = 'auditor'

	#
    # @api.depends('date_from', 'date_to')
    # def compute_bonus_month(self):
    #     for x in self:
    #         sale_obj = x.env['sale.person.bonus']
    #         bonus_line_obj = x.env['hr.bonus.line']
    #         employee_obj = x.env['hr.employee'].search([])
    #         x.bonus_ids.unlink()
    #         for employee in employee_obj:
    #             employee_id = employee.id
    #             rec = sale_obj.search(
    #                 [('date', '>=', x.date_from), ('date', '<=', x.date_to),('employee_id','=',employee_id)
    #                ], order='employee_id')
    #             request_amount = 0.0
    #             for sales in rec:
    #                 request_amount += sales.request_amount
    #             if request_amount != 0.0 :
    #                 vals = {
    #                     'employee_id': employee_id,
    #                     'amount': request_amount,
    #                     'date_bouns': sales.date,
    #                     'invoice_id': sales.invoice_id.id,
    #                     'account_id':sales.exp_account.id,
    #                     'bonus_id': x.id,
    #                                          }
    #                 bonus_line_obj.create(vals)
    #             x.state = 'confirm'
    #         return True

    @api.one
    def finance_approve(self):
        precision = self.env['decimal.precision'].precision_get('bonus')
        self.env.cr.execute("""select current_date;""")
        xt = self.env.cr.fetchall()
        self.comment_date4 = xt[0][0]
        can_close = False
        move_obj = self.env['account.move']
        move_line_obj = self.env['account.move.line']
        currency_obj = self.env['res.currency']
        created_move_ids = []
        bonus_ids = []
        for bonus in self:
            bonus_ids = bonus.bonus_ids
            line_ids = []
            debit_sum = 0.0
            credit_sum = 0.0
            bonus_request_date = bonus.date
            for obj in bonus_ids:
                amount = obj.amount
                reference = bonus.journal_id.name
                journal_id = bonus.journal_id.id
                # currency_id = bonus.currency_id.id
                move_dict = {
                    'narration': reference,
                    'ref': reference,
                    'journal_id': journal_id,
                    # 'currency_id': currency_id,
                    'date': bonus_request_date,
                }

                debit_line = (0, 0, {
                    'name': reference,
                    'partner_id': False,
                    'account_id': bonus.account_id.id,
                    'journal_id': journal_id,
                    # 'currency_id': currency_id,
                    'date': bonus_request_date,
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
                    'account_id': obj.account_id.id,
                    'journal_id': journal_id,
                    # 'currency_id': currency_id,
                    'date': bonus_request_date,
                    'debit': amount < 0.0 and -amount or 0.0,
                    'credit': amount > 0.0 and amount or 0.0,
                    'analytic_account_id': False,
                    'tax_line_id': 0.0,
                })
                line_ids.append(credit_line)
                credit_sum += credit_line[2]['credit'] - credit_line[2]['debit']
                if float_compare(credit_sum, debit_sum, precision_digits=precision) == -1:
                    acc_journal_credit = bonus.journal_id.default_credit_account_id.id
                    if not acc_journal_credit:
                        raise UserError(
                            _('The Expense Journal "%s" has not properly configured the Credit Account!') % (
                                bonus.journal_id.name))
                    adjust_credit = (0, 0, {
                        'name': _('Adjustment Entry'),
                        'partner_id': False,
                        'account_id': acc_journal_credit,
                        'journal_id': journal_id,
                        # 'currency_id': currency_id,
                        'date': bonus_request_date,
                        'debit': 0.0,
                        'credit': debit_sum - credit_sum,
                    })
                    line_ids.append(adjust_credit)

                elif float_compare(debit_sum, credit_sum, precision_digits=precision) == -1:
                    acc_journal_deit = bonus.journal_id.default_debit_account_id.id
                    if not acc_journal_deit:
                        raise UserError(_('The Expense Journal "%s" has not properly configured the Debit Account!') % (
                            bonus.journal_id.name))
                    adjust_debit = (0, 0, {
                        'name': _('Adjustment Entry'),
                        'partner_id': False,
                        'account_id': acc_journal_deit,
                        'journal_id': journal_id,
                        # 'currency_id': currency_id,
                        'date': bonus_request_date,
                        'debit': credit_sum - debit_sum,
                        'credit': 0.0,
                    })
                    line_ids.append(adjust_debit)

                move_dict['line_ids'] = line_ids
                move = self.env['account.move'].create(move_dict)
                bonus.write({'move_id': move.id, 'date': bonus_request_date})
                move.post()
            self.state = 'done'
            self.finance_request = True




class hr_bonus_line(models.Model):
    _name = 'hr.bonus.line'

    employee_id = fields.Many2one('hr.employee', string='Employee')
    amount = fields.Float(string='Amount')
    bonus_id = fields.Many2one('hr.bonus.month', string="Bonus")
    account_id = fields.Many2one('account.account', string="Credit Account")
    date_bonus = fields.Date(string='Date Bonus')
    invoice_id = fields.Many2one('account.invoice', string='Invoice')