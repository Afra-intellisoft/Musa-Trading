# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Assets Management',
    'depends': ['account_asset'],
    'description': """
Assets management
=================
Manage assets owned by a company or a person.
Keeps track of depreciations, and creates corresponding journal entries.

    """,
    'website': 'https://www.odoo.com/page/accounting',
    'category': 'Accounting',
    'author': 'Intellisoft',
    'sequence': 32,
    'demo': [
        #'data/account_asset_demo.yml',
    ],
    'data': [
        #'security/account_asset_security.xml',
        #'security/ir.model.access.csv',
        'views/is_account_asset_view.xml',
        'wizard/asset_view.xml',
        'wizard/asset_report.xml',
        'wizard/report.xml',

    ],
    'qweb': [
        "static/src/xml/account_asset_template.xml",
    ],
}
