from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class CrmCancelVoucher(models.TransientModel):
    _name = 'crm.cancel.voucher'

    crm_id = fields.Many2one('crm.lead', string='Booking')
    line_ids = fields.Many2many('crm.line', string='Dịch vụ',
                                domain="[('crm_id', '=', crm_id),('stage', 'in', ['new', 'chotuvan']), ('number_used', '=', 0), ('prg_voucher_ids', '!=', False)]")
    line_product_ids = fields.Many2many('crm.line.product', string='Sản phẩm',
                                        domain="[('booking_id', '=', crm_id),('stage_line_product', '=', 'new'),('prg_voucher_ids', '!=', False)]")
