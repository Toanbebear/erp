# -*- encoding: utf-8 -*-
{
    'name': "SCI Smart button",
    'version': '1.0.0',
    'summary': 'SCI Smart button',
    'description': """Button khảo sát, conatct,Survey, góp ý,... trong form view """,
    'author': 'ThongDH-2001',
    "depends": [],
    'data': [
        'data/ir_config_parameter.xml',
        'views/assets.xml',

    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': ['static/src/xml/smart_button_template.xml'],
}
