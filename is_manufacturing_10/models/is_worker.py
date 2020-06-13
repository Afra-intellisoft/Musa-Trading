import datetime
import logging
import re
import uuid
from collections import Counter, OrderedDict
from itertools import product
from werkzeug import urls
from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError

class MrpEmployee(models.Model):
	_name = 'mrp.employee'

	name = fields.Char('Shifts Name')
	date_from = fields.Date('Date From')
	serial_no = fields.Char('Serial No', readonly=True)
	worker_name = fields.Many2one('mrp.worker','Worker')
	work_center = fields.Many2one('mrp.workcenter','Workcenter')
	price_daily = fields.Float('Price Daily')
	mrp_adj_id = fields.Many2one('mrp.adjustment', 'Worker')
	product_quantity = fields.Float('Quantity', compute="get_qty", store=True)
	# total = fields.Float('Total', compute="compute_total", store=True)
	paid = fields.Boolean('Paid')

	@api.onchange('worker_name')
	def _onchange_worker_name(self):
		self.serial_no = self.worker_name.serial_no


	@api.multi
	@api.depends('quantity', 'price')
	def compute_total(self):
		for rec in self:
			rec.total = rec.quantity * rec.price


	@api.multi
	@api.depends('worker_ids')
	def compute_price(self):
		for x in self:
			work = x.worker_ids
			for obj in work:
				self.total = obj.total


	@api.depends('mrp_adj_id.mo_ids.product_qty')
	@api.one
	def get_qty(self):
		for rec in self:
			product_qty = 0
			mo = rec.mrp_adj_id.mo_ids
			for obj in mo:
				product_qty = obj.product_qty
			rec.product_quantity = product_qty


class MrpEmployeeLine(models.Model):
	_name = 'mrp.employee.line'

	name = fields.Char('Name')
	worker_name = fields.Many2one('mrp.worker','Worker')
	serial_no = fields.Char('Serial No', readonly=True)
	work_center = fields.Many2one('mrp.workcenter','Workcenter')
	quantity = fields.Float('Quantity')
	price = fields.Float('Price', compute="get_cost", store=True)
	total = fields.Float('Total', compute="compute_total", store=True)
	price_daily = fields.Float('Price Daily')
	worker_id = fields.Many2one('mrp.employee','Worker')
	mrp_id = fields.Many2one('mrp.adjustment', 'Worker')
	paid = fields.Boolean('Paid')

	@api.onchange('worker_name')
	def _onchange_worker_name(self):
		self.serial_no = self.worker_name.serial_no

	# @api.depends('mo_ids.unit_cost')
	# def _unit_count(self):
	# 	for rec in self:
	# 		total = 0
	# 		mo = rec.mo_ids
	# 		for obj in mo:
	# 			unit_cost = obj.unit_cost
	# 	rec.mrp_id.worker_ids.price = unit_cost
	@api.depends('mrp_id.mo_ids.product_id')
	@api.one
	def get_cost(self):
		for rec in self:
			cost_mrp = 0
			mo = rec.mrp_id.mo_ids
			for obj in mo:
				cost_mrp = obj.product_id.cost_mrp
			rec.price =cost_mrp


	@api.multi
	@api.depends('quantity', 'price')
	def compute_total(self):
		for rec in self:
			rec.total = rec.quantity * rec.price

