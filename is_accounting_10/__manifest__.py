# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name' : 'is Accounting 10',
    'version' : '0.1',
     'author': 'IntelliSoft Software',
    'website': 'http://www.intellisoft.sd',
    'sequence': 110,
    'category': 'Others',
    'summary' : 'IntelliSoft Accounting  Musa Customization Module',
    'description': """ Manage Taxes , Zakat ,Collect Currency ,Update Rate """,
    'category': 'Accounting',
    'depends' : [
        'account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/taxes_view.xml',
        'views/is_account_view.xml',
        'data/account_sequence.xml',
        'views/is_zakah_view.xml',
        'views/currency_view.xml',
        'wizard/currencey_report_wizard_view.xml',
        'reports/currency_valuation_report_view.xml',
        'reports/reports.xml',

    ],

    'demo': [

    ],

    'installable' : True,
    'application' : True,
}
