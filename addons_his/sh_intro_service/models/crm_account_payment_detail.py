import json
import os
from datetime import datetime, date, timezone, timedelta
from dateutil.relativedelta import relativedelta
from dateutil import tz
from odoo import fields, api, models, _
from odoo.exceptions import UserError, ValidationError, AccessError
import odoo.tools as tools
from odoo.tools import float_compare
import logging
from odoo import http
from odoo.http import request
import math

class CRMAccountPaymentDetail(models.Model):
    _inherit = 'crm.account.payment.detail'

    # def _get_service_referral_allocation_rate(self):
    #     try:
    #         return self.sudo().env.company.x_service_referral_allocation_rate
    #     except ValueError:
    #         raise UserError(
    #             'Bạn chưa cấu hình Tỉ lệ phân bổ giới thiệu dịch vụ cho công ty %s. Vui lòng vào Thiết lập/ Kế toán/ Internal Account để kiểm tra lại' % self.env.company.name)

    allocation_rate = fields.Float(string='Tỉ lệ (%)', digits='Discount')
    # company_id = fields.Many2one('res.company', string="Công ty thực hiện dịch vụ",
    #                              related='crm_line_id.company_id', readonly=True, store=True)
    allocation_amount = fields.Float(string='Thành tiền', digits='Product Price')

    @api.onchange('allocation_rate')
    def onchange_allocation_rate(self):
        for detail in self:
            detail.allocation_amount = detail.allocation_rate * detail.total / 100





