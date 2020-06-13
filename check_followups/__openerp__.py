# -*- coding: utf-8 -*-
{
    'name': "Check Followup",

    'summary': """
        It Help You To Keep Tracking of Your Checks""",

    'description': """
        This Module Handle The Check Payment and Keep
        Tracking Your check book .
    """,

    'author': "intellisoft Team",
    'category': 'Accounting',
    'version': '0.1',

    'depends': [
        'base','account',
        'account_accountant',
        'account_accountant',
    ],


    'data': [
        'security/ir.model.access.csv',
        'wizard/print_check_wizard.xml',
        'wizard/check_replacement_wizard.xml',
        'wizard/vendor_check_report_wizard_view.xml',
        'wizard/all_check_report_wizard_view.xml',
        'views/views.xml',
        'report/check_bank_template.xml',
        'views/bankTamplate.xml',
        'views/company.xml',
        'report/reports.xml',
        'report/all_check_report_view.xml',
        'report/vendor_check_report_view.xml',
   
    ],
    'demo': [
        'demo/demo.xml',
    ],
    'application': True,
}
