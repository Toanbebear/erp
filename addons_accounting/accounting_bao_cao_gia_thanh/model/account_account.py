# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import timedelta

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AccountAccount(models.Model):
    _inherit = "account.account"

    is_154_erp = fields.Boolean('Is 154 Erp')
    is_154_cl = fields.Boolean('Is 154 CL')
    is_632 = fields.Boolean('Is 632')
    active = fields.Boolean('Có hiệu lực', default=True)


