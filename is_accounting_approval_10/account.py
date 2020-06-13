#!/usr/bin/env python
# -*- coding: utf-8 -*-
##############################################################################
#    Description: Accounting Approval                                        #
#    Author: IntelliSoft Software                                            #
#    Date: Aug 2015 -  Till Now                                              #
##############################################################################


from odoo import models, fields, api, _
from datetime import datetime
from . import amount_to_ar
from odoo.exceptions import  Warning,ValidationError,_logger,UserError


##################################################################
# add financial approval
class finance_approval(models.Model):
    _name = 'finance.approval'
    _description = 'A model for tracking finance approvals.'
    _inherit = ['mail.thread']

    approval_no = fields.Char('Approval No.', help='Auto-generated Approval No. for finance approvals')
    name = fields.Char('Details', compute='_get_description', store=True, readonly=True)
    fa_date = fields.Date('Date', default=lambda self:fields.Date.today())
    requester = fields.Char('Requester', required=True, default=lambda self: self.env.user.name)
    request_amount = fields.Float('Requested Amount', required=True)
    request_currency = fields.Many2one('res.currency', 'Currency',
                                       default=lambda self: self.env.user.company_id.currency_id)
    request_amount_words = fields.Char(string='Amount in Words', readonly=True, default=False, copy=False,
                                       compute='_compute_text', translate=True)
    department_id = fields.Many2one('hr.department',string="Department")
    beneficiary = fields.Many2one('res.partner','no')
    reason = fields.Char('Reason')
    expense_item=fields.Char('Expense Item')
    state = fields.Selection([('draft', 'Draft'), ('to_approve', 'Financial Approval'),
                              ('gm_app', 'General Manager Approval'),('ready','Ready for Payment'), ('reject', 'Rejected'),
                              ('validate', 'Validated')],
                             string='Finance Approval Status', default='draft')
    exp_account = fields.Many2one('account.account', string="Expense or Debit Account")
    credit_account = fields.Many2one('account.account', string="Credit Account")
    payment_method = fields.Selection(
        selection=[('cash', 'Cash'), ('cheque', 'Cheque'), ('transfer', 'Transfer'),
                   ('trust', 'Trust'), ('other', 'Other')], string='Payment Method')
    journal_id = fields.Many2one('account.journal', 'Bank/Cash Journal',
                                 help='Payment journal.',
                                 domain=[('type', 'in', ['bank', 'cash'])])
    move_id = fields.Many2one('account.move', 'Journal Entry', readonly=True)
    mn_remarks = fields.Text('Manager Remarks')
    auditor_remarks = fields.Text('Reviewer Remarks')
    fm_remarks = fields.Text('Finance Man. Remarks')
    gm_remarks = fields.Text('General Man. Remarks')
    view_remarks = fields.Text('View Remarks', readonly=True, compute='_get_remarks', store=True)
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user)
    manager_id = fields.Many2one('res.users', string='Manager')
    partner_id = fields.Many2one('res.partner', string='Beneficiary')
    mn_app_id = fields.Many2one('res.users', string=" Approval By")
    au_app_id = fields.Many2one('res.users', string="Manager Approval By")
    fm_app_id = fields.Many2one('res.users', string="Reviewer Approval By")
    gm_app_id = fields.Many2one('res.users', string="Financial  Approval By")
    general_manager_id = fields.Many2one('res.users', string="GM Approval By")
    at_app_id = fields.Many2one('res.users', string="Validated By")
    # add company_id to allow this module to support multi-company
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.user.company_id)
    # adding analytic account
    analytic_account = fields.Many2one('account.analytic.account', string='Analytic Account/Cost Center')

    check_date = fields.Date('Check Date')
    Account_No = fields.Char('Account Number')
    bank_id = fields.Many2one(related='journal_id.bank_id')
    Check_no = fields.Char('Check Number')
    payment_method_name = fields.Many2one('account.payment.method',string="Payment Method")
    pa_name = fields.Char(related="payment_method_name.name")
    is_custody = fields.Boolean('Is Custody?')
    invoice_id = fields.Many2one('account.invoice', 'Invoice Ref')
    type = fields.Selection([('expense', 'Expense Request'), ('vendor_bill', 'Vendor Bill')],
                             string ='Type', default='expense', Required = True)

    # def button_reject(self):
    #     return {
    #
    #         'view_type': 'form',
    #         'view_mode': 'form',
    #         'res_model': 'reject',
    #         # 'views': [(resource_id, 'form')],
    #         'type': 'ir.actions.act_window',
    #         'target': 'new',
    #     }
    #     self.state = 'reject'

    # Generate name of approval automatically




    @api.one
    @api.depends('approval_no', 'requester', 'beneficiary')
    # @api.onchange('approval_no', 'requester', 'beneficiary')
    def _get_description(self):
        self.name = (self.approval_no and ("Approval No: " + str(self.approval_no)) or " ") + "/" + (
            self.requester and ("Requester: " + self.requester) or " ") + "/" \
                    + (self.beneficiary.name and ("Beneficiary: " + self.beneficiary.name) or " ") + "/" + (
                        self.reason and ("Reason: " + self.reason) or " ")

    # Return request amount in words
    @api.one
    @api.depends('request_amount', 'request_currency')
    def _compute_text(self):
        self.request_amount_words = amount_to_ar.amount_to_text_ar(self.request_amount,
                                                                   self.request_currency.narration_ar_un,
                                                                   self.request_currency.narration_ar_cn)

    # Generate name of approval automatically
    @api.one
    @api.depends('mn_remarks', 'auditor_remarks', 'fm_remarks', 'gm_remarks')
    # @api.onchange('mn_remarks', 'auditor_remarks', 'fm_remarks', 'gm_remarks')
    def _get_remarks(self):
        self.view_remarks = (self.mn_remarks and ("Manager Remarks: " + str(self.mn_remarks)) or " ") + "\n\n" + (
            self.auditor_remarks and ("Account Manager Remarks: " + str(self.auditor_remarks)) or " ") + "\n\n" + (
                                self.fm_remarks and ("Financial Man. Remarks: " + self.fm_remarks) or " ") + "\n\n" + (
                                self.gm_remarks and ("General Man. Remarks: " + self.gm_remarks) or " ")

    # overriding default get
    @api.model
    def default_get(self, fields):
        res = super(finance_approval, self).default_get(fields)
        # get manager user id
        manager = self.env['res.users'].search([('id', '=', self.env.user.id)], limit=1).approval_manager.id
        if manager:
            res.update({'manager_id': manager})
        return res

    # validation
    @api.constrains('request_amount')
    def request_amount_validation(self):
        if self.request_amount <= 0:
            raise Warning(_("Request Amount Must be greater than zero!"))

    @api.model
    def create(self, vals):
        print('you know im from you')
        res = super(finance_approval, self).create(vals)
        print('no messages no anything')

        # get finance approval sequence no.
        next_seq = self.env['ir.sequence'].get('finance.approval.sequence')
        res.update({'approval_no': next_seq})
        return res

    # added to allow for financial manager approval
    @api.one
    def to_approve(self):

        self.state = 'to_approve'
        return True

    # financial approval
    @api.one
    def financial_approval(self):
        # get finance manager group
        fm_group_id = self.env['res.groups'].sudo().search([('name', 'like', 'General Manager')], limit=1).id

        # first of all get all finance managers / advisors
        self.env.cr.execute('''SELECT uid FROM res_groups_users_rel WHERE gid = %s order by uid''' % (fm_group_id))



        # change state
        self.state = 'gm_app'
        self.fm_app_id = self.env.user.id

        # Update footer message
        message_obj = self.env['mail.message']
        message = _("State Changed  Confirm -> <em>%s</em>.") % (self.state)
        msg_id = self.message_post(body=message)

    # financial manager approval
    @api.one
    def gm_approval(self):


        # change state
        self.state = 'ready'
        self.gm_app_id = self.env.user.id

        # Update footer message
        message_obj = self.env['mail.message']
        message = _("State Changed  Confirm -> <em>%s</em>.") % (self.state)
        msg_id = self.message_post(body=message)

    def cancel_button(self):
        self.move_id.button_cancel()
        self.move_id.unlink()
        self.state = 'draft'


    # reject finance approval
    @api.one
    def reject(self):

        self.state = 'reject'
        # Update footer message
        message_obj = self.env['mail.message']
        message = _("State Changed  Confirm -> <em>%s</em>.") % (self.state)
        msg_id = self.message_post(body=message)

    # validate, i.e. post to account moves
    def move_check_followups(self):
        debit_vals = {
            'name': self.name,
            'partner_id': self.partner_id.id,
            'account_id': self.exp_account.id,
            'debit': self.request_amount,
            'analytic_account_id': self.analytic_account.id,
            'company_id': self.company_id.id,
        }

        credit_vals = {
            'name': self.name,
            'partner_id': self.partner_id.id,
            'account_id': self.credit_account.id,
            'credit': self.request_amount,
            'company_id': self.company_id.id,
        }
        vals = {
            'journal_id': self.journal_id.id,
            'credit_account': self.credit_account.id,
            'date': datetime.today(),
            'ref': self.approval_no,
            'CS': self.beneficiary,
            'company_id': self.company_id.id,
            'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]
        }
        return vals

    def move_without_check(self):
        debit_vals = {
            'name': self.name,
            'partner_id': self.partner_id.id,
            'account_id': self.exp_account.id,
            'debit': self.request_amount,
            'analytic_account_id': self.analytic_account.id,
            'company_id': self.company_id.id,
        }
        credit_vals = {
            'name': self.name,
            'partner_id': self.partner_id.id,
            'account_id': self.journal_id.default_credit_account_id.id,
            'credit': self.request_amount,
            'company_id': self.company_id.id,
        }
        vals = {
            'journal_id': self.journal_id.id,
            'date': datetime.today(),
            'ref': self.approval_no,
            'CS': self.beneficiary,
            'company_id': self.company_id.id,
            'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]
        }
        return vals

    @api.one
    def validate(self):
        if self.type == 'expense':
            dictionary = {
                'name': self.reason,
                'account_holder': self.partner_id.id,
                'Date': self.check_date,
                'approval_id': self.id,
                'bank_id': self.bank_id.id,
                'beneficiary_id': self.partner_id.name,
                'journal_id': self.journal_id.id,
                'amount': self.request_amount,
                'currency_id': self.request_currency.id,
                'check_no': self.Check_no,
                'approval_check': True,
                'state': 'out_standing',
                'type': 'outbound',
                'communication': self.approval_no,
                # 'approval_check':True,
            }

            check_obj = self.env['check_followups.check_followups']
            log_obj = self.env['check_followups.checklogs']
            if not self.exp_account:
                raise Warning(_("Expense or debit account must be selected!"))

            if self.partner_id and self.pa_name == 'Check Followups':
                raise Warning(_("Expense Account with Check Followups not Include Supplier selected!"))

            if not self.journal_id and self.pa_name == 'Manual':
                raise Warning(_("Journal must be selected!"))

            # account move entry
            if self.request_currency == self.env.user.company_id.currency_id:
                # corresponding details in account_move_line
                # if self.journal_id.type == 'bank' and self.pa_name == 'Check Followup':
                if self.pa_name == 'Check Followup':
                    self.move_id = self.env['account.move'].create(self.move_check_followups())
                    check = check_obj.create(dictionary)
                    log = {
                        'move_id': self.move_id.id,
                        'name': self.approval_no,
                        'date': self.check_date,
                        'Check': check.id,
                        'beneficiary_id': self.partner_id.id,
                        'account_holder': self.partner_id.id,
                    }
                    log_obj.create(log)

                elif self.pa_name != 'Check Followup':
                    self.move_id = self.env['account.move'].create(self.move_without_check())
                #   self.move_id.post()
                self.state = 'validate'
                self.mn_app_id = self.env.user.id
                # Update footer message
                message_obj = self.env['mail.message']
                message = _("State Changed  Confirm -> <em>%s</em>.") % (self.state)
                msg_id = self.message_post(body=message)
            elif self.request_currency != self.env.user.company_id.currency_id \
                    and self.pa_name == 'Check Followup':
                # check_obj.approval_check = True

                # multi-currency scenario
                # corresponding details in account_move_line

                debit_val = {'move_id': self.move_id.id,
                             # 'name': self.name,
                             'partner_id': self.partner_id.id,
                             'account_id': self.exp_account.id,
                             'analytic_account_id': self.analytic_account.id,
                             'debit': self.request_amount / self.request_currency.rate,
                             'currency_id': self.request_currency.id,
                             'amount_currency': self.request_amount,
                             'company_id': self.company_id.id,
                             }
                credit_val = {'move_id': self.move_id.id,
                              'name': self.approval_no,
                              'partner_id': self.partner_id.id,
                              'account_id': self.journal_id.out_standing.id,
                              'credit': self.request_amount / self.request_currency.rate,
                              'currency_id': self.request_currency.id,
                              'amount_currency': -self.request_amount,
                              'company_id': self.company_id.id,
                              }
                vals = {
                    'journal_id': self.journal_id.id,
                    'date': self.fa_date,
                    'ref': self.approval_no,
                    'CS': self.beneficiary,
                    'company_id': self.company_id.id,
                    'line_ids': [(0, 0, debit_val), (0, 0, credit_val)]
                }
                # add lines
                self.move_id = self.env['account.move'].create(vals)
                #   self.move_id.post()
                check = check_obj.create(dictionary)
                log = {
                    'move_id': self.move_id.id,
                    'name': self.approval_no,
                    'date': self.fa_date,
                    'Check': check.id,
                }

                self.state = 'validate'
                self.mn_app_id = self.env.user.id

            elif self.request_currency != self.env.user.company_id.currency_id and self.pa_name != 'Check Followup':
                debit_val = {'move_id': self.move_id.id,
                             'name': self.approval_no + '/' + str(self.Check_no),
                             'partner_id': self.partner_id.id,
                             'account_id': self.exp_account.id,
                             'analytic_account_id': self.analytic_account.id,
                             'debit': self.request_amount / self.request_currency.rate,
                             'currency_id': self.request_currency.id,
                             'amount_currency': self.request_amount,
                             'company_id': self.company_id.id,
                             }
                credit_val = {'move_id': self.move_id.id,
                              'name': self.approval_no + '/' + str(self.Check_no),
                              'partner_id': self.partner_id.id,
                              'account_id': self.journal_id.default_credit_account_id.id,
                              'credit': self.request_amount / self.request_currency.rate,
                              'currency_id': self.request_currency.id,
                              'amount_currency': -self.request_amount,
                              'company_id': self.company_id.id,
                              }
                vals = {
                    'journal_id': self.journal_id.id,
                    'date': self.fa_date,
                    'ref': self.approval_no,
                    'CS': self.beneficiary,
                    'company_id': self.company_id.id,
                    'line_ids': [(0, 0, debit_val), (0, 0, credit_val)]
                }
                # add lines
                self.move_id = self.env['account.move'].create(vals)
                # self.move_id.post()
                # Change state if all went well!
                self.state = 'validate'
                self.mn_app_id = self.env.user.id

                # Update footer message
                message_obj = self.env['mail.message']
                message = _("State Changed  Confirm -> <em>%s</em>.") % (self.state)
                msg_id = self.message_post(body=message)
            else:
                raise Warning(_("An issue was faced when validating!"))
        else:
            if self.invoice_id.state == 'open':
                invoice_list = []
                payment_method_id = self.payment_method_name.id
                if not payment_method_id:
                    raise Warning(_("Please Specify Payment Method"))
                journal_id = self.journal_id.id
                if not journal_id:
                    raise Warning(_("Please Specify Journal"))
                payment_vals = {
                    'partner_id': self.invoice_id.partner_id.id,
                    'partner_type': 'supplier',
                    'payment_type': 'outbound',
                    'amount': self.request_amount,
                    'company_id': self.invoice_id.company_id.id,
                    'currency_id': self.invoice_id.currency_id.id,
                    'payment_method_id': self.payment_method_name.id,
                    'journal_id': self.journal_id.id,
                    'check_date': self.check_date,
                    'Account_No': self.Account_No,
                    'Bank_id': self.bank_id.id,
                    'Check_no': self.Check_no,
                    'invoice_ids': [(4, self.invoice_id.id)],
                    # 'line_ids': [(0, 0, debit_val), (0, 0, credit_val)]
                }
                payment_id = self.env['account.payment'].create(payment_vals)
                payment_id.post()
                self.state = 'validate'
                self.mn_app_id = self.env.user.id

                # Update footer message
                message_obj = self.env['mail.message']
                message = _("State Changed  Confirm -> <em>%s</em>.") % (self.state)
                msg_id = self.message_post(body=message)
            # if self.invoice_id.state == 'paid':
            #     raise Warning(_("Vendor bill related to this financial approval already paid"))

        # Update footer message
        message_obj = self.env['mail.message']
        message = _("State Changed  Confirm -> <em>%s</em>.") % (self.state)
        msg_id = self.message_post(body=message)

    @api.multi
    def post(self):
        for rec in self:
            for line in rec.line_ids:
                if line.analytic_account_id:
                    for position in line.analytic_account_id.crossovered_budget_line:
                        print('222')
                        if line.account_id in position.general_budget_id.account_ids and line.date <= position.date_to and line.date >= position.date_from:
                        # print'm',abs(-line.balance+position.practical_amount), abs(position.planned_amount) ,position.practical_amount
                            if abs(-line.balance + position.practical_amount) > abs(
                                    position.planned_amount):
                            #  print'm' , line.balance
                                raise ValidationError(_('Budget Exceeded Amount'))

        return super(account_move, self).post()

    @api.one
    def set_to_draft(self):
        self.state = 'draft'
        # self.mn_app_id = None
        self.au_app_id = None
        self.fm_app_id = None
        self.gm_app_id = None
        self.at_app_id = None

        # Update footer message
        message_obj = self.env['mail.message']
        message = _("State Changed  Confirm -> <em>%s</em>.") % (self.state)
        msg_id = self.message_post(body=message)

class CheckFollowupsModel(models.Model):
    _inherit = 'check_followups.check_followups'
    _name = "check_followups.check_followups"

    approval_id = fields.Many2one('finance.approval',readonly=True)
    partner_name = fields.Many2one(related='approval_id.partner_id')
    # @api.model
    # def _get_move_vals(self, move_date):
    #     self.Last_state = self.state
    #     self.write({'state': 'return_acv'})
    #     self.make_a_returning_payment()
    #     return True

    @api.model
    def _get_move_vals(self, move_date):
        """ Return dict to create the check move
        """
        self.ensure_one()

        journal = self.payment_id.journal_id or self.approval_id.journal_id
        # if not journal.sequence_id:
        #     raise UserError(_('Configuration Error !'),
        #                     _('The journal %s does not have a sequence, please specify one.') % journal.name)
        # if not journal.sequence_id.active:
        #     raise UserError(_('Configuration Error !'), _('The sequence of journal %s is deactivated.') % journal.name)
        # name = journal.with_context(ir_sequence_date=str(move_date)).sequence_id.next_by_id()
        return {
            # 'name': name,
            'date': move_date,
            'ref': self.name,
            'company_id': journal.company_id.id,
            'journal_id': journal.id,
            # 'partner_id': self.payment_id.partner_id or False,
        }


    def _get_move_line_accounts(self):
        self.ensure_one()

        if self.type in ['outbound', 'transfer'] and self.approval_id:
            # Vendor Part
            if self.state == 'withdrawal' and self.Last_state == 'out_standing':
                return self.approval_id.journal_id.out_standing.id, self.approval_id.journal_id.default_debit_account_id.id

            if self.state == 'rdv' and self.Last_state == 'out_standing':
                return self.approval_id.journal_id.out_standing.id, self.approval_id.journal_id.rdv.id
            if self.state == 'rdv' and self.Last_state == 'withdrawal':
                return self.approval_id.journal_id.default_debit_account_id.id, self.approval_id.journal_id.rdv.id

            if self.state == 'withdrawal' and self.Last_state == 'rdv':
                return self.approval_id.journal_id.rdv.id, self.approval_id.journal_id.default_debit_account_id.id

            else:
                _logger.error(
                    'can not determine move accounts for {} with state = {}, Last_state = {}. this is unknown change in the state!'.format(
                        self, self.state, self.Last_state))
                raise ValidationError("Unknown check state changes!\nFrom '{}' to '{}'".format(
                    self.Last_state or '', self.state or ''
                ))
        elif not self.approval_id:
            return super(CheckFollowupsModel,self)._get_move_line_accounts()

        else:
            _logger.error(
                'can not determine move accounts for {} with type = {}. type should be either "inbound" or "outbound"'.format(
                    self, self.type))
            raise ValidationError('Error while calculating accounts for check move!')


    approval_check = fields.Boolean('Approval Check',default=False)
# class account_payment(models.Model):
#     _inherit = "account.payment"
#
#     state = fields.Selection([('draft', 'Draft'),
#                               ('au_app', 'Reviewer Approval'),
#                               ('fm_app', 'Financial Approval'),
#                               ('gm_app', 'General Manager Approval'), ('posted', 'Posted'), ('sent', 'Sent'),
#                               ('reconciled', 'Reconciled'), ('cancelled', 'Cancelled')], readonly=True, default='draft',
#                              copy=False, string="Status")
#
#     # added to allow for auditor approval
#     @api.one
#     def au_app(self):
#         self.state = 'au_app'
#         return True
#
#     # added to allow for financial manager / advisor approval
#     @api.one
#     def fm_app(self):
#         self.state = 'fm_app'
#         return True
# #
#     # added to allow for general manager approval
#     @api.one
#     def gm_app(self):
#         self.state = 'gm_app'
#         return True

    # override only draft payment message
    # @api.multi
    # def post(self):
    #     self.state ='draft'
    #     return super(account_payment,self).post()

#
# class Reject(models.Model):
#     _name = 'reject'
#
#     reason = fields.Text(string="Reason")
#     supper_model = fields.Many2one('finance.approval')
#
#     def reject(self):
#         approval_id = self.env['finance.approval'].browse(self._context['active_id'])
#         approval_id.reject_reason = self.reason
#         approval_id.state = 'reject'

