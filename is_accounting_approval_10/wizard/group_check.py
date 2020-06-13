# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare

from itertools import groupby



class fa_register_payments(models.TransientModel):
    _name = "fa.register.payments"
    _description = "Register Payments for multiple financial approval"


    check_date = fields.Date('Check Date')
    journal_id = fields.Many2one('account.journal', string = 'Bank/Cash Journal', help='Payment journal.', domain=[('type', 'in', ['bank', 'cash'])])

    Account_No = fields.Char('Account Number')
    Bank_id = fields.Many2one(related='journal_id.bank_id')
    Check_no = fields.Char('Check Number')
    payment_method_name = fields.Many2one('account.payment.method', string = 'Payment Method')
    pa_name = fields.Char(related="payment_method_name.name")
    partner_id = fields.Many2one('res.partner', string='Beneficiary')
    amount = fields.Float('Amount')
    currency_id = fields.Many2one('res.currency', 'Currency',
                                       default=lambda self: self.env.user.company_id.currency_id)





    # @api.multi
    # def _groupby_invoices(self):
    #     '''Groups the invoices linked to the wizard.
    #
    #     If the group_invoices option is activated, invoices will be grouped
    #     according to their commercial partner, their account, their type and
    #     the account where the payment they expect should end up. Otherwise,
    #     invoices will be grouped so that each of them belongs to a
    #     distinct group.
    #
    #     :return: a dictionary mapping, grouping invoices as a recordset under each of its keys.
    #     '''
    #     if not self.group_invoices:
    #         return {inv.id: inv for inv in self.invoice_ids}
    #
    #     results = {}
    #     # Create a dict dispatching invoices according to their commercial_partner_id, account_id, invoice_type and partner_bank_id
    #     for inv in self.invoice_ids:
    #         partner_id = inv.commercial_partner_id.id
    #         account_id = inv.account_id.id
    #         invoice_type = MAP_INVOICE_TYPE_PARTNER_TYPE[inv.type]
    #         recipient_account =  inv.partner_bank_id
    #         key = (partner_id, account_id, invoice_type, recipient_account)
    #         if not key in results:
    #             results[key] = self.env['account.invoice']
    #         results[key] += inv
    #     return results

    # @api.multi
    # def _prepare_payment_vals(self, invoices):
    #     '''Create the payment values.
    #
    #     :param invoices: The invoices that should have the same commercial partner and the same type.
    #     :return: The payment values as a dictionary.
    #     '''
    #
    #     amount = self._compute_payment_amount(invoices=invoices) if self.multi else self.amount
    #     payment_type = ('inbound' if amount > 0 else 'outbound') if self.multi else self.payment_type
    #     bank_account = self.multi and invoices[0].partner_bank_id or self.partner_bank_account_id
    #     pmt_communication = self.show_communication_field and self.communication \
    #                         or self.group_invoices and ' '.join([inv.reference or inv.number for inv in invoices]) \
    #                         or invoices[0].reference # in this case, invoices contains only one element, since group_invoices is False
    #     values = {
    #         'journal_id': self.journal_id.id,
    #         'payment_method_id': self.payment_method_id.id,
    #         'payment_date': self.payment_date,
    #         'communication': pmt_communication,
    #         'invoice_ids': [(6, 0, invoices.ids)],
    #         'payment_type': payment_type,
    #         'amount': abs(amount),
    #         'currency_id': self.currency_id.id,
    #         'partner_id': invoices[0].commercial_partner_id.id,
    #         'partner_type': MAP_INVOICE_TYPE_PARTNER_TYPE[invoices[0].type],
    #         'partner_bank_account_id': bank_account.id,
    #         'multi': False,
    #         'payment_difference_handling': self.payment_difference_handling,
    #         'writeoff_account_id': self.writeoff_account_id.id,
    #         'writeoff_label': self.writeoff_label,
    #     }
    #
    #     return values
    #
    # @api.multi
    # def get_payments_vals(self):
    #     '''Compute the values for payments.
    #
    #     :return: a list of payment values (dictionary).
    #     '''
    #     if self.multi:
    #         groups = self._groupby_invoices()
    #         return [self._prepare_payment_vals(invoices) for invoices in groups.values()]
    #     return [self._prepare_payment_vals(self.invoice_ids)]

    @api.multi
    def create_payments(self):
        '''Create payments according to the FA.
        Having invoices with different commercial_partner_id or different type (Vendor bills with customer invoices)
        leads to multiple payments.
        In case of all the invoices are related to the same commercial_partner_id and have the same type,
        only one payment will be created.

        :return: The ir.actions.act_window to show created payments.
        '''
        Payment = self.env['account.payment']
        payments = Payment
        for payment_vals in self.get_payments_vals():
            payments += Payment.create(payment_vals)
        payments.post()

        action_vals = {
            'name': _('Payments'),
            'domain': [('id', 'in', payments.ids), ('state', '=', 'posted')],
            'view_type': 'form',
            'res_model': 'account.payment',
            'view_id': False,
            'type': 'ir.actions.act_window',
        }
        if len(payments) == 1:
            action_vals.update({'res_id': payments[0].id, 'view_mode': 'form'})
        else:
            action_vals['view_mode'] = 'tree,form'
        return action_vals

    @api.one
    def validate(self):
        # active_ids = self._context.get('active_ids')
        invoice_ids =[]
        active_ids = self.env['finance.approval'].browse(self._context.get('active_ids'))
        print(active_ids)
        amount = 0.0
        for active in active_ids:
            print(active.invoice_id.state)
            amount += active.request_amount
            invoice_ids.append(active.invoice_id.id)
            if active.invoice_id :
                if active.invoice_id.state != 'open':
                    raise UserError(_("Some invoices already paid"))
                if active.invoice_id.partner_id != self.partner_id:
                    raise UserError(_("Some financial approvals not related to specified partner"))
            if active.state != 'ready':
                raise UserError(_("All financial approvals should be ready for payment"))

        # print(amount)
        # self.amount = amount
        # if self.invoice_id.state == 'open':
            invoice_list = []
        payment_method_id = self.payment_method_name.id
        if not payment_method_id:
            raise Warning(_("Please Specify Payment Method"))
        journal_id = self.journal_id.id
        if not journal_id:
            raise Warning(_("Please Specify Journal"))
        payment_vals = {
            'partner_id': self.partner_id.id,
            'partner_type': 'supplier',
            'payment_type': 'outbound',
            'amount': amount,
            'company_id': self.env.user.company_id.id,
            'currency_id': self.env.user.company_id.currency_id.id,
            'payment_method_id': self.payment_method_name.id,
            'journal_id': self.journal_id.id,
            'check_date': self.check_date,
            'Account_No': self.Account_No,
            'Bank_id': self.Bank_id.id,
            'Check_no': self.Check_no,
            'invoice_ids': [(6, 0, invoice_ids)],
            # 'line_ids': [(0, 0, debit_val), (0, 0, credit_val)]
        }
        print(payment_vals)
        payment_id = self.env['account.payment'].create(payment_vals)
        payment_id.post()
        for active in active_ids:
            active.state = 'validate'
            message_obj = self.env['mail.message']
            message = _("State Changed  Confirm -> <em>%s</em>.") % (active.state)
            msg_id = active.message_post(body=message)


        #     # Update footer message
        #     message_obj = self.env['mail.message']
        #     message = _("State Changed  Confirm -> <em>%s</em>.") % (self.state)
        #     msg_id = self.message_post(body=message)
        # # if self.invoice_id.state == 'paid':
        # #     raise Warning(_("Vendor bill related to this financial approval already paid"))

        # Update footer message
        # message_obj = self.env['mail.message']
        # message = _("State Changed  Confirm -> <em>%s</em>.") % (self.state)
        # msg_id = self.message_post(body=message)
