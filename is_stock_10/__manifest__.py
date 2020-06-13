{
    'name': 'is_stock_10 ',
    'version': '2.0',
    'author': 'Intellisoft',
    'website':'http://www.intellisoft.sd',
    'sequence': 4,
    'category': 'Warehouse',
    'summary': 'Inventory, Logistics, Warehousing , Shipment',
    'description':"A module that manages customers stock",

    'depends': ['stock','product'],
    'data': [
        'security/ir.model.access.csv',
        'views/is_stock_view.xml',
        'report/lot_serial_report.xml',
    ],
    'application': True,
    'installable': True,
    'auto_install': False,
}

