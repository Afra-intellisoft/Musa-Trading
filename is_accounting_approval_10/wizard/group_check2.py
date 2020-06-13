# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare

from itertools import groupby



class fa_register_payments(models.TransientModel):
    _name = "fa.register.payments"
    _inherit = 'account.abstract.payment'
    _description = "Register Payments for multiple financial approval"

    group_invoices = fields.Boolean(string="Group Invoices", help="""If enabled, groups invoices by commercial partner, invoice account,
                                                                    type and recipient bank account in the generated payments. If disabled,
                                                                    a distinct payment will be generated for each invoice.""")
    show_communication_field = fields.Boolean(compute='_compute_show_communication_field')

    @api.depends('invoice_ids.partner_id', 'group_invoices')
    def _compute_show_communication_field(self):
        """ We allow choosing a common communication for payments if the group
        option has been activated, and all the invoices relate to the same
        partner.
        """
        for record in self:
            record.show_communication_field = len(record.invoice_ids) == 1 \
                                              or record.group_invoices and len(record.mapped('invoice_ids.partner_id.commercial_partner_id')) == 1

    @api.onchange('journal_id')
    def _onchange_journal(self):
        res = super(fa_register_payments, self)._onchange_journal()
        invoice_ids = []
        active_ids = self._context.get('active_ids')
        for id in active_ids :
            invoice_ids.append(id.invoice_id)
        invoices = self.env['account.invoice'].browse(invoice_ids)
        self.amount = abs(self._compute_payment_amount(invoices))
        return res

    @api.model
    def default_get(self, fields):
        rec = super(fa_register_payments, self).default_get(fields)
        active_ids = self._context.get('active_ids')

        if not active_ids:
            raise UserError(_("Programming error: wizard action executed without active_ids in context."))

        return rec

    @api.multi
    def _groupby_invoices(self):
        '''Groups the invoices linked to the wizard.

        If the group_invoices option is activated, invoices will be grouped
        according to their commercial partner, their account, their type and
        the account where the payment they expect should end up. Otherwise,
        invoices will be grouped so that each of them belongs to a
        distinct group.

        :return: a dictionary mapping, grouping invoices as a recordset under each of its keys.
        '''
        if not self.group_invoices:
            return {inv.id: inv for inv in self.invoice_ids}

        results = {}
        # Create a dict dispatching invoices according to their commercial_partner_id, account_id, invoice_type and partner_bank_id
        for inv in self.invoice_ids:
            partner_id = inv.commercial_partner_id.id
            account_id = inv.account_id.id
            invoice_type = MAP_INVOICE_TYPE_PARTNER_TYPE[inv.type]
            recipient_account =  inv.partner_bank_id
            key = (partner_id, account_id, invoice_type, recipient_account)
            if not key in results:
                results[key] = self.env['account.invoice']
            results[key] += inv
        return results

    @api.multi
    def _prepare_payment_vals(self, invoices):
        '''Create the payment values.

        :param invoices: The invoices that should have the same commercial partner and the same type.
        :return: The payment values as a dictionary.
        '''
        amount = self._compute_payment_amount(invoices=invoices) if self.multi else self.amount
        payment_type = ('inbound' if amount > 0 else 'outbound') if self.multi else self.payment_type
        bank_account = self.multi and invoices[0].partner_bank_id or self.partner_bank_account_id
        pmt_communication = self.show_communication_field and self.communication \
                            or self.group_invoices and ' '.join([inv.reference or inv.number for inv in invoices]) \
                            or invoices[0].reference # in this case, invoices contains only one element, since group_invoices is False
        values = {
            'journal_id': self.journal_id.id,
            'payment_method_id': self.payment_method_id.id,
            'payment_date': self.payment_date,
            'communication': pmt_communication,
            'invoice_ids': [(6, 0, invoices.ids)],
            'payment_type': payment_type,
            'amount': abs(amount),
            'currency_id': self.currency_id.id,
            'partner_id': invoices[0].commercial_partner_id.id,
            'partner_type': MAP_INVOICE_TYPE_PARTNER_TYPE[invoices[0].type],
            'partner_bank_account_id': bank_account.id,
            'multi': False,
            'payment_difference_handling': self.payment_difference_handling,
            'writeoff_account_id': self.writeoff_account_id.id,
            'writeoff_label': self.writeoff_label,
        }

        return values

    @api.multi
    def get_payments_vals(self):
        '''Compute the values for payments.

        :return: a list of payment values (dictionary).
        '''
        if self.multi:
            groups = self._groupby_invoices()
            return [self._prepare_payment_vals(invoices) for invoices in groups.values()]
        return [self._prepare_payment_vals(self.invoice_ids)]

    @api.multi
    def create_payments(self):
        '''Create payments according to the invoices.
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