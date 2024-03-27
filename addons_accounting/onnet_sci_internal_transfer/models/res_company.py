from odoo import fields, api, models, _
from odoo.exceptions import UserError, AccessError, ValidationError, Warning
import datetime
from datetime import timedelta
import logging
import json

class ResCompany(models.Model):
    _inherit = 'res.company'

    internal_transfer_account = fields.Many2one('account.account', string=_('Phải thu điều chuyển nội bộ'))
    x_internal_payable_account_id = fields.Many2one('account.account', 'Tài khoản phải trả nội bộ')
    x_journal_internal_id = fields.Many2one('account.journal', string='Sổ nhật ký tài khoản nội bộ')
    x_service_referral_allocation_rate = fields.Float(string='Tỉ lệ phân bổ giới thiệu dịch vụ (%)', digits='Discount', default=0.0)
