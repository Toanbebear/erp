from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, date
import itertools


class ApplyCoupon(models.TransientModel):
    _name = 'crm.apply.coupon'
    _description = 'Apply Coupon'

    name = fields.Char('Name')
    type_action = fields.Selection([('apply', 'Áp dụng Coupon'), ('reverse_part', 'Hoàn lại một phần',),
                                    ('reverse_full', 'Hoàn lại tất cả')], string='Hành động thực hiện', default='apply')
    description = fields.Char(string='Giải thích', compute='depends_type_action')
    coupon_id = fields.Many2one('crm.discount.program', string='Coupon')
    COUPON_TYPE = [('1', 'Coupon đơn lẻ'), ('2', 'Coupon áp dụng cho đơn hàng'), ('3', 'Coupon cho combo dịch vụ'),
                   ('4', 'Coupon cho liệu trình'), ('5', 'Coupon cho nhóm khách hàng'), ('6', 'Coupon cho hạng thẻ'),
                   ('7', 'Coupon cho khách hàng mới/cũ'), ('8', 'Coupon cho dịch vụ đã sử dụng')]
    type_coupon = fields.Selection(COUPON_TYPE, string='Loại Coupon')
    crm_id = fields.Many2one('crm.lead', string='Booking/lead')
    partner_id = fields.Many2one('res.partner', string='Partner')
    # campaign_id = fields.Many2one('utm.campaign', string='Campaign', domain="[('campaign_status', '=', '2'), ('brand_id.company_ids', 'in', allowed_company_ids)]")
    campaign_id = fields.Many2one('utm.campaign', string='Campaign')
    hide_type = fields.Boolean(default=False)
    notify = fields.Char()
    index = fields.Integer(default=0)
    apply_combo = fields.One2many('crm.apply.coupon.detail', 'apply_coupon_id', string='Combo')
    line_ids = fields.Many2many(
        string='Danh sách dịch vụ được áp dụng',
        comodel_name='crm.line'
    )
    line_product_ids = fields.Many2many(
        string='Danh sách sản phẩm được áp dụng',
        comodel_name='crm.line.product'
    )


    @api.onchange('crm_id')
    def get_campain_apply_discount_program(self):
        domain = [('campaign_status', '=', '2')]
        if self.crm_id:
            domain += [('brand_id.company_ids', 'in', self.env.user.company_ids.ids)]
        campaign = self.env['utm.campaign'].search(domain)
        # if self.crm_id.kept_campaign:
        #     campaign += self.crm_id.kept_campaign
        deposit = self.env['crm.request.deposit'].search([('status', '=', 'new'), ('booking_id', '=', self.crm_id.id)])
        if deposit:
            for rec in deposit:
                if rec.status == 'new' and rec.campaign_id not in campaign:
                    campaign += rec.campaign_id
        return {'domain': {'campaign_id': [('id', 'in', campaign.ids)]}}

    def get_index(self):
        if self.apply_combo is not None:
            index = None
            count = 0
            for rec in self.apply_combo:
                if rec.check is True:
                    index = rec.index
                    count += 1
            if count > 1:
                raise ValidationError('Không thể chọn cùng lúc nhiều combo')
            elif index:
                self.index = index

    # kiểm tra loại coupon rẽ nhánh
    def check_type_coupon(self):
        if self.crm_id and self.coupon_id.company_ids and \
                self.crm_id.company_id not in self.coupon_id.company_ids:
            raise ValidationError(
                'Chi nhánh %s không có trong danh sách áp dụng coupon giảm giá !!!' % self.crm_id.company_id.name)
        else:
            # self.reverse_prg_ids()
            lines = self.line_ids.filtered(
                lambda line: line.stage in ['new', 'processing', 'chotuvan']
                             and line.number_used == 0
                             and not line.voucher_id
                             and not line.discount_review_id
                             and self.coupon_id not in line.prg_ids)
            if lines and self.coupon_id.coupon_type == '1':  # Rẽ nhánh chạy theo từng loại coupon
                self.check_coupon_type_1(self.line_ids, self.coupon_id)
            elif lines and self.coupon_id.coupon_type == '2':
                self.bill_coupon()
            elif lines and self.coupon_id.coupon_type == '3':
                self.combo_service_coupon()
            elif lines and self.coupon_id.coupon_type == '4':
                self.treatment_coupon()
            elif lines and self.coupon_id.coupon_type == '5':
                self.group_coupon()
            elif lines and self.coupon_id.coupon_type == '6':
                self.cart_class_coupon()
            elif lines and self.coupon_id.coupon_type == '7':
                self.old_new_customers_coupon()
            elif lines and self.coupon_id.coupon_type == '8':
                self.used_service_coupon()

    # # Giảm giá dịch vụ đơn
    # def service_coupon(self):
    #     for discount in self.coupon_id.discount_program_list:
    #         for line in self.crm_id.crm_line_ids:
    #             # kiểm tra giảm giá theo nhóm sản phẩm hoặc sản phẩm
    #             if discount.type_product == 'product':
    #                 check = self.product_coupon(discount, line)
    #             else:
    #                 check = self.group_product_coupon(discount, line)
    #             if self.check_quantity(discount, line) is True:
    #                 # Kiển tra nhóm sản phẩm/sản phẩm và số lượng
    #                 if check is True and self.check_quantity(discount, line) is True:
    #                     self.apply_discount(discount, line)

    @api.depends('type_action')
    def depends_type_action(self):
        for record in self:
            if record.type_action == 'reverse_full':
                record.description = "Sau khi thực hiện hành động này, coupon khuyến mãi sẽ được hủy bỏ ở tất cả các line dịch vụ, bao gồm cả các line đã sử dụng.Điều này có thể gây ra chênh lệch số tiền khách đóng ở những line đã sử dụng"
            elif record.type_action == 'reverse_part':
                record.description = "Sau khi thực hiện hành động này, coupon khuyến mãi mà người dùng chọn sẽ được hủy bỏ ở các line dịch vụ chưa sử dụng"
            else:
                record.description = "Áp dụng coupon khuyến mãi"

    # @api.onchange('type_action', 'type_coupon', 'campaign_id')
    # def onchange_crm_get_coupon(self):
    #     self.coupon_id = False
    #     domain = [('stage_prg', '=', 'active')]
    #     if self.type_action == 'apply':
    #         if self.campaign_id:
    #             domain += [('campaign_id', '=', self.campaign_id.id),
    #                        ('brand_id', '=', self.crm_id.brand_id.id), ('coupon_type', '=', self.type_coupon)]
    #         else:
    #             domain += [('brand_id', '=', self.crm_id.brand_id.id), ('coupon_type', '=', self.type_coupon)]
    #     else:
    #         domain += [('id', 'in', self.crm_id.prg_ids.ids)]
    #     return {'domain': {'coupon_id': domain}}
    @api.onchange('crm_id', 'type_action', 'campaign_id', 'type_coupon')
    def onchange_crm(self):
        deposit = self.env['crm.request.deposit'].search([('status', '=', 'new'), ('booking_id', '=', self.crm_id.id)])
        self.coupon_id = False
        if self.crm_id:
            domain = []
            if self.type_action == 'apply':
                if self.campaign_id and self.campaign_id.campaign_status == '2':
                    domain += [('stage_prg', '=', 'active'), ('campaign_id', '=', self.campaign_id.id),
                               ('brand_id', '=', self.crm_id.brand_id.id), ('coupon_type', '=', self.type_coupon)]
                    self.hide_type = False
                elif self.campaign_id and self.campaign_id.campaign_status != '2':
                    self.hide_type = True
                    domain += [('campaign_id', 'in', deposit.campaign_id.id)]
                else:
                    domain += [('stage_prg', '=', 'active'), ('brand_id', '=', self.crm_id.brand_id.id)]
                    self.hide_type = False
            else:
                domain += [('id', 'in', self.crm_id.prg_ids.ids)]
            coupon_id = self.env['crm.discount.program'].search(domain)
            # if self.crm_id.kept_coupon:
            #     coupon_id += self.env['crm.discount.program'].search([('campaign_id', '=', self.campaign_id.id), ('coupon_type', '=', self.type_coupon)]) # Trường hợp này muốn giữ tất cả các coupon trong chiến dịch
            #     # coupon_id += self.crm_id.kept_coupon # Trường hợp này chỉ giữ coupon mà user muốn đặt cọc
            return {'domain': {'coupon_id': [('id', 'in', coupon_id.ids)]}}

    def mes_success(self):
        view_rec = self.env.ref('crm_coupon.view_apply_coupon_finish')
        action = self.env.ref(
            'crm_coupon.action_view_apply_coupon_success_wizard').read([])[0]
        action['views'] = [(view_rec and view_rec.id or False, 'form')]
        return action

    def create_history(self, discount, line, value=0):
        check = False
        self.update_sale_order(line)
        for rec in self.env['crm.line.discount.history'].search([('discount_program', '=', self.coupon_id.id)]):
            if (line.product_id.type == 'service' and rec.crm_line.id == line.id) or (line.product_id.type == 'product' and rec.crm_line_product.id == line.id):
                check = True
                rec.discount_program_list += discount
                if discount.type_discount == 'percent' or 'cash':
                    if self.coupon_id.coupon_type != 2:
                        rec.discount += discount.discount_bonus
                    rec.discount += discount.discount
                else:
                    rec.discount = discount.discount
        if check is False and self.coupon_id.coupon_type != '2':
            history = self.env['crm.line.discount.history'].create({
                'booking_id': self.crm_id.id,
                'crm_line': line.id if line.product_id.type == 'service' else None,
                'crm_line_product': line.id if line.product_id.type == 'product' else None,
                'discount_program': self.coupon_id.id,
                'discount_program_list': [(3, discount.id)],
                'index': discount.index or 0,
                'type': 'discount',
                'type_discount': discount.type_discount,
                'discount': discount.discount + discount.discount_bonus
            })
            return history
        elif check is False and self.coupon_id.coupon_type == '2':
            history = self.env['crm.line.discount.history'].create({
                'booking_id': self.crm_id.id,
                'crm_line': line.id if line.product_id.type == 'service' else None,
                'discount_program': self.coupon_id.id,
                'discount_program_list': [(3, discount.id)],
                'index': 0,
                'type': 'discount',
                'type_discount': discount.type_discount,
                'discount': discount.discount,
                'value': value
            })
            return history

    @api.onchange('coupon_id')
    def _onchange_coupon_id(self):
        if self.type_coupon is False:
            raise ValidationError('Chưa chọn loại coupon')
        self.apply_combo = None
        self.show_info()
        crm_lines = self.crm_id.crm_line_ids.filtered(
            lambda l: (self.coupon_id not in l.prg_ids) and (l.stage not in ['done', 'waiting', 'cancel']) and not l.discount_review_id)
        self.line_ids = [(6, 0, crm_lines.ids)]

    @api.onchange('line_ids')
    def _onchange_line_ids(self):
        self.apply_combo = None
        self.show_info()

    # hoàn lại coupon
    def reverse_prg_ids(self):
        if self.type_action == 'reverse_part':
            # Lấy ra danh sách (B1) các dịch vụ của BK chưa sử dụng và đc áp CTKM đã chọn
            crm_line_new_ids = self.crm_id.crm_line_ids.filtered(
                lambda l: (l.stage in ('new', 'chotuvan')) and (self.coupon_id in l.prg_ids))
            for line in crm_line_new_ids:
                line_discount_history = self.env['crm.line.discount.history'].search(
                    [('crm_line', '=', line.id), ('booking_id', '=', self.crm_id.id),
                     ('discount_program', '=', self.coupon_id.id)])
                if line_discount_history.type == 'discount':
                    # Nếu xác định line dịch vụ này hưởng khuyến mãi đơn lẻ thì giảm trừ như bình thường
                    if line_discount_history.index == 0:
                        line.prg_ids = [(3, self.coupon_id.id)]
                        self.crm_id.prg_ids = [(3, self.coupon_id.id)]
                        if line_discount_history.type_discount == 'percent':
                            line.discount_percent = line.discount_percent - line_discount_history.discount
                        elif line_discount_history.type_discount == 'cash':
                            line.discount_cash = line.discount_cash - line_discount_history.discount
                        else:
                            line.sale_to = line.sale_to - line_discount_history.discount
                    # Nếu xác định line dịch vụ này hưởng khuyến mãi combo thì:
                    # Bước 1: Tìm bản ghi lịch sử km khác có chung lead/bk, có cùng chỉ số, và cùng CTKM
                    # Bước 2: Kiểm tra line dịch vụ đó đã sử dụng chưa, nếu chưa thì hoàn lại luôn cho cả combo, nếu đã sử dụng sẽ không được hủy CTKM cho cả combo này nữa
                    # Bước 3: Xóa line đã hoàn khỏi danh sách B1
                    elif line_discount_history.index != 0:
                        line_related = self.env['crm.line']
                        line_discount_history_related = self.env['crm.line.discount.history'].search(
                            [('index', '=', line_discount_history.index), ('booking_id', '=', self.crm_id.id),
                             ('discount_program', '=', self.coupon_id.id),
                             ('id', '!=', line_discount_history.id)])
                        line_related += line_discount_history_related.crm_line
                        if line_related.stage in ('new', 'chotuvan'):
                            if line_discount_history_related.type == 'discount':
                                # Hoàn giảm giá ở line liên quan
                                line_related.prg_ids = [(3, self.coupon_id.id)]
                                self.crm_id.prg_ids = [(3, self.coupon_id.id)]
                                if line_discount_history_related.type_discount == 'percent':
                                    line_related.discount_percent = line_related.discount_percent - line_discount_history_related.discount
                                elif line_discount_history_related.type_discount == 'cash':
                                    if self.coupon_id.coupon_type != '2':
                                        line.discount_cash = line.discount_cash - line_discount_history_related.discount
                                    else:
                                        line.discount_cash = line.discount_cash - line_discount_history_related.value
                                else:
                                    line_related.sale_to = line_related.sale_to - line_discount_history_related.discount
                            elif line_discount_history_related.type == 'gift':
                                line_related.unlink()
                            line_discount_history_related.unlink()
                            # Hoàn giảm giá ở line ban đầu
                            line.prg_ids = [(3, self.coupon_id.id)]
                            self.crm_id.prg_ids = [(3, self.coupon_id.id)]
                            if line_discount_history.type_discount == 'percent':
                                line.discount_percent = line.discount_percent - line_discount_history.discount
                            elif line_discount_history.type_discount == 'cash':
                                if self.coupon_id.coupon_type != '2':
                                    line.discount_cash = line.discount_cash - line_discount_history.discount
                                else:
                                    line.discount_cash = line.discount_cash - line_discount_history.value
                            else:
                                line.sale_to = line.sale_to - line_discount_history.discount
                for rec in line_discount_history.discount_program_list.ids:
                    discount_id = self.env['crm.discount.program.list'].search([('id', '=', rec.id)])
                    discount_id.limit_discount += 1
                line_discount_history.unlink()
        else:
            crm_line_ids = self.crm_id.crm_line_ids.filtered(
                lambda l: (self.coupon_id in l.prg_ids))
            for line in crm_line_ids:
                line_discount_history = self.env['crm.line.discount.history'].search(
                    [('crm_line', '=', line.id), ('booking_id', '=', self.crm_id.id),
                     ('discount_program', '=', self.coupon_id.id)])
                for rec in line_discount_history.discount_program_list.ids:
                    discount_id = self.env['crm.discount.program.list'].search([('id', '=', rec.id)])
                    discount_id.limit_discount += 1
                if line_discount_history.type == 'discount':
                    line.prg_ids = [(3, self.coupon_id.id)]
                    self.crm_id.prg_ids = [(3, self.coupon_id.id)]
                    if line_discount_history.type_discount == 'percent':
                        line.discount_percent = line.discount_percent - line_discount_history.discount
                    elif line_discount_history.type_discount == 'cash':
                        # Đối với trường hợp giảm giá đơn hàng (2) thực hiện hoàn theo giá trị đã giảm
                        if self.coupon_id.coupon_type != '2':
                            line.discount_cash = line.discount_cash - line_discount_history.discount
                        else:
                            line.discount_cash = line.discount_cash - line_discount_history.value
                    else:
                        line.sale_to = line.sale_to - line_discount_history.discount
                else:
                    line.unlink()
                line_discount_history.unlink()

            crm_line_product_ids = self.crm_id.crm_line_product_ids.filtered(
                lambda l: (self.coupon_id in l.prg_ids))
            for line in crm_line_product_ids:
                line_discount_history = self.env['crm.line.discount.history'].search(
                    [('crm_line_product', '=', line.id), ('booking_id', '=', self.crm_id.id),
                     ('discount_program', '=', self.coupon_id.id)])
                for rec in line_discount_history.discount_program_list.ids:
                    discount_id = self.env['crm.discount.program.list'].search([('id', '=', rec.id)])
                    discount_id.limit_discount += 1
                if line_discount_history.type == 'discount':
                    line.prg_ids = [(3, self.coupon_id.id)]
                    self.crm_id.prg_ids = [(3, self.coupon_id.id)]
                    if line_discount_history.type_discount == 'percent':
                        line.discount_percent = line.discount_percent - line_discount_history.discount
                    elif line_discount_history.type_discount == 'cash':
                        # Đối với trường hợp giảm giá đơn hàng (2) thực hiện hoàn theo giá trị đã giảm
                        if self.coupon_id.coupon_type != '2':
                            line.discount_cash = line.discount_cash - line_discount_history.discount
                        else:
                            line.discount_cash = line.discount_cash - line_discount_history.value
                    else:
                        line.sale_to = line.sale_to - line_discount_history.discount
                else:
                    line.unlink()
                line_discount_history.unlink()
        if self.coupon_id.coupon_type == '5':
            group = self.env['crm.group.customer'].search([
                ('booking_ids', '=', self.crm_id.id),
                ('coupon_id', '=', self.coupon_id.id)])
            for rec in group:
                rec.booking_ids -= self.crm_id

    def show_info(self):
        # self.reverse_prg_ids()
        if self.coupon_id.coupon_type == '3':
            list_index = self.list_available_combo(self.coupon_id)
            indexs = self.check_suitable_combo(list_index)
            if len(indexs) != 0:
                self.select_combo_index(indexs)
        # elif self.coupon_id.coupon_type == '4':
        #     list_index = self.list_treatment_combo()
        #     indexs = self.check_suitable_combo(list_index)
        #     if len(indexs) != 0:
        #         self.select_combo_index(indexs)

    def update_sale_order(self, line):
        order_id = self.env['sale.order'].search(
            [('booking_id', '=', self.crm_id.id), ('state', '=', 'draft')])
        if order_id:
            order_line_ids = order_id.mapped('order_line')
            order_line_id = order_line_ids.filtered(lambda l: l.crm_line_id == line)
            if order_line_id and ((line.uom_price * line.quantity) != 0):
                order_line_id = order_line_id[0]
                order_line_id.discount = line.discount_percent
                order_line_id.discount_cash = line.discount_cash / (
                            line.quantity * line.uom_price) * order_line_id.uom_price
                order_line_id.sale_to = line.sale_to / (line.quantity * line.uom_price) * order_line_id.uom_price


class ApplyCouponDetail(models.TransientModel):
    _name = 'crm.apply.coupon.detail'
    _description = 'Apply Coupon Detail'

    apply_coupon_id = fields.Many2one('crm.apply.coupon')
    check = fields.Boolean(string='Select')
    index = fields.Integer(string='Combo', readonly=True)
    combo_note = fields.Char('Combo describe')
