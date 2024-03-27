{
    'name': 'Loyalty Extend',
    'version': '1.0',
    'category': 'Sales/CRM',
    'author': 'NAMG',
    'sequence': '10',
    'summary': 'Workflow loyalty',
    'depends': [
        'loyalty', 'crm_his_13', 'crm_booking_order'
    ],
    'data': [
        'data/cron_job.xml',
        'data/data.xml',
        'data/default_data.xml',
        'security/ir.model.access.csv',
        'view/inherit_view_loyalty.xml',
        'view/inherit_rank_view.xml',
        'view/nguoi_than_view.xml',
        'view/history_used_reward.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [],
}
