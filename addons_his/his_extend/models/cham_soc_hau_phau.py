# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import models, _, fields, api

_logger = logging.getLogger(__name__)


class ChamSocHauPhau(models.Model):
    _inherit = 'sh.medical.patient.rounding'

    partner_id = fields.Many2one('res.partner', string='Khách hàng', related='patient.partner_id')
    dob = fields.Date(string='Ngày sinh', related='partner_id.birth_date')
    address = fields.Char('Địa chỉ', compute='_compute_set_address')

    @api.depends('partner_id')
    def _compute_set_address(self):
        for rec in self:
            if rec.partner_id:
                address = []
                if rec.partner_id.street:
                    address.append(rec.partner_id.street)
                if rec.partner_id.district_id:
                    address.append(rec.partner_id.district_id.name)
                if rec.partner_id.state_id:
                    address.append(rec.partner_id.state_id.name)
                if address:
                    rec.address = ','.join(address)
                else:
                    rec.address = 'Chưa có thông tin địa chỉ'
            else:
                rec.address = 'Chưa có thông tin địa chỉ'