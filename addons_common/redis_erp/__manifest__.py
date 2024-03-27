{
    'name': 'Redis ERP',
    'version': '1.0',
    'author': 'Nam DZ',
    'sequence': '1',
    'summary': 'Redis ERP',
    'depends': [
        'crm_base', 'base'
    ],
    'data': [
        'data/cron_job.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [],
}
