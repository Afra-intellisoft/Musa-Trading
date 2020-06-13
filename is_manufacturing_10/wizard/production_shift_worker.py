
from odoo import models, fields, api,_
from datetime import datetime
from odoo.exceptions import UserError, AccessError ,ValidationError
from dateutil import relativedelta

class IsProductionWorker(models.Model):
    _name='is.production.worker'

    start_date=fields.Date('Start Date',required=True)
    worker_id=fields.Many2one('mrp.worker','Worker',required=True)
    end_date=fields.Date('End Date', required=True,
                          default=str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10],
                          )


    @api.multi
    def print_report(self):
        data = {}
        production = []
        if self.start_date and self.end_date:
            records = self.env['mrp.adjustment'].search(
                [('date', '>=', self.start_date), ('date', '<=', self.end_date),('mrp_ids.worker_name', '=', self.worker_id.id)
                 ])

            data['records'] = records.ids
            data['start_date'] = self.start_date
            data['end_date'] = self.end_date
            data['worker_id'] = self.worker_id.name
            return self.env['report'].get_action(self, 'is_manufacturing_10.is_production_worker_template', data=data)


class is_production_worker_wizard(models.AbstractModel):
    _name = 'report.is_manufacturing_10.is_production_worker_template'

    @api.model
    def render_html(self, docids,data):
        # data['00000000'] = self.env['account.analytic.line'].browse(data['records'])
        data['records']=self.env['mrp.adjustment'].browse(data['records'])
        docs=data['records']
        docargs = {

            'data': data,
            'docs': docs,
        }
        return self.env['report'].render('is_manufacturing_10.is_production_worker_template', docargs)
