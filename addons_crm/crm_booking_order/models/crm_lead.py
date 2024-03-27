from odoo import fields, api, models
from lxml import etree
from odoo.exceptions import ValidationError
from odoo.tools.translate import _
from datetime import datetime, date, timedelta
import json
from dateutil.relativedelta import relativedelta
import pytz


class CRMLead(models.Model):
    _inherit = 'crm.lead'

    crm_line_product_ids = fields.One2many('crm.line.product', 'booking_id', string='Dòng sản phẩm')
    # product_pricelist_id = fields.Many2one('product.pricelist', string='Bảng giá sản phẩm',
    #                                        domain="[('brand_id', '=', self.env.company.brand_id), ('type', '=', 'product')]")

    def open_wizard_create_so(self):
        return {
            'name': 'TẠO BÁO GIÁ',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('crm_booking_order.view_form_crm_create_sale_order').id,
            'res_model': 'crm.create.sale.order',
            'context': {
                'default_partner_id': self.partner_id.id,
                'default_booking_id': self.id,
            },
            'target': 'new'
        }

    def open_wizard_create_multi_line_product(self):
        return {
            'name': 'BÁN NHIỀU SẢN PHẨM',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('crm_booking_order.view_form_create_multi_line_product').id,
            'res_model': 'create.multi.line.product',
            'context': {
                'default_booking': self.id,
            },
            'target': 'new'
        }

    @api.depends('crm_line_ids.total', 'crm_line_ids.stage', 'crm_line_product_ids.total', 'crm_line_product_ids.stage_line_product')
    def set_total(self):
        super(CRMLead, self).set_total()
        for rec in self:
            if rec.crm_line_product_ids:
                for line in rec.crm_line_product_ids:
                    if line.stage_line_product != 'cancel':
                        rec.amount_total += line.total
