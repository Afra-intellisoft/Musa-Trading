from odoo import api, fields, models, _
from odoo.exceptions import UserError, Warning
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from odoo.tools import float_compare
import math
import babel
import time
from odoo import tools
import calendar
from odoo.exceptions import UserError, ValidationError



class AccountAssetAsset(models.Model):
    _inherit = 'account.asset.asset'
    _description = "Asset"

    serial_no = fields.Char(string='Serial No')

