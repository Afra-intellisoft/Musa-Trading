from odoo import api, fields, models
from odoo import tools, _
from odoo.exceptions import ValidationError, AccessError
from datetime import datetime
import calendar
from odoo.exceptions import UserError


class hr_payslip(models.Model):
	_name = "hr.payslip"
	_inherit = "hr.payslip"

	@api.depends('employee_id')
	def get_short_loan(self):
		for x in self:
			if x.employee_id:
				loan_ids = x.env['hr.loan.line'].search(
					[('loan_id.employee_id', '=', x.employee_id.id), ('paid', '=', False), ('stopped', '=', False),
					 ('paid_date', '>=', x.date_from),
					 ('paid_date', '<=', x.date_to)])
				loan = 0.0
				for loan_id in loan_ids:
					if loan_id.loan_id.state == 'done':
						loan += loan_id.paid_amount
				x.short_loan = loan

	@api.depends('employee_id')

	def get_long_loan(self):
		for x in self:
			if x.employee_id:
				amount = 0.00
				loan_ids = x.env['hr.monthly'].search(
					[('employee_id', '=', x.employee_id.id), ('state', '=', 'done'), ('date', '>=', x.date_from),
					 ('date', '<=', x.date_to)])
				for loan in loan_ids:
					amount += loan.loan_amount
				x.long_loan = amount

	@api.depends('employee_id')
	def get_waning(self):
		for x in self:
			if x.employee_id:
				amount = 0.00
				warning_ids = x.env['hr.warnings'].search(
					[('employee_id', '=', x.employee_id.id), ('state', '=', 'penalty_approval'),
					 ('warning_date', '>=', x.date_from),
					 ('warning_date', '<=', x.date_to)])
				for obj in warning_ids:
					amount += obj.deduct_amount
				x.warning = amount

	@api.depends('employee_id')
	def get_over(self):
		for x in self:
			if x.employee_id:
				amount = 0.00
				overtime_ids = x.env['hr.overtime'].search(
					[('name', '=', x.employee_id.id), ('state', '=', 'done'),
					 ('overtime_date', '>=', x.date_from),
					 ('overtime_date', '<=', x.date_to)])
				total_overtime = 0.0
				working_sum_hours = 0.0
				holiday_sum_hours = 0.0
				overtime_holiday = 0.0
				overtime_working = 0.0
				for overtime in overtime_ids:
					employee =overtime.name.id
					employee_basic_salary = x.employee_id.contract_id.total_salary
					employee_salary_hour = employee_basic_salary / 240
					if overtime.is_working_day:
						working_sum_hours += overtime.hour
						overtime_working = working_sum_hours * employee_salary_hour * 1.5
					if overtime.is_holiday:
						holiday_sum_hours += overtime.hour
						overtime_holiday = holiday_sum_hours * employee_salary_hour * 2
					total_overtime = overtime_working + overtime_holiday
				x.over = total_overtime

	@api.multi
	def action_payslip_done(self):
		res = super(hr_payslip, self).action_payslip_done()
		self.compute_sheet()
		for rec in self:
			for loan in self.env['hr.loan.line'].search(
					[('paid_date', '>=', rec.date_from), ('paid_date', '<=', rec.date_to),
					 ('loan_id.employee_id', '=', rec.employee_id.id)]):
				loan.paid = True
		return res


	short_loan = fields.Float("Short Loan", readonly=True, compute='get_short_loan', store=True)
	# long_loan = fields.Float("Long Loan", readonly=True, compute='get_long_loan', store=True)
	warning = fields.Float("Warning", readonly=True, compute='get_waning', store=True)
	over = fields.Float("Over", readonly=True, compute='get_over', store=True)


class HrPayslipEmployees(models.TransientModel):
	_inherit = 'hr.payslip.employees'

	@api.multi
	def compute_sheet(self):
		payslips = self.env['hr.payslip']
		[data] = self.read()
		active_id = self.env.context.get('active_id')
		if active_id:
			[run_data] = self.env['hr.payslip.run'].browse(active_id).read(['date_start', 'date_end', 'credit_note'])
			journal_id = self.env['hr.payslip.run'].browse(self.env.context.get('active_id')).journal_id.id
		from_date = run_data.get('date_start')
		to_date = run_data.get('date_end')
		if not data['employee_ids']:
			raise UserError(_("You must select employee(s) to generate payslip(s)."))
		for employee in self.env['hr.employee'].browse(data['employee_ids']):
			slip_data = self.env['hr.payslip'].onchange_employee_id(from_date, to_date, employee.id, contract_id=False)
			contract_id = self.env['hr.contract'].search([('id', '=', slip_data['value'].get('contract_id'))])
			if contract_id:
				if contract_id.date_start > from_date:
					payslip_from = contract_id.date_start
				else:
					payslip_from = from_date
				if contract_id.date_end:
					if contract_id.date_end < to_date:
						payslip_to = contract_id.date_end
					else:
						payslip_to = to_date
				else:
					payslip_to = to_date

				res = {
					'employee_id': employee.id,
					'name': slip_data['value'].get('name'),
					'struct_id': slip_data['value'].get('struct_id'),
					'contract_id': slip_data['value'].get('contract_id'),
					'payslip_run_id': active_id,
					'input_line_ids': [(0, 0, x) for x in slip_data['value'].get('input_line_ids')],
					'worked_days_line_ids': [(0, 0, x) for x in slip_data['value'].get('worked_days_line_ids')],
					'date_from': payslip_from,
					'date_to': payslip_to,
					'credit_note': run_data.get('credit_note'),
					'journal_id': journal_id,
				}
			else:
				res = {
					'employee_id': employee.id,
					'name': slip_data['value'].get('name'),
					'struct_id': slip_data['value'].get('struct_id'),
					'contract_id': slip_data['value'].get('contract_id'),
					'payslip_run_id': active_id,
					'input_line_ids': [(0, 0, x) for x in slip_data['value'].get('input_line_ids')],
					'worked_days_line_ids': [(0, 0, x) for x in slip_data['value'].get('worked_days_line_ids')],
					'date_from': from_date,
					'date_to': to_date,
					'credit_note': run_data.get('credit_note'),
					'company_id': employee.company_id.id,
				}
			payslips += self.env['hr.payslip'].create(res)
		payslips.compute_sheet()
		return {'type': 'ir.actions.act_window_close'}
