from datetime import datetime, date
import logging
import re
import uuid
from collections import Counter, OrderedDict
from itertools import product
from werkzeug import urls
from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import  Warning,ValidationError,_logger,UserError

class MaintenanceRequest(models.Model):
	_inherit = ['maintenance.request']
	_name = 'maintenance.request'

	amount = fields.Float('Amount')
	request = fields.Boolean('Request')
	vendor_id = fields.Many2one('res.partner' ,'Vendor')
	state = fields.Selection(
		[('draft', 'To Submit'), ('finance_approval', 'Finance Approval'),
		], 'Status', default='draft')


	@api.one
	def finance_approval(self):
		finance_obj = self.env['finance.approval']
		if not self.vendor_id:
			raise Warning(_("Vendor must be selected!"))
		finance_vals = {

				'state': 'draft',
				'requester': self.owner_user_id.id,
				'partner_id': self.vendor_id.id,
				'fa_date': self.request_date,
				'request_amount': self.amount,
				'reason': self.description,
			}
		finance_obj.create(finance_vals)
		self.request =True




class MaintenanceEquipment(models.Model):
	_inherit = 'maintenance.equipment'


	@api.model
	def create(self, vals):
		res = super(MaintenanceEquipment, self).create(vals)
		for x in res:
			x.serial_no =  x.factory_id.name + self.env['ir.sequence'].next_by_code('maintenance.equipment') or '/'
		return res

	name = fields.Char('Name')
	serial_no = fields.Char('Serial No', readonly=True)
	amount = fields.Float('Amount')
	purchase_date = fields.Date('Purchase Date')
	attached = fields.Binary('Upload File')
	factory_id = fields.Many2one('factory',string="Factory",required=True)


class Factory(models.Model):
	_name = 'factory'

	name = fields.Char('Name')
