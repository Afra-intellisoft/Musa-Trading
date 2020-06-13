##############################################################################
#    Description: HR Overtime Customization                                        #
#    Author: IntelliSoft Software                                            #
#    Date: Dec 2017 -  Till Now                                              #
##############################################################################

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, Warning
from odoo.tools.float_utils import float_round
from datetime import datetime
from odoo import time
from dateutil import relativedelta
from odoo.tools.float_utils import float_compare, float_round, float_is_zero


class HrCustOvertime(models.Model):
    _name = 'hr.cust.overtime'

    def _default_employee(self):
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

    name = fields.Many2one('hr.employee', string="Employee", default=_default_employee, required=True)
    user_id = fields.Many2one('res.users', 'Ordered by', readonly=True, default=lambda self: self.env.user)
    department_id = fields.Many2one('hr.department', related="name.department_id", readonly=True, string="Department")
    date_from = fields.Date(string='Date From', required=True,
                            default=time.strftime('%Y-%m-01'))
    date_to = fields.Date(string='Date To', required=True,
                          default=str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10],
                          )
    employee_account = fields.Many2one('account.account', string="Debit Account")
    overtime_line_ids = fields.One2many('hr.overtime', 'overtime_line_id', string='Overtime Line')

    state = fields.Selection([('draft', 'Draft'),
                              ('competent', 'Competent Department Manager'),
                              ('general', 'General Department Manager'),
                              ('approve', 'General HR Manager'),
                              ('hr', 'Hr Person'),
                              ('confirm', 'Hr Manager'),
                              ('account', 'Account'),
                              ('done', 'Done'), ('refuse', 'Refused')], 'State', default='draft')

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.state not in ['draft']:
                raise UserError(_('You are not allow to delete the Confirm and Done state records'))
        res = super(HrCustOvertime, self).unlink()
        return res

    @api.one
    def to_competent(self):
        self.state = 'competent'

    @api.one
    def to_general(self):
        self.state = 'general'

    @api.one
    def to_approve(self):
        self.state = 'approve'

    @api.one
    def to_hr(self):
        self.state = 'hr'

    @api.one
    def to_Confirm(self):
        self.state = 'confirm'

    @api.one
    def action_done(self):
        self.state = 'done'
        for x in self.overtime_line_ids:
            x.state = 'done'

    @api.one
    def action_refuse(self):
        self.state = 'refuse'

    @api.one
    def action_reset(self):
        self.state = 'draft'

    @api.constrains('overtime_line_ids')
    def determine_overtime_day(self):
        for rec in self.overtime_line_ids:
            if not rec.is_working_day:
                if not rec.is_holiday:
                    raise Warning(_("Please determine work day of overtime is it work day or holiday day!"))
            if not rec.is_holiday:
                if not rec.is_working_day:
                    raise Warning(_("Please determine work day of overtime is it work day or holiday day!"))

class hr_overtime(models.Model):
    _name = 'hr.overtime'

    overtime_line_id = fields.Many2one('hr.cust.overtime', string="overtime")
    name = fields.Many2one('hr.employee', string="Employee",)
    warning_attach = fields.Binary("Attachment")
   # test = fields.Many2one('hr.employee', string="Employee test")
    user_id = fields.Many2one('res.users', 'Ordered by', readonly=True, default=lambda self: self.env.user)
    department_id = fields.Many2one('hr.department', related="name.department_id", readonly=True, string="Department")
    is_working_day = fields.Boolean(string="Working Day")
    is_holiday = fields.Boolean(string="Holiday Day")
    hour = fields.Float(string="Work Hours", required=True)
    employee_salary = fields.Float(string="Basic Salary", compute="_onchange_employee_d")
    overtime_date = fields.Date(string="Date", required=True)
    comment = fields.Text(string="Comments")

    employee_account = fields.Many2one('account.account', string="Debit Account", related="name.account_id"
                                       )
    # analytic_debit_account_id = fields.Many2one('account.analytic.account',
    #                                             related='department_id.analytic_debit_account_id', readonly=True,
    #                                             string="Analytic Account")

    state = fields.Selection(
        [('draft', 'To Submit'), ('approve', 'Approved'),
         ('confirm', 'Confirmed'), ('hr', 'Hr'), ('account', 'Account'), ('done', 'Done'),
         ('refunded', 'Refunded'),
         ('refuse', 'Refused')],
        'Status', readonly=True, track_visibility='onchange', copy=False, default='draft')

    @api.multi
    def unlink(self):
        if any(self.filtered(lambda hr_overtime: hr_overtime.state not in ('draft', 'refuse'))):
            raise UserError(_('You cannot delete a Overtime which is not draft or refused!'))
        return super(hr_overtime, self).unlink()

    @api.onchange('name')
    def _onchange_employee_d(self):
        for x in self:
            if x.name:
                x.employee_salary = x.name.contract_id.total_salary

    @api.constrains('is_working_day', 'is_holiday')
    def determine_overtime_day(self):
        for rec in self:
            if not rec.is_working_day:
                if not rec.is_holiday:
                    raise Warning(_("Please determine work day of overtime is it work day or holiday day!"))
            if not rec.is_holiday:
                if not rec.is_working_day:
                    raise Warning(_("Please determine work day of overtime is it work day or holiday day!"))

    @api.one
    def loan_confirm(self):
        for x in self:
            x.state = 'approve'

    @api.one
    def hr_validate(self):
        for x in self:
            x.state = 'confirm'

    @api.one
    def to_hr_approve(self):
        for x in self:
            x.state = 'hr'

    @api.one
    def to_account_validate(self):
        for x in self:
            x.state = 'account'

    @api.one
    def action_done(self):
        for x in self:
            x.state = 'done'

    @api.one
    def overtime_refuse(self):
        self.state = 'refuse'

    @api.one
    def overtime_reset(self):
        self.state = 'draft'


class hr_overtime_month(models.Model):
    _name = 'hr.overtime.month'

    name = fields.Char(string='Overtime')
    date_from = fields.Date(string='Date From', required=True,
                            default=time.strftime('%Y-%m-01'))
    date_to = fields.Date(string='Date To', required=True,
                          default=str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10],
                          )
    overtime_line_ids = fields.One2many('overtime.line', 'overtime_line_id', string='Overtime Month')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('done', 'Done'),
        ('refuse', 'Refused'),
        ('auditor', 'Auditor')
    ], string="State", default='draft', track_visibility='onchange', copy=False, )

    journal_id = fields.Many2one('account.journal', string="Journal")
    overtime_account = fields.Many2one('account.account', string="Debit Account")
    account_id = fields.Many2one('account.account', string="Credit Account")
    move_id = fields.Many2one('account.move', string="Journal Entry", readonly=True)
    finance_request = fields.Boolean('Finance Request')

    @api.one
    def over_auditor(self):
        for x in self:
            x.state = 'auditor'

    @api.one
    def refuse(self):
        self.state = 'refuse'

    @api.multi
    def unlink(self):
        if any(self.filtered(lambda over: over.state not in ('draft', 'refuse'))):
            raise UserError(_('You cannot delete a Overtime which is not draft or cancelled!'))
        return super(hr_overtime_month, self).unlink()

    @api.depends('date_from', 'date_to')
    def compute_overtime_month(self):
        for x in self:
            locale = self.env.context.get('lang', 'en_US')
            overtime_obj = x.env['hr.overtime']
            overtime_line_obj = x.env['overtime.line']
            employee_obj = x.env['hr.employee'].search([])
            x.overtime_line_ids.unlink()
            for employee in employee_obj:
                employee_id = employee.id
                overtime_ids = overtime_obj.search(
                    [('overtime_date', '>=', x.date_from), ('overtime_date', '<=', x.date_to),
                     ('name', '=', employee_id), ('state', '=', 'done')], order='name')
                total_overtime = 0.0
                working_sum_hours = 0.0
                holiday_sum_hours = 0.0
                overtime_holiday = 0.0
                overtime_working = 0.0
                for overtime in overtime_ids:
                    employee_basic_salary = employee.contract_id.total_salary
                    employee_salary_hour = employee_basic_salary / 240
                    if overtime.is_working_day:
                        working_sum_hours += overtime.hour
                        overtime_working = working_sum_hours * employee_salary_hour * 1.5
                    if overtime.is_holiday:
                        holiday_sum_hours += overtime.hour
                        overtime_holiday = holiday_sum_hours * employee_salary_hour * 2
                    total_overtime = overtime_working + overtime_holiday
                if working_sum_hours != 0.0 or holiday_sum_hours != 0.0:
                    overtime_line_ids = overtime_line_obj.create({
                        'name': employee_id,
                        'overtime_month_working': working_sum_hours,
                        'overtime_month_holiday': holiday_sum_hours,
                        'overtime_month_value': total_overtime,
                        # 'employee_account': overtime.employee_account.id,
                        # 'analytic_debit_account_id': overtime.analytic_debit_account_id.id,
                        'overtime_line_id': x.id})
            x.state = 'confirm'

        return True


    @api.one
    def finance_approve(self):
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
            for over in lta.overtime_line_ids:
                amount_sum += over.overtime_month_value

            lta_name = 'Overtime of ' + reference
            move_dict = {
                'narration': reference,
                'ref': reference,
                'journal_id': journal_id,
                'date': lta_approve_date,
            }

            debit_line = (0, 0, {
                'name': lta_name,
                'partner_id': False,
                'account_id': lta.overtime_account.id,
                'journal_id': journal_id,
                'move_id': self.move_id,
                'date': lta_approve_date,
                'debit': amount_sum > 0.0 and amount_sum or 0.0,
                'credit': amount_sum < 0.0 and -amount_sum or 0.0,
                'tax_line_id': 0.0,
            })
            line_ids.append(debit_line)
            debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']
            credit_line = (0, 0, {
                'name': lta_name,
                'partner_id': False,
                'account_id': lta.account_id.id,
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
        self.state = 'done'


class overtime_line(models.Model):
    _name = 'overtime.line'

    name = fields.Many2one('hr.employee', string='Employee')
    overtime_month_working = fields.Float(string='Working Day hours')
    overtime_month_holiday = fields.Float(string='Holiday Day Hours')
    overtime_month_value = fields.Float(string='Overtime Value')
    overtime_line_id = fields.Many2one('hr.overtime.month', string='Overtime Month', ondelete='cascade')
    
    employee_account = fields.Many2one('account.account', string="Debit Account")
    # analytic_debit_account_id = fields.Many2one('account.analytic.account',
    #                                             related='name.department_id.analytic_debit_account_id', readonly=True,
    #                                             string="Analytic Account")
