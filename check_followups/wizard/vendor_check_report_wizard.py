# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
import math


class al_check_report_wizard(models.TransientModel):
    _name = 'all.check.repor.wizard'
    date_from = fields.Date('From Date', required="True")
    date_to = fields.Date('To Date', required="True")
    type = fields.Selection([('checks_recivce','Withdrawal Checks'), ('checks_return', 'Return Checks'),('checks_reject', 'Rejected Checks'),
        ('checks_out', 'Out Standing Checks') ], default='checks_out',string='Report Type',required="True")




    @api.multi
    def create_report(self, data):
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['date_from', 'date_to', 'type'])
        print("iAM IN WIZARD....................", data['form'])
        return self.env['report'].get_action(self,'check_followups.al_check_report', data=data)


