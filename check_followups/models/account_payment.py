#-*- coding: utf-8 -*-

from odoo   import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import date
import logging


_logger = logging.getLogger(__name__)


class Payment(models.Model):
    _inherit = 'account.payment'
    partner_bank_account = fields.Many2one('partner.bank.account', 'Partner Account', store=False)
    Account_No = fields.Char(string='Account No')
    Check_no = fields.Char('Check No')
    Bank_id = fields.Many2one('res.bank', string='Bank')
    check_date = fields.Date('Check Date')
    due_date = fields.Date('Due Date')
    notes = fields.Text('Note')
    check_amount_in_words = fields.Char('Amount In Words', compute='_compute_amount_in_words')
    payment_method_name = fields.Char(related='payment_method_id.name')
    child_ids = fields.One2many('account.payment', 'parent_id')
    parent_id = fields.Many2one('account.payment', 'Replacement For', copy=False)



    @api.depends('amount')
    def _compute_amount_in_words(self):
        from . import money_to_text_ar
        for r in self:
            r.check_amount_in_words = money_to_text_ar.amount_to_text_arabic(r.amount, r.currency_id.name)

    @api.onchange('partner_bank_account')
    def _onchange_partner_bank(self):
        self.Bank_id = self.partner_bank_account.Bank_id
        self.Account_No = self.partner_bank_account.Account_No

    @api.onchange('payment_method_id')
    def _onchange_partner_type(self):
        if self.payment_method_id.name == 'Check' and self.payment_type != 'inbound':
            self.Bank_id = self.journal_id.bank_id
            self.Account_No = self.journal_id.bank_acc_number
        else:
            self.Bank_id = False
            self.Account_No = False

    @api.onchange('journal_id', 'payment_method_id')
    def onchange_journal_id_set_outbound_check_info(self):
        if self.payment_type in ['outbound', 'transfer']:
            if self.journal_id and self.payment_method_id == self.env.ref('check_followups.account_payment_method_check_outBound'):
                self.Bank_id = self.journal_id.bank_id
                self.Account_No = self.journal_id.bank_acc_number
                self.Check_no = self.journal_id.Check_no + 1
            else:
                self.Bank_id = False
                self.Account_No = ''
                self.Check_no = 0

    @api.onchange('partner_id', 'payment_method_id')
    def onchange_partner_id_set_inbound_check_info(self):
        if self.partner_id and self.payment_method_id:
            if self.payment_type == 'inbound':
                if self.payment_method_id == self.env.ref('check_followups.account_payment_method_check_inBound'):
                    if len(self.partner_id.Bank_Account_ids) > 0:
                        self.partner_bank_account = self.partner_id.Bank_Account_ids[0]
                        return

                self.partner_bank_account = False
                self.Bank_id = False
                self.Account_No = ''

    @api.multi
    def post(self):
        for r in self:
            inbound_check = r.env.ref('check_followups.account_payment_method_check_inBound')
            outbound_check = r.env.ref('check_followups.account_payment_method_check_outBound')

            if r.payment_method_id in [inbound_check, outbound_check]:
                if not r._context.get('check_payment', False):
                    # no check_payment means this payment is the first payment for the check, and it is not a returning
                    # payment (returning an already existing check to customer or to us)
                    payment_context = {
                        'check_payment': True,
                        'check_last_state': False,
                    }

                    if r.payment_method_id == inbound_check:
                        payment_context.update(dict(check_state='under_collection'))
                    elif r.payment_method_id == outbound_check:
                        # print('sudo',r.journal_id.sudo().Check_no)
                        # r.journal_id.sudo().Check_no = r.Check_no
                        payment_context.update(dict(check_state='out_standing'))

                    r = r.with_context(payment_context)
                    res = super(Payment, self).post()
                    check = r._create_check()
                    for line in r.move_line_ids:
                        if not line.ref:
                            line.ref = check.name
                    return res

            super(Payment, self).post()

    @api.returns('check_followups.check_followups')
    def _create_check(self):
        self.ensure_one()

        check_dict = {
            'payment_id': self.id,
            'type': self.payment_type,
            'amount': self.amount,
            'Date': self.payment_date,
            'bank_id': self.Bank_id.id,
            'Date_due': self.due_date,
            'check_no': self.Check_no,
            'journal_id': self.journal_id.id,
        }
        log_args = {
            'Move_id': self.move_line_ids[0].move_id.id,
            'payment_id': self.id,
            'date': self.payment_date,
        }
        if self.payment_type == 'inbound':
            check_dict.update({
                'state': 'under_collection',
            })

            log_args.update({
                'Description': 'Customer Check is under collection',
            })
        elif self.payment_type in ['outbound', 'transfer']:
            check_dict.update({
                'state': 'out_standing',
            })
            log_args.update({
                'Description': 'Vendor Check is outstanding',
            })

        check = self.env['check_followups.check_followups'].create(check_dict)
        self.payment_reference = check.name
        check.WriteLog(**log_args)
        return check

    def _get_liquidity_move_line_vals(self, amount):
        vals = super(Payment, self)._get_liquidity_move_line_vals(amount)

        if self.payment_method_name =='Check Followup':
            if self.payment_type == 'inbound':
                # compute debit account
                vals['account_id'] = self.journal_id.under_collection.id
            elif self.payment_type == 'outbound':
                # compute credit account
                vals['account_id'] = self.journal_id.out_standing.id

            elif self.payment_type == 'transfer':
                vals['account_id']= self.journal_id.out_standing.id
        print(vals)
        if self.env.context.get('check_payment', False):
            check_state = self.env.context.get('check_state', False)
            check_last_state = self.env.context.get('check_last_state', False)
            if not check_state:
                raise ValidationError('Error while computing payment destination account, check_state is not provided!')
            if self.payment_type == 'inbound':
                # compute debit account
                if check_last_state is False and check_state == 'under_collection':
                    vals['account_id'] = self.journal_id.under_collection.id
                elif check_last_state == 'out_standing' and check_state == 'return_acv':
                    vals['account_id'] = self.journal_id.out_standing.id
                elif check_last_state == 'rdv' and check_state == 'return_acv':
                    vals['account_id'] = self.journal_id.rdv.id
                else:
                    _logger.error('can not determine check payment\'s debit account, Last_state = {}, state = {}.'
                                  ' this is unknown change in the state!'.format(check_last_state, check_state))
                    raise ValidationError('Unknown check payment, unable to determine the payment debit account.')
            elif self.payment_type == 'outbound':
                # compute credit account
                if check_last_state is False and check_state == 'out_standing':
                    print("111")
                    vals['account_id'] = self.journal_id.out_standing.id
                elif check_last_state == 'under_collection' and check_state == 'return_acc':
                    print("222")
                    vals['account_id'] = self.journal_id.under_collection.id
                elif check_last_state == 'rdc' and check_state == 'return_acc':
                    print("333")
                    #print(self.parent_id.property_account_receivable_id)
                    vals['account_id'] = self.journal_id.rdc.id
                else:
                    _logger.error('can not determine check payment\'s credit account, Last_state = {}, state = {}. '
                                  'this is unknown change in the state!'.format(check_last_state, check_state))
                    raise ValidationError('Unknown check payment, unable to determine the payment credit account.')
            elif self.payment_type == 'transfer':
                if check_last_state is False and check_state == 'out_standing':
                    vals['account_id'] = self.journal_id.out_standing.id
                elif check_last_state == 'out_standing' and check_state == 'return_acv':
                    pass
                elif check_last_state == 'rdv' and check_state == 'return_acv':
                    pass
                else:
                    _logger.error('can not determine check payment\'s credit account, Last_state = {}, state = {}. '
                                  'this is unknown change in the state!'.format(check_last_state, check_state))
                    raise ValidationError('Unknown check payment, unable to determine the payment credit account.')

        print(vals)
        #ppp
        return vals

    payment_security_level = {
        'secured': 1,
        'unsecured': 2,
        'risky': 3,
        'none': -1,
    }

    security_level = fields.Selection([
        (payment_security_level['secured'], 'Secured'),
        (payment_security_level['unsecured'], 'Unsecured'),
        (payment_security_level['risky'], 'Risky'),
        (payment_security_level['none'], 'None'),
    ], compute='get_amount_details', string='Security Level')

    @api.multi
    def get_amount_details(self, today_date=False):
        inbound_manual = self.env.ref('account.account_payment_method_manual_in')
        inbound_check = self.env.ref('check_followups.account_payment_method_check_inBound')

        res = {
            'cash_payments': 0.0,
            'under_collection': 0.0,
            'due_checks': 0.0,
            'rdc': 0.0,
            'in_bank': 0.0,
        }
        if not today_date:
            today_date = fields.Date.today()

        for r in self:
            if r.state == 'draft':
                r.security_level = Payment.payment_security_level['none']
                continue
            if len(r.child_ids) > 0:
                replacement_res = r.child_ids.get_amount_details()
                for key in replacement_res:
                    res[key] += replacement_res[key]
                r.security_level = max(r.child_ids.mapped('security_level'))  # notice that this function is called on
                # child_ids first before reading the values of the computed field 'security_level'
                continue

            if r.payment_method_id == inbound_manual:
                res['cash_payments'] += r.amount
                r.security_level = Payment.payment_security_level['secured']
                continue
            if r.payment_method_id == inbound_check:
                check = r.env['check_followups.check_followups'].search([('payment_id', '=', r.id)])
                if check.state in ['in_bank', 'donec']:
                    res['in_bank'] += r.amount
                    r.security_level = Payment.payment_security_level['secured']
                elif check.state == 'under_collection' and check.Date > today_date:
                    res['under_collection'] += r.amount
                    r.security_level = Payment.payment_security_level['unsecured']
                elif check.state == 'under_collection' and check.Date <= today_date:
                    res['due_checks'] += r.amount
                    r.security_level = Payment.payment_security_level['risky']
                elif check.state == 'rdc':
                    res['rdc'] += r.amount
                    r.security_level = Payment.payment_security_level['risky']
                elif check.state == 'return_acc':
                    r.security_level = Payment.payment_security_level['none']
        return res


