{
    'name': 'Loyalty Paris',
    'version': '1.0',
    'category': 'Sales/CRM',
    'author': 'NAMG',
    'sequence': '10',
    'summary': 'Workflow loyalty',
    'depends': [
        'loyalty', 'shealth_all_in_one'
    ],
    'data': [
        'data/cron_job.xml',
        'security/ir.model.access.csv',
        'view/inherit_view_loyalty.xml',
        'view/inherit_rank_view.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [],
}
