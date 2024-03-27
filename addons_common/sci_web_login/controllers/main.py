# -*- encoding: utf-8 -*-
import ast
from odoo.addons.web.controllers.main import Home
import pytz
import datetime
import logging

import odoo
import odoo.modules.registry
from odoo import http
from odoo.http import request
_logger = logging.getLogger(__name__)


#----------------------------------------------------------
# Odoo Web web Controllers
#----------------------------------------------------------
class LoginHome(Home):

    @http.route('/web/login', type='http', auth="none")
    def web_login(self, redirect=None, **kw):
        param_obj = request.env['ir.config_parameter'].sudo()
        request.params['disable_footer'] = ast.literal_eval(param_obj.get_param('login_form_disable_footer')) or False
        request.params['disable_database_manager'] = ast.literal_eval(
            param_obj.get_param('login_form_disable_database_manager')) or False

        request.params['title'] = 'Đăng nhập | ERP SCIGROUP'

        if 'login' in request.params:
            request.params['login'] = request.params['login'].strip()

        return super(LoginHome, self).web_login(redirect, **kw)