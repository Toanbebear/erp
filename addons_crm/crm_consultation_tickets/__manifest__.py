# -*- coding: utf-8 -*-
# Copyright 2016, 2019 Openworx - Mario Gielissen
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

{
    "name": "CRM Consultation",
    "summary": "Phiếu tư vấn ",
    "version": "13.0.0.1",
    "category": "CRM",
    "website": "",
    "description": """
		Phiếu tư vấn trên CRM
    """,
    "author": "Nguyễn Ngọc Hải",
    "installable": True,
    "depends": [
        'web',
        'crm_his_13',

    ],
    "data": [
        'data/ir_sequence.xml',
        'data/paper.xml',
        'security/ir.model.access.csv',
        'views/view_booking.xml',
        'views/assets.xml',
        'views/consultation_ticket_template.xml',
        'views/consultation_report.xml',
        'views/consultation_report_template.xml',

        # #'views/users.xml',
        # #'views/sidebar.xml',
    ],

}
