# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class Company(models.Model):
    _inherit = 'res.company'

    automate_check_withdrawal = fields.Boolean(string='Automate check withdrawal/deposition in bank')
