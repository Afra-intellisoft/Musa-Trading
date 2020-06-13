# -*- coding: utf-8 -*-

from datetime import datetime

from odoo import api, fields, models, _

from odoo.exceptions import UserError

from odoo.addons import decimal_precision as dp

class purchase_request(models.Model):
    _inherit = ['purchase.requisition']
    _description = "Purchase Requisition"

    material_request_id = fields.Many2one('material.request', string="Material", translate=True)
    project_name = fields.Many2one('project.project', string='Project Name', translate=True)

class material_request(models.Model):
    _name = "material.request"
    # _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Material Requesition"
    _order = 'id desc'

    READONLY_STATES = {
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
    }

    def _get_picking_out(self):
        #pick_in = self.env.ref('stock.picking_type_out')
        #if not pick_in:
        company = self.env['res.company']._company_default_get('material.request')
        pick_in = self.env['stock.picking.type'].search([('warehouse_id.company_id', '=', company.id), ('code', '=', 'outgoing')],limit=1, )
        if pick_in:
            return pick_in[0]

    def _default_user(self):
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

    name = fields.Char('Request Reference', required=True, index=True, copy=False,translate=True, default='New')
    ordering_date = fields.Date('Request Date', required=True, states=READONLY_STATES, index=True, copy=False, translate=True, default=fields.Date.today(),
        help="Depicts the date where the Request should be validated and converted into a Approval Request.", readonly=True)
    date_approve = fields.Date('Approval Date', readonly=True, index=True, copy=False,translate=True)
    applicant_name = fields.Many2one('hr.employee', string="Applicant Name",required=True,translate=True,default=_default_user)
    department_id = fields.Many2one('hr.department', related='applicant_name.department_id',string='Department',store=True,translate=True)
    # administration = fields.Many2one('hr.department', related='department_id.parent_id',string='Administration',required=True,store=True,readonly = True)
    project_name = fields.Many2one('project.project',string='Project Name', translate=True)
    description = fields.Text(string='Description', translate=True)
    # locatin = fields.Many2one('project.task',String='Project Location', translate=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirm'),
        ('department_approve', 'Direct Manager Approval'),
        ('Public_approve', 'Public Administration Approval'),
        # ('stock_approve', 'Stock Approval'),
        # ('requested','Purchase Request'),
        ('done', 'Locked'),
        ('cancel', 'Refused')
        ], string='Status', readonly=True, index=True, copy=False, default='draft', track_visibility='onchange',translate=True)
    request_lines = fields.One2many('material.request.line', 'request_id', string='Request Lines', states={'cancel': [('readonly', True)], 'done': [('readonly', True)]}, copy=True,translate=True)
    notes = fields.Text('Terms and Conditions',translate=True)
    refuse_reason = fields.Text(string='Reason of Refuse', translate=True)
    description = fields.Text(string='Description', translate=True)
    checked = fields.Boolean('checked',default=False,translate=True)
    # ordered = fields.Boolean('ordered',default=False,translate=True,compute='_ordered_request',store=True)
    user_id = fields.Many2one('res.users', string='Responsible', default= lambda self: self.env.user,translate=True)
    origin = fields.Char(string='Source Document',translate=True)
    picking_ids = fields.One2many('stock.picking', 'material_request_id', string='Stock Picking', states={'done': [('readonly', True)]},translate=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env['res.company']._company_default_get('material.request'),translate=True)
    account_analytic_id = fields.Many2one('account.analytic.account','Analytic Account',translate=True)
    picking_type_id = fields.Many2one('stock.picking.type', 'Operation Type', required=True, default=_get_picking_out,translate=True)
    picking_count = fields.Integer(compute='_compute_picking_number', string='Requisition', default=0, store=True,translate=True)
    delivered_all = fields.Boolean('delivered all',default=False,readonly=True,compute='_compute_delivered', store=True,translate=True)
    purchase_all = fields.Boolean('Purchase',default=False,readonly=False,compute='_compute_purchased', store=True,translate=True)
    # purchase_ids = fields.One2many('purchase.request', 'material_request_id', string='Purchase Request', states={'done': [('readonly', True)]},translate=True)
    purchase_ids = fields.One2many('purchase.requisition', 'material_request_id', string='Purchase Agreements', states={'done': [('readonly', True)]},translate=True)
    purchase_count = fields.Integer(compute='_compute_purchase_number', string='Purchase Request', default=0, store=True,translate=True)
    request_copy = fields.Selection([
        ('copy', 'Request all product'), ('none', 'Request unavailable product')],
        string='Request Type', required=True, default='none', translate=True)

    request_type = fields.Selection([
        ('project', 'Request for Project'), ('department', 'Request for Department')],
        string='Request Type', required=True, default='department', translate=True)

    custody_applicant_name = fields.Many2one('hr.employee', string="Custody Applicant Name",required=True,translate=True,default=_default_user)
    have_custody = fields.Boolean('Have Custody',default=False,translate=True)



    @api.multi
    @api.depends('picking_ids')
    def _compute_picking_number(self):
        for picking in self:
            picking.picking_count = len(picking.picking_ids)

    # @api.multi
    # @api.depends('purchase_ids.qty_ordered','purchase_ids.product_qty')
    # def _ordered_request(self):
    #     for rec in self:
    #         rec.picking_count = len(rec.picking_ids)


    @api.multi
    @api.depends('purchase_ids')
    def _compute_purchase_number(self):
        for purchase in self:
            purchase.purchase_count = len(purchase.purchase_ids)


    @api.multi
    @api.depends('request_lines','request_lines.delivered')
    def _compute_delivered(self):
        count = 0
        for picking in self:
            for line in picking.request_lines:
                if line.delivered:
                    count += 1
            if (count == len(picking.request_lines)) and picking.state not in ('draft', 'confirmed', 'department_approve') :
                picking.delivered_all = True


    @api.multi
    @api.depends('request_lines', 'request_lines.purchased')
    def _compute_purchased(self):
        count = 0
        for request in self:
            for line in request.request_lines:
                if line.purchased:
                    count += 1
            if (count == len(request.request_lines)) and request.state not in ('draft', 'confirm', 'department_approve') :
                request.purchase_all = True




    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('material.request') or '/'
        return super(material_request, self).create(vals)

    @api.multi
    def unlink(self):
        for order in self:
            if not order.state == 'cancel':
                raise UserError(_('In order to delete a Material Request, you must cancel it first.'))
        return super(material_request, self).unlink()

    # @api.multi
    # def print_quotation(self):
    #     return self.env.ref('purchase.report_purchase_quotation').report_action(self)
    @api.multi
    @api.onchange('project_name')
    def _get_project_account_analytic_id(self):
        for req in self:
            if req.request_type =='project':
                analytic = self.env['account.analytic.account'].search([('name', '=', req.project_name.name)],limit=1,)
                analytic_account = analytic[0]
                self. account_analytic_id = analytic_account


    @api.multi
    def button_Public_approve(self, force=False):
        self.write({'state': 'Public_approve'})
        return {}

    # @api.multi
    # def button_hr_general_manager(self, force=False):
    #     self.write({'state': 'hr_general_manager'})
    #     return {}

    @api.multi
    def button_draft(self):
        self.write({'state': 'draft'})
        return {}




    @api.multi
    def button_confirm(self):
        if not all(obj.request_lines for obj in self):
            raise UserError(_('You cannot confirm Request because there is no product line.'))
        for obj in self:
            users_obj = self.env['res.users']
            users_ids = users_obj.search([('id', '=', self.env.uid)], limit=1)
            if obj.applicant_name.user_id.id != users_ids.id:
                raise UserError(_('ليست لديك الصلاحية للتأكيد'))
            for line in obj.request_lines:
                if line .ordered_qty == 0:
                    raise UserError(_('Pleas Check The Ordered Quantity First.'))
        self.write({'state': 'confirm'})
        return {}

    @api.multi
    def button_department_approve(self):
        self.write({'state': 'department_approve'})
        return {}


    # @api.multi
    # def button_stock_approve(self):
    #     if self.checked:
    #         if self.purchase_count == 0 and self.picking_count == 0:
    #             raise UserError(_('الرجـاء تحـديد القرار اولا'))
    #         else:
    #             self.write({'state': 'stock_approve','date_approve': fields.Datetime.now()})
    #     else:
    #         raise UserError(_('pleas check the availability first.'))
    #     return {}


    @api.multi
    def button_stock_check(self):
        self.checked = True
        if not all(obj.request_lines for obj in self):
            raise UserError(_('Nothing to check the availability for.'))
        else:
            no_quantities_done = all(line.product_qty == 0.0 for line in self.request_lines)
            if no_quantities_done:
                view = self.env.ref('is_material_requisition_golden_12.request_approve_quantities_view')
                wiz = self.env['request.approve.quantities'].create({'lins_ids': [(4, self.id)]})
                return {
                    'name': _('Quantities Approval?'),
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'request.approve.quantities',
                    'views': [(view.id, 'form')],
                    'view_id': view.id,
                    'target': 'new',
                    'res_id': wiz.id,
                    'context': self.env.context,
                }
            available = 0
            for quant in self.request_lines:
                available = quant.product_id.qty_available
                if available >= quant.product_qty:
                    self.checked = True
                    self.env.cr.execute("""update material_request_line set available=%s where id=%s ;""",(True, quant.id,))

                if available < quant.product_qty:
                    self.checked = True
                    self.env.cr.execute("""update material_request_line set available=%s where id=%s ;""",
                                        (False, quant.id,))
        return True
        return {}


    @api.multi
    def button_cancel(self):
        for order in self:
            for pick in order.picking_ids:
                if pick.state == 'done':
                    raise UserError(_('Unable to cancel material request %s as some receptions have already been done.') % (order.name))
            for pick in order.picking_ids.filtered(lambda r: r.state != 'cancel'):
                pick.action_cancel()
            if not order.refuse_reason :
                raise UserError(
                    _('Please Enter Reason for refuse'))

        self.write({'state': 'cancel'})


    @api.multi
    def action_done(self):
        if any(material_request_line.delivered == False for material_request_line in
                self.mapped('request_lines')):
            raise UserError(_('You have to create and validate delivery order for all requested items.'))
        if not self.picking_ids:
            raise UserError(_('You have to create and validate delivery order for this request request.'))

        if any(stock_picking.state not in ['done'] for stock_picking in
                self.mapped('picking_ids')):
            raise UserError(_('You have to cancel or validate delivery order before closing the material request.'))
        self.write({'state': 'done'})

    @api.multi
    def button_stock_picking(self):
        self._create_picking()

    @api.model
    def _prepare_picking(self):
        # if not self.partner_id.property_stock_customer.id:
        #     raise UserError(_("You must set a Customer Location for this Customer %s") % self.partner_id.name)
        picking_type_id = self.picking_type_id
        location = self.env.ref('stock.stock_location_customers')
        # code = self.env['project.project'].search([('project_id','=',self.project_name.id)],limit=1)
        return {
            'picking_type_id': picking_type_id.id,
            'date_order': self.ordering_date,
            'origin': self.name,
            'project_name':self.project_name.id,
            # 'project_code': code.project_code,
            'department_id': self.department_id.id,
            'request_type': self.request_type,
            # 'locatin': self.locatin.name,
            'account_analytic_id': self.account_analytic_id.id,
            'location_dest_id':picking_type_id.default_location_dest_id.id or location.id,
            'location_id':picking_type_id.default_location_src_id.id,
            'company_id': self.company_id.id,
            # 'request_id': self.id,
            'state':'draft',
            'material_request_id':self.id,

        }

    @api.multi
    def _create_picking(self):
        if self.checked:
            StockPicking = self.env['stock.picking']
            creat_pic = False
            for mov in self.request_lines:
                if mov.available and not mov.delivered:
                    creat_pic = True
                    break

            for order in self:
                if creat_pic:
                    res = order._prepare_picking()
                    picking = StockPicking.create(res)
                    moves = order.request_lines._create_stock_moves(picking)
                    moves = moves.filtered(lambda x: x.state not in ('done', 'cancel'))._action_confirm()
                    seq = 0
                    for move in sorted(moves, key=lambda move: move.date_expected):
                        seq += 5
                        move.sequence = seq
                    moves._action_assign()
                    picking.message_post_with_view('mail.message_origin_link',
                                                   values={'self': picking, 'origin': order},
                                                   subtype_id=self.env.ref('mail.mt_note').id)
                else:
                    raise UserError(_('This quantity is not available in inventory or is delivered.'))
        else:
            raise UserError(_('pleas check the availability first.'))
        return True

################################################################################################################

    @api.multi
    def button_purchase_request(self):
        self._create_purchase_request()


        # self.write({'state': 'requested'})

    @api.model
    def _prepare_purchase_request(self):
        return {
            'name': 'New',
            'ordering_date': self.ordering_date,
            'origin': self.name,
            'project_name': self.project_name.id,
            'applicant_name': self.applicant_name.id,
            'account_analytic_id': self.account_analytic_id.id,
            'department_id': self.department_id.id,
            'requisition_id': self.id,
            'request_type':self.request_type,
            # 'locatin': self.locatin.name,
            'material_request_id':self.id,
        }

    @api.multi
    def _create_purchase_request(self):
        PurchaseRequest = self.env['purchase.requisition']
        creat_pur = False
        for mov in self.request_lines:
            if not mov.available:
                creat_pur = True
                break
        for order in self:
            if self.checked:
                if order.request_copy == 'none' and creat_pur:
                    res = order._prepare_purchase_request()
                    request = PurchaseRequest.create(res)
                    request_lines = self.env['material.request.line'].search(
                        [('available', '=', False), ('request_id', '=',order.id)])
                    moves = request_lines._create_purchase_request_line(request)

                elif order.request_copy == 'none' and not creat_pur:
                    raise UserError(_('All quantity is available in inventory please change the request type.'))

                else:
                    res = order._prepare_purchase_request()
                    request = PurchaseRequest.create(res)
                    moves = order.request_lines._create_purchase_request_line(request)

            else:
                raise UserError(_('pleas check the availability first.'))

            request.message_post_with_view('mail.message_origin_link',values={'self': request, 'origin': order},
                                           subtype_id=self.env.ref('mail.mt_note').id)
        return True



class material_request_line(models.Model):
    _name = "material.request.line"
    _description = "Purchase Request Line"
    _rec_name = 'product_id'

    product_id = fields.Many2one('product.product', string='Product', required=True,translate=True)
    product_uom_id = fields.Many2one('uom.uom', string='Product Unit of Measure',translate=True)
    description = fields.Text(string='Description', translate=True)
    ordered_qty = fields.Float(string='Quantity', digits=dp.get_precision('Product Unit of Measure'),translate=True)
    qty_transferred = fields.Float(string='Transferred Quantities', translate=True)
    product_qty = fields.Float(string='Approved Quantity', digits=dp.get_precision('Product Unit of Measure'),translate=True)
    # price_unit = fields.Float(string='Unit Price', digits=dp.get_precision('Product Price'))
    qty_ordered = fields.Float(compute='_compute_ordered_qty', string='Total Ordered Quantities',translate=True)
    request_id = fields.Many2one('material.request', string='Purchase Agreement', ondelete='cascade',translate=True)
    state = fields.Selection(related='request_id.state', store=True, translate=True)
    company_id = fields.Many2one('res.company', related='request_id.company_id', string='Company', store=True, readonly=True, default= lambda self: self.env['res.company']._company_default_get('purchase.requisition.line'),translate=True)
    account_analytic_id = fields.Many2one('account.analytic.account', related='request_id.account_analytic_id', string='Analytic Account',translate=True, store=True)
    schedule_date = fields.Date(string='Scheduled Date', translate=True)
    move_dest_id = fields.Many2one('stock.move', 'Downstream Move', translate=True)
    available = fields.Boolean('available',default=False,readonly=True, translate=True)
    delivered = fields.Boolean('delivered',default=False,readonly=True, translate=True)
    purchased = fields.Boolean('purchased',default=False,compute=('_compute_purchased_qty'),translate=True)
    custody = fields.Boolean('Custody',default=False, translate=True)


    @api.multi
    @api.depends('request_id.purchase_ids.state')
    def _compute_ordered_qty(self):
        for line in self:
            total = 0.0
            for po in line.request_id.purchase_ids.filtered(lambda purchase_requisition: purchase_requisition.state in ['done']):
                for po_line in po.line_ids.filtered(lambda purchase_requisition_line: purchase_requisition_line.product_id == line.product_id):
                    if po_line.qty_ordered != line.product_qty:
                        total += po_line.qty_ordered
                    else:
                        total += po_line.qty_ordered
                    print('po_line.qty_ordered', po_line.qty_ordered)
            line.qty_ordered = total


    @api.multi
    @api.depends('request_id.purchase_ids.state', 'qty_ordered')
    def _compute_purchased_qty(self):
        for line in self:
            if line.qty_ordered < line.product_qty:
                line.purchased = False
            else:
                line.purchased = True


    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.product_uom_id = self.product_id.uom_id.id
            self.product_qty = 0.0
        if not self.account_analytic_id:
            self.account_analytic_id = self.request_id.account_analytic_id.id

    _sql_constraints = [
        ('material_product_uniq', 'unique(product_id,request_id)',
         'Some Product Repeater , Pleas Check The Product list !'),
    ]

    @api.multi
    def _prepare_stock_moves(self, picking):
        """ Prepare the stock moves data for one order line. This function returns a list of
        dictionary ready to be used in stock.move's create()
        """
        res = []
        template = {
            'name': self.product_id.name,
            'product_id': self.product_id.id,
            'price_unit': self.product_id.standard_price,
            'product_uom': self.product_uom_id.id,
            'product_uom_qty': self.product_qty,
            'date': self.request_id.ordering_date,
            'date_expected': self.request_id.ordering_date,
            'location_id': picking.location_id.id,
            'location_dest_id': picking.location_dest_id.id,
            'picking_id': picking.id,
            'state': 'assigned',
            'company_id': self.request_id.company_id.id,
            'picking_type_id': picking.picking_type_id.id,
            'origin': self.request_id.name,
            'warehouse_id': self.request_id.picking_type_id.warehouse_id.id,
            'account_analytic_id': self.account_analytic_id.id,
        }
        return self.env['stock.move'].create(template)

    @api.multi
    def _create_stock_moves(self, picking):
        moves = self.env['stock.move']
        done = self.env['stock.move'].browse()
        for line in self:
            if line.available and not line.delivered:
                val = line._prepare_stock_moves(picking)
                line.delivered = True
            # done = moves.create(val)
            # if line.available == True:
            # for val in line._prepare_stock_moves(picking):
            #     done += moves.create(val)
        return done


    @api.multi
    def _prepare_purchase_request_line(self, request):
        res = []
        template = {
            'product_id': self.product_id.id,
            'product_qty':self.product_qty - self.product_id.qty_available,
            'product_uom_id': self.product_uom_id.id,
            'requisition_id':request.id,
        }
        return self.env['purchase.requisition.line'].create(template)


    @api.multi
    def _create_purchase_request_line(self, request):
        moves = self.env['purchase.requisition.line']
        done = self.env['purchase.requisition.line'].browse()
        for line in self:
            val = line._prepare_purchase_request_line(request)
            # if line.qty_ordered >= line.product_qty:
            #     line.purchased = True
            # else:
            #     line.purchased = False
        return done

