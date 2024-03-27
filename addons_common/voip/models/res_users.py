# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class ResUsers(models.Model):
    _inherit = 'res.users'

    cs_voice_token_ids = fields.One2many("api.access.token.cs", "user_id",
                                         string="Caresoft Voice Access Tokens ",
                                         domain=[('token_type', '=', 'voice')]
                                         )
