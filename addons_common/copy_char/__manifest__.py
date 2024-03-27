# -*- encoding: utf-8 -*-
{
    'name': "Sao chép ký tự",
    'version': '13.0.0.4',
    'summary': 'Sao chép ký tự',
    'category': 'Other',
    'description': """Sao chép ký tự""",
    'author': 'Dungntp',
    "depends" : ['web'],
    'data': [
             'views/copy_char_template.xml',
             ],
    'qweb': [
        "static/src/xml/copy_char.xml",
    ],
    'installable': True,
    'application'   : True,
    'auto_install'  : False,
}
