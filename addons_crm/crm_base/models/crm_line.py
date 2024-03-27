from odoo import fields, api, models, _
from odoo.exceptions import ValidationError


class CrmLine(models.Model):
    _name = 'crm.line'
    _description = 'Crm Line'
    _rec_name = 'product_id'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # them truong company shared va chuyen exam room thanh many2many

    name = fields.Char('Name')
    company_id = fields.Many2one('res.company', string='Company', tracking=True)
    brand_id = fields.Many2one(related='company_id.brand_id', string='Thương hiệu', store=True)
    quantity = fields.Integer('Quantity', default=1, tracking=True)
    number_used = fields.Integer('Number used', compute='set_number_used', store=True, tracking=True)
    unit_price = fields.Monetary('Unit price', tracking=True)
    discount_percent = fields.Float('Discount(%)', store=True, tracking=True)
    type = fields.Selection([('consu', 'Consumable'), ('service', 'Service'), ('product', 'Storable Product')],
                            string='type', tracking=True)
    discount_cash = fields.Monetary('Discount cash', tracking=True)
    sale_to = fields.Monetary('Sale to', tracking=True)
    price_list_id = fields.Many2one('product.pricelist', string='Price list', tracking=True,
                                    domain="[('brand_id', '=', brand_id)]")
    currency_id = fields.Many2one('res.currency', string='Currency', related='price_list_id.currency_id', store=True,
                                  tracking=True)
    total_before_discount = fields.Monetary('Total before discount', compute='get_total_line', store=True,
                                            tracking=True)
    total_discount = fields.Monetary('Tổng tiền đã giảm', compute='get_total_line', store=True, tracking=True)
    total = fields.Monetary('Total', compute='get_total_line', store=True, tracking=True)
    crm_id = fields.Many2one('crm.lead', string='CRM', tracking=True)
    company_shared = fields.Many2many('res.company', 'line_company_shared2_ref', 'company2s', 'line2s',
                                      string='Company shared', related='crm_id.company2_id', tracking=True)
    product_id = fields.Many2one('product.product', string='Product', tracking=True)
    product_ctg_id = fields.Many2one('product.category', string='Category product', related='product_id.categ_id',
                                     store=True, tracking=True)
    other_discount = fields.Monetary('Other discount', digit=(3, 0),
                                     help='This is the reduced amount on the bill and distributed to each service',
                                     tracking=True)
    order_id = fields.One2many('sale.order', 'crm_line_id', string='Order', tracking=True)
    sale_order_line_id = fields.One2many('sale.order.line', 'crm_line_id', 'sale order line', tracking=True)
    stage = fields.Selection(
        [('chotuvan', 'Chờ tư vấn'), ('new', 'Allow to use'), ('processing', 'Processing'), ('done', 'Done'), ('waiting', 'Awaiting approval'),
         ('cancel', 'Cancel')],
        string='Stage',
        compute='set_stage', store=True, tracking=True)
    cancel = fields.Boolean('Cancel', tracking=True)
    type_brand = fields.Selection([('hospital', 'Hospital'), ('academy', 'Academy')], string='Type',
                                  related='crm_id.type_brand', store=True, tracking=True)
    history_discount_ids = fields.One2many('history.discount', 'crm_line_id', string='History discount', tracking=True)
    source_extend_id = fields.Many2one('utm.source', string='Extended source', tracking=True,
                                       domain="[('extend_source', '=', True)]")
    uom_price = fields.Float('Đơn vị xử lý', default=1, tracking=True)
    discount_review_id = fields.Many2one('crm.discount.review', string='Discount review', tracking=True)
    prg_ids = fields.Many2many('crm.discount.program', 'line_prg_ref', 'prg', 'line', string='Discount program',
                               tracking=True)
    color = fields.Integer('Color', tracking=True)
    line_special = fields.Boolean('Line special', tracking=True)
    note = fields.Char('Notes', tracking=True)
    line_booking_date = fields.Datetime('Ngày hẹn lịch', tracking=True)
    status_cus_come = fields.Selection(
        [('no_come', 'Khách chưa đến'), ('come', 'Khách đến'), ('come_no_service', 'Khách đến, không làm dịch vụ')],
        string='Trạng thái khách đến', tracking=True, default='no_come')
    is_input_num = fields.Boolean(default=False, help="Cho phép nhập trường đơn vị xử lý", tracking=True)
    EXTENSIVE_SOURCE_CLASSIFICATION = [('ext01', 'Mở rộng_Dịch vụ trong Phòng/Bộ phận'),
                                       ('ext02', 'Bán chéo_Dịch vụ ngoài Phòng/Bộ phận'),
                                       ('ext03', 'Upsale_Thay đổi dịch vụ'),
                                       ('ext04', 'Mở rộng_Từ KH tái khám'),
                                       ('ext05', 'Mở rộng_Từ KH khiếu nại'),
                                       ('ext06', 'Mở rộng_Từ KH bảo hành'),
                                       ]
    extensive_source_classification = fields.Selection(EXTENSIVE_SOURCE_CLASSIFICATION, string='Phân loại mở rộng')

    # Hủy dịch vụ

    REASON_LINE_CANCEL = [('change_service', 'Đổi sang dịch vụ khác cùng nhóm'), ('consider_more', 'Cân nhắc thêm'),
                          ('due_to_illness', 'Hủy do bệnh lý'), ('create_wrong_service', 'Thao tác tạo sai dịch vụ'),
                          ('not_money', 'Không đủ chi phí'), ('consultant', 'Tham khảo trước'),
                          ('other', 'Lý do khác (Ghi rõ lý do)')]
    reason_line_cancel = fields.Selection(REASON_LINE_CANCEL, string='Lý do hủy dịch vụ')
    cancel_user = fields.Many2one('res.users', 'Người hủy')
    cancel_date = fields.Datetime('Thời gian hủy')

    # Thông tin tư vấn
    CONSULTING_ROLE = [('1', 'Tư vấn độc lập'), ('2', 'Tư vấn đồng thời'), ('3', 'Lễ tân - CVTV cùng tư vấn'),
                       ('4', 'BS da liễu - KTV cùng tư vấn'), ('5', 'Tư vấn chính'), ('6', 'Tư vấn phụ')]
    # consultants_1 = fields.Many2one('res.users', string='Consultants 1', default=lambda self: self.env.user, tracking=True)
    consultants_1 = fields.Many2one('res.users', string='Consultants 1', tracking=True)
    consulting_role_1 = fields.Selection(CONSULTING_ROLE, string='Vai trò tư vấn viên 1', tracking=True)
    consultants_2 = fields.Many2one('res.users', string='Consultants 2', tracking=True)
    consulting_role_2 = fields.Selection(CONSULTING_ROLE, string='Vai trò tư vấn viên 2', tracking=True)
    consultants_3 = fields.Many2one('res.users', string='Consultants 3', tracking=True)
    consulting_role_3 = fields.Selection(CONSULTING_ROLE, string='Vai trò tư vấn viên 3', tracking=True)
    ho_tro = fields.Many2one('res.users', string='Hỗ trợ tư vấn')

    # Dành cho Booking bảo hành
    initial_product_id = fields.Many2one('product.product', help='Trường này dành cho Booking bảo hành',
                                         string='Dịch vụ ban đầu', tracking=True)
    TYPE_GUARANTEE = [('1', 'Một phần trước 01/06/2020'), ('2', 'Một phần trước 01/10/2020'),
                      ('3', 'Một phần sau 01/06/2020'), ('4', 'Một phần sau 01/10/2020'),
                      ('5', 'Toàn phần trước 01/06/2020'), ('6', 'Toàn phần trước 01/10/2020'),
                      ('7', 'Toàn phần sau 01/06/2020'), ('8', 'Toàn phần sau 01/10/2020'), ('9', 'Bảo hành không do lỗi chuyên môn'), ('10', 'Bảo hành chung (TH Paris)')]
    type_guarantee = fields.Selection(TYPE_GUARANTEE,
                                      help='Trường này dành cho Booking bảo hành', string='Loại bảo hành',
                                      tracking=True)
    type_pricelist = fields.Selection('Type', related='price_list_id.type', store='True', tracking=True)
    bh_ngoai_goi = fields.Selection(
        [('1', 'Bảo hành trong gói dịch vụ'), ('2', 'Bảo hành ngoài gói dịch vụ theo chỉ định Bác sĩ')],
        'Chế độ bảo hành (Dành riêng cho thương hiệu Đông Á)')
    check_current_user = fields.Boolean(compute="_check_user")
    # date_done = fields.Datetime('Ngày hoàn thành dịch vụ', compute='set_number_used', store=True)
    gia_truoc_huy = fields.Monetary('Giá trước khi hủy')
    crm_information_ids = fields.One2many('crm.information.consultant', 'crm_line_id', string='Thông tin tư vấn')
    is_pk = fields.Boolean('Tạo từ Phiếu khám', store=False)

    @api.depends('create_uid')
    def _check_user(self):
        for record in self:
            record.check_current_user = True if record.create_uid == self.env.user else False

    @api.onchange('crm_id', 'type_pricelist')
    def get_service_guarantee(self):
        """
        Thêm dịch vụ bảo hành trực tiếp tại crm line
        """
        if self.crm_id and self.type_pricelist == 'guarantee':
            partner = self.crm_id.partner_id
            booking_won = self.env['crm.lead'].sudo().search(
                [('type', '=', 'opportunity'), ('partner_id', '=', partner.id),
                 ('id', '!=', self.env.context.get('default_crm_id')),
                 ('stage_id', 'not in',
                  [self.env.ref('crm_base.crm_stage_cancel').id, self.env.ref('crm_base.crm_stage_out_sold').id])])
            line = self.env['crm.line'].search([('stage', '=', 'done'), ('crm_id', 'in', booking_won.ids)]).mapped(
                'product_id')
            return {'domain': {'initial_product_id': [('id', 'in', line.ids)]}}

    @api.onchange('company_id')
    def _onchange_company_id(self):
        # self.price_list_id = None
        if self.company_id.brand_id:
            return {
                'domain': {'price_list_id': [('brand_id', '=', self.company_id.brand_id.id)]}
            }

    @api.onchange('crm_id')
    def onchange_crm_id(self):
        if self.crm_id and self.crm_id.type == 'opportunity' and self.crm_id.booking_date:
            self.line_booking_date = self.crm_id.booking_date
        if self.crm_id:
            list_company = self.env['res.company']
            if self.crm_id.company_id:
                list_company += self.crm_id.company_id
            if self.crm_id.company2_id:
                list_company += self.crm_id.company2_id
            return {'domain': {'company_id': [('id', 'in', list_company.ids)]}}

    @api.depends('sale_order_line_id.state', 'number_used', 'quantity', 'cancel', 'discount_review_id.stage_id')
    def set_stage(self):
        for rec in self:
            rec.stage = 'new'
            sol_stage = rec.sale_order_line_id.mapped('state')
            if rec.cancel is True:
                rec.stage = 'cancel'
            elif rec.discount_review_id and rec.discount_review_id.stage_id == 'offer':
                rec.stage = 'waiting'
            elif rec.number_used >= rec.quantity:
                rec.stage = 'done'
            elif 'draft' in sol_stage:
                rec.stage = 'processing'

    def unlink(self):
        for rec in self:
            if rec.create_uid != self.env.user:
                raise ValidationError('Bạn không thể xóa dịch vụ của nhân viên khác tạo !!!')
            elif rec.stage == 'new' and rec.number_used > 0:
                raise ValidationError('Bạn chỉ có thể xóa dịch vụ khi khách hàng chưa sử dụng !!!')
            elif rec.stage != 'new':
                raise ValidationError(
                    'Bạn chỉ có thế xóa dịch vụ khi dịch vụ đó đang ở trạng thái được phép sử dụng !!!')
            return super(CrmLine, self).unlink()

    @api.depends('sale_order_line_id.state')
    def set_number_used(self):
        for rec in self:
            rec.number_used = 0
            if rec.sale_order_line_id:
                list_sol = rec.sale_order_line_id.filtered(lambda l: l.state in ['sale', 'done'])
                rec.number_used = len(list_sol)
                # if not rec.date_done and rec.number_used == 1:
                #     rec.date_done = fields.datetime.now()

    # @api.onchange('institution_share')
    # def onchange_institution_share(self):
    #     if self.institution_share:
    #         print(self.env.user.company_ids)
    #         return {'domain': {'company_id': [('id', 'in', self.env.user.company_ids.ids)]}}

    @api.model
    def default_get(self, fields):
        """ Hack :  when going from the pipeline, creating a stage with a sales team in
            context should not create a stage for the current Sales Team only
        """
        ctx = dict(self.env.context)
        if ctx.get('default_type') == 'lead' or ctx.get('default_type') == 'opportunity':
            ctx.pop('default_type')
        return super(CrmLine, self.with_context(ctx)).default_get(fields)

    @api.onchange('product_id')
    def set_unit_price(self):
        if self.product_id:
            item_price = self.env['product.pricelist.item'].search(
                [('pricelist_id', '=', self.price_list_id.id), ('product_id', '=', self.product_id.id)])
            if item_price:
                self.unit_price = item_price.fixed_price
            else:
                raise ValidationError(_('This service is not included in the price list'))
        else:
            self.unit_price = 0
            self.quantity = 1
            self.discount_cash = 0
            self.discount_percent = 0

    @api.depends('quantity', 'unit_price', 'discount_percent', 'discount_cash', 'uom_price', 'sale_to',
                 'other_discount')
    def get_total_line(self):
        for rec in self:
            rec.total_before_discount = rec.unit_price * rec.quantity * rec.uom_price
            if not rec.sale_to:
                rec.total = rec.total_before_discount - rec.total_before_discount * \
                            rec.discount_percent / 100 - rec.discount_cash - rec.other_discount
                rec.total_discount = rec.total_before_discount - rec.total
            else:
                rec.total = rec.sale_to - rec.other_discount

    @api.constrains('discount_percent', 'discount_cash', 'total', 'total_before_discount')
    def error_discount(self):
        for rec in self:
            if rec.discount_percent > 100 or rec.discount_percent < 0:
                raise ValidationError('Giảm giá phần trăm chỉ chấp nhận giá trị trong khoảng 0 đến 100')
            if rec.discount_cash > rec.total_before_discount:
                raise ValidationError('Giảm giá tiền mặt không thể lớn hơn tổng tiền dịch vụ')
            if rec.total < 0:
                raise ValidationError('Tổng tiền sau giảm không được âm')
            if rec.sale_to > (rec.uom_price * rec.quantity * rec.unit_price) or rec.sale_to < 0:
                raise ValidationError('Số tiền giảm còn không hợp lệ')

    # @api.constrains('quantity')
    # def validate_quantity(self):
    #     for rec in self:
    #         if rec.quantity <= 0:
    #             raise ValidationError(_('Quantity must be greater than 0'))
    #         elif rec.quantity >= 100:
    #             raise ValidationError(_('The amount cannot be more than 100'))
    #
    # @api.onchange('quantity')
    # def validate_quantity_crm_line(self):
    #     for rec in self:
    #         if rec.quantity <= 0:
    #             raise ValidationError(_('Quantity must be greater than 0'))
    #         elif rec.quantity >= 100:
    #             raise ValidationError(_('The amount cannot be more than 100'))

    def reverse_prg_ids(self):
        if self.prg_ids:
            for prg in self.prg_ids:
                discount_history_id = self.env['crm.line.discount.history'].search(
                    [('crm_line', '=', self.id), ('booking_id', '=', self.crm_id.id),
                     ('discount_program', '=', prg.id)])
                if discount_history_id.type == 'gift':
                    if discount_history_id.index == 0:
                        discount_history_id.unlink()
                        self.note = 'Line dịch vụ tặng bị hủy do thao tác người dùng ấn hủy'
                else:
                    if discount_history_id.index == 0:
                        self.prg_ids = [(3, prg.id)]
                        if discount_history_id.type_discount == 'percent':
                            self.discount_percent = self.discount_percent - discount_history_id.discount
                        elif discount_history_id.type_discount == 'cash':
                            self.discount_cash = self.discount_cash - discount_history_id.discount
                        else:
                            self.sale_to = self.sale_to - discount_history_id.discount
                    elif discount_history_id.index != 0:
                        # Xóa CTKM ở các line có liên quan (nằm trong combo)
                        line_discount_history_related_ids = self.env['crm.line.discount.history'].search(
                            [('index', '=', discount_history_id.index), ('booking_id', '=', self.crm_id.id),
                             ('discount_program', '=', prg.id),
                             ('id', '!=', discount_history_id.id)])
                        for line_discount_history_related in line_discount_history_related_ids:
                            line_related = self.env['crm.line']
                            line_related += line_discount_history_related.crm_line
                            if line_discount_history_related.type == 'gift':
                                line_discount_history_related.unlink()
                                if line_related.stage != 'done':
                                    line_related.stage = 'cancel'
                                    line_related.prg_ids = [(3, prg.id)]
                                    line_related.note = 'Line dịch vụ tặng bị hủy do dịch vụ đi kèm bị hủy'
                            else:
                                line_related.prg_ids = [(3, prg.id)]
                                if line_discount_history_related.type_discount == 'percent':
                                    line_related.discount_percent = line_related.discount_percent - line_discount_history_related.discount
                                elif line_discount_history_related.type_discount == 'cash':
                                    line_related.discount_cash = line_related.discount_cash - line_discount_history_related.discount
                                else:
                                    line_related.sale_to = line_related.sale_to - line_discount_history_related.discount
                                line_discount_history_related.unlink()
                        # Hủy CTKM và đưa line về trạng thái hủy
                        self.prg_ids = [(3, prg.id)]
                        if discount_history_id.type_discount == 'percent':
                            self.discount_percent = self.discount_percent - discount_history_id.discount
                        elif discount_history_id.type_discount == 'cash':
                            self.discount_cash = self.discount_cash - discount_history_id.discount
                        else:
                            self.sale_to = self.sale_to - discount_history_id.discount
                        discount_history_id.unlink()

    def cancel_line(self):
        return {
            'name': 'HỦY DỊCH VỤ',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('crm_base.view_form_cancel_crm_line').id,
            'res_model': 'crm.line.cancel',
            'context': {
                'default_crm_line_id': self.id,
            },
            'target': 'new',
        }

    def create_quotation(self):
        order = self.env['sale.order'].create({
            'partner_id': self.crm_id.partner_id.id,
            'pricelist_id': self.crm_id.price_list_id.id,
            'company_id': self.crm_id.company_id.id,
            'user_id': self.crm_id.user_id.id,
            'opportunity_id': self.crm_id.id,
            # 'date_order': fields.Datetime.now,
            'crm_line_id': self.id,
        })

        order_line = self.env['sale.order.line'].create({
            'product_id': self.product_id.id,
            'name': self.product_id.name,
            'product_uom_qty': self.quantity,
            'product_uom': self.product_id.uom_id.id,
            'price_unit': self.unit_price,
            'discount': self.discount_percent,
            'order_id': order.id,
        })

        return {
            'name': 'Quotations',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('sale.view_order_form').id,
            'res_model': 'sale.order',
            'res_id': order.id,
        }

    def update_consulting_info(self):
        if self.crm_id.brand_id.id != 3:
            return {
                'name': 'CẬP NHẬT THÔNG TIN TƯ VẤN',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': self.env.ref('crm_base.form_change_consultants').id,
                'res_model': 'crm.line',
                'res_id': self.id,
                'context': {
                    'default_consultants_1': self.consultants_1.id,
                    'default_consultants_2': self.consultants_2.id,
                    'default_consulting_role_1': self.consulting_role_1,
                    'default_consulting_role_2': self.consulting_role_2,
                },
                'target': 'new',
            }
        else:
            return {
                'name': 'CẬP NHẬT THÔNG TIN TƯ VẤN',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': self.env.ref('crm_base.form_change_consultants_paris').id,
                'res_model': 'crm.line',
                'res_id': self.id,
                'context': {
                    'default_crm_information_ids': self.crm_information_ids.ids,
                },
                'target': 'new',
            }


    def update_consulting(self):
        if self.crm_id.brand_id.id != 3:
            self.consultants_1 = self.consultants_1.id
            self.consultants_2 = self.consultants_2.id
            self.consulting_role_1 = self.consulting_role_1
            self.consulting_role_2 = self.consulting_role_2
        else:
            self.crm_information_ids = self.crm_information_ids.ids

    def cron_job_create_date_done(self):
        config = self.env['ir.config_parameter'].sudo()
        limit = config.get_param('limit_datedone_2')
        id_line = config.get_param('id_line_2')
        crm_line_ids = self.env['crm.line'].sudo().search(
            [('number_used', '!=', 0), ('id', '>=', int(id_line)), ('date_done', '=', None)], limit=int(limit))
        for crm_line_id in crm_line_ids:
            for sol in crm_line_id.sale_order_line_id:
                if sol.order_id.state == 'sale':
                    walkin = self.env['sh.medical.appointment.register.walkin'].sudo().search(
                        [('sale_order_id', '=', sol.order_id.id)])
                    if walkin:
                        for reexam in walkin.reexam_ids:
                            if reexam.state == 'Confirmed':
                                select = """update crm_line set date_done = '%s' where id = %s""" % (
                                reexam.date_out.strftime('%Y-%m-%d %H:%M:%S'), crm_line_id.id)
                                self.env.cr.execute(select)
                                break
                    break