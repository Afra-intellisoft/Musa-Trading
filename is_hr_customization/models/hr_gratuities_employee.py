from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import UserError, Warning
import babel
import time

from odoo import tools
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

class HrGratuitiesEmp(models.Model):
    _name ="hr.gratuities.emp"
    _description = "Employee Gratuities"


    name = fields.Char(string='Gratuities')
    employee_id = fields.Many2one('hr.employee',string ='Employee')
    partner_id = fields.Many2one('res.partner',string ='Partner')
    company_id = fields.Many2one('res.company',string ='Company')
    amount = fields.Float(string ='Amount' ,required=True)
    date = fields.Date(string ='Date', default=time.strftime('%Y-%m-15'))


class HrGratuitiesPaysheet(models.Model):
    _name = 'hr.gratuities.paysheet'

    name = fields.Char(string='Name', required=True)
    date = fields.Date(string='Date', default=time.strftime('%Y-%m-15'), required=True)
    done_date = fields.Date(string='Approved Date')
    employee_gratuities_ids = fields.Many2many('hr.gratuities.emp', 'hr_gratuities_id','emp_id', string='Payment')
    journal_id = fields.Many2one('account.journal', string="Journal")
    debit_account = fields.Many2one('account.account', string="Debit Account")
    credit_account = fields.Many2one('account.account', string="Credit Account")
    analytic_debit_account_id = fields.Many2one('account.analytic.account', string="Analytic Account")
    move_id = fields.Many2one('account.move', string="Journal Entry", readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approve', 'Approved'),
        ('done', 'Done'),
        ('finance_approval', 'Finance approval'),
        ('auditor', 'Auditor'),
        ('refuse', 'Refused'),
    ], string="State", default='draft', track_visibility='onchange', copy=False, )

    @api.onchange('date')
    def onchange_date(self):
        for x in self:
            ttyme = datetime.fromtimestamp(time.mktime(time.strptime(x.date, "%Y-%m-%d")))
            locale = self.env.context.get('lang', 'en_US')
            x.name = _('Gratuities for %s') % (
                tools.ustr(babel.dates.format_date(date=ttyme, format='MMMM-y', locale=locale)))

    @api.one
    def action_auditor(self):
        for x in self:
            x.state = 'auditor'

    @api.one
    def action_approve(self):
        self.state = 'approve'
        for grant_id in self.employee_gratuities_ids:
            grant_id.state = 'approve'



    @api.one
    def action_refuse(self):
        self.state = 'refuse'
        for grant_id in self.employee_gratuities_ids:
            grant_id.state = 'refuse'

    @api.one
    def action_reset(self):
        self.state = 'draft'
        for grant_id in self.employee_gratuities_ids:
            grant_id.state = 'draft'

    @api.one
    def action_finance_approval(self):
        move_obj = self.env['account.move']
        move_line_obj = self.env['account.move.line']
        created_move_ids = []
        loan_ids = []
        amount_sum = 0.0
        for lta in self:
            lta_approve_date = fields.Date.today()
            journal_id = lta.journal_id.id
            reference = lta.name
            created_move_ids = []
            loan_ids = []

            line_ids = []
            debit_sum = 0.0
            credit_sum = 0.0
            for lta_temporary_id in lta.employee_gratuities_ids:
                amount_sum += lta_temporary_id.amount

            lta_name = 'Temporary Workers Gratuities of ' + reference
            move_dict = {
                'narration': reference,
                'ref': reference,
                'journal_id': journal_id,
                'date': lta_approve_date,
            }

            debit_line = (0, 0, {
                'name': lta_name,
                'partner_id': False,
                'account_id': lta.debit_account.id,
                'journal_id': journal_id,
                'date': lta_approve_date,
                'move_id': self.move_id,
                'debit': amount_sum > 0.0 and amount_sum or 0.0,
                'credit': amount_sum < 0.0 and -amount_sum or 0.0,
                'analytic_account_id': lta.analytic_debit_account_id.id,
                'tax_line_id': 0.0,
            })
            line_ids.append(debit_line)
            debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']
            credit_line = (0, 0, {
                'name': lta_name,
                'partner_id': False,
                'account_id': lta.credit_account.id,
                'journal_id': journal_id,
                'move_id': self.move_id,
                'date': lta_approve_date,
                'debit': amount_sum < 0.0 and -amount_sum or 0.0,
                'credit': amount_sum > 0.0 and amount_sum or 0.0,
                'analytic_account_id': False,
                'tax_line_id': 0.0,
            })
            line_ids.append(credit_line)
            credit_sum += credit_line[2]['credit'] - credit_line[2]['debit']
            move_dict['line_ids'] = line_ids
            move = self.env['account.move'].create(move_dict)
            lta.write({'move_id': move.id, 'done_date': lta_approve_date})
            move.post()
        self.state = 'finance_approval'

    @api.multi
    def unlink(self):
        for x in self:
            if any(x.filtered(lambda HrGratuitiesPaysheet: HrGratuitiesPaysheet.state not in ('draft', 'refuse'))):
                raise UserError(_('You cannot delete allowance & bonus batch which is not draft or refused!'))
            return super(HrGratuitiesPaysheet, x).unlink()

