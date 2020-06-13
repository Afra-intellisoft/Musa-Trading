# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Employee Directory',
    'version': '1.1',
    'category': 'Human Resources',
    'author': 'Intellisoft',
    'sequence': 75,
    'summary': 'Jobs, Departments, Employees Details',
    'description': """
Human Resources Management
==========================

This application enables you to manage important aspects of your company's staff and other details such as their skills, contacts, working time...


You can manage:
---------------
* Employees and hierarchies : You can define your employee with User and display hierarchies
* HR Departments
* HR Jobs
    """,
    'website': 'http://www.intellisoft.sd',
    # 'images': [
    #     'images/hr_department.jpeg',
    #     'images/hr_employee.jpeg',
    #     'images/hr_job_position.jpeg',
    #     'static/src/img/default_image.png',
    # ],
    'depends': ['hr',
        'hr_payroll_account','is_accounting_approval_10','is_material_requisition','is_custody_clearance_10'
    ],
    'data': [
        # 'security/hr_security.xml',
        'security/ir.model.access.csv',
        'views/hr_views.xml',
        'views/hr_loan_views.xml',
        'views/hr_warning_views.xml',
        'views/hr_overtime_views.xml',
        'views/hr_end_service_views.xml',
        'views/hr_bonus_views.xml',
        'views/hr_temporary_workers.xml',
        'views/hr_gratuities_employee.xml',
        'views/employee_warning_report_views.xml',
        'views/hr_payslip_views.xml',
        'views/is_hr_custody_view.xml',
        'views/is_hr_manfact_view.xml',
        # 'views/hr_report.xml',
        'report/hr_report.xml',
        'report/is_hr_contract_report.xml',
        'report/is_hr_permission_report.xml',
        'report/hr_employee_report.xml',
        'report/is_hr_resignation_report.xml',
        'report/is_hr_receiving_benefits_report.xml',
        'report/is_hr_payslip.xml',
        # 'wizards/wizard_overtime_view.xml',
        'wizards/pay_sheet_view.xml',
        'wizards/is_bonus_view.xml',
        'wizards/is_bonus_report.xml',
        'wizards/hr_temporary_workers_view.xml',
        'wizards/hr_gratuities_payslip.xml',
        'wizards/loan_wazirds_views.xml',
        'wizards/loan_wazirds_report.xml',
        'wizards/worning_wazirds_views.xml',
        'wizards/worning_wazirds_report.xml',
        'wizards/employee_end_service_view.xml',
        'wizards/employee_end_service_report.xml',
        'wizards/is_emp_manfact_views.xml',
        'wizards/is_emp_manfact_report.xml',
        'wizards/is_letter_internal_view.xml',
        'wizards/is_letter_external_view.xml',
        'wizards/is_letter_internal_report.xml',
        'wizards/is_letter_external_report.xml',
        'wizards/is_external_report.xml',
        # 'views/hr_templates.xml',
        'wizards/hr_overtime_view.xml',
        'wizards/hr_overtime_report.xml',
        'data/hr_employee_sequence.xml',
        'data/payroll_rule_data.xml',
        'data/hr_holidays_data.xml',
    ],
    # 'demo': [
    #     'data/hr_demo.xml'
    # ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [],
}
