from odoo import models, fields, api


class HistoryRelativeReward(models.Model):
    _name = "history.relative.reward"
    _description = "Lịch sử sử dụng quà tặng của người thân"

    loyalty = fields.Many2one('crm.loyalty.card', string='Thẻ')
    booking = fields.Many2one('crm.lead', string='Booking')
    partner = fields.Many2one('res.partner', related='booking.partner_id', store=True)
    line = fields.Many2one('crm.line')
    line_product = fields.Many2one('crm.line.product')
    product = fields.Many2one('product.product', string='Dịch vụ/Sản phẩm')
    currency_id = fields.Many2one('res.currency')
    total = fields.Monetary('Tiền phải thu')
    total_received = fields.Monetary('Tiền đã thu')
    total_remaining = fields.Monetary('Tiền còn lại')
    total_used = fields.Monetary('Tiền đã sử dụng')
    customer_name = fields.Char('Người thân sử dụng')
    is_active = fields.Boolean('Active', compute='check_active', store=True)
    stage = fields.Selection([('done', 'Đã sử dụng'), ('upcoming', 'Đang xử lý'), ('cancel', 'Hủy')])

    @api.depends('line', 'line.stage', 'line_product', 'line_product.stage_line_product')
    def check_active(self):
        for record in self:
            record.is_active = True
            if record.line and record.line.stage == 'cancel':
                record.is_active = False
            elif record.line_product and record.line_product.stage_line_product == 'cancel':
                record.is_active = False

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


