# -*- coding: utf-8 -*-
from odoo import api, models, fields

#
# from openerp import api, models, fields
# from openerp.tools import float_round
# from openerp.exceptions import UserError, Warning

class all_check_report(models.AbstractModel):
    _name = 'report.check_followups.all_check_report'

    def get_check(self):
        res = []
        check_list = []
        num_line =0
        total_employee=0
        records = False
        active_ids = self._context.get('active_ids')
        checks = self.env['all.check.report.wizard'].browse(active_ids)
        for check in checks:
            date_from=check.date_from
            date_to=check.date_to
            type=check.type

        if type == 'check_recivce':
            check_ids =self.env['check_followups.check_followups'].search(
                [('Date', '>=',date_from), ('Date', '<=', date_to),
                 ('state', 'in', ('withdrawal','donec')),
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
                        'communication': che.id.communication,
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
        return_checks = self.env['all.check.report.wizard'].browse(active_ids)
        for checks in return_checks:
            date_from=checks.date_from
            date_to=checks.date_to
            type=checks.type

        if type == 'check_return':
            check_return_ids =self.env['check_followups.check_followups'].search(
                [('Date', '>=',date_from), ('Date', '<=', date_to),
                 ('state', '=', 'rdc'),
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
                        'communication': ches.id.communication,
                    })

                total_employee=num_line
                return check_list_return

    def get_check_waiting(self):
        res = []
        check_list_waiting = []
        num_line =0
        total_employee=0
        records = False
        active_ids = self._context.get('active_ids')
        return_checks = self.env['all.check.report.wizard'].browse(active_ids)
        for checks in return_checks:
            date_from=checks.date_from
            date_to=checks.date_to
            type=checks.type

        if type == 'check_waiting':

            check_waiting_ids =self.env['check_followups.check_followups'].search(
                [('Date', '>=',date_from), ('Date', '<=', date_to),
                 ('state', '=', 'wait_bank'),
                 ])

            if check_waiting_ids:
                records = self.env['check_followups.check_followups'].browse(check_waiting_ids)

                for wait in records:
                    num_line+=1
                    check_list_waiting.append({
                         'num_line': num_line,
                        'account_holder': wait.id.account_holder.name,
                        'check_no': wait.id.check_no,
                        'date': wait.id.Date,
                        'amount': wait.id.amount,
                        'notes': wait.id.notes,
                        'communication': wait.id.communication,
                    })

                total_employee=num_line
                return check_list_waiting

    def get_check_reject(self):
            res = []
            check_list_reject = []
            num_line = 0
            total_employee = 0
            records = False
            active_ids = self._context.get('active_ids')
            return_checks = self.env['all.check.report.wizard'].browse(active_ids)
            for checks in return_checks:
                date_from = checks.date_from
                date_to = checks.date_to
                type = checks.type

            if type == 'check_reject':

                check_reject_ids = self.env['check_followups.check_followups'].search(
                    [('Date', '>=', date_from), ('Date', '<=', date_to),
                     ('state', '=', 'rdc'),
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
                            'communication': reject.id.communication,
                        })

                    total_employee = num_line
                    return check_list_reject

    def get_check_collection(self):
        res = []
        check_list_collection = []
        num_line = 0
        total_employee = 0
        records = False
        active_ids = self._context.get('active_ids')
        return_checks = self.env['all.check.report.wizard'].browse(active_ids)
        for checks in return_checks:
            date_from = checks.date_from
            date_to = checks.date_to
            type = checks.type
            print("lllllll")

        if type == 'check_collection':

            check_collection_ids = self.env['check_followups.check_followups'].search(
                [('Date', '>=', date_from), ('Date', '<=', date_to),
                 ('state', '=', 'under_collection'),
                 ])
            print(check_collection_ids,';;')
            if check_collection_ids:
                records = self.env['check_followups.check_followups'].browse(check_collection_ids)

                for collect in records:
                    num_line += 1
                    check_list_collection.append({
                        'num_line': num_line,
                        'account_holder': collect.id.account_holder.name,
                        'check_no': collect.id.check_no,
                        'date': collect.id.Date,
                        'amount': collect.id.amount,
                        'notes': collect.id.notes,
                        'communication': collect.id.communication,
                    })

                total_employee = num_line

                return check_list_collection

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
            if data['form'][0]['type'] == 'check_recivce':
                docargs['check_ids'] = self.get_check()
            elif data['form'][0]['type'] == 'check_return':
                docargs['check_return_ids'] = self.get_check_return()
            elif data['form'][0]['type'] == 'check_waiting':
                docargs['check_waiting_ids'] = self.get_check_waiting()
            elif data['form'][0]['type'] == 'check_reject':
                docargs['check_reject_ids'] = self.get_check_reject()
            elif data['form'][0]['type'] == 'check_collection':
                docargs['check_collection_ids'] = self.get_check_collection()
        return self.env['report'].render('check_followups.all_check_report', docargs)
