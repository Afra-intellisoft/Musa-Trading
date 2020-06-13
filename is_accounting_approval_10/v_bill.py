from odoo import models, fields, api, _


class bill(models.Model):
    _inherit = 'account.invoice'

    finance_ids = fields.One2many('finance.approval', 'invoice_id', 'Finance approvals')
    approval_count = fields.Integer('Approvals', default='0', compute='compute_len')

    @api.depends('finance_ids')
    def compute_len(self):
        for rec in self:
            rec.approval_count = len(rec.finance_ids)

    @api.one
    def get_amount(self):
        vals = {
            'invoice_id': self.id,
            'request_currency': self.currency_id.id,
            'request_amount': self.amount_total,
            'partner_id': self.partner_id.id,
            'invoice_amount': self.amount_untaxed,
            'type': 'vendor_bill',
        }
        self.env['finance.approval'].create(vals)
