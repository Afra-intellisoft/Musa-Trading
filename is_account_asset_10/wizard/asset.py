
from odoo import models, fields, api,_
from datetime import datetime
from odoo.exceptions import UserError, AccessError ,ValidationError
from dateutil import relativedelta

class IsAssetWizard(models.Model):
    _name='is.asset.wizard'

    start_date=fields.Date('Start Date',required=True)
    category_id=fields.Many2one('account.asset.category','Category',required=True)
    end_date=fields.Date('End Date', required=True,
                          default=str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10],
                          )

    target_move = fields.Selection([('posted', 'All Posted Entries'),
                                    ('all', 'All Entries'),
                                    ], string='Target Moves', required=True, default='posted')


    @api.multi
    def print_report(self):
        data = {}
        production = []
        if self.start_date and self.end_date:
            records = self.env['account.asset.asset'].search(
                [('date', '>=', self.start_date), ('date', '<=', self.end_date),('category_id', '=', self.category_id.id)
                 ])

            data['records'] = records.ids
            data['start_date'] = self.start_date
            data['end_date'] = self.end_date
            data['category_id'] = self.category_id.name
            data['target_move'] = self.target_move
            return self.env['report'].get_action(self, 'is_account_asset_10.is_asset_template', data=data)




class is_account_asset_wazirds(models.AbstractModel):
    _name = 'report.is_account_asset_10.is_asset_template'

    @api.model
    def render_html(self, docids,data):
        # data['00000000'] = self.env['account.analytic.line'].browse(data['records'])
        data['records']=self.env['account.asset.asset'].browse(data['records'])
        docs=data['records']
        docargs = {

            'data': data,
            'docs': docs,
        }
        return self.env['report'].render('is_account_asset_10.is_asset_template', docargs)
