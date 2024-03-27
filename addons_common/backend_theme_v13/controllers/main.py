# -*- coding: utf-8 -*-
# Copyright 2016, 2019 Openworx
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import base64
from odoo.http import Controller, request, route
from werkzeug.utils import redirect

DEFAULT_IMAGE = '/backend_theme_v13/static/src/img/material-background.png'
DEFAULT_BRAND_LOGO = '/backend_theme_v13/static/src/img/brand.png'


class DasboardBackground(Controller):

    @route(['/dashboard'], type='http', auth='user', website=False)
    def dashboard(self, **post):
        user = request.env.user
        company = user.company_id
        brand = company.brand_id
        if company.dashboard_background:
            image = base64.b64decode(company.dashboard_background)
        elif brand.dashboard_background:
            image = base64.b64decode(brand.dashboard_background)
        else:
            return redirect(DEFAULT_IMAGE)

        return request.make_response(
            image, [('Content-Type', 'image')])

    @route(['/brand-icon'], type='http', auth='user', website=False)
    def brand_logo(self, **post):
        user = request.env.user
        company = user.company_id
        brand = company.brand_id
        if brand.logo:
            image = base64.b64decode(brand.icon)
        else:
            return redirect(DEFAULT_BRAND_LOGO)

        return request.make_response(
            image, [('Content-Type', 'image')])
