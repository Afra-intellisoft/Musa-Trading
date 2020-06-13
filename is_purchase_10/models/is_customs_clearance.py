from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_is_zero, float_compare
from odoo.exceptions import UserError, Warning
from odoo.tools.misc import formatLang
from odoo.addons.base.res.res_partner import WARNING_MESSAGE, WARNING_HELP
import odoo.addons.decimal_precision as dp


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    invoice_id = fields.Many2one('customs.clearance', string="Customs Clearance")


class CustodyClearance(models.Model):
    _inherit = 'custody.clearance'

    customs_id = fields.Many2one('customs.clearance', string="Customs Clearance")


class StockLandedCost(models.Model):
    _inherit = 'stock.landed.cost'

    cost_id = fields.Many2one('customs.clearance', string="Customs Clearance")


class CustomsClearance(models.Model):
    _name = 'customs.clearance'
    _inherit = ['ir.needaction_mixin', 'mail.thread']


    @api.model
    def _needaction_domain_get(self):
        return [('state', '=', 'open')]

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise Warning(_("Warning! You cannot delete a Customs Clearance which is in %s state.") % (rec.state))
            return super(CustomsClearance, self).unlink()

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('customs.clearance') or '/'
        return super(CustomsClearance, self).create(vals)

    # @api.multi
    # @api.depends('value_goods', 'bank_commission')
    # def compute_total_bank(self):
    # 	for rec in self:
    # 		rec.total_bank = rec.value_goods + rec.bank_commission

    @api.one
    def approve_open(self):
        import_obj = self.env['purchase.order']
        contract_vals = {
            'state': 'purchase',
            'partner_id': self.partner_id.id,
            'customs_id': self.id,
            'partner_ref': self.invoice_no ,
            'currency_id': self.currency_id.id,
            'purchase_type': 'external',
        }
        request_id = import_obj.create(contract_vals)
        clearance_ids = self.clearance_ids
        for service in clearance_ids:
            order_lines_vals = {'order_id': request_id.id,
                                'product_id': service.product_id.id,
                                'name': service.product_id.name,
                                'value_weight': service.value_weight,
                                'product_qty': service.product_qty,
                                'new_price': service.new_price,
                                'product_uom': service.product_uom_qty.id,
                                'price_unit': service.price,
                                'price_subtotal': service.total,
                                'date_planned': service.scheduled_date,
                                }
            product_qty = service.product_qty
            line = self.env['purchase.order.line']
            line.create(order_lines_vals)
            form_ids = self.env['purchase.contract.line'].search(
                [('line_id.name', '=', self.contract_id.name), ('product_id', '=', service.product_id.id),
                 ('expired', '=', False), ])


            if not form_ids:
                raise Warning(
                    _("This Product Has not available in Contract%s") % service.product_id.name)


            for line in form_ids:
                line.qty_done += product_qty
                if line.qty_done > line.product_qty:
                    raise UserError(_("The Qty consumed greater than qty approved"))
        	self.state = 'open'
        xyz = form_ids[-1].line_id
        if any(form.expired == True for form in form_ids):
            xyz.state = 'close'


    name = fields.Char('Serial No', readonly=True)
    currency_id = fields.Many2one('res.currency', string='Currency')
    order_id = fields.Many2one('purchase.order', string='Order')
    track_id = fields.Many2one('purchase.track.quantity', 'Reference', readonly=True)
    amount_bank = fields.Integer('Bank Commission')
    account_invoice_id = fields.Many2one('collect.currency', string='Count Rate')
    average = fields.Float(string='Average Cost Of Rate', related='account_invoice_id.average_dollar',
                           readonly=False, track_visibility='always')
    contracts_count = fields.Integer(string='Contracts', compute="_compute_contracts_count", store=True)
    bl_no = fields.Char('B/L No')
    date_order = fields.Date('Date', default=fields.Date.today(), readonly=True)
    vendor_id = fields.Many2one('res.partner', string='Vendor')
    contract_id = fields.Many2one('purchase.contract', string='Contract', readonly=True)
    request_id = fields.Many2one('purchase.contract', string='Contract', readonly=True)
    clearance_ids = fields.One2many('purchase.contract.line', 'clearance_id', string='Contract')
    customs_ids = fields.One2many('custody.clearance', 'customs_id', string='Contract')
    cost_ids = fields.One2many('stock.landed.cost', 'cost_id', string='Contract')
    # invoice_ids = fields.One2many('account.invoice', 'invoice_id', string='Contract')
    cultivate_id = fields.Many2one('cultivate.form', string='Cultivate Form')
    partner_id = fields.Many2one('res.partner', 'Vendor')
    bank_commission = fields.Float('Amount')
    value_goods = fields.Float('Value Goods')
    rate = fields.Float('Current Rate', compute="_compute_currency_id", store=True)
    currency_id = fields.Many2one('res.currency', string='Currency')
    account_debit_id = fields.Many2one('account.account', string='Account Debit')
    account_credit_id = fields.Many2one('account.account', string='Account Credit')
    move_id = fields.Many2one('account.move', string='Journal Entry', readonly=True)
    journal_id = fields.Many2one('account.journal', 'Bank/Cash Journal',
                                 help='Payment journal.',
                                 domain=[('type', 'in', ['bank', 'cash'])])
    # total_bank = fields.Float('Total', compute="compute_total_bank", store=True)
    agricultural = fields.Boolean('Agricultural Request')
    clearance = fields.Boolean('Clearance Request')
    idbc = fields.Boolean('IDBC')
    date_idbc = fields.Date('Date')
    note_idbc = fields.Text('Note')
    docs_bank = fields.Boolean('Docs Bank')
    date_docs = fields.Date('Date')
    note_docs = fields.Text('Note')
    appeal_signed = fields.Boolean('Appeal Signed')
    date_appeal_signed = fields.Date('Date')
    note_appeal_signed = fields.Text('Note')
    shipping_time = fields.Boolean('Shipping Time')
    date_shipping_time = fields.Date('Date')
    note_shipping_time = fields.Text('Note')
    eta = fields.Boolean('ETA')
    date_eta = fields.Date('Date')
    note_eta = fields.Text('Note')
    shipment_arrive = fields.Boolean('Shipment Arrived')
    done_shipment_arrive = fields.Boolean('Done')
    date_arrive = fields.Date('Date')
    note_arrive = fields.Text('Note')
    health = fields.Boolean('Health')
    date_health = fields.Date('Date')
    note_health = fields.Text('Note')
    custom = fields.Boolean('Custom')
    date_custom = fields.Date('Date')
    note_custom = fields.Text('Note')
    ssmo = fields.Boolean('SSMO')
    date_ssmo = fields.Date('Date')
    note_ssmo = fields.Text('Note')
    docs = fields.Boolean('Docs')
    done_docs = fields.Boolean('Done')
    date = fields.Date('Date')
    note_docs = fields.Text('Note')
    other = fields.Boolean('Other')
    date_other = fields.Date('Date')
    note_other = fields.Text('Note')
    vassal_hooked = fields.Boolean('Vassal Hooked')
    date_vassal_hooked = fields.Date('Date')
    note_vassal_hooked = fields.Text('Note')
    container_dispatch = fields.Boolean('Container Dispatch')
    date_container_dispatch = fields.Date('Date')
    note_container_dispatch = fields.Text('Note')
    moving_containers = fields.Boolean('Moving Containers')
    date_moving = fields.Date('Date')
    note_moving = fields.Text('Note')
    examine_goods = fields.Boolean('Examine Goods')
    date_goods = fields.Date('Date')
    note_goods = fields.Text('Note')
    certificate_received = fields.Boolean('Certificate Received')
    date_certificate = fields.Date('Date')
    note_certificate = fields.Text('Note')
    total_amount_clearance = fields.Float('Total Amount Clearance', compute="_compute_total_amount_clearance",
                                          store=True)
    done_clearance = fields.Boolean('Done')
    rent_car = fields.Boolean('Rent Car')
    invoice = fields.Boolean('Count Invoice')
    date_rent = fields.Date('Date')
    note_rent = fields.Text('Note')
    amount_rent = fields.Float('Amount')
    total_currency = fields.Float('Total Currency Company', compute="_compute_total_currency", store=True)
    attach = fields.Binary(string="Upload File")
    certificate_number = fields.Integer('Certificate No')
    invoice_no = fields.Char('Invoice No')
    clearance_amount = fields.Float('Custody Amount', compute="_compute_contracts_count")
    # clearance_amount = fields.Float('Custody Amount',related='customs_ids.custody_amount',)
    cost_count = fields.Float('Land Cost', compute="_compute_cost_count", store=True)
    requester = fields.Char('Requester', default=lambda self: self.env.user.name)
    done = fields.Boolean('Done')
    state = fields.Selection([
        ('draft', 'New'),
        ('open', 'Running'),
        ('request', 'Request'),
        ('done', 'Done'),
    ], string='Status', track_visibility='onchange', default='draft')

    # request_id = fields.Many2one('purchase.contract', 'Reference')


    @api.one
    def finance_approve(self):
        precision = self.env['decimal.precision'].precision_get('Clearance')
        self.env.cr.execute("""select current_date;""")
        xt = self.env.cr.fetchall()
        self.comment_date4 = xt[0][0]
        can_close = False
        move_obj = self.env['account.move']
        move_line_obj = self.env['account.move.line']
        currency_obj = self.env['res.currency']
        created_move_ids = []
        clearance_ids = []
        for clearance in self:
            line_ids = []
            debit_sum = 0.0
            credit_sum = 0.0
            clearance_request_date = clearance.date
            for obj in clearance:
                # amount = obj.total_amount_ex
                amount = obj.amount_rent
                reference = obj.journal_id.name
                journal_id = clearance.journal_id.id
                currency_id = clearance.currency_id.id
                move_dict = {
                    'narration': reference,
                    'ref': reference,
                    'journal_id': journal_id,
                    'currency_id': currency_id,
                    'date': clearance_request_date,
                }

                debit_line = (0, 0, {
                    'name': reference,
                    'partner_id': False,
                    'account_id': clearance.account_debit_id.id,
                    'journal_id': journal_id,
                    'currency_id': currency_id,
                    'date': clearance_request_date,
                    'debit': amount > 0.0 and amount or 0.0,
                    'credit': amount < 0.0 and -amount or 0.0,
                    'analytic_account_id': False,
                    'tax_line_id': 0.0,
                })
                line_ids.append(debit_line)
                debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']
                credit_line = (0, 0, {
                    'name': reference,
                    'partner_id': False,
                    'account_id': clearance.account_credit_id.id,
                    'journal_id': journal_id,
                    'currency_id': currency_id,
                    'date': clearance_request_date,
                    'debit': amount < 0.0 and -amount or 0.0,
                    'credit': amount > 0.0 and amount or 0.0,
                    'analytic_account_id': False,
                    'tax_line_id': 0.0,
                })
                line_ids.append(credit_line)
                credit_sum += credit_line[2]['credit'] - credit_line[2]['debit']
                if float_compare(credit_sum, debit_sum, precision_digits=precision) == -1:
                    acc_journal_credit = clearance.journal_id.default_credit_account_id.id
                    if not acc_journal_credit:
                        raise UserError(
                            _('The Expense Journal "%s" has not properly configured the Credit Account!') % (
                                clearance.journal_id.name))
                    adjust_credit = (0, 0, {
                        'name': _('Adjustment Entry'),
                        'partner_id': False,
                        'account_id': acc_journal_credit,
                        'journal_id': journal_id,
                        'currency_id': currency_id,
                        'date': clearance_request_date,
                        'debit': 0.0,
                        'credit': debit_sum - credit_sum,
                    })
                    line_ids.append(adjust_credit)

                elif float_compare(debit_sum, credit_sum, precision_digits=precision) == -1:
                    acc_journal_debit = clearance.journal_id.default_debit_account_id.id
                    if not acc_journal_debit:
                        raise UserError(_('The Expense Journal "%s" has not properly configured the Debit Account!') % (
                            clearance.journal_id.name))
                    adjust_debit = (0, 0, {
                        'name': _('Adjustment Entry'),
                        'partner_id': False,
                        'account_id': acc_journal_debit,
                        'journal_id': journal_id,
                        'currency_id': currency_id,
                        'date': clearance_request_date,
                        'debit': credit_sum - debit_sum,
                        'credit': 0.0,
                    })
                    line_ids.append(adjust_debit)

                move_dict['line_ids'] = line_ids
                move = self.env['account.move'].create(move_dict)
                clearance.write({'move_id': move.id, 'date': clearance_request_date})
                move.post()
            self.clearance = True
    @api.onchange('contract_id')
    def _onchange_contract_id(self):
        if not self.contract_id:
            return

        requisition = self.contract_id
        if self.vendor_id:
            partner = self.vendor_id
        else:
            partner = requisition.vendor_id
        payment_term = partner.property_supplier_payment_term_id
        FiscalPosition = self.env['account.fiscal.position']
        fpos = FiscalPosition.get_fiscal_position(partner.id)
        fpos = FiscalPosition.browse(fpos)
        self.partner_id = partner.id
        self.fiscal_position_id = fpos.id
        self.payment_term_id = payment_term.id,
        self.partner_ref = requisition.name
        self.currency_id = requisition.currency_id.id
        self.date = self.date
        order_lines = []
        for line in requisition.line_ids:
            product_lang = line.product_id.with_context({
                'lang': partner.lang,
                'partner_id': partner.id,
            })
            name = product_lang.display_name
            if product_lang.description_sale:
                name += '\n' + product_lang.description_sale
            if line.product_uom_qty != line.product_id.uom_po_id:
                product_qty = line.product_uom_qty._compute_quantity(line.qty_delivery, line.product_id.uom_po_id)
                price_unit = line.price_unit
            else:
                product_qty = line.qty_delivery
                price_unit = line.price
            order_line_values = line._prepare_purchaseorder_line(
                name=name, product_qty=product_qty, price_unit=price_unit,
            )
            order_lines.append((0, 0, order_line_values))
        self.clearance_ids = order_lines

    @api.one
    def approve_done(self):
        self.done = True
        if self.cost_count == 0:
            raise UserError(_("Place Create The Land cost for Pickings"))
        self.state = 'done'

    # @api.depends('clearance_ids.invoice_lines.invoice_id.state')
    # def _compute_invoice(self):
    # 	for order in self:
    # 		invoices = self.env['account.invoice']
    # 		for line in order.clearance_ids:
    # 			invoices |= line.invoice_lines.mapped('invoice_id')
    # 		order.invoice_ids = invoices
    # 		order.invoice_count = len(invoices)

    @api.multi
    @api.depends('clearance_amount', 'amount_rent', 'amount_bank')
    def _compute_total_amount_clearance(self):
        for rec in self:
            rec.total_amount_clearance = rec.clearance_amount + rec.amount_bank + rec.amount_rent

    @api.multi
    @api.depends('currency_id')
    def _compute_currency_id(self):
        for rec in self:
            rec.rate = rec.currency_id.rate

    @api.multi
    @api.depends('rate', 'bank_commission')
    def _compute_total_currency(self):
        for rec in self:
            rec.total_currency = rec.average * rec.bank_commission

    @api.one
    def count_invoice(self):
        import_obj = self.env['account.invoice']
        self.invoice = True
        contract_vals = {
            'state': 'draft',
            'partner_id': self.vendor_id.id,
            'type': 'in_invoice'
        }
        request_id = import_obj.create(contract_vals)

        order_lines_vals = {'invoice_id': request_id.id,
                            'account_id': self.account_debit_id.id,
                            'name': "Service",
                            'price_unit': self.total_currency,
                            }
        line = self.env['account.invoice.line']
        line.create(order_lines_vals)

    @api.depends('customs_ids')
    def _compute_contracts_count(self):
        for rec in self:
            amount = 0.0

            customs = rec.customs_ids
            rec.contracts_count = len(rec.customs_ids)

            for obj in customs:
                amount += obj.custody_amount
            rec.clearance_amount = amount

    @api.depends('cost_ids')
    def _compute_cost_count(self):
        for rec in self:
            customs = rec.cost_ids
            rec.cost_count = len(rec.cost_ids)

    @api.onchange('rent_car')
    def _onchange_rent_car(self):
        if self.rent_car == True:
            self.date_rent = default = fields.Date.today()

    @api.onchange('certificate_received')
    def _onchange_certificate_received(self):
        if self.certificate_received == True:
            self.date_certificate = default = fields.Date.today()
            self.done_clearance = True

    @api.onchange('examine_goods')
    def _onchange_examine_goods(self):
        if self.examine_goods == True:
            self.date_goods = default = fields.Date.today()

    @api.onchange('moving_containers')
    def _onchange_moving_containers(self):
        if self.moving_containers == True:
            self.date_moving = default = fields.Date.today()

    @api.onchange('vassal_hooked')
    def _onchange_vassal_hooked(self):
        if self.vassal_hooked == True:
            self.date_vassal_hooked = default = fields.Date.today()

    @api.onchange('container_dispatch')
    def _onchange_container_dispatch(self):
        if self.container_dispatch == True:
            self.date_container_dispatch = default = fields.Date.today()

    @api.onchange('other')
    def _onchange_other(self):
        if self.other == True:
            self.date_other = default = fields.Date.today()

    @api.onchange('health')
    def _onchange_health(self):
        if self.health == True:
            self.date_health = default = fields.Date.today()

    @api.onchange('docs')
    def _onchange_docs(self):
        if self.docs == True:
            self.date = default = fields.Date.today()
            self.done_docs = default = True

    @api.onchange('ssmo')
    def _onchange_ssmo(self):
        if self.ssmo == True:
            self.date_ssmo = default = fields.Date.today()

    @api.onchange('custom')
    def _onchange_custom(self):
        if self.custom == True:
            self.date_custom = default = fields.Date.today()

    @api.onchange('shipping_time')
    def _onchange_shipping_time(self):
        if self.shipping_time == True:
            self.date_shipping_time = default = fields.Date.today()

    @api.onchange('shipment_arrive')
    def _onchange_shipment_arrive(self):
        if self.shipment_arrive == True:
            self.date_arrive = default = fields.Date.today()
            self.done_shipment_arrive = True

    @api.onchange('eta')
    def _onchange_eta(self):
        if self.eta == True:
            self.date_eta = default = fields.Date.today()

    @api.onchange('appeal_signed')
    def _onchange_appeal_signed(self):
        if self.appeal_signed == True:
            self.date_appeal_signed = default = fields.Date.today()

    @api.onchange('docs_bank')
    def _onchange_docs_bank(self):
        if self.docs_bank == True:
            self.date_docs = default = fields.Date.today()

    @api.onchange('idbc')
    def _onchange_idbc(self):
        if self.idbc == True:
            self.date_idbc = default = fields.Date.today()


class PurchaseVendorInvoice(models.Model):
    _name = 'purchase.vendor.invoice'

    name = fields.Char('Reference NO', required=True)
    auction_no = fields.Char('Auction NO', required=True)
    partner_id = fields.Many2one('res.partner','Supplier', required=True)
    date = fields.Date('Date', default=fields.Date.today)
    attach = fields.Binary(string="Upload File")
    qty_delivery = fields.Float('Qty Delivery')
    invoice_ids = fields.One2many('purchase.contract.line', 'invoice_id', string='Line')
    purchase_inv_ids = fields.One2many('purchase.contract.line', 'purchase_inv_id', string='Line')
    state = fields.Selection([
        ('draft', 'New'),
        ('open', 'Running'),
        ('close', 'Expired'),

    ], string='Status', track_visibility='onchange', default='draft')

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise Warning(_("Warning! You cannot delete a Order  which is in %s state.") % (rec.state))
            return super(PurchaseVendorInvoice, self).unlink()

    @api.one
    def approve_open(self):
        self.state = 'open'

    @api.one
    def approve_done(self):
        self.state = 'done'


class PurchaseTrackQuantity(models.Model):
    _name = 'purchase.track.quantity'

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('purchase.track.quantity') or '/'
        return super(PurchaseTrackQuantity, self).create(vals)

    @api.onchange('contract_id')
    def _onchange_contract(self):
        self.vendor_id = self.contract_id.vendor_id
        self.currency_id = self.contract_id.currency_id


    name = fields.Char('NO', readonly=True)
    vendor_id = fields.Many2one('res.partner', string='Vendor')
    currency_id = fields.Many2one('res.currency', string='Currency')
    auction_no = fields.Char('Auction NO')
    date = fields.Date('Date', default=fields.Date.today)
    stander_id = fields.Many2one('product.product', string="Stander")
    product_uom_id = fields.Many2one('product.uom', string=" Unit of Measure ")
    contract_id = fields.Many2one('purchase.contract', 'Contract')
    quantity_ids = fields.One2many('purchase.contract.line', 'quantity_id', string='Line')
    qty_consumed = fields.Float('Qty', compute="compute_average_quantity",store=True)
    avg_price = fields.Float('Avg price', compute="compute_average_quantity", store=True)
    qty_delivery = fields.Float('Qty Kg', compute="compute_average_quantity", store=True)
    update = fields.Boolean('Update')
    request = fields.Boolean('Request')
    weight = fields.Float('Weight')
    uom_id = fields.Many2one('product.uom', string='Unit of measure')
    state = fields.Selection([
        ('draft', 'New'),
        ('request', 'Request'),
        ('start_clearance', 'Start Clearance'),
    ], string='Status', track_visibility='onchange', default='draft')

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise Warning(
                    _("Warning! You cannot delete a Purchase Track Quantity which is in %s state.") % (rec.state))
            return super(PurchaseTrackQuantity, self).unlink()

    @api.onchange('stander_id')
    def _onchange_stander_id(self):
        self.product_uom_id = self.stander_id.uom_id.id


    @api.multi
    @api.depends('quantity_ids')
    def compute_average_quantity(self):
        qty = 0.0
        total = 0.0
        for rec in self:
            quantity = rec.quantity_ids
            for obj in quantity:
                qty += obj.qty_consumed
                total += obj.total_qty
            if qty > 0.0:
                self.avg_price = total / qty
                self.qty_delivery = qty
                self.qty_consumed = qty/50

    @api.onchange('product_id')
    def _onchange_product_id(self):
        self.uom_id = self.product_id.uom_id.id
        self.weight = self.product_id.weight

    @api.one
    def vendor_request(self):
        vendor = self.env['purchase.vendor.invoice'].search([('name', '=', self.auction_no)], limit=1)
        vendor_ids = self.env['res.partner'].search([])
        product_ids = self.env['product.product'].search([])
        for product in product_ids:
            product = product.id
            grade = []
            for partner in vendor_ids:
                name = partner.id
                vendor = self.env['purchase.contract.line'].search(
                    [('invoice_id.name', '=', self.auction_no), ('vendor_id', '=', name), ('expired_order', '=', False),
                     ('product_id', '=', product)
                     ])
                qty_supplier = 0.0
                price = 0.0
                weight = 0.0
                total = 0.0
                sum = 0.0
                sub_total = 0.0
                if vendor:
                    for rec in vendor:
                        grade = rec.grade_id.id
                        product = rec.product_id.id
                        product_uom_qty = rec.product_uom_qty.id
                        sum += rec.product_qty
                        price += rec.price
                        weight += rec.weight
                        qty_supplier += rec.qty_supplier
                    if weight != 0.0:
                         sub_total = qty_supplier / weight
                    order_lines_vals = {'product_qty': sum,
                                        'price': sub_total,
                                        'grade_id': grade,
                                        'value_weight': qty_supplier,
                                        'product_id': product,
                                        'product_uom_qty': product_uom_qty,
                                        'vendor_id': name,
                                        'quantity_id': self.id,
                                        }
                    line = self.env['purchase.contract.line']
                    line.create(order_lines_vals)
                self.state = 'request'
                self.request = True

    def vendor_update(self):
        quantity_ids = self.quantity_ids
        for line in quantity_ids:
            product = line.product_id.id
            vendor_id = line.vendor_id.id
            qty_consumed = line.qty_consumed
            obj_ids = self.env['purchase.contract.line'].search(
                [('product_id', '=', product), ('vendor_id', '=', vendor_id), ('invoice_id.state', '!=', 'close'),
                 ('expired', '=', False), ('qty_supplier', '>', 0.0)])
            print(obj_ids, 'obj_ids')
            # if not form_ids:
            # 	raise UserError(_("This Product Has not available in agriculture form"))
            total_remain = 0.0
            qty = 0.0
            line = self.env['purchase.vendor.invoice'].search(
                [('state', '=', 'open'),
                 ('invoice_ids.expired', '=', False)])
            for obj in obj_ids:
                qty += obj.qty_supplier
            for rec in obj_ids:
                qty_supplier = rec.qty_supplier
                if qty_consumed > qty:
                    product_remaining = qty_consumed - qty
                    raise UserError(_('There are Remaining qty %s') % (product_remaining))
                else:
                    if qty_consumed <= qty_supplier:
                        opt = qty_supplier - qty_consumed
                        rec.qty_supplier = opt
                        if rec.qty_supplier == 0.0:
                            rec.expired_order = True
                        break
                    if qty_consumed > qty_supplier:
                        test = qty_consumed - qty_supplier
                        rec.qty_supplier = 0.0
                        if rec.qty_supplier == 0.0:
                            rec.expired_order = True
                    qty_consumed = test
        for rec in line:
            invoice_ids = rec.invoice_ids
            for object in invoice_ids:
                expired = object.expired
            if object.expired == True:
                rec.invoice.state = 'close'
        import_obj = self.env['customs.clearance']
        self.update = True
        contract_vals = {
            'state': 'draft',
            'contract_id': self.contract_id.id,
            'partner_id': self.vendor_id.id,
            'currency_id': self.currency_id.id,
            'track_id': self.id,
        }
        request_id = import_obj.create(contract_vals)
        quantity_ids = self.quantity_ids
        # for service in quantity_ids:
        order_lines_vals = {'clearance_id': request_id.id,
                            'product_id': self.stander_id.id,
                            'value_weight': self.stander_id.weight,
                            'product_qty': self.qty_consumed,
                            'product_uom_qty': self.stander_id.uom_id.id,
                            'price': self.avg_price,
                            # 'total': service.total,
                            }
        line = self.env['purchase.contract.line']
        line.create(order_lines_vals)
        self.state = 'start_clearance'
