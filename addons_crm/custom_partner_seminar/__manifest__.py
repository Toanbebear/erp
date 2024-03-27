{
    'name': 'Custom partner seminar',
    'version': '1.0',
    'category': 'Partner',
    'author': 'Z',
    'sequence': '10',
    'summary': 'Custom partner',
    'depends': [
        'crm_base'
    ],
    'data': [
        'views/view_booking.xml',
        'views/view_lead.xml',
        'views/view_partner.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'qweb': [],
}
