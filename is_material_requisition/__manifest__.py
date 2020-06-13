# -*- coding: utf-8 -*-


{
    'name': "Material Requisition Module for Golden Square",

    'description': """
            Intellisoft Module for Material Requisition
    """,
    'author': "Intellisoft",
    'website': "http://www.intellisoft.sd",
    'category': 'Inventory',
    'version': '1.0',
    'depends': [
        'stock',
        'purchase_requisition','account','project',
        'hr',
    ],
    'data': [
        'security/stock_custom_security.xml',
        'security/ir.model.access.csv',
        'views/material_request_views.xml',
        'wizard/request_approve_quantities_views.xml',
        'data/material_request.xml',


    ],
    'auto_install': False,
}
