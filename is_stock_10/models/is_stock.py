import datetime
import logging
import re
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
import uuid
from collections import Counter, OrderedDict
from itertools import product
from werkzeug import urls
import dateutil.parser


from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError
email_validator = re.compile(r"[^@]+@[^@]+\.[^@]+")
_logger = logging.getLogger(__name__)


class productquantity(models.Model):
    _name= 'product.quantity.state'

    def check_product_domain(self):
        for x in self:
            products = []
            qtyi_ids = self.env[' '].search([('picking_id.id', '=', x.operation_id.id)])
            for y in qtyi_ids:
                products.append(y.product_id.id)
                print(products,'ul')
            res={}
            res['domain']={'product_id':[('id', 'in', products)]}


    name = fields.Char('Qantity')
    serial_no = fields.Char('Serial Number')
    product_id = fields.Many2one('product.product', string="Product", required=True)
    product_quantity = fields.Integer('Quantity', required=True)
    product_price = fields.Float('Price')
    tax_id = fields.Float('Taxes',default=17)
    after_price = fields.Float('Taxed Amount',compute="compute_tax",store=True)
    product_state = fields.Many2one('res.country.state',string="State", required=True)
    city = fields.Many2one('city.state',string='City', required=True,domain="[('state_id.id','=',product_state)]")
    operation_id = fields.Many2one('stock.picking',string='operation')
    stock_move_id = fields.Many2one('stock.move',string='operation')
    partner_id = fields.Many2one('res.partner', string='Customer' , required=True,)

    @api.depends('product_price', 'tax_id')
    def compute_tax(self):
        for x in self:
            price_tax = 0.0
            taxes_is = 0.0
            taxes = x.tax_id
            price_after = x.product_price
            qty = x.product_quantity
            qty_price = qty * price_after
            price_tax = qty_price * (taxes / 100.0)
            taxes_is = qty_price + price_tax
            x.after_price = taxes_is


class CityState(models.Model):
    _name = 'city.state'

    name = fields.Char('City')
    city_code = fields.Char('Code')
    state_id = fields.Many2one('res.country.state',string='State')

class stockpicking(models.Model):
    _inherit = 'stock.picking'

    quantity_picking_ids = fields.One2many('product.quantity.state','operation_id',string="Quantity Picking")
    picking_type_name = fields.Char(related='picking_type_id.name',string="Picking")
    picking_type_custom = fields.Selection(related='picking_type_id.code',string="Picking")

    @api.multi
    def do_new_transfer(self):
        for pick in self:
            if not pick.quantity_picking_ids and self.picking_type_custom == 'outgoing':
                raise UserError(_('Place Create The Shipment for Pickings'))
            if pick.state == 'done':
                raise UserError(_('The pick is already validated'))
            pack_operations_delete = self.env['stock.pack.operation']
            if not pick.move_lines and not pick.pack_operation_ids:
                raise UserError(_('Please create some Initial Demand or Mark as Todo and create some Operations. '))
            # In draft or with no pack operations edited yet, ask if we can just do everything
            if pick.state == 'draft' or all([x.qty_done == 0.0 for x in pick.pack_operation_ids]):
                # If no lots when needed, raise error
                picking_type = pick.picking_type_id
                if (picking_type.use_create_lots or picking_type.use_existing_lots):
                    for pack in pick.pack_operation_ids:
                        if pack.product_id and pack.product_id.tracking != 'none':
                            raise UserError(_('Some products require lots/serial numbers, so you need to specify those first!'))
                view = self.env.ref('stock.view_immediate_transfer')
                wiz = self.env['stock.immediate.transfer'].create({'pick_id': pick.id})
                # TDE FIXME: a return in a loop, what a good idea. Really.
                return {
                    'name': _('Immediate Transfer?'),
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'stock.immediate.transfer',
                    'views': [(view.id, 'form')],
                    'view_id': view.id,
                    'target': 'new',
                    'res_id': wiz.id,
                    'context': self.env.context,
                }

            # Check backorder should check for other barcodes
            if pick.check_backorder():
                view = self.env.ref('stock.view_backorder_confirmation')
                wiz = self.env['stock.backorder.confirmation'].create({'pick_id': pick.id})
                # TDE FIXME: same reamrk as above actually
                return {
                    'name': _('Create Backorder?'),
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'stock.backorder.confirmation',
                    'views': [(view.id, 'form')],
                    'view_id': view.id,
                    'target': 'new',
                    'res_id': wiz.id,
                    'context': self.env.context,
                }
            for operation in pick.pack_operation_ids:
                if operation.qty_done < 0:
                    raise UserError(_('No negative quantities allowed'))
                if operation.qty_done > 0:
                    operation.write({'product_qty': operation.qty_done})
                else:
                    pack_operations_delete |= operation
            if pack_operations_delete:
                pack_operations_delete.unlink()


        self.do_transfer()
        return


    @api.constrains('quantity_picking_ids')
    def check_qty(self):
        for x in self:
            if x.state == 'assigned':
                quantity = 0.0
                for rec in x.quantity_picking_ids:
                    quantity += rec.product_quantity
                    price = rec.product_price
                    product_quantity_picking = rec.product_id.name
                qty = self.env['stock.move'].search([('picking_id', '=', x.id)])
                qty_done = 0.0
                for rec in qty:
                    qty_done += rec.product_uom_qty
                    product = rec.product_id.name
                if self.picking_type_custom =='outgoing':
                    if quantity > qty_done or quantity < qty_done:
                        raise Warning(_('he Quantity You Enter  if it Bigger OR Smaller Than Approved Quantity.'))
                    if product != product_quantity_picking:
                        raise Warning(_('The Product You Enter Not equal product Approved'))
                    if price <= 0:
                        raise Warning(_('Place Enter Price'))












