{
    'name': 'is_manufacturing_musa ',
    'version': '2.0',
    'author': 'Intellisoft',
    'website':'http://www.intellisoft.sd',
    'sequence': 4,
    'category': 'Manufacturing',
    'description':"A module that manages manufacturing cost (Odoo 10).",

    'depends': ['mrp','is_accounting_approval_10','maintenance','is_hr_customization'],
    'data': [
        'security/ir.model.access.csv',
        'views/is_manufacturing.xml',
        'views/mrp_adjustment.xml',
        'views/is_maintenance_view.xml',
        'views/manfact_report.xml',
        'views/is_equipments_report.xml',
        'views/is_equipments_details_report.xml',
        'wizard/daily_production_view.xml',
        'wizard/daily_production_report.xml',
        'wizard/production_shift_report.xml',
        'wizard/production_shift_view.xml',
        'wizard/production_product_view.xml',
        'wizard/production_product_report.xml',
        'wizard/production_shift_worker_view.xml',
        'wizard/production_shift_worker_report.xml',
        'data/is_manufact_sequence.xml',
    ],
    'application': True,
    'installable': True,
    'auto_install': False,
}

