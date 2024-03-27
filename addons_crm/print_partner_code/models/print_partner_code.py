# -*- coding: utf-8 -*-
#############################################################################
#
#    SCI SOFTWARE
#
#    Copyright (C) 2019-TODAY SCI Software(<https://www.scisoftware.xyz>)
#    Author: SCI Software(<https://www.scisoftware.xyz>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import json
import logging

from odoo import fields, models, api

_logger = logging.getLogger(__name__)


class PrintPartnerCode(models.Model):
    _name = 'print.partner.code.data'
    _description = 'Bảng lưu thông tin in mã khách hàng'

    code = fields.Char('Mã khách hàng')
    name = fields.Char('Tên khách hàng')
    gender = fields.Char('Giới tính')
    birth_date = fields.Char('Ngày sinh')
    printed = fields.Boolean('Đã in?', default=False)
    company_id = fields.Many2one('res.company', 'Công ty')
    partner_id = fields.Many2one('res.partner', 'Khách hàng')
    # qr_id = fields.Binary(related='partner_id.qr_id')

    @api.model
    def attendance_scan(self):
        data = self.env['print.partner.code.data'].sudo().search([('printed', '=', False)])
        partner_ids = data.mapped('partner_id')
        return self.env.ref('print_partner_code.report_partner_code_165x155').with_context(
            discard_logo_check=True).report_action(partner_ids)
