# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class CrmPhoneCall(models.Model):
    _inherit = 'crm.phone.call'

    call_date = fields.Datetime(index=True)
    company2_id = fields.Many2many('res.company', 'crm_phone_call_res_company_rel', 'phone_call_id', 'company_id',
                                   string='Công ty share', related="crm_id.company2_id", store=True,
                                   index=False, ondelete='cascade')
