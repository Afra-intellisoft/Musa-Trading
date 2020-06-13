from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError, Warning
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_is_zero, float_compare
from odoo.exceptions import UserError, AccessError
from odoo.tools.misc import formatLang
from odoo.addons.base.res.res_partner import WARNING_MESSAGE, WARNING_HELP
import odoo.addons.decimal_precision as dp
class Respartner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    custom_supplier = fields.Boolean('Supplier')

    @api.onchange('also_supplier')
    def get_supplier(self):
        if not self.also_supplier == False:
            raise UserError(_("This Vendor Has Supplier ?"))

class PurchaseOrder(models.Model):
    _name = 'purchase.order'
    _inherit = 'purchase.order'

    purchase_type = fields.Selection([('internal', 'Internal Purchase') ,('external', 'External Purchase')], string='Purchases Type',default='internal')
    contract = fields.Boolean('Contract Request')
    note = fields.Text('Note')
    customs_id = fields.Many2one('customs.clearance', string="Reference")


    # @api.one
    # def contract_request(self):
    #     import_obj = self.env['purchase.contract']
    #     self.contract = True
    #     contract_vals = {
    #         'state': 'draft',
    #         'reference': self.id,
    #         'date': self.date_order,
    #         'vendor_id': self.partner_id.id,
    #         'currency_id': self.currency_id.id,
    #     }
    #
    #     request_id = import_obj.create(contract_vals)
    #     for service in self.order_line:
    #         order_lines_vals = {'line_id': request_id.id,
    #                             'product_id': service.product_id.id,
    #                             'value_weight': service.weight,
    #                             'total': service.price_subtotal,
    #                             'product_qty': service.product_qty,
    #                             'product_uom_qty': service.product_uom.id,
    #                             'price': service.price_unit,
    #                             }
    #         line = self.env['purchase.contract.line']
    #         line.create(order_lines_vals)

class AccountInvoiceLine(models.Model):
    _name = 'account.invoice.line'
    _inherit = 'account.invoice.line'

    contract_id = fields.Many2one('purchase.contract.line','Line')


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'
    _name = 'account.invoice'

    contract_id = fields.Many2one('purchase.contract', string='Add Contract Order',)

    @api.onchange('state', 'partner_id', 'invoice_line_ids')
    def _onchange_allowed_contract_ids(self):
        '''
		The purpose of the method is to define a domain for the available
		purchase orders.
		'''
        result = {}

        # A PO can be selected only if at least one PO line is not already in the invoice
        contract_line_ids = self.invoice_line_ids.mapped('contract_id')
        contract_ids = self.invoice_line_ids.mapped('contract_id').filtered(lambda r: r.line_ids <= contract_line_ids)

        result['domain'] = {'contract_id': [
            ('invoice_status', '=', 'to invoice'),
            ('partner_id', 'child_of', self.partner_id.id),
            ('id', 'not in', contract_ids.ids),
        ]}
        return result

    @api.onchange('contract_id')
    def contract_change(self):
        if not self.contract_id:
            return {}
        if not self.partner_id:
            self.partner_id = self.contract_id.vendor_id.id

        new_lines = self.env['account.invoice.line']
        for line in self.contract_id.line_ids:
            # Load a PO line only once
            if line in self.invoice_line_ids.mapped('contract_id'):
                continue
            data = self._prepare_invoice_line_from_po_line(line)
            new_line = new_lines.new(data)
            new_line._set_additional_fields(self)
            new_lines += new_line

        self.invoice_line_ids += new_lines
        self.contract_id = False
        return {}

class PurchaseOrderLine(models.Model):
    _name = 'purchase.order.line'
    _inherit = 'purchase.order.line'

    @api.multi
    @api.depends('value_weight','product_qty')
    def compute_count_weight(self):
        for rec in self:
            rec.weight = rec.value_weight * rec.product_qty


    @api.depends('product_qty', 'price_unit', 'taxes_id')
    def _compute_amount(self):
        for line in self:
            if line.order_id.purchase_type == 'internal':
                taxes = line.taxes_id.compute_all(line.price_unit, line.order_id.currency_id, line.product_qty, product=line.product_id, partner=line.order_id.partner_id)
                line.update({
                    'price_tax': taxes['total_included'] - taxes['total_excluded'],
                    'price_total': taxes['total_included'],
                    'price_subtotal':line.price_unit*line.product_qty,
                })
            if line.order_id.purchase_type == 'external':
                taxes = line.taxes_id.compute_all(line.price_unit, line.order_id.currency_id, line.weight,
                                                  product=line.product_id, partner=line.order_id.partner_id)
                line.update({
                    'price_tax': taxes['total_included'] - taxes['total_excluded'],
                    'price_total': taxes['total_included'],
                    'price_subtotal':line.price_unit*line.weight,
                })

    weight = fields.Float('Weight', compute="compute_count_weight", store=True)
    value_weight = fields.Float('Value Weight')
    new_price = fields.Float('Price Doc')
    # price_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal', store=True)
    #
    # @api.depends('weight', 'price_unit', 'taxes_id','product_qty',)
    # def _compute_amount(self):
    #     for line in self:
    #         taxes = line.taxes_id.compute_all(line.price_unit, line.order_id.currency_id, line.weight, product=line.product_id, partner=line.order_id.partner_id)
    #         if line.product_id.agricultural != False:
    #             weight = line.weight
    #             total = weight * line.price_unit
    #             line.update({
    #                 'price_tax': taxes['total_included'] - taxes['total_excluded'],
    #                 'price_total': taxes['total_included'],
    #                 'price_subtotal': taxes['total_excluded'],
    #                 'price_subtotal': taxes['total'],
    #             })

    @api.onchange('product_id')
    def _onchange_product_id(self):
        self.value_weight = self.product_id.weight

class PurchaseContract(models.Model):
    _name = 'purchase.contract'

    @api.model
    def create(self, vals):


        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('purchase.contract') or '/'
        price = 0
        # for line in self.line_ids:
        #     price = line.price
        #     product_id = line.product_id.name
        #     print(price, 'price')
        #     print(product_id, 'product_id')
        #     if price == 0:
        #
        #
        #         print(self.line_ids,'self.line_ids.price')
        #     # raise UserError(_('There are Remaining qty %s'))
        #     raise Warning(_("period can't exceed 10 months"))

        return super(PurchaseContract, self).create(vals)

    @api.constrains('line_ids')
    def request_amount_validation(self):
        for line in self.line_ids:
            price = line.price
            product_qty = line.product_qty
            if price <= 0:
                raise Warning(_("Price Must be greater than zero!"))
            if product_qty <= 0:
                raise Warning(_("Quantity Must be greater than zero!"))

    def _get_default_company_id(self):
        return self._context.get('force_company', self.env.user.company_id.id)

    company_id = fields.Many2one('res.company', string='Company',
                                 default=_get_default_company_id)
    name = fields.Char('Contract', readonly=True)
    purchase_count = fields.Integer(compute='_compute_orders_number', string='Count', default=0, store=True, )
    invoice = fields.Char('Invoice Reference')
    reference = fields.Many2one('purchase.order','Reference', readonly=True)
    clearance_ids = fields.One2many('customs.clearance','contract_id','Reference')
    note = fields.Text('Note')
    date_invoice = fields.Date('Date Invoice')
    delivery_location = fields.Char('Delivery Location')
    date = fields.Date('Date' ,default=fields.Date.today(), readonly=True)
    vendor_id = fields.Many2one('res.partner', string='Vendor')
    currency_id = fields.Many2one('res.currency', string='Currency')
    date_from = fields.Date('Date From')
    date_to = fields.Date('Date To')
    line_ids = fields.One2many('purchase.contract.line','line_id',string='Contract')
    clearance = fields.Boolean('Clearance Request')
    state = fields.Selection([
            ('draft', 'New'),
            ('open', 'Running'),
            ('start_clearance', 'Start Clearance'),
            ('close', 'Expired'),
        ], string='Status', track_visibility='onchange', help='Status of the contract', default='draft')

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise Warning(_("Warning! You cannot delete a Purchase Contract which is in %s state.") % (rec.state))
            return super(PurchaseContract, self).unlink()

    @api.depends('clearance_ids')
    def _compute_orders_number(self):
        for rec in self:
            rec.purchase_count = len(rec.clearance_ids)




    # @api.one
    # def clearance_request(self):
    #     import_obj = self.env['customs.clearance']
    #     self.clearance = True
    #     contract_vals = {
    #         'state': 'draft',
    #         'partner_id': self.vendor_id.id,
    #         'contract_id': self.id,
    #     }
    #     request_id = import_obj.create(contract_vals)
    #     line_ids = self.line_ids
    #     for service in line_ids:
    #         order_lines_vals = {'clearance_id': request_id.id,
    #                             'product_id': service.product_id.id,
    #                             'weight': service.value_weight,
    #                             'product_qty': service.product_qty,
    #                             'product_uom_qty': service.product_uom_qty.id,
    #                             # 'price': service.price,
    #                             # 'total': service.total,
    #                             }
    #         line = self.env['purchase.contract.line']
    #         line.create(order_lines_vals)
    #         self.state = 'start_clearance'

    #
    @api.one
    def agriculture_request(self):
        line_ids = self.line_ids
        name = self.id
        for line in line_ids:
            product_name = line.product_id.name
            weight = line.weight
            if line.product_id.agriculture_id.id:
                form_ids = self.env['purchase.contract.line'].search(
                    [('product_id.agriculture_id', '=', line.product_id.agriculture_id.id),('cultivate_id.state', '!=', 'close'),
                     ('expired_agricultural', '=', False), ('qty_remaining', '>', 0.0)])
                if not form_ids:
                    raise Warning(
                        _("This product has no enough quantity approved %s") % line.product_id.name)
                total_qty = 0.0
                for obj in form_ids:
                    total_qty += obj.qty_remaining
                for form in form_ids:
                    form.contract_form_id = name
                    qty_remaining = form.qty_remaining
                    other_qty = 0.0
                    if weight > total_qty:
                        qty = weight - total_qty
                        raise UserError(_('There are Remaining qty %s') % (qty))
                    else:
                        if weight <= qty_remaining:
                            # form.line_id = self.id
                            form.qty_consumed += weight
                            form.qty_contract = weight
                            # form.product_id = form.product_id.name
                            # if form.qty_consumed == form.qty_approve:
                            #     form.expired = True
                            break
                        if weight > qty_remaining:
                            other_qty = weight - qty_remaining
                            form.qty_consumed += qty_remaining
                            form.qty_contract = qty_remaining
                            # form.product_id = form.product_id.name
                            # if form.qty_consumed == form.qty_approve:
                            #     form.expired = True

                    weight = other_qty
        # xyz = form_ids[-1].cultivate_id
        # if any(test.expired_agricultural == True for test in form_ids):
        #     xyz.state = 'close'

        self.state = 'open'



class PurchaseContractLine(models.Model):
    _name = 'purchase.contract.line'

    @api.onchange('total_qty_supplier')
    def _onchange_total(self):
        self.qty_supplier = self.total_qty_supplier

    @api.onchange('product_id')
    def _onchange_product_id(self):
        self.value_weight = self.product_id.weight
        self.product_uom_qty = self.product_id.uom_id.id

    @api.multi
    @api.depends('value_weight','product_qty')
    def compute_weight(self):
        for rec in self:
            rec.weight = rec.value_weight * rec.product_qty

    @api.multi
    @api.depends('weight','price')
    def compute_total(self):
        for rec in self:
            rec.total = rec.price * rec.weight
    @api.multi
    @api.depends('weight','price','commission')
    def compute_total_supplier(self):
        for rec in self:
            rec.total_qty_supplier  = (rec.price +rec.commission )* rec.weight

    @api.multi
    @api.depends('product_qty', 'qty_done')
    def compute_qty_custom(self):
        for rec in self:
            rec.qty_custom = rec.product_qty - rec.qty_done

    @api.multi
    @api.depends('qty_consumed','price')
    def compute_total_qty(self):
        for rec in self:
            rec.total_qty = rec.price * rec.qty_consumed

    @api.depends('product_qty', 'qty_done')
    def compute_expired(self):
        for rec in self:
            if rec.product_qty == rec.qty_done:
                rec.expired = True


    @api.depends('qty_approve', 'qty_consumed')
    def compute_expired_agricultural(self):
        for rec in self:
            if rec.qty_approve == rec.qty_consumed:
                rec.expired_agricultural = True


    name = fields.Char('Name')
    no_invoice = fields.Char('Invoice No')
    expired = fields.Boolean('Expired', compute='compute_expired', store=True)
    expired_agricultural = fields.Boolean('Expired', compute='compute_expired_agricultural', store=True)
    total = fields.Float('Total' ,compute="compute_total", store=True)
    total_qty_supplier = fields.Float('Total' ,compute="compute_total_supplier", store=True)
    total_qty = fields.Float('Total' ,compute="compute_total_qty", store=True)
    product_id = fields.Many2one('product.product','Product')
    weight = fields.Float('Total Weight', compute="compute_weight", store=True)
    price = fields.Float('Price')
    qty_custom = fields.Float('Qty Remaining' ,compute="compute_qty_custom", store=True)
    expired_order = fields.Boolean('Expired')
    qty_supplier = fields.Float('Qty remaining')
    value_weight = fields.Float('Weight')
    new_price = fields.Float('Price Doc')
    qty_approve = fields.Float('Qty Approve')
    qty_delivery = fields.Float('Qty Delivery')
    qty_done = fields.Float('Qty Consumed')
    commission = fields.Float('Commission' ,default='.28')
    lot_number = fields.Char('Lot No')
    product_qty = fields.Float('Quantity')
    qty_consumed = fields.Float('Qty Consumed' )
    qty_remain = fields.Float('Qty Remaining' )
    qty_remaining = fields.Float('Qty Remaining', compute="compute_qty_remaining", store=True)
    product_uom_qty = fields.Many2one('product.uom', string='Unit of measure')
    line_id = fields.Many2one('purchase.contract', string='Contract')
    contract_form_id = fields.Many2one('purchase.contract', string='Reference Contract')
    qty_contract = fields.Float('Qty')
    clearance_id = fields.Many2one('customs.clearance', string='Clearance')
    cultivate_id = fields.Many2one('cultivate.form', string='Agricultural')
    form_id = fields.Many2one('cultivate.form', string='Agricultural' ,domain=[('state', '=', 'open')])
    grade_id = fields.Many2one('product.grade', string='Grade')
    container_number = fields.Char('Container No')
    code_number = fields.Char('Code No')
    path_number = fields.Char('Batch No')
    expiration_date = fields.Date('Expiration Date')
    scheduled_date = fields.Date('Scheduled Date')
    note = fields.Char('Note')
    invoice_id = fields.Many2one('purchase.vendor.invoice', string='Invoice')
    purchase_inv_id = fields.Many2one('purchase.vendor.invoice', string='Invoice')
    vendor_id = fields.Many2one('res.partner', string='Vendor')
    quantity_id = fields.Many2one('purchase.track.quantity', string='Quantity')
    # invoice_lines = fields.One2many('account.invoice.line', 'contract_id', string="Bill Lines", readonly=True, copy=False)


    @api.multi
    @api.depends('qty_approve', 'qty_consumed')
    def compute_qty_remaining(self):
        for rec in self:
            rec.qty_remaining = rec.qty_approve - rec.qty_consumed


    def _prepare_purchaseorder_line(self, name, product_qty=0.0, price_unit=0.0, taxes_ids=False):
        self.ensure_one()
        requisition = self.line_id
        qty = self.product_qty
        unit_of_measure = self.product_id.uom_po_id

        return {
            'name': name,
            'product_id': self.product_id.id,
            'product_uom_qty': self.product_id.uom_po_id.id,
            'product_qty': self.qty_custom,
            'price': price_unit,
            'weight': self.weight,
            'total': self.total,
            'value_weight': self.product_id.weight,
            'taxes_id': [(6, 0, taxes_ids)],
        }



class ProductGrade(models.Model):
	_name = 'product.grade'
	name = fields.Char('Grade')



class ProductStander(models.Model):
	_name = 'product.stander'
	name = fields.Char('Stander')


class CultivateForm(models.Model):
    _name = 'cultivate.form'

    name = fields.Char('Form NO', required=True)
    date = fields.Date('Date', default=fields.Date.today(), readonly=True)
    date_start = fields.Date('Start Date', required=True, default=fields.Date.today)
    date_end = fields.Date('End Date', required=True)
    capacity = fields.Float('Capacity')
    attach = fields.Binary(string="Upload File")
    notes = fields.Text('Notes')
    cultivate_ids = fields.One2many('purchase.contract.line', 'cultivate_id',string='Agricultural')
    form_ids = fields.One2many('purchase.contract.line', 'cultivate_id',string='Agricultural')
    state = fields.Selection([
                ('draft', 'New'),
                ('open', 'Running'),
                ('close', 'Expired'),

            ], string='Status', track_visibility='onchange', default='draft')


    # @api.onchange('cultivate_ids.expired')
    # def compute_cultivate(self):
    #     cultivate_ids = self.cultivate_ids
    #     for rec in cultivate_ids:
    #         expired = rec.expired
    #     if expired == True:
    #         self.state = 'close'


    @api.multi
    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise Warning(_("Warning! You cannot delete a Agricultural Form which is in %s state.") % (rec.state))
            return super(CultivateForm, self).unlink()

class ProductTemplate(models.Model):
    _name = 'product.template'
    _inherit = 'product.template'

    agriculture_id = fields.Many2one('product.agriculture','Agriculture')

    # agriculture = fields.Boolean('Agriculture Form')

    @api.onchange('agriculture_id')
    def get_agriculture(self):
        if not self.agriculture_id == True:
            raise UserError(_("This Product Has Agriculture Form ?"))




class ProductAgriculture(models.Model):
    _name = 'product.agriculture'

    name = fields.Char('Name')
