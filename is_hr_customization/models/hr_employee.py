import logging

from odoo import api, fields, models
from odoo import tools, _
from odoo.exceptions import ValidationError
from odoo.modules.module import get_module_resource
from odoo.exceptions import UserError, Warning
from datetime import datetime,date
import calendar

class HrEmployee(models.Model):
	_name = 'hr.employee'
	_description = 'Employee'
	_inherit = ['hr.employee']

	@api.multi
	def _inverse_remaining_leaves(self):
		status_list = self.env['hr.holidays.status'].search([('limit', '=', False)])
		actual_remaining = self._get_remaining_leaves()
		for employee in self.filtered(lambda employee: employee.remaining_leaves):
			if len(status_list) != 1:
				raise UserError(
					_("The feature behind the field 'Remaining Legal Leaves' can only be used when there is only one "
					  "leave type with the option 'Allow to Override Limit' unchecked. (%s Found). "
					  "Otherwise, the update is ambiguous as we cannot decide on which leave type the update has to be done. "
					  "\n You may prefer to use the classic menus 'Leave Requests' and 'Allocation Requests' located in Leaves Application "
					  "to manage the leave days of the employees if the configuration does not allow to use this field.") % (
						len(status_list)))
			status = status_list[0] if status_list else None
			if not status:
				continue
			difference = employee.remaining_leaves - actual_remaining.get(employee.id, 0)
			if difference > 0:
				leave = self.env['hr.holidays'].create({
					'name': _('Allocation for %s') % employee.name,
					'employee_id': employee.id,
					'holiday_status_id': status.id,
					'type': 'add',
					'holiday_type': 'employee',
					'number_of_days_temp': difference
				})
				leave.action_approve()
				if leave.double_validation:
					leave.action_validate()

	@api.model
	def add_anual_leave(self):
		today = date.today()
		str_now = datetime.strptime(str(today), '%Y-%m-%d')
		employees = self.env['hr.employee'].search([])
		for employee in employees:
			remaining_leaves = employee.remaining_leaves
			if employee.hiring_date:
				hiring_date = datetime.strptime(str(employee.hiring_date), '%Y-%m-%d')
				month_range = calendar.monthrange(str_now.year, str_now.month)[1]
				contract_ids = self.env['hr.contract'].search([('employee_id', '=', employee.id)])
				if contract_ids:
					last_contract = contract_ids[-1]
					type = last_contract.type_id
					deserved_leave = 0.0
					total_leave = last_contract.legal_leave
					employee_period = (str_now - hiring_date).days
					if employee_period > 365.25:
						if ((str_now - hiring_date).days + 1) >= month_range:
							if total_leave == '20':
								deserved_leave = 1.66
							if total_leave == '25':
								deserved_leave = 2.08
							if total_leave == '30':
								deserved_leave = 2.5
							employee.remaining_leaves += deserved_leave
						if ((str_now - hiring_date).days + 1) < month_range:
							if total_leave == '20':
								desr = 1.66 / month_range
								deserved_leave = (desr * ((str_now - hiring_date).days + 1)) + remaining_leaves
							if total_leave == '25':
								desr = 2.08 / month_range
								deserved_leave = (desr * ((str_now - hiring_date).days + 1)) + remaining_leaves
							if total_leave == '30':
								desr = 2.5 / month_range
								deserved_leave = (desr * ((str_now - hiring_date).days + 1)) + remaining_leaves
							employee.remaining_leaves = deserved_leave

	@api.depends('birthday')
	def _calculate_age(self):
		str_now = datetime.now().date()
		age = ''
		for employee in self:
			if employee.birthday:
				date_start = datetime.strptime(str(employee.birthday), '%Y-%m-%d').date()
				total_days = (str_now - date_start).days
				employee_years = int(total_days / 365)
				remaining_days = total_days - 365 * employee_years
				employee_months = int(12 * remaining_days / 365)
				employee_days = int(0.5 + remaining_days - 365 * employee_months / 12)
				age = str(employee_years) + ' Year(s) ' + str(employee_months) + ' Month(s) ' + str(
					employee_days) + ' day(s)'
			employee.age = age


	loan_ids = fields.One2many('hr.monthly', 'employee_id', 'Long Lone')
	account_id = fields.Many2one('account.account', 'Account Employee')
	# employee_id = fields.Many2one('hr.gratuities.paysheet')
	short_loan_ids = fields.One2many('hr.loan', 'employee_id', 'Short Lone')
	# custody_ids = fields.One2many('hr.custody', 'employee', 'Custody')
	hr_warning_ids = fields.One2many('hr.warnings', 'employee_id', 'Warnings')
	hiring_date = fields.Date('Hiring Date', required='True')
	relation = fields.Char('Relation Name')
	home_address = fields.Char('Home Address')
	relative_relation = fields.Char('Relative Relation')
	phone = fields.Char('Phone')
	age = fields.Char(compute='_calculate_age', string='Age', store=True)
	custody_count = fields.Integer(compute='_custody_count', store=True ,string='# Custody')
	remaining_leaves = fields.Float(compute='_compute_remaining_leaves', digits=(12, 6),
									string='Remaining Legal Leaves', inverse='_inverse_remaining_leaves',
									help='Total number of legal leaves allocated to this employee, change this value to create allocation/leave request. '
										 'Total based on all the leave types without overriding limit.')

	bank_id = fields.Many2one('hr.bank', 'Bank Name')
	branch_id = fields.Many2one('hr.bank.branches', 'Branch Name', domain="[('bank_id','=',bank_id)]")
	bank_account_no = fields.Char('Bank Account No')

	@api.multi
	def _custody_count(self):
		for each in self:
			custody_ids = self.env['hr.custody'].search([('employee', '=', each.id)])
			each.custody_count = len(custody_ids)

	@api.multi
	def custody_view(self):
		for each1 in self:
			custody_obj = self.env['hr.custody'].search([('employee', '=', each1.id)])
			custody_ids = []
			for each in custody_obj:
				custody_ids.append(each.id)
			view_id = self.env.ref('is_hr_customization.hr_custody_form_view').id
			if custody_ids:
				if len(custody_ids) <= 1:
					value = {
						'view_type': 'form',
						'view_mode': 'form',
						'res_model': 'hr.custody',
						'view_id': view_id,
						'type': 'ir.actions.act_window',
						'name': _('Custody'),
						'res_id': custody_ids and custody_ids[0]
					}
				else:
					value = {
						'domain': str([('id', 'in', custody_ids)]),
						'view_type': 'form',
						'view_mode': 'tree,form',
						'res_model': 'hr.custody',
						'view_id': False,
						'type': 'ir.actions.act_window',
						'name': _('Custody'),
						'res_id': custody_ids
					}

				return value



class hr_bank(models.Model):
    _name = 'hr.bank'
    name = fields.Char(string='Bank Name')
    journal_id = fields.Many2one('account.journal','Journal')
    branch_ids = fields.One2many('hr.bank.branches','bank_id','Bank Branches')
    account_id = fields.Many2one('account.account', 'Account')

class hr_bank_branches(models.Model):
    _name = 'hr.bank.branches'
    name = fields.Char(string='Branch Name')
    bank_id = fields.Many2one('hr.bank', 'Bank')


class HrContract(models.Model):
	_name = 'hr.contract'
	_description = 'Contract'
	_inherit = ['hr.contract']
	# _rec_name ='sequence_name'



	@api.model
	def create(self, vals):
		if vals.get('name_ex', 'New') == 'New':
			vals['name_ex'] = self.env['ir.sequence'].next_by_code('hr.contract') or '/'
		return super(HrContract, self).create(vals)

	name_ex = fields.Char('Contract', readonly=True)
	gross = fields.Float('Gross')
	# gratuities = fields.Float('Gratuities')
	paid_leave = fields.Float('Paid Leave')
	incentive = fields.Float('Incentive')
	benefits = fields.Float('Benefits', compute="add_annual_benefits", store=True)
	# taker_benefits = fields.Float('Taker Benefits', compute="compute_taker_benfits", store=True)
	total_salary = fields.Float('Total Salary', compute="compute_salary", store=True)
	legal_leave = fields.Selection(
		[('20', '20 days'), ('25', '25 days'), ('30', '30 days')], string='Legal Leave', default='20', required=True)
	attach = fields.Binary("Attachment CV", required=True)
	text = fields.Text("Terms Contract",default="t")



	@api.multi
	@api.depends('wage', 'gross')
	def compute_salary(self):
		for rec in self:
			rec.total_salary = rec.wage + rec.gross

	# @api.constrains('employee_id', 'total_salary', 'incentive', 'paid_leave')
	# def compute_benfits(self):
	# 	for line in self:
	# 		if line.employee_id:
	# 			employee_id = line.employee_id.id
	# 			hr_employee = line.env['hr.employee'].search([('id', '=', employee_id)])
	# 			if not hr_employee.hiring_date:
	# 				raise UserError(_('Please Add employee Hiring date!'))
	# 			hiring = str(hr_employee.hiring_date)
	# 			hiring_date = datetime.strptime(hiring, '%Y-%m-%d')
	# 			today = date.today()
	# 			str_now = datetime.strptime(str(today), '%Y-%m-%d')
	# 			employement_period = (str_now - hiring_date).days
	#
	# 			if employement_period >= 365.25:
	# 				line.benefits = (line.total_salary * 12 * 92 / 100 * 25 / 100) + line.incentive + line.paid_leave
	@api.model
	def add_annual_benefits(self):
		today = date.today()
		str_now = datetime.strptime(str(today), '%Y-%m-%d')
		employees = self.env['hr.employee'].search([])
		for employee in employees:
			remaining_leaves = employee.remaining_leaves
			if employee.hiring_date:
				hiring_date = datetime.strptime(str(employee.hiring_date), '%Y-%m-%d')
				month_range = calendar.monthrange(str_now.year, str_now.month)[1]
				contract_ids = self.env['hr.contract'].search([('employee_id', '=', employee.id)])
				if contract_ids:
					last_contract = contract_ids[-1]
					type = last_contract.type_id
					deserved_leave = 0.0
					total_salary = last_contract.total_salary
					# if hiring_date < str_now:
					# if ((str_now - hiring_date).days + 1) >= month_range:
					deserved_leave = (total_salary * 25/100*92/100) + last_contract.incentive + last_contract.paid_leave
					last_contract.benefits += deserved_leave



class Hr_permission(models.Model):
	_name = 'hr.permission'

	name = fields.Many2one('hr.permission.details',string="Permission")
	employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
	date = fields.Date(string="Date", default=fields.Date.today(), readonly=True)
	date_from = fields.Datetime(string='Date From')
	date_to = fields.Datetime(string='Date To')
	time_permission = fields.Float(string='Time Permission', compute="_calculate_age", store=True)
	reasons = fields.Text(string="Reasons", required=True)
	supervisor_notes = fields.Text(string="Supervisor Notes")
	type = fields.Selection(
		[('rest', 'Rest'), ('other', 'Other')]
	)
	state = fields.Selection(
		[('draft', 'To Submit'), ('cancel', 'Cancel'), ('submit', 'Submit'),
		 ('hr_approve', 'Approve')], 'Status', default='draft')
	request_unit_half = fields.Boolean('Half Day')
	request_date_from = fields.Date('Request Start Date')
	request_date_to = fields.Date('Request End Date')
	request_date_from_period = fields.Selection([
		('am', 'Morning'), ('pm', 'Afternoon')],
		string="Date Period Start", default='am')
	attach = fields.Binary("Attachment")

	@api.one
	def submit_request(self):
		self.state = 'submit'

	@api.one
	def approve_request(self):
		self.state = 'hr_approve'

	@api.one
	def request_cancel(self):
		self.state = 'cancel'



class Hr_permission_details(models.Model):
	_name = 'hr.permission.details'

	name = fields.Char('Permission')

class Hr_task_line(models.Model):
	_name = 'hr.task.line'

	product_id = fields.Many2one('product.product', 'Product')
	quantity = fields.Float('Quantity')
	note = fields.Text('Note')
	price = fields.Float('Price')
	purchase = fields.Boolean('Purchase')
	uom_id = fields.Many2one('product.uom', 'Product Uom')
	account_id = fields.Many2one('account.account', 'Account')
	task_id = fields.Many2one('hr.task', 'Task')

	@api.onchange('product_id')
	def _onchange_product_id(self):
		self.uom_id = self.product_id.uom_id.id
		self.account_id = self.product_id.property_account_expense_id.id

class Hr_task(models.Model):
	_name = 'hr.task'

	name = fields.Many2one('hr.employee', string="Employee", required=True)
	task_ids = fields.One2many('hr.task.line','task_id', string="Task")
	department_id = fields.Many2one('hr.department', string='Department')
	date = fields.Date(string="Date", default=fields.Date.today(), readonly=True)
	note = fields.Text(string="Note")
	task_type = fields.Selection(
		[('finance', 'Finance'), ('material', 'Material')], 'Task Type', default='finance')
	# reason = fields.Text(string="Reason")
	amount = fields.Float(string="Amount")
	description = fields.Text(string="Description")
	payment_finance_approval_id = fields.Many2one('finance.approval', 'Payment Finance Approval No.', readonly=True)
	state = fields.Selection(
		[('draft', 'To Submit'), ('submit', 'Submit'),
		 ('approve', 'Approve'),('request', 'Material Requested'),('finance', 'Finance Requested'), ('done', 'Done')], 'Status', default='draft')

	@api.one
	def order_stock(self):
		material_obj = self.env['material.request']
		# self.material = True
		material_vals = {
			'state': 'draft',
			'applicant_name': self.name.id,
		}
		request_id = material_obj.create(material_vals)
		for obj in self.task_ids:
			product_id = obj.product_id.id
			quantity = obj.quantity
		# self.request_id = request_id.id
		material_order_lines_vals = {'request_id': request_id.id,
									 'product_id': product_id,
									 'ordered_qty': quantity,
									 }
		line = self.env['material.request.line']
		line.create(material_order_lines_vals)
		self.state = 'request'

	@api.one
	def submit_request(self):
		self.state = 'submit'


	# @api.one
	# def finance_request(self):
	# 	financial_approval_vals = {'emp': self.name.id,
	# 							   'amount_ids': [(0, 0, {'request_amount': self.amount,
	# 													  'reason': self.description})],
	# 							   }
	# 	self.payment_finance_approval_id = self.env['finance.approval'].create(financial_approval_vals)
	# 	self.state = 'finance'
	@api.one
	def finance_request(self):
		finance_obj = self.env['finance.approval']
		finance_vals = {

				'state': 'draft',
				'requester': self.name.name,
				'fa_date': self.date,
				'request_amount': self.amount,
				'reason': self.description,
			}
		finance_obj.create(finance_vals)
		self.state ='finance'
		# self.request =True
	@api.one
	def approve_request(self):
		self.state = 'approve'

	@api.one
	def done_request(self):
		self.state = 'done'

	@api.onchange('name')
	def onchange_emp(self):
		if self.name:
		   self.department_id = self.name.department_id

class Hr_employee_training(models.Model):
	_name = 'hr.employee.training'

	name = fields.Many2one('res.users', string='Responsible')
	course_id = fields.Many2one('hr.course', string="Course")
	specialist_id = fields.Many2one('hr.specialist', string="Specialist")
	hall_id = fields.Many2one('hr.hall', string="Hall")
	line_ids = fields.One2many('hr.employee.training.line','line_id', string="Hall")
	emp_line_ids = fields.Many2many('hr.employee', 'training_id', 'line_id', string="Course")
	# emp_line_ids = fields.One2many('hr.employee.training.line', 'emp_line_id',string="Employee")
	date = fields.Date(string="Date", default=fields.Date.today(), readonly=True)
	date_from = fields.Date(string='Date From')
	date_to = fields.Date(string='Date To')
	note = fields.Text(string="Note")
	description = fields.Text(string="Description")
	# custody_count = fields.Integer(compute='_custody_count', string='# Custody')
	state = fields.Selection(
		[('draft', 'To Submit'), ('submit', 'Submit'),
		 ('approve', 'Approve'), ('done', 'Done')], 'Status', default='draft')


	# count of all custody contracts
	# @api.multi
	# def _custody_count(self):
	# 	for each in self:
	# 		custody_ids = self.env['hr.custody'].search([('employee', '=', each.id)])
	# 		each.custody_count = len(custody_ids)

	# smart button action for returning the view of all custody contracts related to the current employee


	@api.one
	def submit_request(self):
		self.state = 'submit'

	@api.one
	def approve_request(self):
		self.state = 'approve'

	@api.one
	def done_request(self):
		self.state = 'done'

class Hr_employee_training_line(models.Model):
	_name = 'hr.employee.training.line'

	name = fields.Char('Name Course')
	line_id = fields.Many2one('hr.employee.training', string="Training")
	attach = fields.Binary("Attachment")





# class Hr_employee_training_line(models.Model):
#     _name = 'hr.employee.training.line'
#
#     employee_id = fields.Many2one('hr.employee', string="Employee")
#     emp_line_id = fields.Many2one('hr.employee.training', string="Employee")


class Hr_course(models.Model):
	_name = 'hr.course'
	name = fields.Char('Name')

class Hr_specialist(models.Model):
	_name = 'hr.specialist'
	name = fields.Char('Name')

class Hr_Hall(models.Model):
	_name = 'hr.hall'
	name = fields.Char('Name')

class HrDestination(models.Model):
	_name = 'hr.destination'
	name = fields.Char('Name')

class HrLetterExternal(models.Model):
	_name = 'hr.letter.external'



	@api.model
	def create(self, vals):
		res = super(HrLetterExternal, self).create(vals)
		for x in res:
		# if vals.get('name', 'New') == 'New':
			x.name =  x.letter_type_id.name + self.env['ir.sequence'].next_by_code('hr.letter.external') or '/'
		return res

	def _default_employee(self):
		return self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

	name = fields.Char('Serial No', readonly=True)
	date = fields.Date('Date Order', default=fields.Date.today(), readonly=True)
	destination_id = fields.Many2one('hr.destination','Sent To')
	# type_letter = fields.Char('Type Letter')
	subject_id = fields.Many2one('is.subject','Subject')
	is_department_id = fields.Many2one('is.letter.department','Department')
	letter_type_id = fields.Many2one('is.letter.type','Type Letter')
	note = fields.Html('Note')
	employee_id = fields.Many2one('hr.employee','Employee', default=_default_employee, readonly=True)
	job_id = fields.Many2one('hr.job','Job Position', related="employee_id.job_id", readonly=True)
	state = fields.Selection(
		[('draft', 'To Submit'), ('submit', 'Submit'),
		 ('approve', 'Approve'), ('done', 'Done')], 'Status', default='draft')



	@api.one
	def submit_request(self):
		self.state = 'submit'


	@api.one
	def done_request(self):
		self.state = 'done'

class IsLetterType(models.Model):
	_name = 'is.letter.type'

	name = fields.Char('Name')

class IsLetterDepartment(models.Model):
	_name = 'is.letter.department'

	name = fields.Char('Name')

class IsSubject(models.Model):
	_name = 'is.subject'

	name = fields.Char('Name')

class HrLetterInternal(models.Model):
	_name = 'hr.letter.internal'



	@api.model
	def create(self, vals):
		if vals.get('name', 'New') == 'New':
			# obj = vals['type_letter']
			vals['name'] = self.env['ir.sequence'].next_by_code('hr.letter.internal') or '/'
		return super(HrLetterInternal, self).create(vals)

	def _default_employee(self):
		return self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

	name = fields.Char('Serial No', readonly=True)
	type_letter = fields.Char('Type Letter')
	date_order = fields.Date(string="Date Request", default=fields.Date.today(), readonly=True)
	date_execute = fields.Date('Date Execute')
	destination_id = fields.Many2one('hr.destination','Sent To')
	# type_letter = fields.Selection(
	# 	[('Internal', 'Internal'), ('External', 'External'),
	# 	 ], 'Type Letter', default='Internal')
	subject_id = fields.Many2one('is.subject','Subject')
	subject_sub= fields.Char('Sub Subject')
	note = fields.Html('Note')
	date = fields.Date('Date Execution')
	hr_emp_ids = fields.Many2many('hr.employee', 'hr_emp_id', 'letter_id', string="Employee")
	employee_id = fields.Many2one('hr.employee','Employee', default=_default_employee, readonly=True)
	job_id = fields.Many2one('hr.job','Job Position', related="employee_id.job_id", readonly=True)
	state = fields.Selection(
		[('draft', 'To Submit'), ('submit', 'Submit'),
		 ('approve', 'Approve'), ('done', 'Done')], 'Status', default='draft')



	@api.one
	def submit_request(self):
		self.state = 'submit'


	@api.one
	def done_request(self):
		self.state = 'done'
