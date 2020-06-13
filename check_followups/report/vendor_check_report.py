# -*- coding: utf-8 -*-
from odoo import api, models, fields

#
# from openerp import api, models, fields
# from openerp.tools import float_round
# from openerp.exceptions import UserError, Warning

class all_check_report(models.AbstractModel):
    _name = 'report.check_followups.al_check_report'

    def get_check(self):
        res = []
        check_list = []
        num_line =0
        total_employee=0
        records = False
        active_ids = self._context.get('active_ids')
        checks = self.env['all.check.repor.wizard'].browse(active_ids)
        for check in checks:
            date_from=check.date_from
            date_to=check.date_to
            type=check.type

        if type == 'checks_recivce':
            print(type, "iam here")
            check_ids =self.env['check_followups.check_followups'].search(
                [('Date', '>=',date_from), ('Date', '<=', date_to),
                 ('state', 'in', ('withdrawal','donev')),
                 ])
            if check_ids:
                records = self.env['check_followups.check_followups'].browse(check_ids)
                for che in records:
                    num_line+=1

                    check_list.append({
                        'num_line': num_line,
                        'account_holder': che.id.account_holder.name,
                        'check_no': che.id.check_no,
                        'date': che.id.Date,
                        'amount': che.id.amount,
                        'notes': che.id.notes,
                        # 'communication': che.id.communication,
                    })
                total_employee=num_line
                return check_list


    def get_check_return(self):
        res = []
        check_list_return = []
        num_line =0
        total_employee=0
        records = False
        active_ids = self._context.get('active_ids')
        return_checks = self.env['all.check.repor.wizard'].browse(active_ids)
        for checks in return_checks:
            date_from=checks.date_from
            date_to=checks.date_to
            type=checks.type

        if type == 'checks_return':
            check_return_ids =self.env['check_followups.check_followups'].search(
                [('Date', '>=',date_from), ('Date', '<=', date_to),
                 ('state', '=', 'return_acv'),
                 ])

            if check_return_ids:
                records = self.env['check_followups.check_followups'].browse(check_return_ids)
                for ches in records:
                    num_line+=1

                    check_list_return.append({
                         'num_line': num_line,
                        'account_holder': ches.id.account_holder.name,
                        'check_no': ches.id.check_no,
                        'date': ches.id.Date,
                        'amount': ches.id.amount,
                        'notes': ches.id.notes,
                        # 'communication': ches.id.communication,
                    })
                total_employee=num_line
                return check_list_return

    def get_check_reject(self):
        res = []
        check_list_reject = []
        num_line = 0
        total_employee = 0
        records = False
        active_ids = self._context.get('active_ids')
        return_checks = self.env['all.check.repor.wizard'].browse(active_ids)
        for checks in return_checks:
            date_from = checks.date_from
            date_to = checks.date_to
            type = checks.type

        if type == 'checks_reject':
            print(type, "iam here")
            check_reject_ids = self.env['check_followups.check_followups'].search(
                [('Date', '>=', date_from), ('Date', '<=', date_to),
                 ('state', '=', 'rdv'),
                 ])

            if check_reject_ids:
                records = self.env['check_followups.check_followups'].browse(check_reject_ids)
                for reject in records:
                    num_line += 1

                    check_list_reject.append({
                        'num_line': num_line,
                        'account_holder': reject.id.account_holder.name,
                        'check_no': reject.id.check_no,
                        'date': reject.id.Date,
                        'amount': reject.id.amount,
                        'notes': reject.id.notes,
                        # 'communication': ches.id.communication,
                    })
                total_employee = num_line
                return check_list_reject


    def get_check_outstanding(self):
        res = []
        check_list_outstand = []
        num_line = 0
        total_employee = 0
        records = False
        active_ids = self._context.get('active_ids')
        return_checks = self.env['all.check.repor.wizard'].browse(active_ids)
        for checks in return_checks:
            date_from = checks.date_from
            date_to = checks.date_to
            type = checks.type

        if type == 'checks_out':
            print(type, "iam here")
            check_out_ids = self.env['check_followups.check_followups'].search(
                [('Date', '>=', date_from), ('Date', '<=', date_to),
                 ('state', '=', 'out_standing'),
                 ])

            if check_out_ids:
                records = self.env['check_followups.check_followups'].browse(check_out_ids)
                for out in records:
                    num_line += 1

                    check_list_outstand.append({
                        'num_line': num_line,
                        'account_holder': out.id.account_holder.name,
                        'check_no': out.id.check_no,
                        'date': out.id.Date,
                        'amount': out.id.amount,
                        'notes': out.id.notes,
                        # 'communication': ches.id.communication,
                    })
                total_employee = num_line
                return check_list_outstand

    @api.model
    def render_html(self, docids, data):
        self.model = self.env.context.get('active_model')
        docargs = {
            'doc_ids': self.ids,
            'doc_model': self,
            'docs': self,
            'data': data['form'],
            'type': data['form'][0]['type'],
            'date_from': data['form'][0]['date_from'],
            'date_to': data['form'][0]['date_to'], }
        if data['form'][0]['type']:
            if data['form'][0]['type'] == 'checks_recivce':
                docargs['check_ids'] = self.get_check()
            elif data['form'][0]['type'] == 'checks_return':
                docargs['check_return_ids'] = self.get_check_return()
            elif data['form'][0]['type'] == 'checks_reject':
                docargs['check_reject_ids'] = self.get_check_reject()
            elif data['form'][0]['type'] == 'checks_out':
                docargs['check_out_ids'] = self.get_check_outstanding()
        return self.env['report'].render('check_followups.al_check_report', docargs)
