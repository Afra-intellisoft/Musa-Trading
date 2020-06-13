from datetime import datetime, date
import logging
import re
import uuid
from collections import Counter, OrderedDict
from itertools import product
from werkzeug import urls
from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError


class ProductTemplate(models.Model):
	_inherit = ['product.template']
	_name = 'product.template'

	cost_mrp = fields.Float('Mrp Cost')


class MrpProduction(models.Model):
	_inherit = ['mrp.production']
	_name = 'mrp.production'

	@api.multi
	def button_plan(self):
		""" Create work orders. And probably do stuff, like things. """
		orders_to_plan = self.filtered(lambda order: order.routing_id and order.state == 'confirmed')
		for order in orders_to_plan:
			quantity = order.product_uom_id._compute_quantity(order.product_qty,
															  order.bom_id.product_uom_id) / order.bom_id.product_qty
			boms, lines = order.bom_id.explode(order.product_id, quantity, picking_type=order.bom_id.picking_type_id)
			order._generate_workorders(boms)
			finished_move = self.move_finished_ids.filtered(
				lambda x: x.product_id == self.product_id and x.state in ('progress') and x.quantity_done > 0)

			for finished in finished_move:
				picking_obj = self.env['stock.picking']
				picking_type = self.env['stock.picking.type'].search(
					[('default_location_dest_id', '=', finished.location_dest_id.id), ('code', '=', 'incoming')])
				picking = picking_obj.create(
					{'picking_type_id': picking_type.id, 'location_id': finished.location_id.id,
					 'location_dest_id': finished.location_dest_id.id
						, 'move_ids_without_package': finished})
		orders_to_plan.write({'state': 'planned'})


	@api.multi
	def button_mark_done(self):

		self.ensure_one()
		for wo in self.workorder_ids:
			if wo.time_ids.filtered(lambda x: (not x.date_end) and (x.loss_type in ('productive', 'performance'))):
				raise UserError(_('Work order %s is still running') % wo.name)
		self.post_inventory()
		moves_to_cancel = (self.move_raw_ids | self.move_finished_ids).filtered(
			lambda x: x.state not in ('done', 'cancel'))
		self.write({'state': 'done', 'date_finished': fields.Datetime.now()})
		finished_move = self.move_finished_ids.filtered(
			lambda x: x.product_id == self.product_id and x.state in ('done') and x.quantity_done > 0)

		for finished in finished_move:
			picking_obj = self.env['stock.picking']
			picking_type = self.env['stock.picking.type'].search(
				[('default_location_dest_id', '=', finished.location_dest_id.id), ('code', '=', 'incoming')])
			picking = picking_obj.create({'picking_type_id': picking_type.id, 'location_id': finished.location_id.id,
										  'location_dest_id': finished.location_dest_id.id
											 , 'move_ids_without_package': finished})
			finished.picking_id = picking.id
			date_name = datetime.strptime(str(datetime.today().date()), '%Y-%m-%d')
			date_in_words = datetime.strftime(date_name, "%A")
			#
			# if date_in_words == 'Friday':
			# 	if self.date_planned_start.hour + 2 == 24 and self.date_planned_start.minute == 0 and self.date_planned_start.second == 0:
			# 		sequence = self.env['ir.sequence'].search([(
			# 			'code', '=', 'samil_blend.sequence',
			# 		)], limit=1)
			# 		sequence.write({'number_next_actual': 1})
			# 		# pre-blend
			# 		pre_sequence = self.env['ir.sequence'].search([(
			# 			'code', '=', 'samil.preblend.sequence',
			# 		)], limit=1)
			# 		pre_sequence.write({'number_next_actual': 1})
			return self.write({'state': 'done'})

	cost_ids = fields.One2many('manufacturing.cost.line', 'cost_id', 'Production')
	shift_id = fields.Many2one('mrp.adjustment', 'Shift')
	customer_id = fields.Many2one('res.partner', 'Customer')
	# adjustment_id = fields.Many2one('mrp.adjustment', 'Adjustment')
	unit_cost = fields.Float('Unit Cost', compute='compute_cost', store=True)
	cost_mrp = fields.Float('Mrp Cost')
	real_qty = fields.Float('Actual Quantity', compute='compute_real_qty', store=True)
	# cost_additional = fields.Float('Cost additional',compute='_shift_count',  store=True)
	cost_additional = fields.Float('Additional Cost', compute='_shift_count', store=True)
	blend = fields.Boolean('Blend', store=True)
	pre_blend = fields.Boolean('Pre Blend', store=True)
	date = fields.Date('Deadline Start', default=fields.Date.today(), readonly=True)

	@api.onchange('product_id')
	def _onchange_product_id(self):
	    self.cost_mrp = self.product_id.cost_mrp

	@api.depends('move_finished_ids')
	@api.one
	def compute_cost(self):
		if self.move_finished_ids:
			finished_move = self.move_finished_ids.filtered(
				lambda x: x.product_id == self.product_id and x.state in ('done') and x.quantity_done > 0)
			for move in finished_move:
			    self.unit_cost = move.price_unit

	@api.multi
	@api.depends('quantity', 'price')
	def compute_price(self):
		for rec in self:
			rec.total = rec.price * rec.quantity

	@api.multi
	@api.depends('cost_additional', 'unit_cost')
	def compute_real_qty(self):
		for rec in self:
			rec.real_qty = rec.cost_additional + rec.unit_cost

	@api.depends('shift_id.total')
	def _shift_count(self):
		for rec in self:
			total = 0
			cost_additional = rec.shift_id.total
		rec.cost_additional = cost_additional

	# rec.write({'cost_additional': cost_additional})
	# @api.onchange('shift_id')
	# def _onchange_shift_id(self):
	# 	for rec in self:

	# @api.one
	# def _shift_count(self):
	# 	for rec in self:
	#
	# 		shift = self.env['mrp.adjustment'].search([('name', '=', rec.shift_id)])
	# 		print(shift, 'shift',rec.shift_id.name,rec.name,)
	# 		for obj in shift:
	# 			total = obj.total
	# 			name = obj.name
	# 			print(name, 'name')
	# 			print(total, 'total')
	# 		self.cost_additional = total
	# @api.multi
	# def _shift_count(self):
	# 	for each in self:
	# 		shift = self.env['mrp.adjustment'].search([('name', '=', self.shift_id.id)])
	# 		for obj in shift:
	# 			self.cost_additional = obj.total


class ManufacturingCostLine(models.Model):
	_name = 'manufacturing.cost.line'

	cost_id = fields.Many2one('mrp.production', 'Worker')
	quantity = fields.Float('Quantity')
	total = fields.Float('Total', compute="compute_price", store=True)
	price = fields.Float('Price')

	@api.multi
	@api.depends('quantity', 'price')
	def compute_price(self):
		for rec in self:
			rec.total = rec.price * rec.quantity




class ProductProduct(models.Model):
    _name = 'product.product'
    _inherit = 'product.product'

