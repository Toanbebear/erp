# -*- coding: utf-8 -*-

{
    'name': 'Web xls',
    'category': 'Tools',
    'version': '1.0',
    "author" : 'Helmi Dhaoui',
    'website' : 'http://tunisofts.com',
    'description':
        """
Odoo Web xls view module.
========================

This module provides an xls view for the Odoo Web Client.
        """,
    'depends': ['web'],
    'data': [
        'views/webclient_templates.xml',
    ],
    'qweb': [
        "static/src/xml/web_xls.xml",
    ],
    'images': ['static/description/icon.png'],
    'bootstrap': True,  # load translations for login screen
    'live_test_url': 'https://www.youtube.com/embed/3mqaWgg38dc',
    'installable': True,
}
