# -*- coding: utf-8 -*-
{
    'name': "Permission Export Button",
    'description': "Give visibility permission of the Export Button in list view Menu and export label in action Button ...",
    'version': '13.0.1.0',
    'summary': 'A useful module which allows  export Button and export label easily using the access rights and permissions from the user Settings',
    'license': 'LGPL-3',
    'author': 'Ahmed Hegazy, Samah Kandil, \
            Python and Odoo developers',
    'website':"linkedin.com/in/ahmedhegazy1995/\
                linkedin.com/in/samah-kandil-odoo/",
    'category': 'web',
    'images':['static/description/new_logo.png'],
    'depends': ['base','web'],
    'data': [
        'security/security_groups.xml',
        'view/permit_export_view.xml',
    ],
}
