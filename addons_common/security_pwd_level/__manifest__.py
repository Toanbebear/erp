{
    'name': 'Security Level',
    'version': '1.0',
    'author': 'z',
    'sequence': '1',
    'summary': 'Security Level',
    'depends': [
        'base',
        'web',
        'auth_signup'
    ],
    'data': [
        'views/change_pwd_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [],
}
