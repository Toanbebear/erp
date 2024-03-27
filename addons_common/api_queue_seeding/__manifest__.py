{
	'name': 'API Queue Seeding',
	'version': '1.0.0',
	'summary': '',
	'description': '',
	"category": "API",
	'author': 'g',
	'website': 'Website',
	'depends': ['queue_job', 'crm', 'crm_base', 'account', 'crm_sale_payment'],
	'data': [
		'data/data.xml',
		'data/ir_config_param.xml',
		'views/crm_sms_inherit_view.xml'
	],
	'demo': [],
	'installable': True,
	'auto_install': False,
	'application': True,
}