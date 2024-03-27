# -*- coding: utf-8 -*-
{
    'name': 'Ảnh Booking trên Nextcloud',
    'version': '1.0',
    'author': 'Thongdh',
    'sequence': '10',
    'summary': 'Đồng bộ hình ảnh booking với nextcloud',
    'depends': [
        "nextcloud", "crm_base"
    ],
    'data': [
        "security/ir.model.access.csv",
        "views/booking.xml",
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'qweb': ["static/xml/*.xml"],
}
