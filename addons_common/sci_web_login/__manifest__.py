# -*- encoding: utf-8 -*-
{
    'name': 'SCI Web Login',
    'summary': 'SCI Web Login',
    'version': '13.0.1.0',
    'category': 'Website/Website',
    'summary': """
The new configurable SCI Web Login
""",
    'author': "SCI",
    'website': "https://www.scigroup.com.vn",
    'license': 'AGPL-3',
    'depends': ['web', 'website'],
    'data': [
        'data/ir_config_parameter.xml',
        'templates/website_templates.xml',
        'templates/webclient_templates.xml',
    ],
    'qweb': [
    ],
    'installable': True,
    'application': True,
    'images': ['static/description/banner.png'],
}
