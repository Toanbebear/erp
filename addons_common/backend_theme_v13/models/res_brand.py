# -*- coding: utf-8 -*-
# Copyright 2016, 2019 Openworx
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import models, fields


class ResBrand(models.Model):
    _inherit = 'res.brand'

    dashboard_background = fields.Binary(attachment=True)
    icon = fields.Binary(string="Brand icon")
