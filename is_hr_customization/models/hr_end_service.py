from odoo import api, fields, models, _
from odoo.exceptions import UserError, Warning
from datetime import datetime,date
import calendar


import math
from odoo.tools.float_utils import float_compare, float_round, float_is_zero

class end_duty(models.Model):
    _name = 'end.duty'
    name = fields.Char( string ='Name' , compute='compute_string', store=True)
    date_of_form = fields.Date ( string =" Date Of Form" , default=fields.Date.today(),required=True)
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    # staff_no = fields.Char( string ='Employee Number', related ='employee_id.staff_no')
    staff_no = fields.Char( string ='Employee Number')
    department_id = fields.Many2one('hr.department', string='  Department',related ='employee_id.department_id',required=True)
    job_id = fields.Many2one('hr.job',  related ='employee_id.job_id', string='Job Title')
    hiring_date = fields.Date( string = " Start Day" , related ='employee_id.hiring_date',required=True)
    end_day = fields.Date( string = " End day" ,  required=True)

    year_experience = fields.Integer(string='Years of Experience')
    month_experience = fields.Integer(string='Months of Experience')
    fench_experience = fields.Char(compute='_get_experience', string='Full Experience', store=True)

    wage = fields.Float (related ='employee_id.contract_id.total_salary', string = "Salary")
    # benefits = fields.Float (related ='employee_id.contract_id.benefits', string = "Benefits")
    salary_amount = fields.Float(string="Salary six months", compute='compute_total_amount', store=True)
    total_amount = fields.Float(  compute='compute_total_amount',  string="Total Amount")
    state = fields.Selection(
        [('draft', 'To Submit'), ('sent', 'Sent'), ('confirm', ' Confirm'), ('confirmed', ' Confirmed')
            , ('approve', 'Approve'), ('done', 'Done'), ('end', 'End')], 'Status', default='draft')
    other_receivables = fields.Float( string = ' Other Receivables')
    # leave_balance = fields.Float( related ='employee_id.leave_balance' , string = ' leaves B    alance')
    leave_balance = fields.Float(string = ' leaves B    alance')
    value_vacation = fields.Float(  compute='compute_receivables' , string = 'Value of vacation' , store=True )
    reason =fields.Selection([('dismissal','Dismissal'),('contract','End of Contract'),('probation','Probation Period'),('resignation','Resignation'),('retirement','Retirement'),('other','Other')],string="Reasons", required=True)
    dedication = fields.Float( string = 'Dedication')
    loan_dedication = fields.Float( string = 'Balance Amount of Loan', compute ='compute_loan_dedication' , store=True )
    hr_warning = fields.Float( string = 'Balance Amount of Warning', compute ='compute_warning_dedication'  , store=True)
    loan_amount = fields.Float( string = 'Balance Amount of Benefits', compute ='compute_benefits_loan_dedication' , store=True )
    dedication_notes = fields.Char( string = 'Dedication Notes')
    total_receivables = fields.Float(  compute='compute_receivables' , string = 'Total Receivables', store=True)
    total = fields.Float( compute ='compute_total' , string = ' Total ')
    overtime = fields.Float( string = ' Overtime' ,compute ='compute_over', store=True)
    month = fields.Float( string = 'Number of Month')
    debit_account = fields.Many2one('account.account', string="Debit  Account", related="employee_id.account_id")
    credit_account = fields.Many2one('account.account', string="Credit Account")
    journal_id = fields.Many2one('account.journal', string="Journal")
    move_id = fields.Many2one('account.move', string="Journal Entry", readonly=True)
    request_amount_words = fields.Char(string='Amount in Words', readonly=True, default=False, copy=False,
                                       compute='_compute_text', translate=True)
    currency = fields.Many2one('res.currency', 'Currency',
                                       default=lambda self: self.env.user.company_id.currency_id)

    custody_name = fields.Many2one('custody.property', string='Property', compute ='compute_custody'  , store=True)


    @api.one
    @api.depends('employee_id')
    def compute_custody(self):
        for x in self:
            if x.employee_id:
                dedication = self.env['hr.custody'].search([('employee.id', '=', self.employee_id.id),('state', '=', 'approved')])
                for custody in dedication:
                    x.custody_name = custody.custody_name.id


    @api.depends('hiring_date','date_of_form')
    def _get_experience(self):
        experience = ''
        for employee in self:
            if employee.hiring_date:
                str_now = datetime.strptime(str(employee.date_of_form), '%Y-%m-%d').date()
                date_start = datetime.strptime(str(employee.hiring_date), '%Y-%m-%d').date()
                total_days = (str_now - date_start).days
                employee_years = int(total_days / 365)
                total_days = total_days - 365 * employee_years
                employee_months = int(12 * total_days / 365)
                employee_days = int(0.5 + total_days - 365 * employee_months / 12)
                experience = str(employee_years) + ' Year(s) ' + str(employee_months) + ' Month(s) ' + str(
                    employee_days) + ' day(s)'
            employee.fench_experience = experience

    # @api.one
    # @api.depends('total', 'request_currency')
    # def _compute_text(self):
    #     self.request_amount_words = amount_to_text_ar(self.total, self.request_currency.narration_ar_un,
    #                                                   self.request_currency.narration_ar_cn)

    @api.one
    def send_request(self):
        self.state = 'sent'

    @api.one
    def confirm_request(self):
        self.state = 'confirm'

    @api.one
    def approve_request(self):
        self.state = 'approve'


    @api.depends('employee_id', 'end_day')
    def compute_string(self):
        for x in self:
            if x.employee_id:
                x.name = x.employee_id.name + ' ' + str(x.end_day)
    @api.one
    @api.depends('employee_id')
    def compute_loan_dedication(self):
        for x in self:
            if x.employee_id:
                dedication = self.env['hr.loan'].search([('employee_id.id', '=', self.employee_id.id),('state', '=', 'done')])
                for loan in dedication:
                    x.loan_dedication = loan.balance_amount

    @api.one
    @api.depends('employee_id')
    def compute_benefits_loan_dedication(self):
        for x in self:
            today = date.today()
            str_now = datetime.strptime(str(today), '%Y-%m-%d')
            if x.hiring_date:
                hiring_date = datetime.strptime(str(x.hiring_date), '%Y-%m-%d')
                month_range = calendar.monthrange(str_now.year, str_now.month)[1]
                employee_period = (str_now - hiring_date).days
                if employee_period > 365.25:
                    if x.employee_id:
                        dedication = self.env['hr.contract'].search([('employee_id.id', '=', self.employee_id.id)])
                        for loan in dedication:
                            x.loan_amount = loan.benefits

    @api.one
    @api.depends('employee_id')
    def compute_over(self):
        for x in self:
            if x.employee_id:
                dedication = self.env['hr.overtime'].search([('name.id', '=', self.employee_id.id),('state', '=', 'done')])
                # print(dedication)
                working_sum_hours = 0.0
                holiday_sum_hours =0.0
                overtime_holiday =0.0
                sum_hours = 0.0
                for loan in dedication:
                    hour = loan.hour
                    wage = loan.employee_salary/ 240
                    if loan.is_working_day:
                        working_sum_hours += loan.hour
                        overtime_working = working_sum_hours * wage * 1.5
                    if loan.is_holiday:
                        holiday_sum_hours += loan.hour
                        overtime_holiday = holiday_sum_hours * wage * 2
                    sum_hours = overtime_working + overtime_holiday
                    x.overtime = sum_hours



    @api.one
    @api.depends('employee_id')
    def compute_warning_dedication(self):
        for x in self:
            if x.employee_id:
                dedication = self.env['hr.warnings'].search([('employee_id.id', '=', self.employee_id.id),('state', '=', 'penalty_approval')])
                for warning in dedication:
                    x.hr_warning = warning.deduct_amount

    @api.one
    def done_request(self):
        for request in self:
            precision = self.env['decimal.precision']
            line_ids = []
            debit_sum = 0.0
            credit_sum = 0.0
            request_name = request.name
            amount = request.total
            journal_id = request.journal_id.id
            approve_date = fields.Date.today()
            debit_account = request.debit_account.id
            credit_account = request.debit_account.id
        move_dict = {
            'narration': request_name,
            'ref': '/',
            'journal_id': journal_id,
            'date': approve_date,
        }
        debit_line = (0, 0, {
            'name': request_name,
            'partner_id': False,
            'account_id': debit_account,
            'journal_id': journal_id,
            'date': approve_date,
            'debit': amount > 0.0 and amount or 0.0,
            'credit': amount < 0.0 and -amount or 0.0,
            'analytic_account_id': False,
            'tax_line_id': 0.0,
        })
        line_ids.append(debit_line)
        debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']
        credit_line = (0, 0, {
            'name': request_name,
            'partner_id': False,
            'account_id': credit_account,
            'journal_id': journal_id,
            'date': approve_date,
            'debit': amount < 0.0 and -amount or 0.0,
            'credit': amount > 0.0 and amount or 0.0,
            'analytic_account_id': False,
            'tax_line_id': 0.0,
        })
        line_ids.append(credit_line)
        credit_sum += credit_line[2]['credit'] - credit_line[2]['debit']
        move_dict['line_ids'] = line_ids
        move = self.env['account.move'].create(move_dict)
        request.write({'move_id': move.id, 'date_approve': approve_date})
        move.post()
        request.state = 'done'


    @api.one
    def end_request(self):
        self.state = 'end'

    @api.depends('dedication','total_receivables')
    def compute_total(self):
        if self.employee_id:
            for x in self:
                t = self.total_receivables -( self.dedication + self.loan_dedication + self.hr_warning)
                self.total=t

    @api.depends('wage')
    def compute_total_amount(self):
        if self.employee_id:
            for x in self:

                # x.salary_amount = x.wage*x.month*.67
                x.salary_amount = x.wage*x.month

    @api.depends('employee_id')
    def compute_receivables(self):
        for x in self:
            x.remaining_leaves = x.employee_id.remaining_leaves
            value_day = x.employee_id.contract_id.wage/30
            value_vacation = value_day*x.remaining_leaves
            x.value_vacation = value_vacation
            over = x.overtime
            leaves = over +value_vacation
            receivables = leaves + over+x.loan_amount
            ded = x.hr_warning+ x.loan_dedication
            loan = receivables - ded
            x.total_receivables = receivables


    @api.multi
    def unlink(self):
        for rec in self:
            if any(rec.filtered(lambda end_duty: end_duty.state not in ('draft', 'refuse'))):
                raise UserError(_('You cannot delete a Receivables which is not draft or refused!'))
            return super(end_duty, rec).unlink()


class resignation (models.Model):
    _name = 'resignation'

    def _default_employee(self):
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

    name = fields.Char( string ='Name',required=True)
    type = fields.Selection([('resignation','resignation'),('non-renewal','Non-renewal')] , string ='Type',required=True)
    employee_id = fields.Many2one('hr.employee',  string='Employee ', default=_default_employee, required=True)
    department_id = fields.Many2one('hr.department', string='  Department',related ='employee_id.department_id',required=True)
    job_id = fields.Many2one('hr.job', relatrd ='employee_id.job_id',  string='Job Title')
    date = fields.Date(string=" Date ", default=fields.Date.today())
    request_date = fields.Date( string='Request Date')
    accept_date = fields.Date( string='Date Accepte' )
    reasons = fields.Text( string ='The Reasons',required=True)
    supervisor_not = fields.Text( string =' Supervisor Notes')
    mnagre_not = fields.Text( string =' Manger Notes')
    hr_not = fields.Text( string =' HR Notes')
    hr_date = fields.Date(string='HR Date')
    parent_id = fields.Many2one('hr.employee',   related ='employee_id.parent_id' , string='Manger')
    genral_manger_not = fields.Text(string ='CEO Notes')
    genral_manger_date = fields.Date(string='CEO Date')
    state = fields.Selection(
        [('draft', 'To Submit'),  ('sent', 'Sent'),('confirm', ' confirm')
        , ('approve', 'approve') , ('done', 'Done'), ('accept', 'Accept')], 'Status', default='draft')



    @api.one
    def send_request(self):
        self.state = 'sent'

    @api.one
    def confirm_request(self):
        self.state = 'confirm'

    @api.one
    def approve_request(self):
        self.state = 'approve'

    @api.one
    def done_request(self):
        self.state = 'done'
        self.accept_date = fields.Date.today()
class separation_staff(models.Model):
    _name = 'separation.staff'
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    date = fields.Date(string ='Date', default=fields.Date.today())
    sent_date = fields.Date(string='Date')
    confirm_date = fields.Date(string='Confirm Date')
    approve_date = fields.Date(string='Approve Date')
    done_date = fields.Date(string='Approve Date')
    reasons = fields.Text( string ='Reasons', required=True)
    type = fields.Selection([
        ('separation','Separation'),('end_contract','End contract') ])
    state = fields.Selection(
        [('draft', 'To Submit'), ('sent', 'Sent'), ('confirm', ' Confirm')
            , ('approve', 'Approve'), ('done', 'Done')], 'Status', default='draft')
    date_start = fields.Date(  related = 'employee_id.contract_id.date_start' , string = 'Date Start')
    material = fields.Integer( string ='Material')
    depr_nots = fields.Text( string ="Supervisor Notes" )
    accu_nots= fields.Text( string = " Finance Notes")
    gm_nots= fields.Text( string = "  Notes")

    @api.one
    def send_request(self):
        self.state = 'sent'
        self.send_date = fields.Date.today()

    @api.one
    def confirm_request(self):
        self.state = 'confirm'
        self.confirm_date = fields.Date.today()

    @api.one
    def approve_request(self):
        self.state = 'approve'
        self.approve_date = fields.Date.today()

    @api.one
    def done_approve(self):
        self.state = 'done'
        self.last_date = fields.Date.today()
        y = self._cr.execute("update hr_employee set last_date=%s , active=%s  where id=%s", (self.last_date, 'False', self.employee_id.id))

















