
from odoo import models, fields, api,_
from datetime import datetime
from odoo.exceptions import UserError, AccessError ,ValidationError
from dateutil import relativedelta

class end_service_wizard(models.Model):
    _name='end.service.wizard'

    start_date=fields.Date('Start Date',required=True)
    end_date=fields.Date('End Date', required=True,
                          default=str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10],
                          )
    employee_id = fields.Many2one('hr.employee', 'Employee')

    @api.multi
    def print_report(self):
        data = {}
        vehicles = []
        if self.start_date and self.end_date:
            records = self.env['hr.payslip'].search(
                [('date_from', '>=', self.start_date), ('date_to', '<=', self.end_date), ('state', '=', 'done'), ('employee_id', '=', self.employee_id.id),
                 ])
            # raise UserError(records)
            # print(records,'tttttttttttttttt')
            # for t in records:
            #     raise UserError(t)
            #     vehicle_id = t.vehicle_id.name
            #     vehicles.append(vehicle_id)
                # raise UserError(vehicles)
                # order = vehicle.cost_ids
                # for vehicle in vehicle_id:
                #     name = vehicle.name
                # order = vehicle.cost_ids
                # for main in order:
                #     product_id = main.product_id.name
                #     price = main.amount
                #     cost_subtype_id = main.cost_subtype_id.name
                #     quantity = main.quantity




            data['records'] = records.ids
            # data['vehicles'] = vehicles
            # vehicles = vehicles
            data['start_date'] = self.start_date
            data['end_date'] = self.end_date
            data['employee_id'] = self.employee_id.name
            # data['cost_subtype_id'] = cost_subtype_id
            # data['quantity'] = quantity
            return self.env['report'].get_action(self, 'is_hr_customization.end_service_template', data=data)


class is_hr_end(models.AbstractModel):
    _name = 'report.is_hr_customization.end_service_template'


    @api.model
    def render_html(self, docids,data):
        # data['records'] = self.env['account.analytic.line'].browse(data['records'])
        data['records']=self.env['hr.payslip'].browse(data['records'])
        docs=data['records']
        docargs = {

            'data': data,
            'docs': docs,
        }
        return self.env['report'].render('is_hr_customization.end_service_template', docargs)
