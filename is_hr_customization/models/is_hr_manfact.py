# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import AccessError, UserError
from odoo.tools import float_compare


class is_hr_count_manufacturing(models.Model):
	_name = 'is.hr.count.manufacturing'

	name = fields.Char('Name')
	date = fields.Date('Date', default=fields.Date.today(), readonly=True)
	date_order = fields.Date('Date')
	manufacturing_ids = fields.One2many('is.hr.count.manufacturing.line', 'manufacturing_id', 'Line')
	manufacturing_boy_ids = fields.One2many('is.hr.count.manufacturing.line.boy', 'boy_id', 'Line')
	state = fields.Selection([('draft', 'Draft'), ('in_progress', 'In Progress'), ('finance_approval', 'Finance Approval'), ('auditor', 'Auditor')],
							 string='State', default='draft')
	account_id = fields.Many2one('account.account', string="Debit Account")
	account_credit = fields.Many2one('account.account', string="Credit Account")
	journal_id = fields.Many2one('account.journal', string="Journal")
	move_id = fields.Many2one('account.move', string="Journal Entry", readonly=True)

	@api.one
	def action_auditor(self):
		for x in self:
			x.state = 'auditor'
	@api.one
	def finance_approve(self):
		precision = self.env['decimal.precision'].precision_get('Payroll')
		self.env.cr.execute("""select current_date;""")
		xt = self.env.cr.fetchall()
		self.comment_date4 = xt[0][0]
		# if not self.employee_account or not self.loan_account or not self.journal_id:
		# 	raise Warning(_("You must enter employee account & Loan account and journal to approve "))
		# if not self.loan_line_ids:
		# 	raise Warning(_('You must compute Loan Request before Approved'))
		can_close = False
		# loan_obj = self.env['hr.loan']
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
			# company_currency = loan.employee_id.company_id.currency_id.id
			# current_currency = self.env.user.company_id.currency_id.id
			for obj in loan.manufacturing_ids:
				amount = obj.total
				loan_name = obj.worker_name.name
				reference = obj.worker_name.name
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
					'account_id': loan.account_id.id,
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
					'account_id': loan.account_credit.id,
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

				# company_currency = loan.employee_id.company_id.currency_id.id
				# current_currency = self.env.user.company_id.currency_id.id
			for obj in loan.manufacturing_boy_ids:
				price_daliy = obj.price_daily
				loan_name = obj.worker_name.name
				reference = obj.worker_name.name
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
					'account_id': loan.account_id.id,
					'journal_id': journal_id,
					'date': loan_request_date,
					'debit': price_daliy > 0.0 and price_daliy or 0.0,
					'credit': price_daliy < 0.0 and -price_daliy or 0.0,
					'analytic_account_id': False,
					'tax_line_id': 0.0,
				})
				line_ids.append(debit_line)
				debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']
				credit_line = (0, 0, {
					'name': loan_name,
					'partner_id': False,
					'account_id': loan.account_credit.id,
					'journal_id': journal_id,
					'date': loan_request_date,
					'debit': price_daliy < 0.0 and -price_daliy or 0.0,
					'credit': price_daliy > 0.0 and price_daliy or 0.0,
					'analytic_account_id': False,
					'tax_line_id': 0.0,
				})
				line_ids.append(credit_line)
				credit_sum += credit_line[2]['credit'] - credit_line[2]['debit']
				if float_compare(credit_sum, debit_sum, precision_digits=precision) == -1:
					acc_journal_credit = loan.journal_id.default_credit_account_id.id
					if not acc_journal_credit:
						raise UserError(
							_('The Expense Journal "%s" has not properly configured the Credit Account!') % (
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
						raise UserError(
							_('The Expense Journal "%s" has not properly configured the Debit Account!') % (
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
			self.state = 'finance_approval'


class is_hr_count_manufacturing_line(models.Model):
	_name = 'is.hr.count.manufacturing.line'

	name = fields.Char('Name')
	worker_name = fields.Many2one('mrp.worker', 'Worker')
	manufacturing_id = fields.Many2one('is.hr.count.manufacturing', 'Worker')
	total = fields.Float('Total')


class is_hr_count_manufacturing_line_boy(models.Model):
	_name = 'is.hr.count.manufacturing.line.boy'

	name = fields.Char('Name')
	worker_name = fields.Many2one('mrp.worker', 'Worker')
	boy_id = fields.Many2one('is.hr.count.manufacturing', 'Worker')
	price_daily = fields.Float('Price Daily')



class MrpWorker(models.Model):
	_name = 'mrp.worker'
	name = fields.Char('Name')
	serial_no = fields.Char('Serial No', readonly=True)

	@api.model
	def create(self, values):
		values['serial_no'] = self.env['ir.sequence'].get('mrp.worker') or ''
		res = super(MrpWorker, self).create(values)
		return res
