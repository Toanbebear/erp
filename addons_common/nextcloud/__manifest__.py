# -*- coding: utf-8 -*-
{
    'name': 'Connect Nextcloud',
    'version': '1.0',
    'author': 'Thongdh',
    'sequence': '10',
    'summary': 'Kết nối tới Nextcloud',
    'depends': [
        'web_image'
    ],
    'data': [
        "views/nextcloud_setting_views.xml"
    ],
    'external_dependencies': {'python': ['webdavclient3', 'xmltodict', 'PyJWT']},
    'installable': True,
    'application': False,
    'auto_install': False,
    'qweb': [],
}
