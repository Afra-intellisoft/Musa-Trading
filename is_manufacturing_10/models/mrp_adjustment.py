# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from datetime import datetime
from odoo.exceptions import AccessError, UserError

class mrp_adjustment(models.Model):
    _name='mrp.adjustment'


    name = fields.Char('Name',compute='get_name')
    date=fields.Date('Date',required=True)
    shift_id=fields.Selection([('Morning','Morning'),('After Noon','After Noon'),('After Night','After Night')],'Shift',required=True)
    batch_id=fields.Many2one('stock.production.lot','Batch No.')
    production_sup=fields.Many2one('hr.employee','Production Supervisor',required=True)
    team_leader=fields.Many2one('hr.employee','Team Leader',required=True)
    mo_ids = fields.One2many('mrp.production', 'shift_id')
    # , domain = [('state', '=', 'done')]
    mrp_ids = fields.One2many('mrp.employee.line', 'mrp_id','Worker')
    # mrp_boy_ids = fields.One2many('mrp.employee.line', 'mrp_id','Worker')
    mrp_boy_ids = fields.One2many('mrp.employee', 'mrp_adj_id','Worker')
    # mrp_id = fields.Many2one('mrp.employee', 'Worker')
    journal_id=fields.Many2one('account.journal','Journal')
    price=fields.Float('price',compute='compute_eff')
    state=fields.Selection([('draft','Draft'),('in_progress','In Progress'),('finished','Finished')],string='State',default='draft')
    total = fields.Float('Total', compute="get_total_all", store=True)
    total_other = fields.Float('Total Ather', compute="get_total_other", store=True)
    total_sub = fields.Float('Total Sub', compute="get_total", store=True)

    @api.multi
    @api.depends('total_other','total_sub')
    def get_total_all(self):
        for x in self:
            total_other = x.total_other
            total_sub = x.total_sub
            gen = total_other + total_sub
        self.total = gen

    @api.depends('mrp_boy_ids.price_daily','mrp_boy_ids.product_quantity')
    @api.one
    def get_total_other(self):
        for rec in self:
            total = 0
            mo = rec.mrp_boy_ids
            counter = 0
            gen_total =0
            price_daily =0
            price_daily =0
            for obj in mo:
                counter += 1
                price_daily = obj.price_daily
                product_quantity = obj.product_quantity
                worker_name = obj.worker_name.id
                gen_total = price_daily * counter/product_quantity
            rec.total_other = gen_total


    @api.depends('mrp_ids.total')
    @api.one
    def get_total(self):
        for rec in self:
            total = 0
            mo = rec.mrp_ids
            for obj in mo:
                total += obj.total
            rec.total_sub = total


    # @api.onchange('mrp_id')
    # def _onchange_mrp_id(self):
    #     self.total = self.mrp_id.total

    @api.depends('date','shift_id')
    @api.one
    def get_name(self):
        if self.shift_id and self.date:
            self.name=str(self.date)+"/" +str(self.shift_id)

    # @api.one
    # def confirm(self):
    #     self.state='confirm'

    @api.one
    def confirm(self):
        manufacturing_obj = self.env['is.hr.count.manufacturing']
        line = self.env['is.hr.count.manufacturing.line']
        boy_line = self.env['is.hr.count.manufacturing.line.boy']
        manufacturing_vals = {
            'state': 'draft',
            'name': self.name,
            'date_order': self.date,
        }
        request_id = manufacturing_obj.create(manufacturing_vals)
        boy_id = self.mrp_boy_ids
        boy = boy_id.search([('paid', '=', False)])
        for obj in boy:
            worker_name = obj.worker_name.id
            price_daliy = obj.price_daily
            order_lines_vals = {'boy_id': request_id.id,
                                         'worker_name': worker_name,
                                         'price_daily': price_daliy,
                                         }
            boy_line.create(order_lines_vals)
            obj.paid = 'True'
        # mrp = self.env['mrp.employee.line'].search([('paid', '=', False)])
        mrp_id = self.mrp_ids
        mrp = mrp_id.search([('paid', '=', False)])
        for model in mrp:
            worker_name = model.worker_name.id
            total = model.total
            manufacturing_order_lines_vals = {'manufacturing_id': request_id.id,
                                         'worker_name': worker_name,
                                         'total': total,
                                         }
            line.create(manufacturing_order_lines_vals)
            self.state = 'in_progress'
            #     self.write({'mrp_ids.paid':True})
            model.paid = 'True'

    @api.one
    def close(self):
        if self.mo_ids:
            land_object = self.env['stock.landed.cost']
            land_product=self.env['product.product'].search([('name','=','Product land cost')],limit=1)
            for rec in self.mo_ids:
                entries=[]
                # if rec.product_id.blend==True:
                if rec.state=='done':


                    finished_move = rec.move_finished_ids.filtered(
                        lambda x: x.product_id == rec.product_id and x.state in ('done') and x.quantity_done > 0)
                    # create scrap
                    # scrap_id = self.env['stock.scrap'].create({'product_id':finished_move.product_id.id,
                    #                                            'scrap_qty':rec.real_qty,'origin':self.name,'product_uom_id':rec.product_uom_id.id})
                    # scrap_id.action_validate()
                    # Create landed cost
                    vals = {
                        'product_id': land_product.id,
                        'price_unit': rec.cost_additional,
                        'split_method': 'equal',


                    }
                    entries.append((0, 0, vals))
                    for move in finished_move:
                        if move.picking_id:

                            land_id=land_object.create({'date':datetime.today(),'account_journal_id':self.journal_id.id,'cost_lines':[(0, 0, vals)],
                                                'picking_ids':[(4, move.picking_id.id)]})
                            land_id.compute_landed_cost()
                            land_id.button_validate()
            self.state='finished'






