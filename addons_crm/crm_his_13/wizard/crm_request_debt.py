from odoo import fields, api, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, AccessError, ValidationError, Warning
import datetime
from datetime import timedelta
import logging
from lxml import etree
import json


class RequestDebt(models.TransientModel):
    _name = 'crm.debt.request'
    _description = 'Request Debt'

    # Todo Bỏ model này

    name = fields.Char('Desc')
    type_action = fields.Selection([('payment', 'Thanh toán đủ'), ('debt', 'Duyệt nợ và thanh toán')],
                                   string='Hành động thực hiện', default='payment')
    sale_order_id = fields.Many2one('sale.order', string='Order')
    partner_id = fields.Many2one('res.partner', string='Partner')
    walkin_id = fields.Many2one('sh.medical.appointment.register.walkin', string='Phiếu khám')
    company_id = fields.Many2one('res.company', string='Company')
    amount_total = fields.Monetary('Amount total')
    amount_owed = fields.Monetary('Amount owed')
    currency_id = fields.Many2one('res.currency', string='Currency')
