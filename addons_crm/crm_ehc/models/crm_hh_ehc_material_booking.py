from odoo import fields, models


class MaterialBookingEHC(models.Model):
    _name = 'crm.hh.ehc.material.booking'
    _description = 'Material Booking EHC'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    booking_id = fields.Many2one('crm.lead', string='Booking')
    currency_id = fields.Many2one('res.currency', string='Tiền tệ')
    material_id = fields.Many2one('product.product', string='Thuốc/ Vật tư')
    quantity = fields.Integer('Số lượng')
    unit_price = fields.Monetary('Đơn giá')
    total = fields.Monetary('Thành tiền')
    total_discount = fields.Monetary('Thành tiền')
    key_data = fields.Integer('Key data')


class InheritCRM(models.Model):
    _inherit = 'crm.lead'

    material_ehc_ids = fields.One2many('crm.hh.ehc.material.booking', 'booking_id',
                                                string='Vật tư/ Thuốc tiêu hao EHC')