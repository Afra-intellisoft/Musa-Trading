from odoo import api, fields, models, _
from odoo.exceptions import UserError, Warning
from datetime import datetime,date



class warning_management(models.Model):
    _name = 'hr.warnings'
    _description = 'Warning Management'
    _inherit = ['mail.thread']


    name = fields.Char('Warning',compute="compute_string" , required=True )
    employee_id = fields.Many2one('hr.employee', string="To Employee",required=True)
    warning= fields.Many2one('warning.warning', string ='Warning Name ',required=True)
    leval = fields.Selection(
        [('first', 'First penalty'),
        ('second', 'Second penalty'),
        ('third', 'Third penalty'),
        ('four', 'Four penalty'),
      ],string ='Leval',required=True)
    explanation_date = fields.Date("Explanation Form Date",default=fields.date.today())
    warning_date = fields.Date("warning Date")
    explanation = fields.Text("Reason")
    action_taken = fields.Text("Corrective action to be taken")
    note = fields.Text("The consequences if this happens again")
    warning_date = fields.Date("Warning Date", default=fields.date.today())
    pen_type = fields.Many2one('penalty.penalty', string = 'Penalty' , compute='_get_pen_type')
    deduct_dayes = fields.Float( string ='Deduct Dayes', compute="_get_pen_type")
    deduct_amount = fields.Float( string ='Deduct Amount' , compute='_get_penalty')
    # pen_type = fields.Selection([('none', 'No Penalty'), ('penalty', 'Penalty')], string='Decision')
    pen_desc = fields.Text("Penalty Description")
    improvement_steps = fields.Text( string = 'Steps for improvement')

    state = fields.Selection([('draft', 'To Submit'),('confirm', 'HOD Approve'), ('refuse', 'Refused'),
         ('seen', 'Seen By Employee'),('cancel', 'Cancel'),('approve','Manager Approve'), ('hr', 'HR Approval'),('penalty_approval', 'Done'),('auditor','Auditor')],
        'Status', readonly=True, track_visibility='onchange', copy=False, default="draft")
    wage = fields.Float( strin ="Old salary" , related = "employee_id.contract_id.total_salary")
    hr_notes = fields.Text( string ='HR Notes',required=True)
    check_notification = fields.Boolean(string='Check Notification')
    user_id = fields.Many2one('res.users', related = "employee_id.user_id", string='User')

    # @api.constrains('employee_id')
    # def emp_warning(self):
    #     for line in self:
    #         if line.employee_id:
    #             employee_id = line.employee_id.id
    #             hr_employee = self.search([('employee_id', '=', employee_id)])
    #             if self.leval  == 'four':
    #                 raise UserError(_('You can not request Loan before you complete One Year!'))
    @api.one
    def warning_auditor(self):
        for x in self:
            x.state = 'auditor'

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise Warning(_("Warning! You cannot delete warning which is in %s state.") % (rec.state))
            return super(warning_management, self).unlink()

    @api.model
    def create(self, values):
        values['name'] = self.env['ir.sequence'].get('hr.warnings') or ' '
        res = super(warning_management, self).create(values)
        return res


    @api.depends('warning', 'leval')
    def _get_pen_type(self):
        for pen in self:
            if pen.warning:
                warnings = pen.env['penalty.penalty'].search(
                    [('warnings_id', '=', pen.warning.id), ('leval', '=', pen.leval)])
                pen.pen_type = warnings
                pen.pen_desc = pen.warning.name
                for x in warnings:
                    pen.deduct_dayes = x.deduct_dayes
                    pen.note = x.note
                    pen.action_taken = x.action_taken

    @api.depends('warning_date','employee_id')
    def compute_string(self):
        for x in self:
            if x.employee_id:
                x.name = 'WAR' + ' ' +x.employee_id.name+ str(x.warning_date)

    @api.constrains('employee_id', 'warning','leval')
    def _emp_warnings(self):
        for warnings in self:
            if warnings.warning:
                first_warnings_ids = warnings.env['hr.warnings'].search(
                    [('employee_id', '=', warnings.employee_id.id),
                     ('warning', '=', warnings.warning.id),
                     ('leval', '=', warnings.leval)

                   ])
				#
                # for first in first_warnings_ids:
                #     warning_date = first.warning_date
                #     warning = str(warning_date)
                #     print(warning,'warning')
                #     rec = datetime.strptime(warning, '%Y-%m-%d')
                #     today = date.today()
                #     str_now = datetime.strptime(str(today), '%Y-%m-%d')
                #     employement_period = (str_now - rec).days
                #     print(employement_period,'employement_period')
                if len(first_warnings_ids) > 1 :
                    for x in first_warnings_ids:
                        raise Warning(_("This Employee Already Took This warnings"))





    @api.depends('vehicle_id')
    def get_vehicle(self):
        for x in self:
            if x.vehicle_id:
                amount = 0.00
                # print(x.vehicle_id.name)
                vehicle_ids = x.env['fleet.maintenance.order'].search(
                    [('vehicle_id', '=', x.vehicle_id.id), ('state', '=', 'done'), ('main_date', '>=', x.main_date),
                     ('main_date', '<=', x.main_date)])
                for rec in vehicle_ids:
                    if rec == 3:
                        raise Warning(_("Warning! You cannot delete warning which is in %s state.") % (rec.state))

    @api.model
    def create(self, values):
        values['name'] = self.env['ir.sequence'].get('hr.warnings') or ' '
        res = super(warning_management, self).create(values)
        return res

    @api.one
    def warning_seen(self):
        self.state = 'seen'

    @api.one
    def warning_submit_approve(self):
        self.state = 'confirm'

    @api.one
    def button_approve(self):
        self.state = 'approve'

    # @api.model
    # def notify(self):
    #     for rec in self.search([]):
    #         manager_group_id = self.env['res.groups'].search([('name', 'like', 'Billing Manager')]).id
    #         if rec.user_id.id:
    #             if rec.check_notification == False:
    #                 # print('##########0', rec.check_notification)
    #                 activity = self.env['mail.activity.type'].search([('name', 'like', 'test')], limit=1)
    #                 rec.env.cr.execute(
    #                     '''SELECT uid FROM res_groups_users_rel WHERE gid = %s order by uid''' % manager_group_id)
    #                 for mg in rec.env.cr.fetchall():
    #                     vals = {
    #                         'activity_type_id': activity.id,
    #                         'res_id': rec.id,
    #                         'res_model_id': rec.env['ir.model'].search([('model', 'like', 'hr.warnings')],
    #                                                                    limit=1).id,
    #                         'user_id': rec.user_id.id or 1,
    #                         'summary': 'notification',
    #                     }
    #                     # print(vals)
    #                     rec.check_notification = True
    #                 # add lines
    #                 rec.env['mail.activity'].create(vals)


    @api.one
    def warning_hr_approval(self):
        self.state = 'hr'

    @api.one
    def warning_penalty_approval(self):
        self.state = 'penalty_approval'

    @api.one
    def warning_refuse(self):
        self.state = 'refuse'

    @api.one
    def warning_reset(self):
        self.state = 'draft'


    @api.depends('deduct_dayes','wage')
    def _get_penalty(self):
        for deduct in self:
            if deduct.wage:
                pre_day = deduct.wage/30
                deduct_cost = deduct.deduct_dayes*pre_day
                deduct.deduct_amount = deduct_cost


class warning_warnings(models.Model):
    _name = 'warning.warning'
    _description = 'Warning Management'
    name = fields.Char('Warnings' ,required=True)
    penalty_ids = fields.One2many('penalty.penalty','warnings_id',string = 'Penalty')

class penalty_penalty(models.Model):
    _name = 'penalty.penalty'
    _description = 'penalty Management'
    name = fields.Char('Penalty Name' ,required=True)
    note = fields.Text('Consequences' ,required=True)
    action_taken = fields.Text("Corrective action to be taken")
    leval = fields.Selection(
        [('first', ' First penalty'),
         ('second', ' Second penalty'),
         ('third', ' Third penalty'),
         ('four', ' Four penalty'),
         ], string='leval',required=True)

    deduct = fields.Boolean( string = 'Deduct From Salary')
    deduct_dayes= fields.Float( string = 'Deduct Days ')
    warnings_id = fields.Many2one( 'warning.warning', string ='Warnings')






