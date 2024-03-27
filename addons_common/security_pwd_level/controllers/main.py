# -*- encoding: utf-8 -*-
from odoo.addons.website.controllers.main import Website
import logging
import werkzeug
import hashlib
from datetime import datetime
from datetime import timedelta
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


# ----------------------------------------------------------
# Odoo Web web Controllers
# ----------------------------------------------------------
def hash_password(password):
    password_bytes = password.encode('utf-8')

    hash_object = hashlib.sha256(password_bytes)
    return hash_object.hexdigest()


class LoginHome(Website):

    @http.route(website=True, auth="public", sitemap=False)
    def web_login(self, redirect=None, *args, **kw):
        response = super(Website, self).web_login(redirect=redirect, *args, **kw)
        if not redirect and request.params['login_success']:
            if request.env['res.users'].browse(request.uid).has_group('base.group_user'):
                user = request.env['res.users'].sudo().search([('login', '=', request.params['login'])])
                if user:
                    if len(request.params['password']) < 6:
                        user.sudo().write({
                            'pwd_level': 'not_safe',
                        })
                    if user.pwd_date and user.pwd_level == 'safe':
                        date_now = datetime.now().date()
                        if (datetime.now().date() - user.pwd_date).days > 90:
                            user.sudo().write({
                                'pwd_level': 'expired',
                            })
                    if user.pwd_level in ['not_safe', 'expired']:
                        request.session.logout(keep_db=True)
                        url = '/web/form_change_password/%s' % user.id
                        return werkzeug.utils.redirect(url)
                redirect = b'/web?' + request.httprequest.query_string
            else:
                redirect = '/my'
            return http.redirect_with_hash(redirect)
        return response

    @http.route('/web/form_change_password/<int:id>', type='http', auth='public', website=True, sitemap=False)
    def web_change_password(self, id=None, *args, **kw):
        user = request.env['res.users'].sudo().browse(int(id))
        values = {
            'login': user.login
        }
        if user.pwd_level == 'not_safe':
            response = request.render('security_pwd_level.change_pwd', values)
        else:
            response = request.render('security_pwd_level.change_pwd_expired', values)
        return response

    @http.route('/web/change_password', type='http', auth='public', website=True, sitemap=False)
    def change_password(self, *args, **kw):
        user = request.env['res.users'].sudo().search([('login', '=', request.params['login'])])
        pwd_new_hash = hash_password(request.params['password'])
        if user:
            if user.pwd != pwd_new_hash:
                # đổi mk
                record = request.env['change.password.wizard'].sudo().create({
                    'user_ids': [(0, 0, {
                        'wizard_id': False,
                        'user_id': user.id,
                        'user_login': user.login,
                        'new_passwd': request.params['password'],
                    })]
                })
                record.change_password_button()

                # lưu mk
                pwd_hash = hash_password(request.params['password'])
                user.sudo().write({
                    'pwd': pwd_hash,
                    'pwd_level': 'safe',
                    'pwd_date': datetime.now().date(),
                })
                response = request.render('security_pwd_level.change_pwd_success')
                return response
            else:
                pass
        else:
            redirect = b'/web?'
            return http.redirect_with_hash(redirect)

    @http.route('/web/change_password_success', type='http', auth='public', website=True, sitemap=False)
    def change_password_success(self, *args, **kw):
        redirect = b'/web?'
        return http.redirect_with_hash(redirect)
