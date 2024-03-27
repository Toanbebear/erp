from odoo import fields, models, api
from odoo.exceptions import ValidationError


class StatementService(models.Model):
    _name = 'statement.service'
    _description = 'Lịch trình thanh toán'

    booking_id = fields.Many2one('crm.lead', string='Booking')
    partner_id = fields.Many2one('res.partner')
    phone = fields.Char(related='booking_id.phone', store=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    date = fields.Datetime('Ngày')
    product_ids = fields.Many2many('product.product', 'statement_product_rel', 'statement_id', 'product_ids', string='Product')
    currency_id = fields.Many2one('res.currency', string='Tiền tệ', default=lambda self: self.env.company.currency_id)
    amount = fields.Monetary('Số tiền')
    note = fields.Text('Ghi chú')
    paid = fields.Boolean('Đã trả')

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        fields = super(StatementService, self).fields_get(allfields, attributes=attributes)

        # Xử lý không cho xuất số điện thoại
        for field_name in fields:
            if field_name in ['phone']:
                fields[field_name]['exportable'] = False

        return fields