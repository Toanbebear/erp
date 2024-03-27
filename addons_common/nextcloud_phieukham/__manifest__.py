# -*- coding: utf-8 -*-
{
    'name': 'Ảnh phiếu khám trên Nextcloud',
    'version': '1.0',
    'author': 'Thongdh',
    'sequence': '10',
    'summary': 'Đồng bộ hình ảnh phiếu khám với nextcloud',
    'depends': [
        "nextcloud", "shealth_all_in_one"
    ],
    'data': [
        "security/ir.model.access.csv",
        "views/walkin.xml",

    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'qweb': ["static/xml/*.xml"],
}
