# -*- coding: utf-8 -*-
# Copyright 2016, 2019 Openworx - Mario Gielissen
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

{
    "name": "SCI Theme",
    "summary": "SCI Backend Theme V13",
    "version": "13.0.0.1",
    "category": "Theme/Backend",
    "website": "http://www.scisoftware.xyz",
	"description": """
		SCI Backend Theme
    """,
	'images':[
        'images/screen.png'
	],
    "author": "SCI Dev",
    "license": "LGPL-3",
    "installable": True,
    "depends": [
        'web',
        'ow_web_responsive',
        'sci_brand',
    ],
    "data": [
        'views/assets.xml',
		'views/res_company_view.xml',
		'views/res_brand_view.xml',
		#'views/users.xml',
        #'views/sidebar.xml',
    ],
    'qweb': [
        "static/src/xml/menu.xml",
    ]

}

