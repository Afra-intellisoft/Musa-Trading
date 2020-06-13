#!/usr/bin/env python
# -*- coding: utf-8 -*-
##############################################################################
#    Description: Custody Clearance                                          #
#    Author: IntelliSoft Software                                            #
#    Date: Aug 2015 -  Till Now                                              #
##############################################################################

from odoo import models, fields, api, _
from datetime import datetime
from odoo.tools import amount_to_text
from amount_to_ar import amount_to_text_ar
from odoo.exceptions import except_orm, Warning, ValidationError, UserError
import sys

reload(sys)
sys.setdefaultencoding('utf-8')



################################
# add custody clearance approval
class custody_clearance(models.Model):
	_name = 'custody.clearance'
	_description = 'A model for tracking custody clearance.'
	# _inherit = ['mail.thread', 'ir.needaction_mixin']

	clearance_no = fields.Char('Clearance No.', help='Auto-generated Clearance No. for custody clearances')
	name = fields.Char('Details', compute='_get_description', store=True, readonly=True)
	cc_date = fields.Date('Date', default=datetime.today())
	requester = fields.Char('Requester', required=True, default=lambda self: self.env.user.name)
	clearance_amount = fields.Float('Requested Amount', required=True)
	clearance_currency = fields.Many2one('res.currency', 'Currency',
										 default=lambda self: self.env.user.company_id.currency_id)
	difference_amount = fields.Float('Difference Amount', readonly=True)
	custody_amount = fields.Float('Custody Amount', readonly=True)
	clearance_amount_words = fields.Char(string='Amount in Words', readonly=True, default=False, copy=False,
										 compute='_compute_text', translate=True)
	reason = fields.Char('Reason')
	state = fields.Selection([('draft', 'Draft'), ('mn_app', 'Manager Approval'), ('fm_app', 'Financial Approval'),
							  ('au_app', 'Reviewer Approval'), ('reject', 'Rejected'),
							  ('validate', 'Validated')],
							 string='Custody Clearance Status', default='draft')
	journal_id = fields.Many2one('account.journal', 'Bank/Cash Journal',
								 help='Payment journal.',
								 domain=[('type', 'in', ['bank', 'cash'])])
	clearance_journal_id = fields.Many2one('account.journal', 'Clearance Journal', help='Clearance Journal')
	cr_account = fields.Many2one('account.account', string="Credit Account")
	move_id = fields.Many2one('account.move', 'Clearance Journal Entry', readonly=True)
	move2_id = fields.Many2one('account.move', 'Payment/ Receipt Journal Entry', readonly=True)
	mn_remarks = fields.Text('Manager Remarks')
	auditor_remarks = fields.Text('Auditor Remarks')
	fm_remarks = fields.Text('Finance Man. Remarks')
	view_remarks = fields.Text('View Remarks', readonly=True, compute='_get_remarks', store=True)
	user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user)
	manager_id = fields.Many2one('res.users', string='Manager')
	mn_app_id = fields.Many2one('res.users', string="Manager Approval By")
	fm_app_id = fields.Many2one('res.users', string="Financial Approval By")
	au_app_id = fields.Many2one('res.users', string="Auditor Approval By")
	at_app_id = fields.Many2one('res.users', string="Validated By")
	is_custody = fields.Boolean('Is Custody?')
	# add company_id to allow this module to support multi-company
	company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.user.company_id)
	# link with finance approval
	finance_approval_id = fields.Many2one('finance.approval', 'Finance Approval No.' ,domain=[('is_custody', '=',True)])
	# clearance lines
	custody_clearance_line_ids = fields.One2many('custody.clearance.line', 'custody_clearance_id',
												 string='Clearance Details')
	# payment difference finacial approval
	payment_finance_approval_id = fields.Many2one('finance.approval', 'Payment Finance Approval No.', readonly=True)
	emp = fields.Many2one('hr.employee', 'employee', compute='compute_manager', store=True)

	@api.onchange('finance_approval_id')
	def onchange_finance_approval_id(self):
		if self.finance_approval_id:
			self.clearance_currency = self.finance_approval_id.request_currency.id
			# print self.approval_id.request_amount
			self.clearance_amount = self.finance_approval_id.request_amount
			self.is_custody = self.finance_approval_id.is_custody
	@api.one
	def compute_manager(self):

		employee_id = self.env['hr.employee'].search([('user_id', '=', self.user_id.id)], limit=1)
		employee_id.name
		# for rec in employee_id:
		self.emp = employee_id

	# Generate name of custody automatically
	@api.one
	@api.depends('clearance_no', 'requester', 'clearance_amount')
	def _get_description(self):
		self.name = (self.clearance_no and ("Clearance No: " + str(self.clearance_no)) or " ") + "/" + (
			self.requester and ("Requester: " + self.requester) or " ") + "/" \
					+ (self.clearance_amount and ("Clearance Amount: " + str(self.clearance_amount)) or " ") + "/" + (
						self.reason and ("Reason: " + self.reason) or " ")

	# Return clearance amount in words
	@api.one
	@api.depends('clearance_amount', 'clearance_currency')
	def _compute_text(self):
		self.clearance_amount_words = amount_to_text_ar(self.clearance_amount, self.clearance_currency.narration_ar_un,
														self.clearance_currency.narration_ar_cn)

	# Generate remarks
	@api.one
	@api.depends('mn_remarks', 'auditor_remarks', 'fm_remarks')
	def _get_remarks(self):
		self.view_remarks = (self.mn_remarks and ("Manager Remarks: " + str(self.mn_remarks)) or " ") + "\n\n" + (
			self.fm_remarks and ("Financial Man. Remarks: " + self.fm_remarks) or " ") + "\n\n" + (
								self.auditor_remarks and ("Auditor Remarks: " + str(self.auditor_remarks)) or " ")

	# overriding default get
	@api.model
	def default_get(self, fields):
		res = super(custody_clearance, self).default_get(fields)
		# get manager user id
		manager = self.env['res.users'].search([('id', '=', self.env.user.id)], limit=1).approval_manager.id
		if manager:
			res.update({'manager_id': manager})
		return res

	# overriding create to save number with commit
	@api.model
	def create(self, vals):
		res = super(custody_clearance, self).create(vals)
		# get custody clearance sequence no.
		next_seq = self.env['ir.sequence'].get('custody.clearance.sequence')
		res.update({'clearance_no': next_seq})
		return res

	# Permit deletion of validated record
	@api.multi
	def unlink(self):
		for approval in self:
			if approval.state not in ['draft']:
				raise UserError(_("You are not allowed to delete non draft record!"))
		return super(custody_clearance, self).unlink()

	# manager approval
	@api.one
	def manager_approval(self):
		self.state = 'mn_app'
		self.mn_app_id = self.env.user.id

		# Update footer message
		message_obj = self.env['mail.message']
		message = _("State Changed  Confirm -> <em>%s</em>.") % (self.state)
		# msg_id = self.message_post(body=message)

	# financial manager approval
	@api.one
	def fm_approval(self):
		self.state = 'fm_app'
		self.fm_app_id = self.env.user.id

		# Update footer message
		message_obj = self.env['mail.message']
		message = _("State Changed  Confirm -> <em>%s</em>.") % (self.state)
		# msg_id = self.message_post(body=message)

	# auditor approval
	@api.one
	def auditor_approval(self):
		self.state = 'au_app'
		self.au_app_id = self.env.user.id

		# Update footer message
		message_obj = self.env['mail.message']
		message = _("State Changed  Confirm -> <em>%s</em>.") % (self.state)
		# msg_id = self.message_post(body=message)

	# reject finance approval
	@api.one
	def reject(self):
		self.state = 'reject'

		# Update footer message
		message_obj = self.env['mail.message']
		message = _("State Changed  Confirm -> <em>%s</em>.") % (self.state)
		# msg_id = self.message_post(body=message)

	# validate, i.e. post to account moves
	@api.model
	def get_currency(self, line=None, total=None):
		if total:
			return total
		if self.clearance_currency != self.env.user.company_id.currency_id:
			return line.amount / self.clearance_currency.rate

		else:
			return line.amount

	# validate and check difference
	@api.one
	def validate(self):
		# if not self.clearance_journal_id:
		# 	raise Warning(_("Clearance journal must be selected!"))
		if not self.journal_id:
			raise Warning(_("Payment journal must be selected!"))
		if not self.cr_account:
			raise Warning(_("Credit account must be selected!"))

		#################
		# clearance part#
		#################
		# account move entry
		db_total = 0
		entries = []
		for line in self.custody_clearance_line_ids:
			if not line.exp_account:
				raise ValidationError(_("Please select account!"))
			debit_val = {
				'move_id': self.move_id.id,
				'name': line.name,
				'account_id': line.exp_account.id,
				'debit': self.get_currency(line),
				'analytic_account_id': line.analytic_account.id,
				'currency_id': (self.clearance_currency != self.env.user.company_id.currency_id)
							   and self.clearance_currency.id or None,
				'amount_currency': (self.clearance_currency != self.env.user.company_id.currency_id) and line.amount
								   or None,
				'company_id': self.company_id.id,
			}
			entries.append((0, 0, debit_val))
			db_total += line.amount
		self.custody_amount = db_total


		# create credit entry which is total of debit
		credit_val = {
			'move_id': self.move_id.id,
			'name': line.name,
			'account_id': self.cr_account.id,
			'credit': self.get_currency(total=db_total),
			'currency_id': (self.clearance_currency != self.env.user.company_id.currency_id)
						   and self.clearance_currency.id or None,
			'amount_currency': (self.clearance_currency != self.env.user.company_id.currency_id) and -(db_total)
							   or None,
			'company_id': self.company_id.id,
		}
		entries.append((0, 0, credit_val))

		vals = {
			'journal_id': self.journal_id.id,
			'date': datetime.today(),
			'ref': self.clearance_no,
			'company_id': self.company_id.id,
			'line_ids': entries,
		}

		self.move_id = self.env['account.move'].create(vals)

		##################
		# difference part#
		##################
		# get difference
		self.difference_amount = self.clearance_amount - db_total
		print(self.custody_amount,'custody_amount')
		print(self.difference_amount,'difference_amount')
		if self.difference_amount == 0:
			# Change state if all went well!
			self.state = 'validate'
			self.at_app_id = self.env.user.id
			# Update footer message
			message_obj = self.env['mail.message']
			message = _("State Changed  Confirm -> <em>%s</em>.") % (self.state)
			# msg_id = self.message_post(body=message)
		# difference greater
		elif self.difference_amount > 0:
			# account move entry
			if self.clearance_currency == self.env.user.company_id.currency_id:
				temp_move_line_db = {
					'move_id': self.move2_id.id,
					'name': self.name + ": Receipt of difference",
					'account_id': self.journal_id.default_debit_account_id.id,
					'debit': self.difference_amount,
					'company_id': self.company_id.id,
				}
				# add credit entry
				temp_move_line_cr = {'move_id': self.move2_id.id,
									 'name': self.name + ": Receipt of difference",
									 'account_id': self.cr_account.id,
									 'credit': self.difference_amount,
									 'company_id': self.company_id.id,
									 }
				account_move_vals = {'journal_id': self.journal_id.id,
									 'date': datetime.today(),
									 'ref': self.clearance_no,
									 'CS': self.requester,
									 'company_id': self.company_id.id,
									 'line_ids': [(0, 0, temp_move_line_db), (0, 0, temp_move_line_cr)]
									 }
				self.move2_id = self.env['account.move'].create(account_move_vals)

				# Change state if all went well!
				self.state = 'validate'
				self.at_app_id = self.env.user.id
				# Update footer message
				message_obj = self.env['mail.message']
				message = _("State Changed  Confirm -> <em>%s</em>.") % (self.state)
				# msg_id = self.message_post(body=message)
			elif self.clearance_currency != self.env.user.company_id.currency_id:
				temp_move_line_db = {'move_id': self.move2_id.id,
									 'name': self.name + ": Receipt of difference",
									 'account_id': self.journal_id.default_debit_account_id.id,
									 'currency_id': self.clearance_currency.id,
									 'amount_currency': self.difference_amount,
									 'debit': self.difference_amount / self.clearance_currency.rate,
									 'company_id': self.company_id.id,
									 }
				# add credit entry
				temp_move_line_cr = {'move_id': self.move2_id.id,
									 'name': self.name + ": Receipt of difference",
									 'account_id': self.cr_account.id,
									 'currency_id': self.clearance_currency.id,
									 'amount_currency': -self.difference_amount,
									 'credit': self.difference_amount / self.clearance_currency.rate,
									 'company_id': self.company_id.id,
									 }
				account_move_vals = {'journal_id': self.journal_id.id,
									 'date': datetime.today(),
									 'ref': self.clearance_no,
									 'CS': self.requester,
									 'company_id': self.company_id.id,
									 'line_ids': [(0, 0, temp_move_line_db), (0, 0, temp_move_line_cr)]
									 }

				self.move2_id = self.env['account.move'].create(account_move_vals)
				# Change state if all went well!
				self.state = 'validate'
				self.at_app_id = self.env.user.id
				# Update footer message
				message_obj = self.env['mail.message']
				message = _("State Changed  Confirm -> <em>%s</em>.") % (self.state)
				# msg_id = self.message_post(body=message)
			else:
				raise Warning(_("An issue was faced when validating difference!"))
		# difference less
		elif self.difference_amount < 0:
			# account move entry
			if self.clearance_currency == self.env.user.company_id.currency_id:
				# temp_move_line_db = {'move_id': self.move2_id.id,
				#                      'name': self.name + ": Payment of difference",
				#                      'account_id': self.cr_account.id,
				#                      'debit': abs(self.difference_amount),
				#                      'company_id': self.company_id.id,
				#                      }
				# # add credit entry
				# temp_move_line_cr = {'move_id': self.move2_id.id,
				#                      'name': self.name + ": Payment of difference",
				#                      'account_id': self.journal_id.default_debit_account_id.id,
				#                      'credit': abs(self.difference_amount),
				#                      'company_id': self.company_id.id,
				#                      }
				#
				# account_move_vals = {'journal_id': self.journal_id.id,
				#                      'date': datetime.today(),
				#                      'ref': self.clearance_no,
				#                      'company_id': self.company_id.id,
				#                      'line_ids': [(0, 0, temp_move_line_db), (0, 0, temp_move_line_cr)]
				#                      }
				# self.move2_id = self.env['account.move'].create(account_move_vals)
				# Musa required that payment of difference goes through financial approval
				financial_approval_vals = {'requester': self.requester,
										   'amount_ids': [(0, 0, {'amount': abs(self.difference_amount),
																  'reason': 'Payment of difference. دفع فرق تصفية'})],

										   }
				self.payment_finance_approval_id = self.env['finance.approval'].create(financial_approval_vals)
				# Change state if all went well!
				self.state = 'validate'
				self.at_app_id = self.env.user.id
				# Update footer message
				message_obj = self.env['mail.message']
				message = _("State Changed  Confirm -> <em>%s</em>.") % (self.state)
				# msg_id = self.message_post(body=message)
			elif self.clearance_currency != self.env.user.company_id.currency_id:
				# temp_move_line_db = {'move_id': self.move2_id.id,
				#                      'name': self.name + ": Payment of difference",
				#                      'account_id': self.cr_account.id,
				#                      'currency_id': self.clearance_currency.id,
				#                      'amount_currency': abs(self.difference_amount),
				#                      'debit': abs(self.difference_amount) / self.clearance_currency.rate,
				#                      'company_id': self.company_id.id,
				#                      }
				# # add credit entry
				# temp_move_line_cr = {'move_id': self.move2_id.id,
				#                      'name': self.name + ": Payment of difference",
				#                      'account_id': self.journal_id.default_debit_account_id.id,
				#                      'currency_id': self.clearance_currency.id,
				#                      'amount_currency': -(abs(self.difference_amount)),
				#                      'credit': abs(self.difference_amount) / self.clearance_currency.rate,
				#                      'company_id': self.company_id.id,
				#                      }
				# account_move_vals = {'journal_id': self.journal_id.id,
				#                      'date': datetime.today(),
				#                      'ref': self.clearance_no,
				#                      'company_id': self.company_id.id,
				#                      'line_ids': [(0, 0, temp_move_line_db), (0, 0, temp_move_line_cr)]
				#                      }
				# self.move2_id = self.env['account.move'].create(account_move_vals)
				# Musa required that payment of difference goes through financial approval
				financial_approval_vals = {'requester': self.requester,
										   'amount_ids': [(0, 0, {'amount': abs(self.difference_amount),
																  'reason': 'Payment of difference. دفع فرق تصفية'})],

										   # 'reason': 'Payment of difference. دفع فرق تصفية',
										   'request_currency': self.clearance_currency.id,
										   }
				self.payment_finance_approval_id = self.env['finance.approval'].create(financial_approval_vals)
				# Change state if all went well!
				self.state = 'validate'

				# Update footer message
				message_obj = self.env['mail.message']
				message = _("State Changed  Confirm -> <em>%s</em>.") % (self.state)
				# msg_id = self.message_post(body=message)
		else:
			raise Warning(_("An issue was faced when validating!"))
		# Update footer message
		message_obj = self.env['mail.message']
		message = _("State Changed  Confirm -> <em>%s</em>.") % (self.state)
		# msg_id = self.message_post(body=message)

	@api.one
	def set_to_draft(self):
		self.state = 'draft'
		self.mn_app_id = None
		self.fm_app_id = None
		self.au_app_id = None
		self.at_app_id = None

		# Update footer message
		message_obj = self.env['mail.message']
		message = _("State Changed  Confirm -> <em>%s</em>.") % (self.state)
		# msg_id = self.message_post(body=message)

	# include a badge
	@api.model
	def _needaction_domain_get(self):
		isma = self.user_id.has_group('is_accounting_approval_10.manager_access_group')
		isau = self.user_id.has_group('is_accounting_approval_10.auditor_access_group')
		isfm = self.user_id.has_group('account.group_account_manager')

		sau = isau and 'fm_app' or None
		sfm = isfm and 'mn_app' or None
		sma = isma and 'draft' or None

		return [('state', 'in', (sau, sfm, sma))]


######################################################
# Custody clearance line model
class custody_clearance_line(models.Model):
	_name = 'custody.clearance.line'
	_description = 'Custody clearance details.'

	custody_clearance_id = fields.Many2one('custody.clearance', string='Custody Clearance', ondelete="cascade")
	name = fields.Char('Narration', required=True)
	amount = fields.Float('Amount', required=True)
	notes = fields.Char('Notes')
	exp_account = fields.Many2one('account.account', string="Expense or Debit Account")
	analytic_account = fields.Many2one('account.analytic.account', string='Analytic Account/Cost Center')
	company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.user.company_id)
