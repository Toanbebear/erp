{
    'name': 'Information Employee',
    'version': '1.0',
    'category': 'Human Resources',
    'sequence': 1,
    'summary': 'Centralize employee information',

    'company': 'Tập đoàn SCI Group',
    'website': "scigroup.com.vn",
    'depends': [
        'sci_hrms',
        'hr',
        'base_unit_vn',
        'qrcodes'
    ],
    'data': [
        'views/employee_information_template.xml',
        'views/hr_employee_inherit.xml',
    ],
    'qweb': [
    ],
    'demo': [],
    'images': [],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
###################################################################################
