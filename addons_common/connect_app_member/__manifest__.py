{
    "name": "API Connect App Member",
    "version": "1.0.1",
    "category": "API",
    "author": "SonZ",
    "website": "",
    "summary": "API Connect App Member",
    "support": "",
    "description": """ RESTFUL API For App Member """,
    "depends": ["web", "crm", "shealth_all_in_one", "queue_job", "contacts"],
    "data": [
        'data/cron_job.xml',
        'security/ir.model.access.csv',
        'views/da_data_default.xml',
        'views/da_cron.xml'
    ],
    "license": "LGPL-3",
    "installable": True,
    "auto_install": False,
}
