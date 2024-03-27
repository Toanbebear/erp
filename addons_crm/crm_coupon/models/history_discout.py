from odoo import fields, models, api, _


class HistoryDiscount(models.Model):
    _inherit = 'crm.line.discount.history'
    _description = 'Inherit history discount'

    discount_program_list = fields.Many2many('crm.discount.program.list', 'discount_list_id', 'history_id', string='Coupon chi tiết')
    crm_line_product = fields.Many2one('crm.line.product', 'Line Booking Product')

    # đối với trường hợp giảm giá đơn hàng cần bổ số giá trị giảm thực tế trên crm line
    value = fields.Float('Giá trị giảm')
