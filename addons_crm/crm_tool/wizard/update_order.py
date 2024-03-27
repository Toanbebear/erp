from odoo import api, fields, models
from odoo.exceptions import ValidationError


class UpdateOrderWizard(models.TransientModel):
    _name = 'crm.update.order'
    _description = 'CRM Update Sale Order Wizard'

    def domain_get_crm_line(self):
        order_id = self.env['sale.order'].browse(self.env.context.get('default_order_id'))
        booking = order_id.booking_id
        line = self.env['crm.line'].sudo().search([('crm_id', '=', booking.id)])
        return [('id', 'in', line.ids)]

    ACTION_TYPE = [('attach_booking', 'Gắn Booking vào Order'),
                   ('update_order_line', 'Cập nhật từng dòng sản phẩm')]
    action_type = fields.Selection(ACTION_TYPE, string='Bạn muốn ...')
    order_id = fields.Many2one('sale.order', string='Báo giá')
    partner_id = fields.Many2one(related="order_id.partner_id", string="Khách hàng")
    partner_code = fields.Char(related="partner_id.code_customer", string="Mã khách hàng")
    partner_phone = fields.Char(related="partner_id.phone", string="Số điện thoại")
    booking_id = fields.Many2one('crm.lead', string='Booking',
                                 domain="[('type', '=', 'opportunity'), ('partner_id', '=', partner_id)]")
    order_line_id = fields.Many2one('sale.order.line', string='Dòng sản phẩm',
                                    domain="[('order_id', '=', order_id)]")
    uom_price = fields.Float('Đơn vị xử lý')
    price_unit = fields.Float('Đơn giá')
    discount = fields.Float('Chiết khấu (%)')
    discount_cash = fields.Monetary('Giảm giá tiền mặt (Giảm cho một buổi)')
    sale_to = fields.Monetary('Giảm còn (Giảm cho một buổi)')
    other_discount = fields.Monetary('Giảm khác (Giảm cho một buổi)')
    currency_id = fields.Many2one('res.currency', string='Tiền tệ', tracking=True, related='order_id.currency_id')
    line = fields.Many2one('crm.line', string='Gắn với crm line', domain=domain_get_crm_line)

    @api.onchange('order_line_id')
    def onchange_order_line(self):
        if self.order_line_id:
            self.uom_price = self.order_line_id.uom_price
            self.price_unit = self.order_line_id.price_unit
            self.discount = self.order_line_id.discount
            self.discount_cash = self.order_line_id.discount_cash
            self.sale_to = self.order_line_id.sale_to
            self.other_discount = self.order_line_id.other_discount
            self.line = self.order_line_id.crm_line_id.id

    def update_order(self):
        self.ensure_one()
        if not self.env.user.has_group('crm_tool.group_tool'):
            raise ValidationError(
                'Bạn không có quyền thao tác chức năng này.\nLiên hệ Giám đốc CRM để biết thêm thông tin ^^')
        if self.action_type == 'attach_booking':
            if self.order_id.booking_id:
                raise ValidationError(
                    'Báo giá này đã được gắn với %s. Bạn không thể cập nhật lại' % self.order_id.booking_id.name)
            # elif self.order_id.state not in ['sale', 'done']:
            #     raise ValidationError('Bạn không thể gắn Booking vào đơn hàng này do đã được xác nhận')
            # elif self.order_id.pricelist_type != 'product':
            #     raise ValidationError('Chức năng này không được sử dụng cho HÓA ĐƠN BÁN DỊCH VỤ')
            else:
                self.order_id.write({
                    'booking_id': self.booking_id.id
                })
        elif self.action_type == 'update_order_line':
            # if self.order_id.invoice_ids and ('draft' in self.order_id.invoice_ids.mapped('state')):
            #     raise ValidationError(
            #         'Bạn không thể chỉnh sửa vì SO này đã có hóa đơn nháp.\nVui lòng hủy hóa đơn nháp đó rồi thử lại')
            # elif self.order_id.invoice_ids and ('posted' in self.order_id.invoice_ids.mapped('state')):
            #     raise ValidationError(
            #         'Bạn không thể chỉnh sửa vì SO này đã có hóa đơn đã vào sổ.\nVui lòng làm theo các bước sau:\n\n1. Đưa hóa đơn về trạng thái Nháp rồi HỦY hóa đơn đó\n2.Thực hiện chỉnh sửa SO về giá trị mong muốn\n3.Thực hiện tạo hóa đơn cho SO vừa chỉnh sửa và xác nhận (vào sổ) hóa đơn đó')
            # else:
            self.order_line_id.write({
                'uom_price': self.uom_price,
                'price_unit': self.price_unit,
                'discount': self.discount,
                'discount_cash': self.discount_cash,
                'sale_to': self.sale_to,
                'other_discount': self.other_discount,
                'crm_line_id': self.line.id
            })
        # elif self.action_type == 'update_order_line':
        #     raise ValidationError(
        #         'Bạn không được cấp quyền sử dụng tính năng này. Hãy liên hệ:\nNGUYỄN KHÁNH HƯƠNG GIANG (843) - Miền Bắc \nLÊ ĐÌNH ANH (877) - Miền Nam')

        # UPDATE ORDERS
        loyalty = self.env['crm.loyalty.card'].search(
            [('partner_id', '=', self.partner_id.id), ('brand_id', '=', self.order_id.booking_id.brand_id.id)])
        if loyalty:
            loyalty.amount = sum(
                [so.amount_total for so in self.partner_id.sale_order_ids if so.state in ('sale', 'sent')])
            loyalty.set_rank(loyalty.amount, loyalty.rank_id, loyalty.partner_id)
