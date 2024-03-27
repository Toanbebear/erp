from odoo import models, fields, api


class HistoryRelativeReward(models.Model):
    _name = "history.relative.reward"
    _description = "Lịch sử sử dụng quà tặng của người thân"

    loyalty = fields.Many2one('crm.loyalty.card', string='Thẻ')
    booking = fields.Many2one('crm.lead', string='Booking')
    line = fields.Many2one('crm.line')
    # line_product = fields.Many2one('crm.line.product')
    product = fields.Many2one('product.product', string='Dịch vụ/Sản phẩm')
    currency_id = fields.Many2one('res.currency')
    total = fields.Monetary('Tiền phải thu')
    total_received = fields.Monetary('Tiền đã thu')
    total_remaining = fields.Monetary('Tiền còn lại')
    total_used = fields.Monetary('Tiền đã sử dụng')

    @api.depends('total_received', 'total_remaining')
    def calculate_total_used(self):
        for record in self:
            record.total_used = 0
            if record.total_received and record.total_remaining:
                record.total_used = record.total_received - record.total_remaining

    @api.depends('line', 'line.sale_order_line_id')
    def calculate_product(self):
        for record in self:
            record.total = 0
            record.total_received = 0
            record.total_remaining = 0
            if record.line and record.line.sale_order_line_id:
                line = record.line
                record.total = line.total
                record.total_received = line.total_received
                record.total_remaining = sum(line.sale_order_line_id.mapped('price_subtotal'))
            # if record.line_product and record.line_product.remaining_amount:
            #     line = record.line_product
            #     record.total = line.total
            #     record.total_received = line.total_received
            #     record.total_remaining = sum(line.order_line.mapped('price_subtotal'))


