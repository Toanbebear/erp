{
    'name': 'Tạo lịch hẹn với khách hàng',
    'version': '1.0',
    'author': 'Nguyễn Ngọc Hải',
    'sequence': '10',
    'summary': 'Tạo lịch hẹn với khách hàng thông qua Calendar',
    'depends': [
        'crm_his_13',
        'calendar',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/calendar_event.xml',
        'views/crm_lead.xml',
        'views/phonecall.xml',
        'views/doctor_schedule.xml',
        'views/assets.xml',
        'wizard/create_an_appointment.xml',
        'wizard/select_service.xml',

        # 'wizard/check_partner_qualify.xml',
    ],
    'sequence': 0,
    'installable': True,
    'application': False,
    'auto_install': False,
    'qweb': [
        'static/src/xml/crm_calendar.xml',
        # 'static/src/xml/notification_calendar.xml',
    ],
}
