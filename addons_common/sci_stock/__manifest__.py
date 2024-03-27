# -*- encoding: utf-8 -*-
{
    'name': "SCI Stock",
    'version': '1.0.0',
    'summary': 'SCI Stock',
    'category': 'Operations/Inventory',
    'description': """Module viết các vấn đề liên quan đến kho""",
    'author': 'NamAhihi',
    "depends": ['stock', 'shealth_all_in_one'],
    'data': [
        'data/cron_job.xml',
        'views/stock_picking_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
