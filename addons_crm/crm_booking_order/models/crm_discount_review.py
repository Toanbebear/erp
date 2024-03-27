from odoo import fields, api, models
from lxml import etree
from odoo.exceptions import ValidationError
from odoo.tools.translate import _
from datetime import datetime, date, timedelta
import json
from dateutil.relativedelta import relativedelta
import pytz


class CRMDiscountReview(models.Model):
    _inherit = 'crm.discount.review'

    line_product = fields.Many2one('crm.line.product', string='Dòng sản phẩm', tracking=True)

    @api.depends('crm_line_id', 'total_amount_after_discount', 'line_product')
    def calculate_total_discount_cash(self):
        super(CRMDiscountReview, self).calculate_total_discount_cash()
        for record in self:
            if record.type == 'so' and record.line_product:
                if record.type_discount == 'discount_pr':
                    record.total_discount_cash = record.line_product.total_before_discount * (record.discount / 100)
                elif record.type_discount == 'discount_cash':
                    record.total_discount_cash = record.discount

    @api.depends('discount', 'booking_id', 'crm_line_id', 'order_id', 'order_line_id', 'line_product', 'type')
    def _compute_total_amount_after_discount(self):
        super(CRMDiscountReview, self)._compute_total_amount_after_discount()
        for record in self:
            if record.discount and record.booking_id and record.line_product and record.type == 'so':
                record.total_amount_after_discount = record.line_product.total - record.total_discount_cash

    def add_note_refuse(self):
        res = super(CRMDiscountReview, self).add_note_refuse()
        if self.line_product:
            self.line_product.stage_line_product = 'new'
        return res

    def approve(self):
        super(CRMDiscountReview, self).approve()
        if self.rule_discount_id and self.type == 'so' and self.line_product:
            self.line_product.discount_other += self.total_discount_cash
            self.stage_id = 'approve'
            self.color = 4
            self.user_approve = self.env.user.id
            self.line_product.crm_discount_review = self.id
            self.line_product.stage_line_product = 'new'

