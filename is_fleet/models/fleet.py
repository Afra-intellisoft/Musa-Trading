# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
from datetime import datetime,date
import odoo.addons.decimal_precision as dp
from odoo.tools.float_utils import float_is_zero, float_compare
import calendar
from datetime import datetime,date


class FleetVehicle(models.Model):
    _name = 'fleet.vehicle'
    _inherit = 'fleet.vehicle'

    name = fields.Char(string='Name')
    max_odometer = fields.Float(string='Max Odometer')
    employee_id = fields.Many2one('hr.employee', string="Driver")
    allowed_driver = fields.Boolean('Allowed Driver go to home')




    # @api.one
    # @api.constrains('vehicle_id','max_odometer')
    # def max_odometer(self):
    #     for vehicle in self:
    #         max_odometer = vehicle.max_odometer
    #         date_year = vehicle.date.year
    #         print(date_year, 'year')
    #         vehicle = self.search(
    #             [('vehicle_id', '=', self.vehicle_id)])
    #         print(vehicle, 'vehicle')
    #         for rec in vehicle:
    #             date_vehicle = rec.date
    #             if date_vehicle.month == date_month and date_vehicle.year == date_year:
    #                 count += 1
    #         if count >= 2:
    #             raise Warning(_(
    #                 "This employee must complete payments for a current running loan, in order to request another"))
	#
class FleetVehicleCost(models.Model):
    _name = 'fleet.vehicle.cost'
    _inherit = 'fleet.vehicle.cost'

    product_id = fields.Many2one('product.product','Product Service')
    quantity = fields.Float('Quantity')
    price = fields.Float('Price')
    total = fields.Float('Total', compute="compute_total", store=True)
    note = fields.Text('Note')
    uom_id = fields.Many2one('product.uom','Product Uom')
    account_id = fields.Many2one('account.account', 'Account')
    vendor_id = fields.Many2one('res.partner', 'Vendor')

    @api.multi
    @api.depends('price', 'quantity')
    def compute_total(self):
        for rec in self:
            rec.total = rec.price * rec.quantity



    @api.onchange('product_id')
    def _onchange_product_id(self):
        self.uom_id = self.product_id.uom_id.id
        self.account_id = self.product_id.property_account_expense_id.id



class FleetVehicleLogServices(models.Model):
    _name = 'fleet.vehicle.log.services'
    _inherit = 'fleet.vehicle.log.services'


    def _default_user(self):
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

    attach = fields.Binary("Attachment File", required=True)
    user_id = fields.Many2one('hr.employee', string="User",required=True,translate=True,default=_default_user)
    requisition_id = fields.Many2one('purchase.requisition', string="requisition")
    name = fields.Char(string='Name')
    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')
    request = fields.Boolean('request')
    state = fields.Selection([('draft', 'Draft'), ('send', 'Send Request'), ('approve', 'Approve'), ('purchases', 'Purchase Agreemented'), ('request', 'Material Requested'), ('invoice', 'Invoice Requested')],
                             string='Custody Clearance Status', default='draft')

    @api.multi
    def unlink(self):
        for x in self:
            if any(x.filtered(lambda FleetVehicleLogServices: FleetVehicleLogServices.state not in ('draft', 'refuse'))):
                raise UserError(_('You cannot delete a Loan which is not draft or refused!'))
            return super(FleetVehicleLogServices, x).unlink()

    @api.one
    def order_send(self):
      self.state = 'send'

    @api.one
    def order_approve(self):
      self.state = 'approve'

    @api.one
    def order_stock(self):
        material_obj = self.env['material.request']
        # self.material = True
        material_vals = {
            'state': 'draft',
            'applicant_name': self.user_id.id,
        }
        request_id = material_obj.create(material_vals)
        for obj in self.cost_ids:
            product_id = obj.product_id.id
            quantity = obj.quantity
        # self.request_id = request_id.id
        material_order_lines_vals = {'request_id': request_id.id,
                                     'product_id': product_id,
                                     'ordered_qty': quantity,
                                     }
        line = self.env['material.request.line']
        line.create(material_order_lines_vals)
        self.state = 'request'
    @api.one
    def order_purchases(self):
        purchase_obj = self.env['purchase.requisition']
        material_vals = {
            'state': 'draft',
            'description': self.notes,
            'user_id': self.user_id.id,
        }

        request_id = purchase_obj.create(material_vals)
        for service in self.cost_ids:
            # name= service.cost_subtype_id.id
            product= service.product_id.id
            material_order_lines_vals = {'requisition_id': request_id.id,
                                         # 'product_id': service.cost_subtype_id.id,
                                         'product_qty': service.quantity,
                                         'product_id': product,
                                         'product_uom_id': service.uom_id.id,
                                         # 'name': service.cost_subtype_id.id,
                                         }
            line = self.env['purchase.requisition.line']
            line.create(material_order_lines_vals)
            self.state = 'purchases'

    @api.one
    def account_validate(self):
        invoice_obj = self.env['account.invoice']
        self.request = True
        account_invoice_vals = {
            'type': 'out_invoice',
            'state': 'draft',
            'partner_id': self.vendor_id.id,
        }
        invoice_id = invoice_obj.create(account_invoice_vals)
        if not self.vendor_id:
            raise UserError('Please Enter Vendor')
        for service in self.cost_ids:
            sale_order_lines_vals = {'invoice_id': invoice_id.id,
                                     'product_id': service.product_id.id,
                                     'quantity': service.quantity,
                                     'account_id': service.account_id.id,
                                     'price_unit': service.amount,
                                     'name': service.product_id.name,
                                     'discount': 0.0,
                                     }
            line = self.env['account.invoice.line']
            line.create(sale_order_lines_vals)
            self.state = 'invoice'
class FleetVehicleLogFuel(models.Model):
    _name = 'fleet.vehicle.log.fuel'
    _inherit = {'fleet.vehicle.log.fuel','mail.thread'}


    def _default_user(self):
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

    product_id = fields.Many2one('product.product',string='Product')
    user_id = fields.Many2one('hr.employee', string="User",required=True,translate=True,default=_default_user)
    material = fields.Boolean('Material Request')
    request_id = fields.Many2one('material.request', string='Purchase Agreement', ondelete='cascade',translate=True)
    request = fields.Boolean('Request')
    next_date = fields.Date('Next Date Change Fuel')
    state = fields.Selection([('draft', 'Draft'), ('done', 'Request done')],
                             string='Custody Clearance Status', default='draft')

    @api.one
    def material_request(self):
        material_obj = self.env['material.request']
        self.material = True
        material_vals = {
            'state': 'draft',
            'applicant_name': self.user_id.id,
        }

        request_id = material_obj.create(material_vals)
        self.request_id = request_id.id
        material_order_lines_vals = {'request_id': request_id.id,
                                     'product_id': self.product_id.id,
                                     'ordered_qty': self.liter,
                                     }
        line = self.env['material.request.line']
        line.create(material_order_lines_vals)
        self.state = 'done'

    # @api.model
    # def compute_mail_activity(self):
    #     current_date = fields.Date.today()
    #     contracts = self.search([])
    #     for x in contracts:
    #         name = x.product_id.name
    #         date_rr = x.next_date
    #         if date_rr == current_date:
    #            print(date_rr,'date_rr')
    #            print(current_date,'current_date')
    #             # d = dateutil.parser.parse(date_rr).date()
    #             # if date_rr == current_date:
    #            # print(d,current_date)
    #            user_ids = self.env['mail.channel'].search([('name','=','Administration')])
    #            subtype_id = self.env['mail.message.subtype'].search([('name','=','Discussions')]).id
    #            mail_message_vals = {'message_type':'comment',
    #                                'body':'the product'+ ' ' + name+' '+'will expirtion' + ' ' + date_rr,
    #                                'res_id': x.id,
    #                                'subtype_id': subtype_id,
    #                                'model':'mail.channel',
    #                                'channel_ids':[(6,0,user_ids.ids)],
    #                                'record_name': name,
    #                                 }
    #     self.env['mail.message'].create(mail_message_vals)
    #     print(mail_message_vals,'mail_message_vals')

        # else:
        #     print('kkkkkkkkkkkkkkkkkkkkkkkkkkkk')

class FleetVehicleOdometer(models.Model):
    _name = 'fleet.vehicle.odometer'
    _inherit = 'fleet.vehicle.odometer'
    # @api.one
    # @api.constrains('vehicle_id')
    # def get_vehicle(self):
    #     test =  self.value
    #     print(test,'test')
    #     for rec in self:
    #         value =+ rec.value
    #         max_odometer = rec.vehicle_id.max_odometer
    #         print(max_odometer,'max')
    #         print(value,'value')
    #         if value >= max_odometer:
    #             raise Warning(_(
    #                         "This employee must complete payments for a current running loan, in order to request another"))


    @api.constrains('vehicle_id')
    def get_vehicle(self):
        value = 0.0
        for fleet in self:
            if fleet.vehicle_id:
                fleet_id = fleet.env['fleet.vehicle.odometer'].search(
                    [('vehicle_id', '=', fleet.vehicle_id.id)])
                for rec in fleet_id:
                    max_odometer = rec.vehicle_id.max_odometer
                    value += rec.value
                    if max_odometer < value :
                        raise UserError('You have exceeded distance allowed')



class AccountInvoiceLine(models.Model):
    _name = 'account.invoice.line'
    _inherit = 'account.invoice.line'

    order_line_id = fields.Many2one('fleet.maintenance.order.line',string='Order')
	#
    # @api.one
    # @api.constrains('vehicle_id')
    # def _constrains_vehicle(self):
    #     for vehicle in self:
    #         count = 0
    #         date_month = str(vehicle.date.month)
    #         print(date_month, 'monthhhh')
    #         date_year = vehicle.date.year
    #         print(date_year, 'year')
    #         vehicle = self.search(
    #             [('vehicle_id', '=', self.vehicle_id)])
    #         print(vehicle, 'vehicle')
    #         for rec in vehicle:
    #             date_vehicle = rec.date
    #             if date_vehicle.month == date_month and date_vehicle.year == date_year:
    #                 count += 1
    #         if count >= 2:
    #             raise Warning(_(
    #               maintenance  "This employee must complete payments for a current running loan, in order to request another"))
class FleetJMaintenanceOrder(models.Model):
  _name="fleet.maintenance.order"
  _description = 'Create a Maintenance order'
  _rec_name = 'main_no'

  main_no = fields.Char('Maintenance No.', help='Auto-generated Maintenance No. for Maintenance Order', readonly=True,track_visibility='onchange')
  note = fields.Text('Details')
  driver_id = fields.Many2one('hr.employee', string="Driver")
  order_ids = fields.One2many('fleet.maintenance.order.line','order_id', string="Order Line")
  license_plate = fields.Char(string=" License plate ")
  request = fields.Boolean('Request')
  vehicle_id = fields.Many2one('fleet.vehicle', string="Vehicle", required=True, help="Vehicle",track_visibility='onchange')
  image = fields.Binary(related='vehicle_id.image', string="Image of Vehicle",track_visibility='onchange')
  image_medium = fields.Binary(related='vehicle_id.image_medium', string="Logo (medium)",track_visibility='onchange')
  name = fields.Char(string="Name", default="Maintenance Order", readonly=True, copy=False,track_visibility='onchange')
  customer_id = fields.Many2one('res.partner', 'Customer', required=True, store=True, track_visibility='onchange')
  start_date = fields.Datetime('Start Date', track_visibility='onchange')
  end_date = fields.Datetime('End Date', track_visibility='onchange')
  main_date = fields.Date("Date Order", readonly="True",default=fields.date.today())
  days_left = fields.Float('Days Left', readonly="True", compute="compute_days_left", track_visibility='onchange')
  company_id = fields.Many2one(
       'res.company',
       'Company',
       default=lambda self: self.env['res.company']._company_default_get('maintenance.order') ,required=True
   ,track_visibility='onchange')
  state = fields.Selection([('draft', 'Draft'), ('submit', 'Submitted'),('approval','Approve'),('progress', 'In Progress'),('done','Done')],string="State",
                                  default='draft',track_visibility='onchange')


  contracts_count = fields.Integer(compute='_compute_contracts_count', string='Contracts')

  def _compute_contracts_count(self):
      contract_data = self.env['account.invoice'].sudo().read_group([('customer_id', 'in', self.ids)], ['customer_id'],
                                                                ['customer_id'])
      result = dict((data['customer_id'][0], data['customer_id_count']) for data in contract_data)
      for employee in self:
          employee.contracts_count = result.get(employee.id, 0)



  @api.multi
  @api.onchange('vehicle_id')
  def get_type(self):
      if self.vehicle_id:
         self.license_plate = self.vehicle_id.license_plate
         self.driver_id = self.vehicle_id.employee_id


  @api.one
  def order_submit(self):
      self.state = 'submit'

  @api.one
  def order_approval(self):
      self.state = 'approval'

  @api.one
  def order_progress(self):
      self.state = 'progress'

  @api.one
  def order_done(self):
      self.state = 'done'



  @api.model
  def create(self, vals):
      res = super(FleetJMaintenanceOrder, self).create(vals)
      next_seq = self.env['ir.sequence'].get('workshop.maintenance.order.no')
      res.update({'main_no': next_seq})
      return res

  @api.model
  def compute_days_left(self):
      for order_ids in self.search([]):
          for order in order_ids:
              today_time = datetime.strptime(str(fields.datetime.today()), '%Y-%m-%d %H:%M:%S.%f')
              myFormat = "%Y-%m-%d %H:%M:%S"
              today_time.strftime(myFormat)
              if order.end_date:
                  end_date = datetime.strptime(str(order.end_date), '%Y-%m-%d %H:%M:%S')
                  order.days_left = (end_date - today_time).days


  @api.one
  def account_validate(self):
            invoice_obj = self.env['account.invoice']
            self.request = True
            account_invoice_vals = {
                'type': 'out_invoice',
                'state': 'draft',
                'partner_id': self.customer_id.id,
            }
            invoice_id = invoice_obj.create(account_invoice_vals)
            if not self.customer_id:
                raise UserError('Please Enter vendor')
            for service in self.order_ids:
                sale_order_lines_vals = {'invoice_id': invoice_id.id,
                                         'product_id': service.product_id.id,
                                         'quantity': service.quantity,
                                         'name': service.name,
                                         'account_id': service.account_id.id,
                                         'price_unit': service.price,
                                         'discount': 0.0,
                                         }
                line = self.env['account.invoice.line']
                line.create(sale_order_lines_vals)



class FleetJMaintenanceOrderLine(models.Model):
    _name = 'fleet.maintenance.order.line'
    # rec_name ='name'

    # @api.depends('invoice_lines.invoice_id.state')
    # def _compute_qty_invoiced(self):
    #     for line in self:
    #         qty = 0.0
    #         for inv_line in line.invoice_lines:
    #             if inv_line.invoice_id.state not in ['cancel']:
    #                 if inv_line.invoice_id.type == 'in_invoice':
    #                     qty += inv_line.uom_id._compute_quantity(inv_line.quantity, line.product_uom)
    #                 elif inv_line.invoice_id.type == 'in_refund':
    #                     qty -= inv_line.uom_id._compute_quantity(inv_line.quantity, line.product_uom)
    #         line.qty_invoiced = qty

    name = fields.Char(string="Description")
    product_id = fields.Many2one('product.product' ,'Product')
    account_id = fields.Many2one('account.account' ,'Account')
    product_uom = fields.Many2one('product.uom' ,'Product Uom')
    order_id = fields.Many2one('fleet.maintenance.order')
    price = fields.Float(string="Price")
    quantity = fields.Float(string="Quantity")
    price_install = fields.Float(string="Price Install")
    total = fields.Float(string="Total",compute="compute_total", store=True)
    # invoice_lines = fields.One2many('account.invoice.line', 'order_line_id', string="Bill Lines", readonly=True,
    #                                 copy=False)
    # qty_invoiced = fields.Float(compute='_compute_qty_invoiced', string="Billed Qty",
    #                             digits=dp.get_precision('Product Unit of Measure'), store=True)
    # main_date = fields.Date("Date Maintenance", readonly="True")

    @api.multi
    @api.depends('price', 'price_install')
    def compute_total(self):
        for rec in self:
            if rec.price:
                rec.total = rec.price + rec.price_install

    @api.onchange('product_id')
    def _onchange_product_id(self):
        self.name = self.product_id.name
        self.product_uom = self.product_id.uom_id
        self.price = self.product_id.lst_price
        self.account_id = self.product_id.property_account_expense_id.id

