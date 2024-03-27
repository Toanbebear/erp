from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class DiscountReview(models.TransientModel):
    _name = 'discount.review'
    _description = 'Discount Review'

    REASON = [('1', 'Chi nhánh - KH Bảo hành'), ('2', 'Chi nhánh - KH Đối ngoại BGĐ Bệnh viện/Chi nhánh'),
              ('3', 'Chi nhánh - KH Đối ngoại Ban Tổng GĐ Tập đoàn'), ('4', 'Chi nhánh - Thuê phòng mổ'),
              ('5', 'Chi nhánh - Theo phân quyền Quản lý'), ('6', 'MKT - KH từ nguồn Seeding'),
              ('7', 'MKT - KH trải nghiệm dịch vụ'), ('8', 'MKT - KH đồng ý cho dùng hình ảnh truyền thông'),
              ('9', 'MKT – Theo phân quyền Quản lý'), ('10', 'SCI - Áp dụng chế độ Người nhà/CBNV (chưa có Coupon)'),
              ('11', 'SCI - Hệ thống chưa có Coupon theo CTKM đang áp dụng'), ('12', 'Khác (Yêu cầu ghi rõ lý do)'),
              ('13', 'SCI_Chương trình thiện nguyện/Hoạt động của Tập đoàn')]

    name = fields.Text('Ghi chú')
    reason = fields.Selection(REASON, string='Lý do xin giảm')
    crm_line_id = fields.Many2one('crm.line', string='Service',
                                  domain="[('crm_id','=',booking_id),('stage','in',['new', 'processing']),('number_used','=',0),('unit_price', '!=', 0),('discount_review_id', '=', False)]")
    booking_id = fields.Many2one('crm.lead', string='Booking')
    partner_id = fields.Many2one('res.partner', string='Customer')
    type_discount = fields.Selection([('discount_pr', 'Discount percent'), ('discount_cash', 'Discount cash')],
                                     string='Type discount')
    rule_discount_id = fields.Many2one('crm.rule.discount', string='Discount limit')
    discount = fields.Float('Discount')
    type = fields.Selection([('booking', 'Dịch vụ'), ('so', 'Sản phẩm')], string='Giảm giá cho', default='booking')
    order_id = fields.Many2one('sale.order', string='Sale Order')
    order_line_id = fields.Many2one('sale.order.line', string='Order line', domain="[('order_id','=',order_id)]")
    send_email = fields.Boolean('Bạn có muốn gửi mail đến người duyệt không?')
    approver_id = fields.Many2one('res.users', string='Gửi mail tới')

    @api.onchange('rule_discount_id')
    def onchange_rule_discount(self):
        if self.rule_discount_id:
            return {'domain': {'approver_id': [('id', 'in', self.rule_discount_id.user_ids.ids)]}}

    @api.constrains('discount', 'type_discount')
    def error_discount(self):
        for rec in self:
            if rec.type == 'booking' and rec.crm_line_id:
                # Duyệt giảm giá sâu cho BK
                if rec.type_discount == 'discount_pr':
                    if rec.discount <= 0 or rec.discount > 100:
                        raise ValidationError('Chỉ nhận giảm giá trong khoảng từ 0 đến 100 !!!')
                    elif rec.discount < rec.rule_discount_id.discount or rec.discount > rec.rule_discount_id.discount2:
                        raise ValidationError('Tổng giảm giá xin duyệt của line dịch vụ này '
                                              'không thỏa mãn quy tắc giảm giá bạn chọn !!!')
                if rec.type_discount == 'discount_cash':
                    if rec.discount > rec.crm_line_id.total:
                        raise ValidationError(
                            'Số tiền xin duyệt giảm giá đang lớn hơn tổng tiền phải thu của line dịch vụ !!!')
                    # elif (100 - (rec.crm_line_id.total - rec.discount) / rec.crm_line_id.total_before_discount * 100 \
                    #       > rec.rule_discount_id.discount2) or (
                    #         100 - (rec.crm_line_id.total - rec.discount) / rec.crm_line_id.total_before_discount * 100 \
                    #         < rec.rule_discount_id.discount):
                    elif (round((rec.discount / rec.crm_line_id.total_before_discount) * 100,
                                6) > rec.rule_discount_id.discount2) or (
                            round((rec.discount / rec.crm_line_id.total_before_discount) * 100,
                                  6) < rec.rule_discount_id.discount):
                        raise ValidationError('Tổng giảm giá xin duyệt của line dịch vụ này '
                                              'không thỏa mãn quy tắc giảm giá bạn chọn !!!')
            elif rec.type == 'so' and rec.order_line_id:
                # Duyệt giảm giá sâu cho SO (bán sản phẩm)
                if rec.type_discount == 'discount_pr':
                    if rec.discount <= 0 or rec.discount > 100:
                        raise ValidationError('Chỉ nhận giảm giá trong khoảng từ 0 đến 100 !!!')
                    elif (rec.discount > rec.rule_discount_id.discount2) or (
                            rec.discount < rec.rule_discount_id.discount):
                        raise ValidationError('Giảm giá đề xuất '
                                              'không thỏa mãn quy tắc giảm giá bạn chọn !!!')
                if rec.type_discount == 'discount_cash':
                    order_line = rec.order_line_id
                    total_before_discount = order_line.uom_price * order_line.product_uom_qty * order_line.price_unit
                    ceiling_price = total_before_discount * (rec.rule_discount_id.discount2 / 100)
                    floor_price = total_before_discount * (rec.rule_discount_id.discount / 100)
                    if rec.discount > rec.order_line_id.price_subtotal:
                        raise ValidationError('Số tiền xin giảm giá đang lớn hơn giá của line đơn hàng !!!')
                    elif rec.discount > ceiling_price or rec.discount < floor_price:
                        raise ValidationError('Giảm giá đề xuất '
                                              'không thỏa mãn quy tắc giảm giá bạn chọn !!!')

    def _get_rv_data(self):
        if self.order_id:
            rv_vals = {'type': 'so',
                       'name': self.name,
                       'order_line_id': self.order_line_id.id,
                       'order_id': self.order_id.id,
                       'partner_id': self.partner_id.id,
                       'reason': self.reason,
                       'company_id': self.env.company.id,
                       'type_discount': self.type_discount,
                       'discount': self.discount,
                       'rule_discount_id': self.rule_discount_id.id,
                       'currency_id': self.order_id.currency_id.id,
                       'total_amount_before_deep_discount': self.order_line_id.price_subtotal
                       }
        else:
            rv_vals = {'name': self.name,
                       'type': 'booking',
                       'crm_line_id': self.crm_line_id.id,
                       'booking_id': self.booking_id.id,
                       'partner_id': self.partner_id.id,
                       'reason': self.reason,
                       # 'company_id': self.booking_id.company_id.id,
                       'company_id': self.env.company.id,
                       'type_discount': self.type_discount,
                       'discount': self.discount,
                       'rule_discount_id': self.rule_discount_id.id,
                       'currency_id': self.booking_id.currency_id.id,
                       'total_amount_before_deep_discount': self.crm_line_id.total,
                       'total_amount': self.crm_line_id.total_before_discount
                       }
        return rv_vals

    def offer(self):
        rv_vals = self._get_rv_data()
        rv = self.env['crm.discount.review'].create(rv_vals)
        if not self.order_id and self.crm_line_id:
            self.crm_line_id.stage = 'waiting'
        view_rec = self.env.ref('crm_base.view_discount_review_finish',
                                raise_if_not_found=False)
        action = self.env.ref(
            'crm_base.action_view_discount_review_wizard', raise_if_not_found=False
        ).read([])[0]
        action['views'] = [(view_rec and view_rec.id or False, 'form')]

        #################################### ĐOẠN NÀY LÀ HÀM GỬI MAIL
        if self.send_email:
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            name = dict(self._fields['reason'].selection).get(self.reason)
            if self.name:
                name += ' (%s)' % self.name
            if self.type == 'booking':
                product = self.crm_line_id.product_id.name
            else:
                product = self.line_product.product_id.name
            if self.type_discount == 'discount_pr':
                discount = '{0:,.0f}'.format(int(self.discount)) + ' %'
            else:
                discount = '{0:,.0f}'.format(int(self.discount)) + ' đồng'
            link = "<a href=%s/web#id=%s&model=crm.discount.review&view_type=form'>Click vào đây</a>" % (
                base_url, str(rv.id))
            body = "Dear %s,</br>" \
                   "Anh/chị vừa nhận được yêu cầu giảm giá sâu.</br>" \
                   "Booking: %s </br>" \
                   "Khách hàng: %s </br>" \
                   "Dịch vụ/Sản phẩm: %s </br>" \
                   "Mức xin giảm : %s </br>" \
                   "Lý do xin giảm: %s </br>" \
                   "Người gửi yêu cầu: %s </br>" \
                   "Chi tiết yêu cầu vui lòng truy cập : %s</br>" \
                   "Trân trọng !" % (
                       self.approver_id.name.upper(), self.booking_id.name, self.partner_id.name, product, discount,
                       name,
                       self.env.user.name, link)
            mail = {
                'subject': ('GIẢM GIÁ SÂU: Khách hàng ' + str(self.partner_id.name).upper()),
                'body_html': body,
                'email_to': self.approver_id.login,
            }
            self.env['mail.mail'].create(mail).send()

        return action
