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
import logging

from odoo import fields, models, api

_logger = logging.getLogger(__name__)


class CrmCheckInOTP(models.Model):
    _name = 'crm.check.in.otp'
    _description = 'OTP check in'

    phone = fields.Char('Số điện thoại')
    otp = fields.Char('Mã OTP')
    company_id = fields.Many2one('res.company', string='Chi nhánh checkin')
    stage = fields.Selection([('sent', 'Đã gửi'), ('error', 'Lỗi')])
