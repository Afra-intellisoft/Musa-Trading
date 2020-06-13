#######################################################################
#    IntelliSoft Software                                             #
#    Copyright (C) 2016 (<http://intellisoft.sd>) all rights reserved.#
#######################################################################

{
    'name': 'IntelliSoft Custody Clearance',
    'author': 'IntelliSoft Software',
    'website': 'http://www.intellisoft.sd',
    'description': "A module that allows for custody clearance.",
    'depends': ['account', 'is_accounting_approval_10'],
    'category': 'Accounting',
    'data': [
        'security/security_view.xml',
        'security/ir.model.access.csv',
        'views/clearance_sequence.xml',
        'views/clearance_approval_view.xml',
        'views/reports_registration.xml',
        'views/report_clearance_approval.xml',
    ],
    'installable': True,
    'auto_install': False,
}
