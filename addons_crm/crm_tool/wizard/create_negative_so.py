import datetime

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class NegativeSODetail(models.TransientModel):
    _name = "create.negative.so.detail"
    _description = "Create negative SO detail"

    negative_so = fields.Many2one('create.negative.so')
    booking = fields.Many2one('crm.lead')
    line = fields.Many2one('crm.line', string='Dịch vụ',
                           domain="[('crm_id', '=', booking)]")
    price_list = fields.Many2one(related='line.price_list_id')
    currency_id = fields.Many2one(related='booking.currency_id')
    stage_line = fields.Selection(
        [('new', 'Được sử dụng'), ('processing', 'Đang xử trí'), ('done', 'Hoàn thành'), ('waiting', 'Chờ giảm thêm'),
         ('cancel', 'Hủy')], string='Trạng thái')
    amount = fields.Monetary('Số tiền')

    @api.onchange('line')
    def onchange_line(self):
        if self.line:
            self.stage_line = self.line.stage


class NegativeSODetailProduct(models.TransientModel):
    _name = "create.negative.so.detail.product"
    _description = "Create negative SO detail"

    negative_so = fields.Many2one('create.negative.so')
    booking = fields.Many2one('crm.lead')
    line = fields.Many2one('crm.line.product', string='Sản phẩm', domain="[('booking_id', '=', booking)]")
    price_list = fields.Many2one(related='line.product_pricelist_id')
    currency_id = fields.Many2one(related='booking.currency_id')
    stage_line = fields.Selection(
        [('new', 'Mới'), ('processing', 'Hóa đơn nháp'), ('sold', 'Hoàn thành'), ('waiting', 'Chờ phê duyệt'),
         ('cancel', 'Hủy')], string='Trạng thái')
    amount = fields.Monetary('Số tiền')

    @api.onchange('line')
    def onchange_line(self):
        if self.line:
            self.stage_line = self.line.stage_line_product


class NegativeSO(models.TransientModel):
    _name = "create.negative.so"
    _description = "Tạo đơn hàng âm"

    booking = fields.Many2one('crm.lead', string='Booking')
    company_id = fields.Many2one(related='booking.company_id')
    service_price_list = fields.Many2many('product.pricelist', compute='get_price_list')
    product_price_list = fields.Many2many('product.pricelist', compute='get_price_list')
    company = fields.Many2one('res.company', default=lambda self: self.env.company)
    partner = fields.Many2one('res.partner', string='Khách hàng')
    currency_id = fields.Many2one(related='booking.currency_id')
    details = fields.One2many('create.negative.so.detail', 'negative_so', 'Chi tiết',
                              domain="[('price_list', '=', price_list_id)]")
    details_prd = fields.One2many('create.negative.so.detail.product', 'negative_so', 'Chi tiết sản phẩm',
                                  domain="[('price_list', '=', price_list_id_prd)]")
    note = fields.Text('Nhập lý do')
    type = fields.Selection([('service', 'Dịch vụ'), ('product', 'Sản phẩm')], default='service', string='Loại')
    account_511 = fields.Many2one('account.account', domain="[('company_id', '=', company)]",
                                  string='Tài khoản doanh thu giảm trừ')
    price_list_id = fields.Many2one('product.pricelist', domain="[('id', 'in', service_price_list)]",
                                    string='Bảng giá')
    price_list_id_prd = fields.Many2one('product.pricelist',
                                        domain="[('id', 'in', product_price_list)]",
                                        string='Bảng giá')
    sh_room_id = fields.Many2one('sh.medical.health.center.ot', string='Phòng xuất hàng',
                                 domain="[('institution.his_company', '=', company_id)]")

    @api.depends('booking')
    def get_price_list(self):
        booking = self.env['crm.lead'].sudo().browse(self._context.get('default_booking'))
        list_ids = []
        list_prd_ids = []
        for price_list in booking.crm_line_ids.price_list_id:
            list_ids.append(price_list.id)
        for price_list in booking.crm_line_product_ids.product_pricelist_id:
            list_prd_ids.append(price_list.id)
        self.service_price_list = [(6, 0, list_ids)]
        self.product_price_list = [(6, 0, list_prd_ids)]

    def confirm(self):
        account_131101 = self.env['account.account'].sudo().search(
            [('company_id', '=', self.env.company.id), ('code', '=', '131101')], limit=1)
        if not account_131101:
            raise ValidationError(
                'Không tìm thấy tài khoản phải thu 131101 của khách hàng.\nVui lòng liên hệ kế toán thương hiệu để được hỗ trợ')
        account_521201 = self.env['account.account'].sudo().search(
            [('company_id', '=', self.env.company.id), ('code', '=', '521201')], limit=1)
        if not account_521201:
            raise ValidationError(
                'Không tìm thấy tài khoản giảm trừ doanh thu 521201 của chi nhánh này.\nVui lòng liên hệ kế toán thương hiệu để được hỗ trợ')
        # domain_511 = [('company_id', '=', self.env.company.id)]
        account_511301 = self.env['account.account'].sudo().search(
            [('company_id', '=', self.env.company.id), ('code', '=', '511301')], limit=1)
        # if not self.account_511:
        if not account_511301:
            raise ValidationError(
                'Không tìm thấy tài khoản giảm trừ doanh thu của chi nhánh này.\nVui lòng liên hệ kế toán thương hiệu để được hỗ trợ')
        journal_noi_bo = self.env['account.journal'].sudo().search(
            [('company_id', '=', self.env.company.id), ('name', '=', 'Sổ công nợ phải trả nội bộ')])
        if not journal_noi_bo:
            raise ValidationError(
                'Không tìm thấy "Sổ công nợ phải trả nội bộ" của chi nhánh.\nVui lòng liên hệ kế toán thương hiệu để được hỗ trợ')

        if self.details:
            for record in self.details:
                used = sum(
                    record.line.sale_order_line_id.filtered(lambda l: l.state in ['done', 'sale']).mapped(
                        'price_subtotal'))
                if used < record.amount:
                    raise ValidationError('Số tiền hoàn tối đa của dịch vụ %s là: %s đ' % (
                        record.line.service_id.name, '{0:,.0f}'.format(used)))
            order = self.env['sale.order'].create({
                'partner_id': self.partner.id,
                'pricelist_id': self.price_list_id.id,
                'company_id': self.env.company.id,
                'booking_id': self.booking.id,
                'campaign_id': self.booking.campaign_id.id,
                'source_id': self.booking.source_id.id,
                'note': '%s:%s' % (self.booking.name, self.note),
                'currency_id': self.currency_id.id
            })
            for detail in self.details:
                if detail.amount:
                    self.env['sale.order.line'].create({
                        'order_id': order.id,
                        'crm_line_id': detail.line.id,
                        'product_id': detail.line.product_id.id,
                        'product_uom': detail.line.product_id.uom_id.id,
                        'uom_price': 1,
                        'company_id': self.env.company.id,
                        'price_unit': 0 - detail.amount,
                        'price_subtotal': 0 - detail.amount
                    })
            order.action_confirm()
            # journal_id = self.env['account.journal'].sudo().search(
            #     [('company_id', '=', order.company_id.id), ('type', '=', 'sale')])
            ################# SINH BÚT TOÁN GIẢM TRỪ DOANH THU QUA 521201
            invoice_521 = order.with_context(force_company=order.company_id.id)._create_invoices(final=True)
            for line in invoice_521.line_ids:
                if line.account_id.code.startswith('511'):
                    line.account_id = account_521201.id
                    line.write({
                        'account_id': account_521201.id,
                    })
            for line in invoice_521.invoice_line_ids:
                line.tax_ids = False
            invoice_521.with_context(force_company=invoice_521.company_id.id).action_post()

            ################################ SINH BÚT TOÁN KẾT CHUYỂN 521201 - 511
            lines_511 = [(5, 0, 0)]
            lines_511.append((0, 0, {
                'account_id': account_521201.id,
                'partner_id': order.partner_id.id,
                'credit': abs(order.amount_total),
                'date': datetime.date.today()
            }))
            lines_511.append((0, 0, {
                'account_id': account_511301.id,
                'partner_id': order.partner_id.id,
                'debit': abs(order.amount_total),
                'date': datetime.date.today()
            }))

            value_511 = {
                'partner_id': self.partner.id,
                'partner_shipping_id': self.partner.id,
                'tas_type': 'other',
                'order_id': order.id,
                'invoice_origin': order.name,
                'amount_untaxed': abs(order.amount_total),
                'amount_residual': abs(order.amount_total),
                'amount_untaxed_signed': order.amount_total,
                'amount_residual_signed': order.amount_total,
                'lydo': order.note,
                'invoice_date': order.date_order,
                'source_id': order.source_id.id,
                'journal_id': journal_noi_bo.id,
                'company_id': self.env.company.id,
                'currency_id': self.env.company.currency_id.id,
                'line_ids': lines_511
            }
            invoice_511 = self.env['account.move'].sudo().with_context(force_company=self.env.company.id).create(
                value_511)
            invoice_511.with_context(force_company=invoice_511.company_id.id).action_post()

    def confirm_prd(self):
        account_131101 = self.env['account.account'].sudo().search(
            [('company_id', '=', self.env.company.id), ('code', '=', '131101')], limit=1)
        if not account_131101:
            raise ValidationError(
                'Không tìm thấy tài khoản phải thu 131101 của khách hàng.\nVui lòng liên hệ kế toán thương hiệu để được hỗ trợ')
        account_521201 = self.env['account.account'].sudo().search(
            [('company_id', '=', self.env.company.id), ('code', '=', '521201')], limit=1)
        if not account_521201:
            raise ValidationError(
                'Không tìm thấy tài khoản giảm trừ doanh thu 521201 của chi nhánh này.\nVui lòng liên hệ kế toán thương hiệu để được hỗ trợ')
        # domain_511 = [('company_id', '=', self.env.company.id)]
        # account_511301 = self.env['account.account'].sudo().search(
        #     [('company_id', '=', self.env.company.id), ('code', '=', '511301')], limit=1)
        if not self.account_511:
            raise ValidationError(
                'Không tìm thấy tài khoản giảm trừ doanh thu của chi nhánh này.\nVui lòng liên hệ kế toán thương hiệu để được hỗ trợ')
        journal_noi_bo = self.env['account.journal'].sudo().search(
            [('company_id', '=', self.env.company.id), ('name', '=', 'Sổ công nợ phải trả nội bộ')])
        if not journal_noi_bo:
            raise ValidationError(
                'Không tìm thấy "Sổ công nợ phải trả nội bộ" của chi nhánh.\nVui lòng liên hệ kế toán thương hiệu để được hỗ trợ')

        if self.details_prd:
            for record in self.details_prd:
                # used = sum(
                #     record.line.sale_order_line_id.filtered(lambda l: l.state in ['done', 'sale']).mapped(
                #         'price_subtotal'))
                used = sum(self.env['sale.order.line'].sudo().search([('line_product', '=', record.line.id)]).mapped(
                    'price_subtotal'))
                if used == 0:
                    raise ValidationError('Không có tiền để hoàn')
                elif used < record.amount:
                    raise ValidationError('Số tiền hoàn tối đa của dịch vụ %s là: %s đ' % (
                        record.line.service_id.name, '{0:,.0f}'.format(used)))
            order = self.env['sale.order'].create({
                'partner_id': self.partner.id,
                'pricelist_id': self.price_list_id_prd.id,
                'company_id': self.env.company.id,
                'booking_id': self.booking.id,
                'campaign_id': self.booking.campaign_id.id,
                'source_id': self.booking.source_id.id,
                'note': '%s:%s' % (self.booking.name, self.note),
                'currency_id': self.currency_id.id,
                'sh_room_id': self.sh_room_id.id
            })
            for detail in self.details_prd:
                if detail.amount:
                    self.env['sale.order.line'].create({
                        'order_id': order.id,
                        'line_product': detail.line.id,
                        'product_id': detail.line.product_id.id,
                        'product_uom': detail.line.product_id.uom_id.id,
                        'uom_price': 1,
                        'company_id': self.env.company.id,
                        'price_unit': 0 - detail.amount,
                        'price_subtotal': 0 - detail.amount
                    })
            order.action_confirm()
            # journal_id = self.env['account.journal'].sudo().search(
            #     [('company_id', '=', order.company_id.id), ('type', '=', 'sale')])
            ################# SINH BÚT TOÁN GIẢM TRỪ DOANH THU QUA 521201
            invoice_521 = order.with_context(force_company=order.company_id.id)._create_invoices(final=True)
            for line in invoice_521.line_ids:
                if line.account_id.code.startswith('511'):
                    line.account_id = account_521201.id
                    line.write({
                        'account_id': account_521201.id,
                    })
            invoice_521.with_context(force_company=invoice_521.company_id.id).action_post()

            ######################################## XỬ LÝ BÚT TOÁN CỦA SO ÂM HẠCH TOÁN NGƯỢC NỢ CÓ GIỮA 1529 và 632
            line_1529 = invoice_521.line_ids.filtered(lambda l: l.account_id.code.startswith('1529'))
            account_1529 = line_1529.mapped('account_id')[0]
            line_632 = invoice_521.line_ids.filtered(lambda l: l.account_id.code.startswith('632'))
            account_632 = line_632.mapped('account_id')[0]
            list_1529 = "(" + ", ".join(map(str, line_1529.ids)) + ")"
            list_632 = "(" + ", ".join(map(str, line_632.ids)) + ")"
            self.env.cr.execute(""" UPDATE account_move_line
                                    SET account_id = %s
                                    WHERE id in %s;""" % (account_632.id, list_1529))
            self.env.cr.execute(""" UPDATE account_move_line
                                    SET account_id = %s
                                    WHERE id in %s;""" % (account_1529.id, list_632))

            ################################ SINH BÚT TOÁN KẾT CHUYỂN 521201 - 511
            lines_511 = [(5, 0, 0)]
            lines_511.append((0, 0, {
                'account_id': account_521201.id,
                'partner_id': order.partner_id.id,
                'credit': abs(order.amount_total),
                'date': datetime.date.today()
            }))
            lines_511.append((0, 0, {
                'account_id': self.account_511.id,
                'partner_id': order.partner_id.id,
                'debit': abs(order.amount_total),
                'date': datetime.date.today()
            }))

            value_511 = {
                'partner_id': self.partner.id,
                'partner_shipping_id': self.partner.id,
                'tas_type': 'other',
                'order_id': order.id,
                'invoice_origin': order.name,
                'amount_untaxed': abs(order.amount_total),
                'amount_residual': abs(order.amount_total),
                'amount_untaxed_signed': order.amount_total,
                'amount_residual_signed': order.amount_total,
                'lydo': order.note,
                'invoice_date': order.date_order,
                'source_id': order.source_id.id,
                'journal_id': journal_noi_bo.id,
                'company_id': self.env.company.id,
                'currency_id': self.env.company.currency_id.id,
                'line_ids': lines_511
            }
            invoice_511 = self.env['account.move'].sudo().with_context(force_company=self.env.company.id).create(
                value_511)
            invoice_511.with_context(force_company=invoice_511.company_id.id).action_post()
