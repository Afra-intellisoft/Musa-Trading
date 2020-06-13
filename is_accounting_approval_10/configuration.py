##############################################################################
#    Description: Accounting Approval                                        #
#    Author: IntelliSoft Software                                            #
#    Date: Aug 2015 -  Till Now                                              #
##############################################################################

from odoo import models, fields, api, _
from datetime import datetime
from odoo.tools import image_resize_image
import base64

# inherit to add manager for approvals
class res_users(models.Model):
    _inherit='res.users'

    approval_manager = fields.Many2one('res.users', 'Manager for Approval(s)')
    user_signature = fields.Binary('Signature')
    resized_user_signature = fields.Binary('Resized Signature', store=True, compute="_get_image")

    @api.one
    @api.depends('user_signature')
    def _get_image(self):
        if self.user_signature:
            self.resized_user_signature = self.user_signature

    @api.one
    def resize_signature(self):
        if self.user_signature:
            self.resized_user_signature = image_resize_image(self.user_signature, size=(100, 50))

#################################################################################################
# inherit
class res_currency(models.Model):
    _inherit='res.currency'

    narration_ar_un = fields.Char('Arabic Narration Main')
    narration_ar_cn = fields.Char('Arabic Narration Denomination')


