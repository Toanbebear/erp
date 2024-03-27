from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class ApplyDiscount(models.TransientModel):
    _inherit = 'crm.apply.voucher'

    def domain_voucher(self):
        if 'default_crm_id' in self._context:
            crm_id = self.env['crm.lead'].sudo().browse(int(self._context.get('default_crm_id')))
            line_ids = crm_id.crm_line_ids.filtered(lambda d: (d.stage in ('new', 'chotuvan', 'cancel')))
            voucher = line_ids.prg_voucher_ids
            return [('id', 'in', voucher.ids)]

    line_ids = fields.Many2many('crm.line', string='Dịch vụ',
                                domain="[('crm_id', '=', crm_id),('stage', 'in', ['new', 'processing','chotuvan']), ('total', '!=', 0), ('number_used', '=', 0), ('discount_review_id', '=', False)]")
    line_product_ids = fields.Many2many('crm.line.product', string='Sản phẩm',
                                        domain="[('booking_id', '=', crm_id),('stage_line_product', 'in', ['new', 'processing']), ('total', '!=', 0),('crm_discount_review', '=', False)]")
    is_cancel = fields.Boolean('Hủy voucher')
    voucher_program_line_ids = fields.Many2one('crm.voucher.program', string='Voucher đã gán', domain=domain_voucher)
    apply_for_cancel = fields.Selection(related='voucher_program_line_ids.apply_for')
    voucher_id_cancel = fields.Many2one('crm.voucher')

    @api.onchange('voucher_program_line_ids')
    def domain_voucher_id_cancel(self):
        voucher = self.env['crm.voucher'].sudo().search(
            [('crm_id', '=', self.crm_id.id), ('voucher_program_id', '=', self.voucher_program_line_ids.id)])
        return {'domain': {'voucher_id_cancel': [('id', 'in', voucher.ids)]}}

    def cancel_voucher(self):
        if self.voucher_id_cancel:
            self.voucher_id_cancel.crm_id = False
            self.voucher_id_cancel.partner2_id = False
            self.voucher_id_cancel.stage_voucher = 'active'
        if self.apply_for_cancel == 'product':
            product_ids = self.env['crm.line.product'].sudo().search(
                [('crm_id', '=', self.crm_id.id), ('prg_voucher_ids', 'like', self.voucher_program_line_ids.id),
                 ('stage', '=', 'new')])
            for line in product_ids:
                line.prg_voucher_ids = [(3, self.voucher_program_line_ids.id)]
                if self.voucher_id_cancel:
                    line.voucher_id = [(3, self.voucher_id_cancel.id)]
                discount = self.voucher_program_line_ids.voucher_program_list.filtered(
                    lambda d: d.product_id == line.product_id)
                if discount.type_discount == 'percent':
                    total_discount = discount.discount
                    line.discount_percent -= total_discount
                elif discount.type_discount == 'cash':
                    total_discount = discount.discount * line.quantity * line.uom_price
                    line.discount_cash -= total_discount
                else:
                    total_discount = discount.discount * line.quantity * line.uom_price
                    line.sale_to -= total_discount
        else:
            line_ids = self.env['crm.line'].sudo().search(
                [('crm_id', '=', self.crm_id.id), ('prg_voucher_ids', 'like', self.voucher_program_line_ids.id),
                 ('stage', 'in', ('new', 'chotuvan', 'cancel')), ('number_used', '=', 0)])
            for line in line_ids:
                line.prg_voucher_ids = [(3, self.voucher_program_line_ids.id)]
                if self.voucher_id_cancel:
                    line.voucher_id = [(3, self.voucher_id_cancel.id)]
                discount = self.voucher_program_line_ids.voucher_program_list.filtered(
                    lambda d: d.product_id == line.product_id or d.product_ctg_id == line.service_id.service_category)
                if discount.type_discount == 'percent':
                    total_discount = discount.discount
                    line.discount_percent -= total_discount
                elif discount.type_discount == 'cash':
                    total_discount = discount.discount * line.quantity * line.uom_price
                    line.discount_cash -= total_discount
                else:
                    total_discount = discount.discount * line.quantity * line.uom_price
                    line.sale_to -= total_discount

    def update_sale_order_line_by_voucher_discount_invoice(self, line, total_discount):
        order_ids = self.env['sale.order'].sudo().search([('booking_id', '=', line.crm_id.id), ('state', '=', 'draft')])
        order_line_ids = order_ids.mapped('order_line')
        order_line_id = order_line_ids.filtered(lambda l: l.crm_line_id == line)
        order_line_id = order_line_id[0]
        if order_line_id and ((line.uom_price * line.quantity) != 0):
            order_line_id.other_discount += total_discount / (line.quantity * line.uom_price) * order_line_id.uom_price

    def update_sale_order_line_by_voucher_discount_service(self, line, total_discount, type_discount):
        order_ids = self.env['sale.order'].sudo().search([('booking_id', '=', line.crm_id.id), ('state', '=', 'draft')])
        order_line_ids = order_ids.mapped('order_line')
        order_line_id = order_line_ids.filtered(lambda l: l.crm_line_id == line)
        if order_line_id:
            order_line_id = order_line_id[0]
        if order_line_id and ((line.uom_price * line.quantity) != 0):
            order_line_id = order_line_id[0]
            if type_discount == 'percent':
                order_line_id.discount = line.discount_percent
            elif type_discount == 'cash':
                order_line_id.discount_cash = total_discount / (
                        line.quantity * line.uom_price) * order_line_id.uom_price
            else:
                order_line_id.sale_to = total_discount / (line.quantity * line.uom_price) * order_line_id.uom_price
                order_line_id.price_subtotal = total_discount / (
                        line.quantity * line.uom_price) * order_line_id.uom_price

    def create_crm_line_by_voucher(self, discount, voucher):
        if discount.product_id.type == 'product':
            product_pricelist = self.env['product.pricelist'].search(
                [('type', '=', 'product'), ('brand_id', '=', self.crm_id.brand_id.id)], limit=1)
            product_pricelist_item = self.env['product.pricelist.item'].search(
                [('pricelist_id', '=', product_pricelist.id), ('product_id', '=', discount.product_id.id)], limit=1)
            self.env['crm.line.product'].create({
                'product_id': discount.product_id.id,
                'price_unit': product_pricelist_item.fixed_price,
                'product_uom': discount.product_id.uom_so_id.id,
                'product_uom_qty': discount.gift,
                'discount_percent': 100,
                'company_id': self.crm_id.company_id.id,
                'source_extend_id': self.crm_id.source_id.id,
                'product_pricelist_id': product_pricelist.id,
                'prg_voucher_ids': [(4, voucher.voucher_program_id.id)],
                'note': voucher.voucher_program_id.name,
                'booking_id': self.crm_id.id,
                'consultants_1': self.env.user.id
            })
        else:
            product_pricelist = self.env['product.pricelist'].search(
                [('type', '=', 'service'), ('brand_id', '=', self.crm_id.brand_id.id)], limit=1)
            product_pricelist_item = self.env['product.pricelist.item'].search(
                [('pricelist_id', '=', product_pricelist.id), ('product_id', '=', discount.product_id.id)], limit=1)
            service = self.env['sh.medical.health.center.service'].search([('product_id', '=', discount.product_id.id)],
                                                                          limit=1)
            self.env['crm.line'].create({
                'name': discount.product_id.name,
                'service_id': service.id,
                'product_id': discount.product_id.id,
                'unit_price': product_pricelist_item.fixed_price,
                'price_list_id': product_pricelist.id,
                'company_id': self.crm_id.company_id.id,
                'prg_voucher_ids': [(4, voucher.voucher_program_id.id)],
                'voucher_id': [(4, voucher.id)],
                'source_extend_id': self.crm_id.source_id.id,
                'status_cus_come': 'come',
                'note': voucher.voucher_program_id.name,
                'consultants_1': self.env.user.id,
                'quantity': discount.gift,
                'type': 'service',
                'discount_percent': 100
            })
        voucher.crm_id = self.crm_id.id
        voucher.partner2_id = self.crm_id.partner_id
        # self.crm_id.prg_voucher_ids = [(4, voucher.voucher_program_id.id)]
        if not voucher.partner_id:
            voucher.partner_id = self.crm_id.partner_id

    def set_discount_product(self, list_lines, discount, voucher):
        voucher_program_id = voucher.voucher_program_id
        for line in list_lines:
            if discount.type_discount == 'percent':
                total_discount = discount.discount
                line.discount_percent += total_discount
            elif discount.type_discount == 'cash':
                total_discount = discount.discount * line.product_uom_qty
                line.discount_cash += total_discount
            line.prg_voucher_ids = [(4, voucher_program_id.id)]
            line.voucher_id = [(4, voucher.id)]
        voucher.crm_id = self.crm_id.id
        voucher.partner2_id = self.crm_id.partner_id
        if not voucher.partner_id:
            voucher.partner_id = self.crm_id.partner_id
        return voucher

    def check_code_voucher(self):
        voucher_id = self.env['crm.voucher'].search([('name', '=', self.name), ('stage_voucher', '=', 'active')])
        if self.crm_id.customer_come == 'yes':
            line_new_ids = self.line_ids.filtered(lambda l: (l.stage == 'chotuvan'))
            if line_new_ids:
                raise ValidationError('Bạn không thể áp dụng voucher khi có dịch vụ ở trạng thái chờ tư vấn')
        else:
            if self.line_ids:
                raise ValidationError('Khách hàng chưa đến cửa bạn không thể nhập mã voucher')
        if voucher_id:
            if voucher_id.crm_id and voucher_id.crm_id.id != self.crm_id.id:
                raise ValidationError(
                    'Voucher đã được gán cho %s. Vui lòng kiểm tra và nhập lại' % voucher_id.crm_id.name)
            line_duplicate = self.line_ids.filtered(
                lambda l: self.voucher_program_id in l.prg_voucher_ids)
            for line in line_duplicate:
                if line.voucher_id:
                    if voucher_id not in line.voucher_id:
                        raise ValidationError(
                            'Áp dụng không thành công do dịch vụ %s đã được áp dụng chương trình khuyến mãi %s' % (
                                line.service_id.name, self.voucher_program_id.name))
                else:
                    raise ValidationError(
                        'Áp dụng không thành công do dịch vụ %s đã được áp dụng chương trình khuyến mãi %s' % (
                            line.service_id.name, self.voucher_program_id.name))
            line_product_duplicate = self.line_product_ids.filtered(
                lambda l: self.voucher_program_id in l.prg_voucher_ids)
            for line in line_product_duplicate:
                if line.voucher_id:
                    if voucher_id not in line.voucher_id:
                        raise ValidationError(
                            'Áp dụng không thành công do sản phẩm %s đã được áp dụng chương trình khuyến mãi %s' % (
                                line.product_id.name, self.voucher_program_id.name))
                else:
                    raise ValidationError(
                        'Áp dụng không thành công do sản phẩm %s đã được áp dụng chương trình khuyến mãi %s' % (
                            line.product_id.name, self.voucher_program_id.name))
        if not voucher_id:
            raise ValidationError(
                'Không thể áp dụng voucher do bạn đã nhập sai mã voucher. Vui lòng kiểm tra và nhập lại')
        elif not self.voucher_program_id:
            raise ValidationError('Không tìm thấy chương trình voucher khả dụng. Vui lòng kiểm tra lại')
        else:
            voucher_id.stage_voucher = 'used'
            if self.voucher_prg_type == 'discount_service':
                self.check_service(self.line_ids, voucher_id)
            elif self.voucher_prg_type == 'discount_product':
                self.check_product(self.line_product_ids, voucher_id)
            else:
                self.discount_invoice(self.line_ids, voucher_id)

    def apply_voucher_program(self):
        if not self.name and self.voucher_program_id:
            line_duplicate = self.line_ids.filtered(
                lambda l: self.voucher_program_id in l.prg_voucher_ids)
            line_product_duplicate = self.line_product_ids.filtered(
                lambda l: self.voucher_program_id in l.prg_voucher_ids)
            if line_duplicate or line_product_duplicate:
                raise ValidationError(
                    'Không áp dụng thành công do dịch vụ(sản phẩm) đã được áp dụng chương trình %s' % self.voucher_program_id.name)

            voucher_prg = self.voucher_program_id
            code = voucher_prg.create_code(voucher_prg.prefix, 1, voucher_prg.voucher_ids.mapped('name'))
            voucher_id = self.env['crm.voucher'].create(
                {'voucher_program_id': voucher_prg.id,
                 'name': code[0],
                 'stage_voucher': voucher_prg.stage_prg_voucher
                 })
            voucher_id.stage_voucher = 'active'
            voucher_prg.current_number_voucher += 1
            if self.voucher_prg_type == 'discount_service':
                self.check_service(self.line_ids, voucher_id)
            elif self.voucher_prg_type == 'discount_product':
                self.check_product(self.line_product_ids, voucher_id)
            else:
                self.discount_invoice(self.line_ids, voucher_id)

    def check_service(self, line_ids, voucher):
        prg = voucher.voucher_program_id
        if prg.voucher_program_list:
            for discount in prg.voucher_program_list:
                if discount.gift:
                    self.create_crm_line_by_voucher(discount, voucher)
                elif discount.type_product == 'product':
                    list_lines = line_ids.filtered(
                        lambda l: (l.product_id == discount.product_id) and not l.discount_review_id and (
                                prg not in l.prg_voucher_ids))
                    if list_lines:
                        self.set_dc_service(list_lines, discount, voucher)
                else:
                    list_lines = line_ids.filtered(lambda
                                                       l: l.product_id == discount.product_id or l.service_id.service_category == discount.product_ctg_id and (
                            prg not in l.prg_voucher_ids))
                    if list_lines:
                        self.set_dc_service(list_lines, discount, voucher)

    def check_product(self, line_product_ids, voucher):
        prg = voucher.voucher_program_id
        if prg.voucher_program_list:
            for discount in prg.voucher_program_list:
                if discount.gift:
                    self.create_crm_line_by_voucher(discount, voucher)
                elif discount.type_product == 'product':
                    list_lines = line_product_ids.filtered(
                        lambda l: (l.product_id == discount.product_id) and (prg not in l.prg_voucher_ids))
                    if list_lines:
                        self.set_dc_product(list_lines, discount, voucher)

    def set_dc_service(self, lines, discount, voucher):
        for line in lines:
            if self.crm_id.customer_come == 'yes':
                line_new_ids = self.line_ids.filtered(lambda l: (l.stage == 'chotuvan'))
                if line_new_ids:
                    raise ValidationError('Bạn không thể áp dụng voucher khi có dịch vụ ở trạng thái chờ tư vấn')
            if discount.type_discount == 'percent':
                total_discount = discount.discount
                line.discount_percent += total_discount
            elif discount.type_discount == 'cash':
                total_discount = discount.discount * line.quantity * line.uom_price
                line.discount_cash += total_discount
            else:
                total_discount = discount.discount * line.quantity * line.uom_price
                line.sale_to = total_discount
            self.update_sale_order_line_by_voucher_discount_service(line, total_discount, discount.type_discount)
            line.prg_voucher_ids = [(4, voucher.voucher_program_id.id)]
            line.voucher_id = [(4, voucher.id)]
        voucher.crm_id = self.crm_id.id
        voucher.partner2_id = self.crm_id.partner_id
        if not voucher.partner_id:
            voucher.partner_id = self.crm_id.partner_id

    def set_dc_product(self, lines, discount, voucher):
        for line in lines:
            if discount.type_discount == 'percent':
                total_discount = discount.discount
                line.discount_percent += total_discount
            elif discount.type_discount == 'cash':
                total_discount = discount.discount * line.quantity * line.uom_price
                line.discount_cash += total_discount
            else:
                total_discount = discount.discount * line.quantity * line.uom_price
                line.sale_to = total_discount
            # self.update_sale_order_line_by_voucher_discount_service(line, total_discount, discount.type_discount)
            line.prg_voucher_ids = [(4, voucher.voucher_program_id.id)]
            line.voucher_id = [(4, voucher.id)]
        voucher.crm_id = self.crm_id.id
        voucher.partner2_id = self.crm_id.partner_id
        if not voucher.partner_id:
            voucher.partner_id = self.crm_id.partner_id

    def discount_invoice(self, line_ids, voucher):

        """ Các bước thực hiện:
            Đầu vào là 1 Booking (IN_1), các line được chỉ định áp dụng voucher (IN_2), mã voucher (IN_3)
            B1: Từ IN_1 sẽ tính được tổng tiền các line DV trong IN_1 để biết được tổng hóa đơn KH đky là bao nhiêu
            B2 : Tính tổng tiền của IN_2.
            B3 : Tìm mức giảm cao nhất phù hợp với tổng tiền Booking
            B4 : Áp dụng voucher
                + Nếu loại voucher là giảm %: ( X : Số % được giảm tìm được ở B3)
                    Dùng vòng for chạy trong IN_2. Số tiền giảm sẽ được tính theo công thức:
                            Tiền giảm  =  Tiền của line * ( X / 100)
                            cột giảm khác của line DV += Tiền giảm
                        Nếu line DV đó ở trạng thái ĐANG XỬ LÝ sẽ chạy vào hàm update_sale_order_line_by_voucher_discount_invoice
                + Nếu loại voucher là giảm tiền mặt (Y : Số % được giảm tìm được ở B3. chia số tiền Y vào IN_2)
                    Dùng vòng lặp for chạy trong IN_2. Số tiền giảm của line này sẽ được tính theo công thức:
                            Tiền giảm =  (tiền của line / B2) * Y
                            Làm tròn Tiền giảm đến hàng nghìn
                            cột giảm khác của line DV += Tiền giảm
                        Nếu line DV đó ở trạng thái ĐANG XỬ LÝ sẽ chạy vào hàm update_sale_order_line_by_voucher_discount_invoice
                    Đối với loại voucher là giảm tiền mặt và tổng tiền giảm ở các line lớn hơn Y :
                        Thực hiện giảm số tiền chênh lệch vào phần tử đầu tiên của IN_2
            B5 : Sau khi áp dụng xong sẽ thực hiện:
                + Gán voucher đó cho KH này
                + Chuyển trạng thái của voucher là Đã sử dụng
                + Gán CT voucher của line DV này là CT Voucher của IN_3
                """

        prg = voucher.voucher_program_id
        crm_line_booking = self.crm_id.crm_line_ids.filtered(lambda l: l.stage not in ['cancel', 'done'])
        booking_total = sum(crm_line_booking.mapped('total'))
        line_ids_total = sum(self.line_ids.mapped('total'))
        discount_invoice_ids = prg.voucher_program_discount_invoice.filtered(
            lambda invoice: invoice.invoice_value_minimum <= booking_total)
        if discount_invoice_ids:
            list_value_invoice = discount_invoice_ids.mapped('invoice_value_minimum')
            list_value_invoice.sort(reverse=True)
            discount_invoice_id = discount_invoice_ids.filtered(
                lambda invoice: invoice.invoice_value_minimum == list_value_invoice[0])
            if prg.type_discount_invoice == '2':
                for line in line_ids:
                    total_discount = line.total * (discount_invoice_id.discount / 100)
                    line.other_discount += total_discount
                    line.voucher_id = [(4, voucher.id)]
                    if line.stage == 'processing':
                        self.update_sale_order_line_by_voucher_discount_invoice(line, total_discount)
                voucher.crm_id = self.crm_id.id
                voucher.partner2_id = self.crm_id.partner_id
                # self.crm_id.prg_voucher_ids = [(4, voucher.voucher_program_id.id)]
                if not voucher.partner_id:
                    voucher.partner_id = self.crm_id.partner_id
                line_ids.write({
                    'prg_voucher_ids': [(4, prg.id)]
                })
            else:
                total_discount_all_line = 0
                for line in line_ids:
                    total_discount = round(((line.total / line_ids_total) * discount_invoice_id.discount) / 1000) * 1000
                    line.other_discount += total_discount
                    total_discount_all_line += total_discount
                    line.voucher_id = [(4, voucher.id)]
                    if line.stage == 'processing':
                        self.update_sale_order_line_by_voucher_discount_invoice(line, total_discount)
                if total_discount_all_line > discount_invoice_id.discount:
                    line_ids[0].other_discount -= (total_discount_all_line - discount_invoice_id.discount)
                if total_discount_all_line < discount_invoice_id.discount:
                    line_ids[0].other_discount += (discount_invoice_id.discount - total_discount_all_line)
                voucher.crm_id = self.crm_id.id
                voucher.partner2_id = self.crm_id.partner_id
                # self.crm_id.prg_voucher_ids = [(4, voucher.voucher_program_id.id)]
                if not voucher.partner_id:
                    voucher.partner_id = self.crm_id.partner_id
                line_ids.write({
                    'prg_voucher_ids': [(4, prg.id)]
                })
