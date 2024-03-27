# -*- coding: utf-8 -*-
{
    'name': 'SCI HRM',
    'version': '1.0.1',
    'category': 'Human Resources',
    'sequence': 1,
    'summary': 'Centralize employee information',
    'author': 'SCI-IT',
    'company': 'SCI Group',
    'website': "https://scigroup.com.vn",
    'depends': ['hr',
                'hr_recruitment',
                'sci_hrms',
                'hr_contract',
                # 'website_hr_recruitment',
                # 'ohrms_core',
                # 'ms_templates',
                # 'web_monetary_format',
                # 'sh_message',
                # 'sci_project',
                'qrcodes'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_team_views.xml',
        'views/hr_department_sector_views.xml',
        'views/hr_group_job_views.xml',
        'views/hr_job_views.xml',
        'views/hr_department_views.xml',
        'views/hr_employee_views.xml',
        'views/sci_hrm_menus.xml',

    ],
    'qweb': [
        # 'static/src/xml/view.xml'
    ],
    'demo': [],
    'images': [],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
###################################################################################
