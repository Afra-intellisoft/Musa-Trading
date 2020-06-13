#######################################################################
#    IntelliSoft Software                                             #
#    Copyright (C) 2017 (<http://intellisoft.sd>) all rights reserved.#
#######################################################################

{
    'name': 'IntelliSoft Accounting Approval 10',
    'author': 'IntelliSoft Software',
    'website': 'http://www.intellisoft.sd',
    'description': "A module that customizes the accounting module. Migrated to Odoo 10.",
    'depends': ['is_accounting_10','check_followups', 'hr','mail','base'],
    'category': 'Accounting',

    'data': [
        'security/security_view.xml',
        'security/ir.model.access.csv',
        # 'data/load.xml',
        'views/approval_sequence.xml',
        'views/res_users_view.xml',
        'views/res_currency_view.xml',
        # 'views/account_voucher_view.xml',
        'views/finance_approval_view.xml',
        'views/reports_registration.xml',
        'views/report_finance_approval.xml',
        'views/v_bill.xml',
        'wizard/group_check_view.xml',

    ],
    'installable': True,
    'auto_install': False,
}