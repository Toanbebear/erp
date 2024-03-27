from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, date


class ApplyDiscount(models.TransientModel):
    _name = 'crm.apply.voucher'
    _description = 'Apply Discount'

    crm_id = fields.Many2one('crm.lead', string='Booking/lead')
    brand_id = fields.Many2one('res.brand', related='crm_id.brand_id')
    is_code_voucher = fields.Boolean('Bạn có mã voucher không?')
    name = fields.Char('Mã Voucher')
    partner_id = fields.Many2one('res.partner', string='Partner')
    voucher_program_id = fields.Many2one('crm.voucher.program', string='Voucher',
                                         domain="[('stage_prg_voucher', '=', 'active'), ('brand_id', '=', brand_id)]")
    apply_for = fields.Selection(related='voucher_program_id.apply_for')
    voucher_prg_type = fields.Selection(related='voucher_program_id.type_voucher')
    line_ids = fields.Many2many('crm.line', string='Dịch vụ',
                                domain="[('crm_id', '=', crm_id),('stage', 'in', ['new', 'processing']), ('total', '!=', 0), ('number_used', '=', 0), ('discount_review_id', '=', False)]")
    line_product_ids = fields.Many2many('crm.line.product', string='Sản phẩm',
                                domain="[('booking_id', '=', crm_id),('stage_line_product', 'in', ['new', 'processing']), ('total', '!=', 0),('crm_discount_review', '=', False)]")

    @api.onchange('name')
    def onchange_line_ids(self):
        self.voucher_program_id = False
        if self.name:
            voucher = self.env['crm.voucher'].sudo().search([('name', '=', self.name)], limit=1)
            if voucher:
                self.voucher_program_id = voucher.voucher_program_id.id

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
        voucher.stage_voucher = 'used'

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
        voucher.crm_id = self.crm_id.id
        voucher.partner2_id = self.crm_id.partner_id
        if not voucher.partner_id:
            voucher.partner_id = self.crm_id.partner_id
        voucher.stage_voucher = 'used'
        return voucher

    def check_code_voucher(self):
        voucher_id = self.env['crm.voucher'].search([('name', '=', self.name), ('stage_voucher', '=', 'active')])
        if not voucher_id:
            raise ValidationError('Mã voucher không hợp lệ hoặc đã được sử dụng')
        elif not self.voucher_program_id:
            raise ValidationError('Không tìm thấy chương trình voucher khả dụng. Vui lòng kiểm tra lại')
        else:
            self.apply_voucher_program()

    def apply_voucher_program(self):
        if not self.name and self.voucher_program_id:
            voucher_prg = self.voucher_program_id
            code = voucher_prg.create_code(voucher_prg.prefix, 1, voucher_prg.voucher_ids.mapped('name'))
            voucher_id = self.env['crm.voucher'].create(
                {'voucher_program_id': voucher_prg.id,
                 'name': code[0],
                 'stage_voucher': voucher_prg.stage_prg_voucher
                 })
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
                        lambda l: (l.product_id == discount.product_id) and not l.discount_review_id)
                    if list_lines:
                        self.set_dc_service(list_lines, discount, voucher)
                else:
                    list_lines = line_ids.filtered(lambda
                                                       l: l.product_id == discount.product_id or l.service_id.service_category == discount.product_ctg_id)
                    if list_lines:
                        self.set_dc_service(list_lines, discount, voucher)

    def check_product(self, line_product_ids, voucher):
        prg = voucher.voucher_program_id
        print(prg)
        if prg.voucher_program_list:
            for discount in prg.voucher_program_list:
                if discount.gift:
                    self.create_crm_line_by_voucher(discount, voucher)
                elif discount.type_product == 'product':
                    list_lines = line_product_ids.filtered(lambda l: (l.product_id == discount.product_id))
                    print(list_lines)
                    if list_lines:
                        self.set_dc_product(list_lines, discount, voucher)

    def set_dc_service(self, lines, discount, voucher):
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
            self.update_sale_order_line_by_voucher_discount_service(line, total_discount, discount.type_discount)
            line.prg_voucher_ids = [(4, voucher.voucher_program_id.id)]
        voucher.crm_id = self.crm_id.id
        voucher.partner2_id = self.crm_id.partner_id
        if not voucher.partner_id:
            voucher.partner_id = self.crm_id.partner_id
        voucher.stage_voucher = 'used'

    def set_dc_product(self, lines, discount, voucher):
        for line in lines:
            print(line)
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
        voucher.crm_id = self.crm_id.id
        voucher.partner2_id = self.crm_id.partner_id
        if not voucher.partner_id:
            voucher.partner_id = self.crm_id.partner_id
        voucher.stage_voucher = 'used'

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
                    if line.stage == 'processing':
                        self.update_sale_order_line_by_voucher_discount_invoice(line, total_discount)
                voucher.crm_id = self.crm_id.id
                voucher.partner2_id = self.crm_id.partner_id
                # self.crm_id.prg_voucher_ids = [(4, voucher.voucher_program_id.id)]
                if not voucher.partner_id:
                    voucher.partner_id = self.crm_id.partner_id
                voucher.stage_voucher = 'used'
                line_ids.write({
                    'prg_voucher_ids': [(4, prg.id)]
                })
            else:
                total_discount_all_line = 0
                for line in line_ids:
                    total_discount = round(((line.total / line_ids_total) * discount_invoice_id.discount) / 1000) * 1000
                    line.other_discount += total_discount
                    total_discount_all_line += total_discount
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
                voucher.stage_voucher = 'used'
                line_ids.write({
                    'prg_voucher_ids': [(4, prg.id)]
                })