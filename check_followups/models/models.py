# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import date
from datetime import datetime
import logging


_logger = logging.getLogger(__name__)


class CheckFollowups(models.Model):
    _name = 'check_followups.check_followups'
    _inherit = ['ir.needaction_mixin', 'mail.thread']
    _description = 'Checks Followup'

    @api.depends('payment_id')
    def _compute_partners(self):
        for r in self:
            if r.payment_id and r.payment_id.payment_type == 'inbound':
                r.beneficiary_id = r.payment_id.company_id.partner_id
                r.account_holder = r.payment_id.partner_id
            elif r.payment_id and r.payment_id.payment_type == 'outbound':
                r.beneficiary_id = r.payment_id.partner_id
                r.account_holder = r.payment_id.company_id.partner_id
            elif r.payment_id and r.payment_id.payment_type == 'transfer':
                r.beneficiary_id = r.account_holder = r.payment_id.company_id.partner_id

    name = fields.Char("Check", readonly=True, default='New')
    payment_id = fields.Many2one('account.payment')
    type = fields.Selection([('outbound', 'Vendor'), ('inbound', 'Customer'), ('transfer', 'Transfer')], string="Type")
    Date = fields.Date('Date')
    manger = fields.Boolean('Manger')
    amount = fields.Monetary('Amount', readonly=True)
    currency_id = fields.Many2one('res.currency', string='Currency')
    communication = fields.Char(related='payment_id.communication', readonly=True)
    Date_due = fields.Date(string='Due Date')
    Date_late = fields.Date(tring='Date Late')
    notes = fields.Text(string='Note')
    check = fields.Boolean('Approved')
    check_no = fields.Float('Check No')
    journal_id = fields.Many2one('account.journal', 'Bank/Cash Journal',
                                 help='Payment journal.',
                                 domain=[('type', 'in', ['bank', 'cash'])])
    account_holder = fields.Many2one('res.partner', string='Account Holder', readonly=True, compute=_compute_partners, store=True)
    beneficiary_id = fields.Many2one('res.partner', string='Beneficiary', readonly=True, compute=_compute_partners)
    partner_id = fields.Many2one('res.partner', compute='_compute_partner', readonly=True, store=True)
    bank_id = fields.Many2one('res.bank','Bank')
    state = fields.Selection([
        ('under_collection', 'Under Collection'),
        ('wait_bank', 'Waiting In Bank'),
        ('in_bank', 'In Bank'),
        ('rdc', 'Check Rejected'),
        ('return_acc', 'Return to Partner'),
        ('donec', 'Done'),
        ('out_standing', 'Out Standing'),
        ('withdrawal', 'Deposit in Bank'),
        ('rdv', 'Check Rejected'),
        ('approve_manger', 'Approve Manager'),
        ('return_acv', 'Return to Partner'),
        ('donev', 'Done')])
    Last_state = fields.Char()
    log_ids = fields.One2many('check_followups.checklogs', 'Check', readonly=True)
    _order = 'id desc'

    @api.depends('payment_id')
    def _compute_partner(self):
        for r in self:
            r.partner_id = r.payment_id and r.payment_id.partner_id or False

    @api.model
    def _needaction_domain_get(self):
        return ['|', ('state', '=', 'under_collection'), ('state', '=', 'out_standing')]

    @api.onchange('payment_id','approval_id')
    def _compute_currency_id(self):
        for r in self:
            if r.payment_id:
                r.currency_id = r.payment_id.currency_id
            if r.approval_id:
                r.currency_id = r.approval_id.request_currency


    @api.multi
    def action_withdrawl(self):
        self.Last_state = self.state
        self.write({'state': 'withdrawal'})
        self.make_move()
        return True




    @api.multi
    def action_mnapp(self):
        self.check = True
        self.write({'state': 'under_collection'})
        return True

    @api.model
    def cron_checks_withdrawal(self):
        records = self.env['check_followups.check_followups']\
            .search([('state', 'in', ['under_collection', 'out_standing']), ('Date', '<=', fields.Date.today()),
                     ('payment_id.company_id.automate_check_withdrawal', '=', True)])
        for rec in records.filtered(lambda r: r.state == 'out_standing'):
            rec.action_withdrawl()
        for rec in records.filtered(lambda r: r.state == 'under_collection'):
            rec.action_submitted()

    @api.multi
    def action_rejectv(self):
        if self.notes == False:
            raise UserError(_('Write The Reason To Check Rejected'))
        else:
            self.Last_state = self.state
            self.write({'state': 'rdv'})
            self.make_move()

    @api.multi
    def action_returnv(self):
        if self.manger == False:
            raise UserError('This Check would only be done approve manager .')
        else:
            self.Last_state = self.state
            self.write({'state': 'return_acv'})
            self.make_a_returning_payment()
        # return True


    @api.multi
    def action_approve_manger(self):
        self.Last_state = self.state
        # self.write({'state': 'approve_manger'})
        self.write({'manger': True})
        return True

    @api.multi
    def action_donev(self):
        self.Last_state = self.state
        self.write({'state': 'donev'})
        return True

    @api.depends('Date_due')
    def action_submitted(self):
        today = date.today()
        str_now = datetime.strptime(str(today), '%Y-%m-%d')
        Date_due = datetime.strptime(str(self.Date_due), '%Y-%m-%d')
        if Date_due <= str_now:
            self.Last_state = self.state
            self.write({'state': 'in_bank'})
            self.make_move()
        else:
            raise UserError(_('Due Date !'))
       # wait bank
    @api.depends('Date_due')
    def action_bankc(self):
        today = date.today()
        str_now = datetime.strptime(str(today), '%Y-%m-%d')
        Date_due = datetime.strptime(str(self.Date_due), '%Y-%m-%d')
        if Date_due <= str_now:
            self.Last_state = self.state
            self.write({'state': 'wait_bank'})
        else:
            raise UserError(_('Its not time for due date !'))


    @api.depends('notes')
    def action_rejectc(self):
        if self.notes == False:
            raise UserError(_('Write The Reason To Check Rejected'))
        else:
            self.Last_state = self.state
            self.write({'state': 'rdc'})
            self.make_move()

    @api.multi
    def action_donec(self):
        self.Last_state = self.state
        self.write({'state': 'donec'})
        return True

    @api.multi
    def action_returnc(self, communication=''):
        self.Last_state = self.state
        self.write({'state': 'return_acc'})
        self.make_a_returning_payment(communication)
        return True

    @api.multi
    def make_move(self):
        for r in self:
            today_date = fields.Date.today()
            aml = r.env['account.move.line']
            debit, credit,ss, amount_currency = aml.with_context(date=r.payment_id.payment_date).compute_amount_fields(r.amount, r.payment_id.currency_id, r.payment_id.company_id.currency_id)
            move = r.env['account.move'].create(r._get_move_vals(today_date))


            debit_account_id, credit_account_id = r._get_move_line_accounts()
            amount = r.payment_id.amount
            lines = []
            currency_id = False
            if amount_currency:
                currency_id = r.payment_id.currency_id.id
            lines.append((0, 0, r._get_move_line_vals(debit, credit, amount_currency, currency_id, debit_account_id)))
            lines.append((0, 0, r._get_move_line_vals(credit, debit, amount_currency, currency_id, credit_account_id)))
            move.write({'line_ids': lines})
            move.post()


            last_state_label = dict(r.fields_get(allfields=['state'])['state']['selection'])[r.Last_state]
            state_label = dict(r.fields_get(allfields=['state'])['state']['selection'])[r.state]
            description = "Move From " + last_state_label + " To " + state_label

            self.WriteLog(move.id, description, str(today_date))

    #######################################
    # Helper functions to create the move #
    #######################################
    def _get_move_vals(self, move_date):
        """ Return dict to create the check move
        """
        self.ensure_one()
        journal = self.journal_id
        if not journal.sequence_id:
            raise UserError(_('Configuration Error !'), _('The journal %s does not have a sequence, please specify one.') % journal.name)
        if not journal.sequence_id.active:
            raise UserError(_('Configuration Error !'), _('The sequence of journal %s is deactivated.') % journal.name)
        name = journal.with_context(ir_sequence_date=str(move_date)).sequence_id.next_by_id()
        return {
            'name': name,
            'date': move_date,
            'ref': self.name,
            'company_id': self.payment_id.company_id.id,
            'journal_id': self.journal_id.id,
            'partner_id': self.payment_id.partner_id and self.payment_id.partner_id.id or False,
        }

    def _get_move_line_vals(self, debit, credit, amount_currency, currency_id, account_id, name=''):
        self.ensure_one()
        return {
            'name': name and name or self.name,
            'credit': credit,
            'debit': debit,
            'account_id': account_id,
            'currency_id': currency_id,
            'amount_currency': debit>0 and amount_currency or -amount_currency,
            'partner_id': self.payment_id.partner_id.id,
        }

    ##########################################
    # ///Helper functions to create the move #
    ##########################################

    @api.multi
    def make_a_returning_payment(self, communication=''):
        self.ensure_one()

        today = fields.Date.today()
        payment_dict = {
            'payment_date': today,
            'payment_reference': self.payment_id.payment_reference,
            'communication': communication and communication or self.payment_id.communication,
        }

        payment_context = {
            'check_payment': True,
            'check_last_state': self.Last_state,
            'check_state': self.state,
        }

        if self.type == 'transfer':
            payment_context.update(change_account_in_aml_to_out_standing=True)
            payment_dict.update(payment_type='transfer')
            payment_dict.update(journal_id=self.payment_id.destination_journal_id.id)
            payment_dict.update(destination_journal_id=self.journal_id.id)
            payment_context.update(journal_id_to_change=self.journal_id.id)
        elif self.Last_state in ['out_standing', 'rdv']:
            payment_dict.update(payment_type='inbound')
        elif self.Last_state in ['under_collection', 'rdc']:
            payment_dict.update(payment_type='outbound')

        payment = self.payment_id.copy(payment_dict)
        payment.with_context(payment_context).post()
        for line in payment.move_line_ids:
            if not line.ref:
                line.ref = self.name

        last_state_label = dict(self.fields_get(allfields=['state'])['state']['selection'])[self.Last_state]
        state_label = dict(self.fields_get(allfields=['state'])['state']['selection'])[self.state]
        description = "Move From " + last_state_label + " To " + state_label

        self.WriteLog(payment.move_line_ids[0].move_id.id, description, str(today), payment_id=payment.id)

    def _get_move_line_accounts(self):
        self.ensure_one()
        if self.type == 'inbound':
            # Customer part
            if self.state == 'in_bank' and self.Last_state == 'under_collection' or self.Last_state =='wait_bank':
                return self.journal_id.default_credit_account_id.id, self.journal_id.under_collection.id
            if self.state == 'rdc' and self.Last_state == 'under_collection':
                return self.journal_id.rdc.id, self.payment_id.under_collection.id
            elif self.state == 'under_collection' and self.Last_state == 'rdc':
                return self.journal_id.under_collection.id, self.journal_id.rdc.id
            elif self.state == 'rdc' and self.Last_state == 'in_bank':
                return self.journal_id.rdc.id, self.journal_id.default_credit_account_id.id
            elif self.state == 'in_bank' and self.Last_state == 'rdc':
                return self.journal_id.default_credit_account_id.id, self.journal_id.rdc.id
            else:
                _logger.error('can not determine move accounts for {} with state = {}, Last_state = {}. this is unknown change in the state!'.format(self, self.state, self.Last_state))
                raise ValidationError("Unknown check state changes!\nFrom '{}' to '{}'".format(
                    self.Last_state or '', self.state or ''
                ))

        elif self.type in ['outbound', 'transfer']:
            # Vendor Part
            if self.state == 'withdrawal' and self.Last_state == 'out_standing':
                return self.payment_id.journal_id.out_standing.id, self.payment_id.journal_id.default_debit_account_id.id
            elif self.state == 'rdv' and self.Last_state == 'out_standing':
                return self.payment_id.journal_id.out_standing.id, self.payment_id.journal_id.rdv.id
            elif self.state == 'rdv' and self.Last_state == 'withdrawal':
                return  self.payment_id.journal_id.default_debit_account_id.id, self.payment_id.journal_id.rdv.id
            elif self.state == 'withdrawal' and self.Last_state == 'rdv':
                return self.payment_id.journal_id.rdv.id , self.payment_id.journal_id.default_debit_account_id.id
            else:
                _logger.error('can not determine move accounts for {} with state = {}, Last_state = {}. this is unknown change in the state!'.format(self, self.state, self.Last_state))
                raise ValidationError("Unknown check state changes!\nFrom '{}' to '{}'".format(
                    self.Last_state or '', self.state or ''
                ))

        else:
            _logger.error('can not determine move accounts for {} with type = {}. type should be either "inbound" or "outbound"'.format(self, self.type))
            raise ValidationError('Error while calculating accounts for check move!')

    @api.model
    def create(self, vals):
        if vals['type'] == 'inbound':
            vals['name'] = self.env['ir.sequence'].get('check_followups.check_followups')+'/'+vals['check_no']
        else:
            vals['name'] = self.env['ir.sequence'].get('check_followups.check_followups_vender')+'/'+vals['check_no']
        return super(CheckFollowups, self).create(vals)

    def unlink(self, cr, uid, ids, context=None):
        raise UserError('You Cannot Delete The Check')

    def WriteLog(self, Move_id, Description, date, payment_id=False):
        self.ensure_one()
        log = {
            'move_id': Move_id,
            'name': Description,
            'date': date,
            'Check': self.id,
            'payment_id': payment_id,
        }
        return self.env['check_followups.checklogs'].create(log)


class PartnerAccounts(models.Model):
    _name = 'partner.bank.account'
    Account_No = fields.Char('Account No', required=True)
    Bank_id = fields.Many2one('res.bank', 'Bank',required=True)
    Partner_Id = fields.Many2one('res.partner','Partner', required=True)
    _rec_name = 'Account_No'


class Partner(models.Model):
    _inherit = 'res.partner'
    Bank_Account_ids = fields.One2many('partner.bank.account', 'Partner_Id')
    check_ids = fields.One2many('check_followups.check_followups', 'account_holder')


class bank_res(models.Model):
    _inherit = 'res.bank'
    amount_textx = fields.Integer('Amount in Text X-axis')
    amount_texty = fields.Integer('Amount in Text Y-axis')
    acc_holderx = fields.Integer('Account Holder X-axis')
    acc_holdery = fields.Integer('Account Holder Y-axis')
    datex = fields.Integer('Date X-axis')
    datey = fields.Integer('Date Y-axis')
    amountx = fields.Integer('Amount X-axis')
    amounty = fields.Integer('Amount Y-axis')
    account_holder_width = fields.Integer('Name Width')
    money_text_width = fields.Integer('Money Area Width')
    money_text_height = fields.Integer('Money Area Height')


class JournalAccount(models.Model):
    _inherit = 'account.journal'
    under_collection = fields.Many2one('account.account')
    rdc = fields.Many2one('account.account','Return / Receivable')
    ################################### Customer accounts
    out_standing = fields.Many2one('account.account')
    rdv = fields.Many2one('account.account','Return / Payable')
    ################################### Vender accounts
    Check_no = fields.Integer('Check No')


class CheckLogs(models.Model):
    _name = 'check_followups.checklogs'

    move_id = fields.Many2one('account.move', string='Move')
    name = fields.Char('Description')
    date = fields.Date('Date')
    Check = fields.Many2one('check_followups.check_followups')
    payment_id = fields.Many2one('account.payment', 'Payment')


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.model
    def create(self, vals):
        if self._context.get('change_account_in_aml_to_out_standing', False):
            journal = self.env['account.journal'].browse(vals['journal_id'])
            if journal.id == self._context.get('journal_id_to_change') and vals['debit'] > 0.0:
                check_last_state = self._context['check_last_state']
                if check_last_state == 'out_standing':
                    vals['account_id'] = journal.out_standing.id
                elif check_last_state == 'rdv':
                    vals['account_id'] = journal.rdv.id
                else:
                    raise ValidationError('Unknown check payment, unable to determine the transfer payment debit '
                                          'account.')

        return super(AccountMoveLine, self).create(vals)

class AccountJournal(models.Model):
    _inherit = 'account.journal'

    check_vendor_id = fields.Integer(string='Check Num',compute='compute_vendor_check')
    check_vendor_total = fields.Integer(string='Check Total',compute='compute_vendor_check')

    check_num_id = fields.Integer(string='Check Num',compute='compute_check')
    check_total = fields.Integer(string='Check Total',compute='compute_check')
    check_ids = fields.One2many('check_followups.check_followups', 'journal_id', string='Check')

    @api.depends('check_ids')
    @api.multi
    def compute_check(self):
           nbr = 0
           for check in self:
                check_num_count = check.env['check_followups.check_followups'].search_count([('state', '=', 'under_collection'),('journal_id','=',check.id)])
                check.check_num_id = check_num_count
                for rec in check.check_ids:
                    if rec.state in ('under_collection'):
                        check.check_total += rec.amount

    @api.depends('check_ids')
    @api.multi
    def compute_vendor_check(self):
        nbr = 0
        for check_id in self:
            check_vendor_count = check_id.env['check_followups.check_followups'].search_count(
                [('state', '=', 'out_standing'), ('journal_id', '=', check_id.id)])
            check_id.check_vendor_id = check_vendor_count
            for rec in check_id.check_ids:
                if rec.state in ('out_standing'):
                    check_id.check_vendor_total += rec.amount


