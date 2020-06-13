from odoo import api, fields, models, _
from odoo.exceptions import UserError, Warning
from datetime import datetime,date
from dateutil.relativedelta import relativedelta
from odoo.tools import float_compare
import math
import babel
import time
from odoo import tools
import calendar



class hr_loan(models.Model):
	_name = 'hr.loan'
	_inherit = ['mail.thread']
	_description = "HR Loan Request"
	# @api.model
	# def create(self, vals):
	# 	if vals.get('name', 'New') == 'New':
	# 		vals['name'] = self.env['ir.sequence'].next_by_code('hr.loan') or '/'
	# 	return super(hr_loan, self).create(vals)


	@api.model
	def create(self, vals):
		no_month = vals['no_month']
		if no_month > 10:
			raise Warning(_("period can't exceed 10 months"))
		if vals.get('name', 'New') == 'New':
			vals['name'] = self.env['ir.sequence'].next_by_code('hr.loan') or '/'
		return super(hr_loan, self).create(vals)

	@api.multi
	def write(self, values):
		res = super(hr_loan, self).write(values)
		no_month = self.no_month
		no_month = no_month
		if no_month > 10:
			raise Warning(_("period can't exceed 10 months"))
		return res

	def _default_employee(self):
		return self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

	def _get_default_company_id(self):
		return self._context.get('force_company', self.env.user.company_id.id)

	company_id = fields.Many2one('res.company', string='Company',
								 default=_get_default_company_id,readonly=True)
	name = fields.Char(string="Loan Name", default="/", readonly=True)
	date = fields.Date(string="Date Request", default=fields.Date.today(), readonly=True)
	employee_id = fields.Many2one('hr.employee', string="Employee", default=_default_employee, required=True)
	parent_id = fields.Many2one('hr.employee', related="employee_id.parent_id", string="Manager")
	department_id = fields.Many2one('hr.department', related="employee_id.department_id", readonly=True,
									string="Department")
	job_id = fields.Many2one('hr.job', related="employee_id.job_id", readonly=True, string="Job Position")
	employee_account = fields.Many2one('account.account', related="employee_id.account_id", string="Debit Account" )
	loan_account = fields.Many2one('account.account', string="Credit Account")
	journal_id = fields.Many2one('account.journal', string="Journal")
	loan_amount = fields.Float(string="Loan Amount", required=True)
	attach = fields.Binary("Attachments", help="here you can attach a file or a document to the record !!")
	total_amount = fields.Float(string="Total Amount", readonly=True, compute='_compute_amount')
	balance_amount = fields.Float(string="Balance Amount", compute='_compute_amount')
	total_paid_amount = fields.Float(string="Total Paid Amount", compute='_compute_amount')
	no_month = fields.Integer(string="No Of Month", default=1)
	payment_start_date = fields.Date(string="Start Date of Payment", required=True, default=fields.Date.today())
	loan_line_ids = fields.One2many('hr.loan.line', 'loan_id', string="Loan Line", index=True)
	entry_count = fields.Integer(string="Entry Count", compute='compute_entery_count')
	move_id = fields.Many2one('account.move', string="Journal Entry", readonly=True)
	refund_move_id = fields.Many2one('account.move', string="Journal Refund Entry", readonly=True)
	refund_amount = fields.Float(string='Refund')
	hr_note = fields.Text(string='Hr Note')
	emp_note = fields.Text(string='Employee Note')
	refund_amount = fields.Float(string='Refund')
	refund_date = fields.Date(string="Date Refund", readonly=True)
	state = fields.Selection(
		[('draft', 'To Submit'), ('approve', 'Approved'),
		 ('confirm', 'Confirmed'), ('gm_approve', 'Confirmed'), ('done', 'Done'), ('refunded', 'Refunded'),
		 ('refuse', 'Refused'), ('auditor', 'Auditor')],
		'Status', readonly=True, track_visibility='onchange', copy=False, default='draft')

	# @api.onchange('employee_id')
	# def onchange_emp_salary(self):
	#     self.emp_salary = self.employee_id.contract_id.total_salary

	@api.multi
	def unlink(self):
		for x in self:
			if any(x.filtered(lambda hr_loan: hr_loan.state not in ('draft', 'refuse'))):
				raise UserError(_('You cannot delete a Loan which is not draft or refused!'))
			return super(hr_loan, x).unlink()



	@api.one
	def _compute_amount(self):
		total_paid_amount = 0.00
		for loan in self:
			for line in loan.loan_line_ids:
				if line.paid:
					total_paid_amount += line.paid_amount

			balance_amount = loan.loan_amount - total_paid_amount
			loan.total_amount = loan.loan_amount
			loan.balance_amount = balance_amount
			loan.total_paid_amount = total_paid_amount
		# print self.balance_amount

	# @api.onchange('employee_id')
	# def _onchange_employee_d(self):
	#     for x in self:
	#         if x.employee_id:
	#             x.emp_salary = x.employee_id.contract_id.wage
	@api.one
	def loan_auditor(self):
		for x in self:
			x.state = 'auditor'

	@api.one
	def loan_refuse(self):
		for x in self:
			x.state = 'refuse'

	@api.one
	def loan_reset(self):
		for x in self:
			x.state = 'draft'

	@api.one
	def loan_confirm(self):
		for x in self:
			x.state = 'approve'

	@api.one
	def loan_gm_approve(self):
		for x in self:
			x.state = 'gm_approve'

	@api.one
	def hr_validate(self):
		for x in self:
			x.state = 'confirm'

	# @api.one
	@api.onchange('no_month')
	def validate_month(self):
		for x in self:
			if x.no_month < 1:
				raise Warning(_("Loan period can't be less than 1 month"))

			# return {'value':{'no_month':no_month}}

	@api.one
	def loan_validate(self):
		precision = self.env['decimal.precision'].precision_get('Payroll')
		self.env.cr.execute("""select current_date;""")
		xt = self.env.cr.fetchall()
		self.comment_date4 = xt[0][0]
		if not self.employee_account or not self.loan_account or not self.journal_id:
			raise Warning(_("You must enter employee account & Loan account and journal to approve "))
		if not self.loan_line_ids:
			raise Warning(_('You must compute Loan Request before Approved'))
		can_close = False
		loan_obj = self.env['hr.loan']
		move_obj = self.env['account.move']
		move_line_obj = self.env['account.move.line']
		currency_obj = self.env['res.currency']
		created_move_ids = []
		loan_ids = []
		for loan in self:
			line_ids = []
			debit_sum = 0.0
			credit_sum = 0.0
			loan_request_date = loan.date
			company_currency = loan.employee_id.company_id.currency_id.id
			current_currency = self.env.user.company_id.currency_id.id
			amount = loan.loan_amount
			loan_name = 'Loan For ' + loan.employee_id.name
			reference = loan.name
			journal_id = loan.journal_id.id
			move_dict = {
				'narration': loan_name,
				'ref': reference,
				'journal_id': journal_id,
				'date': loan_request_date,
			}
			debit_line = (0, 0, {
				'name': loan_name,
				'partner_id': False,
				'account_id': loan.employee_account.id,
				'journal_id': journal_id,
				'date': loan_request_date,
				'debit': amount > 0.0 and amount or 0.0,
				'credit': amount < 0.0 and -amount or 0.0,
				'analytic_account_id': False,
				'tax_line_id': 0.0,
			})
			line_ids.append(debit_line)
			debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']
			credit_line = (0, 0, {
				'name': loan_name,
				'partner_id': False,
				'account_id': loan.loan_account.id,
				'journal_id': journal_id,
				'date': loan_request_date,
				'debit': amount < 0.0 and -amount or 0.0,
				'credit': amount > 0.0 and amount or 0.0,
				'analytic_account_id': False,
				'tax_line_id': 0.0,
			})
			line_ids.append(credit_line)
			credit_sum += credit_line[2]['credit'] - credit_line[2]['debit']
			if float_compare(credit_sum, debit_sum, precision_digits=precision) == -1:
				acc_journal_credit = loan.journal_id.default_credit_account_id.id
				if not acc_journal_credit:
					raise UserError(_('The Expense Journal "%s" has not properly configured the Credit Account!') % (
						loan.journal_id.name))
				adjust_credit = (0, 0, {
					'name': _('Adjustment Entry'),
					'partner_id': False,
					'account_id': acc_journal_credit,
					'journal_id': journal_id,
					'date': loan_request_date,
					'debit': 0.0,
					'credit': debit_sum - credit_sum,
				})
				line_ids.append(adjust_credit)

			elif float_compare(debit_sum, credit_sum, precision_digits=precision) == -1:
				acc_journal_deit = loan.journal_id.default_debit_account_id.id
				if not acc_journal_deit:
					raise UserError(_('The Expense Journal "%s" has not properly configured the Debit Account!') % (
						loan.journal_id.name))
				adjust_debit = (0, 0, {
					'name': _('Adjustment Entry'),
					'partner_id': False,
					'account_id': acc_journal_deit,
					'journal_id': journal_id,
					'date': loan_request_date,
					'debit': credit_sum - debit_sum,
					'credit': 0.0,
				})
				line_ids.append(adjust_debit)
			move_dict['line_ids'] = line_ids
			move = self.env['account.move'].create(move_dict)
			loan.write({'move_id': move.id, 'date': loan_request_date})
			move.post()
			self.state = 'done'

	@api.multi
	def compute_loan_line(self):
		for loan in self:
			loan_line = self.env['hr.loan.line']
			loan_line.search([('loan_id', '=', self.id)]).unlink()
			date_start_str = datetime.strptime(str(loan.payment_start_date), '%Y-%m-%d')
			counter = 1
			amount_per_time = loan.loan_amount / loan.no_month
			for i in range(1, loan.no_month + 1):
				if i != loan.no_month:
					line_id = loan_line.create({
						'paid_date': date_start_str,
						'paid_amount': round(amount_per_time, 2),
						'employee_id': loan.employee_id.id,
						'loan_id': loan.id})
				elif i == loan.no_month:
					line_id = loan_line.create({
						'paid_date': date_start_str,
						'paid_amount': round(amount_per_time, 2) +
									   round(loan.loan_amount - (round(amount_per_time, 2) * loan.no_month), 2),
						'employee_id': loan.employee_id.id,
						'loan_id': loan.id})
				counter += 1
				date_start_str = date_start_str + relativedelta(months=1)

		return True

	@api.model
	@api.multi
	def compute_entery_count(self):
		for loan in self:
			count = 0
			entry_count = loan.env['account.move.line'].search_count([('loan_id', '=', loan.id)])
			loan.entry_count = entry_count

	@api.multi
	def button_reset_balance_total(self):
		total_paid_amount = 0.00
		for loan in self:
			for line in loan.loan_line_ids:
				if line.paid:
					total_paid_amount += line.paid_amount
			balance_amount = loan.loan_amount - total_paid_amount
			self.write({'total_paid_amount': total_paid_amount, 'balance_amount': balance_amount})

	@api.constrains('employee_id')
	def _emp_loan_unpaid(self):
		for loan in self:
			if loan.employee_id:
				past_loans_ids = loan.env['hr.loan'].search(
					[('employee_id', '=', loan.employee_id.id), ('state', '=', 'done')])
				for past_loans in past_loans_ids:
					loan_line_ids = loan.env['hr.loan.line'].search([('loan_id', '=', past_loans.id)])
					for loan_line in loan_line_ids:
						if not loan_line.paid:
							raise Warning(_(
								"This employee must complete payments for a current running loan, in order to request another"))


class hr_loan_line(models.Model):
	_name = "hr.loan.line"
	_description = "HR Loan Request Line"

	paid_date = fields.Date(string="Payment Date", required=True)
	employee_id = fields.Many2one('hr.employee', string="Employee")
	paid_amount = fields.Float(string="Paid Amount", required=True)
	paid = fields.Boolean(string="Paid")
	stopped = fields.Boolean(string="Stop Loan")
	notes = fields.Text(string="Notes")
	loan_id = fields.Many2one('hr.loan', string="Loan Ref.", ondelete='cascade')
	payroll_id = fields.Many2one('hr.payslip', string="Payslip Ref.")

	@api.one
	def action_paid_amount(self):
		for line in self:
			context = self._context
			can_close = False
			loan_obj = self.env['hr.loan']
			move_obj = self.env['account.move']
			move_line_obj = self.env['account.move.line']
			currency_obj = self.env['res.currency']
			created_move_ids = []
			loan_ids = []
			if not line.payroll_id:
				if line.loan_id.state != 'done':
					raise Warning(_("Loan Request must be approved"))
				paid_date = line.paid_date
				company_currency = line.employee_id.company_id.currency_id.id
				current_currency = self.env.user.company_id.currency_id.id
				amount = line.paid_amount
				loan_name = line.employee_id.name
				reference = line.loan_id.name
				journal_id = line.loan_id.journal_id.id
				move_vals = {
					'name': loan_name,
					'date': paid_date,
					'ref': reference,
					'journal_id': journal_id,
					'state': 'draft',
				}
				move_id = move_obj.create(move_vals)
				move_line_vals = {
					'name': loan_name,
					'ref': reference,
					'move_id': move_id.id,
					'account_id': line.loan_id.employee_account.id,
					'analytic_account_id': False,
					'debit': 0.0,
					'credit': amount,
					'journal_id': journal_id,
					'date': paid_date,
					'loan_id': line.loan_id.id,
				}
				move_line_obj.create(move_line_vals)
				move_line_vals2 = {
					'name': loan_name,
					'ref': reference,
					'move_id': move_id.id,
					'account_id': line.loan_id.loan_account.id,
					'analytic_account_id': False,
					'credit': 0.0,
					'debit': amount,
					'journal_id': journal_id,
					'date': paid_date,
					'loan_id': line.loan_id.id,
				}
				move_line_obj.create(move_line_vals2)
				self.write({'paid': True})
			else:
				self.write({'paid': True})
		return True

	@api.one
	@api.constrains('paid_amount')
	def _loan_line_installment(self):
		for x in self:
			if x.paid_amount:
				short_loan_ids = x.env['hr.monthly'].search(
					[('employee_id', '=', x.employee_id.id), ('state', '=', 'done')])
				short_loan_amt = 0.00
				for loan in short_loan_ids:
					DATETIME_FORMAT = "%Y-%m-%d"
					short_loan_date = datetime.strptime(loan.date, DATETIME_FORMAT)
					installment_loan_date = datetime.strptime(x.paid_date, DATETIME_FORMAT)
					if short_loan_date.month == installment_loan_date.month:
						short_loan_amt += loan.loan_amount
				# if x.paid_amount + short_loan_amt > x.loan_id.emp_salary * 0.8:
				#     raise Warning(_("Monthly Loan  Cannot Exceed 70%% of The Employee's Salary!"))
				short_loan_ids = x.env['hr.monthly'].search(
					[('employee_id', '=', x.employee_id.id), ('state', '=', 'done')])
				short_loan_amt = 0.00
				for loan in short_loan_ids:
					DATETIME_FORMAT = "%Y-%m-%d"
					short_loan_date = datetime.strptime(loan.date, DATETIME_FORMAT)
					installment_loan_date = datetime.strptime(x.paid_date, DATETIME_FORMAT)
					if short_loan_date.month == installment_loan_date.month:
						short_loan_amt += loan.loan_amount
					# if x.paid_amount + short_loan_amt > x.loan_id.emp_salary:
					#     raise Warning(_("Monthly Loan Cannot Exceed The Employee's Salary!"))


class hr_monthly(models.Model):
	_name = 'hr.monthly'
	# _inherit = ['mail.thread']

	@api.model
	def create(self, vals):
		# no_month = vals['no_month']
		# if no_month > 10:
		# 	raise Warning(_("period can't exceed 10 months"))
		if vals.get('name', 'New') == 'New':
			vals['name'] = self.env['ir.sequence'].next_by_code('hr.monthly') or '/'
		return super(hr_monthly, self).create(vals)


	def _default_employee(self):
		return self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

	def _get_default_company_id(self):
		return self._context.get('force_company', self.env.user.company_id.id)

	company_id = fields.Many2one('res.company', string='Company',
								 default=_get_default_company_id,readonly=True)
	name = fields.Char(string="Loan Name", default="/", readonly=True)
	date = fields.Date(string="Date Request", default=fields.Date.today(), readonly=True)
	date_pay = fields.Date(string="Loan Pay Date", readonly=True)
	employee_id = fields.Many2one('hr.employee', string="Employee", default=_default_employee, required=True)
	department_id = fields.Many2one('hr.department', related="employee_id.department_id", readonly=True,string="Department")
	loan_amount = fields.Float(string="Loan Amount", required=True)
	employee_salary = fields.Float(string="Employee Salary",  related="employee_id.contract_id.benefits")
	employee_account = fields.Many2one('account.account', related="employee_id.account_id", string="Debit Account")
	loan_account = fields.Many2one('account.account', string="Credit Account",related="employee_id.account_id")
	journal_id = fields.Many2one('account.journal', string="Journal")
	move_id = fields.Many2one('account.move', string="Journal Entry", readonly=True)
	move_id_pay = fields.Many2one('account.move', string="Loan Pay Entry", readonly=True)
	state = fields.Selection(
		[('draft', 'To Submit'), ('confirm', 'To Approve'),
		 ('approve', 'Approved by HR'), ('done', 'Done'), ('paid', 'Paid'),
		 ('refuse', 'Refused'),('auditor', 'Auditor')],
		'Status', default='draft', readonly=True)

	@api.one
	def loan_auditor(self):
		for x in self:
			x.state = 'auditor'


	@api.model
	def _needaction_domain_get(self):
		hr = self.employee_id.user_id.has_group('hr.group_hr_manager')
		gm = self.employee_id.user_id
		account = self.employee_id.user_id.has_group('account.group_account_manager')

		hr_approve = hr and 'confirm' or None
		account_approve = account and 'approve' or None

		return [('state', 'in', (hr_approve, account_approve))]

	@api.one
	def loan_confirm(self):
		self.state = 'confirm'

	@api.one
	def loan_approve(self):
		for line in self:
			if line.employee_id:
				employee_id = line.employee_id.id
				hr_contract = line.env['hr.contract'].search([('employee_id', '=', employee_id)])
				loan_amount = self.loan_amount
				amount = 0.0
				for loan in hr_contract:
					benefits = loan.benefits
					amount = benefits - loan_amount
			        loan.benefits = amount
			self.state = 'approve'

	@api.one
	def action_paid(self):
		can_close = False
		loan_obj = self.env['hr.monthly']
		move_obj = self.env['account.move']
		move_line_obj = self.env['account.move.line']
		created_move_ids = []
		loan_ids = []
		for loan in self:
			if loan.state == 'done':
				loan_pay_date = fields.Date.today()
				amount = loan.loan_amount
				loan_name = 'Loan Payment For ' + loan.employee_id.name
				reference = loan.name
				journal_id = loan.journal_id.id
				move_obj = self.env['account.move']
				move_line_obj = self.env['account.move.line']
				currency_obj = self.env['res.currency']
				created_move_ids = []
				loan_ids = []

				line_ids = []
				debit_sum = 0.0
				credit_sum = 0.0
				move_dict = {
					'narration': loan_name,
					'ref': reference,
					'journal_id': journal_id,
					'date': loan_pay_date,
				}

				debit_line = (0, 0, {
					'name': loan_name,
					'partner_id': False,
					'account_id': loan.loan_account.id,
					'journal_id': journal_id,
					'date': loan_pay_date,
					'debit': amount > 0.0 and amount or 0.0,
					'credit': amount < 0.0 and -amount or 0.0,
					'analytic_account_id': False,
					'tax_line_id': 0.0,
				})
				line_ids.append(debit_line)
				debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']
				credit_line = (0, 0, {
					'name': loan_name,
					'partner_id': False,
					'account_id': loan.employee_account.id,
					'journal_id': journal_id,
					'date': loan_pay_date,
					'debit': amount < 0.0 and -amount or 0.0,
					'credit': amount > 0.0 and amount or 0.0,
					'analytic_account_id': False,
					'tax_line_id': 0.0,
				})
				line_ids.append(credit_line)
				credit_sum += credit_line[2]['credit'] - credit_line[2]['debit']
				move_dict['line_ids'] = line_ids
				move = self.env['account.move'].create(move_dict)
				loan.write({'move_id_pay': move.id, 'date_pay': loan_pay_date})
				move.post()
		self.state = 'paid'



	@api.constrains('employee_id')
	def con(self):
		for line in self:
			if line.employee_id:
				employee_id = line.employee_id.id
				hr_employee = line.env['hr.employee'].search([('id', '=', employee_id)])
				if not hr_employee.hiring_date:
					raise UserError(_('Please Add employee Hiring date!'))
				hiring = str(hr_employee.hiring_date)
				hiring_date = datetime.strptime(hiring, '%Y-%m-%d')
				today = date.today()
				str_now = datetime.strptime(str(today), '%Y-%m-%d')
				employee_period = (str_now - hiring_date).days
				if employee_period < 365.25:
					raise UserError(_('You can not request Loan before you complete One Year!'))
				# long = line.env['hr.monthly'].search([('employee_id', '=', employee_id), ('state', '=', 'done')
				# 	raise UserError(_('Please Add Long!'))
				# past_loans_ids = line.env['hr.monthly'].search(
				# 	[('employee_id', '=', line.employee_id.id), ('state', '=', 'done')])
				# if not past_loans_ids:
				# 	raise Warning(_(
				# 		"This employee must complete payments for a current running loan, in order to request another"))

	@api.depends('employee_id')
	def _compute_salary(self):
		for line in self:
			if line.employee_id:
				employee_id = line.employee_id.id
				hr_employee = line.env['hr.employee'].search([('name', '=', employee_id)])
				for emp in hr_employee:
					# benefits = emp.contract_id.benefits
					company_id = emp.company_id
					department_id = emp.department_id
				self.employee_salary = emp.contract_id.benefits
				self.company_id = company_id
				self.department_id = department_id

	@api.one
	def loan_validate(self):
		if not self.employee_account or not self.loan_account or not self.journal_id:
			raise Warning(_("You must enter employee account & Loan account and journal to approve "))
		move_obj = self.env['account.move']
		move_line_obj = self.env['account.move.line']
		currency_obj = self.env['res.currency']
		created_move_ids = []
		loan_ids = []
		for monthh_loan in self:
			line_ids = []
			debit_sum = 0.0
			credit_sum = 0.0
			loan_date = monthh_loan.date
			company_currency = monthh_loan.employee_id.company_id.currency_id.id
			current_currency = self.env.user.company_id.currency_id.id
			amount = monthh_loan.loan_amount
			# employee_salary = self.employee_id.contract_id.total_salary
			# if amount > employee_salary/2 :
			#     raise Warning(_("Loan should not exceed half of employee salary"))
			loan_name = 'Loan For ' + monthh_loan.employee_id.name
			reference = monthh_loan.name
			journal_id = monthh_loan.journal_id.id
			move_dict = {
				'narration': loan_name,
				'ref': reference,
				'journal_id': journal_id,
				'date': loan_date,
			}
			debit_line = (0, 0, {
				'name': loan_name,
				'partner_id': False,
				'account_id': monthh_loan.employee_account.id,
				'journal_id': journal_id,
				'date': loan_date,
				'debit': amount > 0.0 and amount or 0.0,
				'credit': amount < 0.0 and -amount or 0.0,
				'analytic_account_id': False,
				'tax_line_id': 0.0,
			})
			line_ids.append(debit_line)
			debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']
			credit_line = (0, 0, {
				'name': loan_name,
				'partner_id': False,
				'account_id': monthh_loan.loan_account.id,
				'journal_id': journal_id,
				'date': loan_date,
				'debit': amount < 0.0 and -amount or 0.0,
				'credit': amount > 0.0 and amount or 0.0,
				'analytic_account_id': False,
				'tax_line_id': 0.0,
			})
			line_ids.append(credit_line)
			credit_sum += credit_line[2]['credit'] - credit_line[2]['debit']
			move_dict['line_ids'] = line_ids
			move = self.env['account.move'].create(move_dict)
			monthh_loan.write({'move_id': move.id, 'date': loan_date})
			move.post()
			self.state = 'done'

	# @api.one
	# @api.constrains('loan_amount')
	# def _loan_amount(self):
	#     if self.loan_amount:
	#         salary = self.employee_salary
	#         allowable_loan = salary * 70 / 100
	#         if self.loan_amount > allowable_loan:
	#             raise Warning(_("Monthly Loan Cannot Exceed 70% of The Employee's Salary!"))

	@api.one
	def loan_refuse(self):
		self.state = 'refuse'

	@api.one
	def loan_reset(self):
		self.state = 'draft'

	@api.multi
	def unlink(self):
		for rec in self:
			if rec.state != 'draft':
				raise Warning(_("Warning! You cannot delete a Loan which is in %s state.") % (rec.state))
			return super(hr_monthly, self).unlink()


class WizardLoan(models.Model):
	_name = 'wizard.loan'
	_description = 'Pay Loan'
	loan_id = fields.Many2one('hr.loan', 'Loan', ondelete='cascade')
	refund_amount = fields.Float('Refund')

	def refund_loan(self):
		for loan in self:
			if loan.loan_id:
				refund_amount = loan.refund_amount
				hr_loan_id = loan.loan_id
				unpaid_amount = hr_loan_id.balance_amount
				total_amount = hr_loan_id.loan_amount
				reaming_amount = unpaid_amount - refund_amount
				if reaming_amount == 0:
					if hr_loan_id.state == 'done':
						loan_amount = 0.0
						acc_journal_credit = hr_loan_id.journal_id.default_credit_account_id.id
						acc_journal_debit = hr_loan_id.journal_id.default_credit_account_id.id
						if not acc_journal_credit:
							raise UserError(
								_('The Expense Journal "%s" has not properly configured the Credit Account!') % (
									hr_loan_id.journal_id.name))

						precision = self.env['decimal.precision'].precision_get('Payroll')
						self.env.cr.execute("""select current_date;""")
						xt = self.env.cr.fetchall()
						self.comment_date4 = xt[0][0]
						loan_line_ids = hr_loan_id.loan_line_ids
						for loan_line in loan_line_ids:
							paid = loan_line.paid
							if not paid:
								loan_line.paid = True
								created_move_ids = []
								loan_ids = []
								line_ids = []
								debit_sum = 0.0
								credit_sum = 0.0
								refund_date = fields.Date.today()
								journal_id = hr_loan_id.journal_id.id
								company_currency = hr_loan_id.employee_id.company_id.currency_id.id
								current_currency = hr_loan_id.env.user.company_id.currency_id.id
								ref_loan_name = 'Refund Loan For ' + hr_loan_id.employee_id.name
								reference = 'Refund Loan'
								move_dict = {
									'narration': ref_loan_name,
									'ref': reference,
									'journal_id': journal_id,
									'date': refund_date,
								}
								debit_line = (0, 0, {
									'name': ref_loan_name,
									'partner_id': False,
									'account_id': hr_loan_id.loan_account.id,
									'journal_id': journal_id,
									'date': refund_date,
									'debit': unpaid_amount > 0.0 and unpaid_amount or 0.0,
									'credit': unpaid_amount < 0.0 and -unpaid_amount or 0.0,
									'analytic_account_id': False,
									'tax_line_id': 0.0,
								})
								line_ids.append(debit_line)
								debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']
								credit_line = (0, 0, {
									'name': ref_loan_name,
									'partner_id': False,
									'account_id': hr_loan_id.employee_account.id,
									'journal_id': journal_id,
									'date': refund_date,
									'debit': unpaid_amount < 0.0 and -unpaid_amount or 0.0,
									'credit': unpaid_amount > 0.0 and unpaid_amount or 0.0,
									'analytic_account_id': False,
									'tax_line_id': 0.0,
								})
								line_ids.append(credit_line)
								credit_sum += credit_line[2]['credit'] - credit_line[2]['debit']
								if float_compare(credit_sum, debit_sum, precision_digits=precision) == -1:
									adjust_credit = (0, 0, {
										'name': _('Adjustment Entry'),
										'partner_id': False,
										'account_id': acc_journal_debit,
										'journal_id': journal_id,
										'date': refund_date,
										'debit': 0.0,
										'credit': debit_sum - credit_sum,
									})
									line_ids.append(adjust_credit)

								elif float_compare(debit_sum, credit_sum, precision_digits=precision) == -1:
									if not acc_journal_debit:
										raise UserError(_(
											'The Expense Journal "%s" has not properly configured the Debit Account!') % (
															hr_loan_id.journal_id.name))
									adjust_debit = (0, 0, {
										'name': _('Adjustment Entry'),
										'partner_id': False,
										'account_id': acc_journal_credit,
										'journal_id': journal_id,
										'date': refund_date,
										'debit': credit_sum - debit_sum,
										'credit': 0.0,
									})
									line_ids.append(adjust_debit)
								move_dict['line_ids'] = line_ids
								move = loan.env['account.move'].create(move_dict)
								hr_loan_id.write({'refund_move_id': move.id, 'refund_date': refund_date,
												  'state': 'refunded'})
								move.post()
				else:
					raise UserError(_('You Have To Refund %s') % unpaid_amount)


class StopLoans(models.TransientModel):
    _name = 'wizard.loan.stop'
    date_from = fields.Date('Date From',  default=time.strftime('%Y-%m-01'), required=True)
    date_to = fields.Date('Date To', required=True)

    @api.multi
    def action_stop_loans(self):
        for rec in self:
            loan_line = self.env['hr.loan.line'].browse(self.env.context.get('active_ids'))

            loan_ids = loan_line.search([('paid_date', '>=', rec.date_from),
                                                        ('paid_date', '<=', rec.date_to),
                                                        ('loan_id.state', '=', 'done')])
            for loan in loan_ids:
                loan_id = loan.loan_id
                new_installment_amount = loan_id.loan_amount
                if loan_id:
                    loan_line_rec = loan_id.loan_line_ids.search(
                        [('paid_date', '>=', rec.date_from), ('paid_date', '<=', rec.date_to)
                            , ('loan_id.state', '=', 'done'), ('employee_id', '=', loan_id.employee_id.id)])
                    if not loan_line_rec:
                        raise UserError(_('Dates you select are not exits in this loan'))
                    else:
                        employee_id = loan_id.employee_id
                        loan_line_ids = loan_line.search([('employee_id', '=', employee_id.id), ('paid_date', '<=', rec.date_to)
                                                             , ('paid_date', '>=', rec.date_from), ('paid', '=', False),
                                                          ('loan_id.state', '=', 'done')])
                        for loan_line_id in loan_line_ids:
                            paid_amount = loan_line_id.paid_amount
                            paid_date = loan_line_id.paid_date
                            loan_id1 = loan_line_id.loan_id
                            loan_update_id = loan_line_id.id
                            per_loan = loan_line.search([('employee_id', '=', employee_id.id), ('loan_id.state', '=', 'done')
                                                         ])
                            for per in per_loan:
                                per_date_pay = per.paid_date
                                per_paid_amount = per.paid_amount
                                per_date_pay = datetime.strptime(str(per_date_pay), '%Y-%m-%d') + relativedelta(months=1)
                                per_loan_id = per.loan_id
                                per_id = per.id
                            amount = per_paid_amount
                            # if per_paid_amount < paid_amount:
                            if per_paid_amount < new_installment_amount:
                                x = new_installment_amount - per_paid_amount
                                if x < new_installment_amount:
                                    new_installment_amount = x + per_paid_amount
                                else:
                                    new_installment_amount = x
                                self._cr.execute(
                                    "update hr_loan_line set paid_amount=%s   where id = %s",
                                    (new_installment_amount, per_id))
                                paid_amount = per_paid_amount
                            loan_line.create({
                                'paid_date': per_date_pay,
                                'paid_amount': round(paid_amount, 2),
                                'employee_id': employee_id.id,
                                'loan_id': per_loan_id.id})
                            self._cr.execute(
                                "update hr_loan_line set stopped=%s   where loan_id=%s and paid_date =%s and id = %s",
                                (True, loan_id1.id, paid_date, loan_update_id))


class account_move_line(models.Model):
	_inherit = "account.move.line"

	loan_id = fields.Many2one('hr.loan', string="Loan", ondelete='cascade')

