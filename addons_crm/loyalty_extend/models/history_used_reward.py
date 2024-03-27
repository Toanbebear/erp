from odoo import api, fields, models


class HistoryUsedReward(models.Model):
    _name = 'history.used.reward'
    _description = 'Lịch sử sử dụng quà tặng thẻ thành viên'

    reward_line_id = fields.Many2one('crm.loyalty.line.reward', 'Quà tặng khách hàng')
    date_used = fields.Datetime('Thời điểm sử dụng')
    booking_id = fields.Many2one('crm.lead', 'Booking sử dụng')
    loyalty_id = fields.Many2one('crm.loyalty.card', 'Thẻ thành viên')
    line = fields.Many2one('crm.line')
    line_product = fields.Many2one('crm.line.product')
    product = fields.Many2one('product.product', string='Dịch vụ/Sản phẩm')
    currency_id = fields.Many2one('res.currency')
    total = fields.Monetary('Tiền phải thu')
    total_received = fields.Monetary('Tiền đã thu')
    total_remaining = fields.Monetary('Tiền còn lại')
    total_used = fields.Monetary('Tiền đã sử dụng')
    stage = fields.Selection([('done', 'Đã sử dụng'), ('upcoming', 'Đang xử lý'), ('cancel', 'Hủy')])
    customer_name = fields.Char('Tên khách hàng')

    @api.depends('total_received', 'total_remaining')
    def calculate_total_used(self):
        for record in self:
            record.total_used = 0
            if record.total_received and record.total_remaining:
                record.total_used = record.total_received - record.total_remaining

    @api.depends('line', 'line.sale_order_line_id', 'line_product', 'line_product.order_line')
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
            if record.line_product and record.line_product.order_line:
                line = record.line_product
                record.total = line.total
                record.total_received = line.total_received
                record.total_remaining = sum(line.order_line.mapped('price_subtotal'))