from odoo import fields, models, api
from odoo.exceptions import ValidationError


class UpdateBookingWizard(models.TransientModel):
    _name = 'crm.update.booking'
    _description = 'CRM Update Booking Wizard'

    CONSULTING_ROLE = [('1', 'Tư vấn độc lập'), ('2', 'Tư vấn đồng thời'), ('3', 'Lễ tân - CVTV cùng tư vấn'),
                       ('4', 'BS da liễu - KTV cùng tư vấn'), ('5', 'Tư vấn chính'), ('6', 'Tư vấn phụ')]

    TYPE_ACTION = [('effect', 'BOOKING HIỆU LỰC'),
                   ('expire', 'BOOKING HẾT HIỆU LỰC'),
                   ('won', 'ĐÓNG BOOKING ĐỂ TẠO BOOKING BẢO HÀNH'),
                   ('name', 'ĐỔI TÊN BOOKING'),
                   ('update_source', 'ĐỔI NGUỒN (Admin)'),
                   ('name_customer', 'ĐỔI TÊN KHÁCH HÀNG'),
                   ('gender', 'GIỚI TÍNH'),
                   ('stage', 'CHUYỂN TRẠNG THÁI BOOKING'),
                   ('stage_line', 'CHUYỂN TRẠNG THÁI LINE DỊCH VỤ'),
                   ('consultant_line_product', 'CẬP NHẬT TƯ VẤN VIÊN LINE SẢN PHẨM')]
    GENDER = [('male', 'Nam'),
              ('female', 'Nữ'),
              ('transguy', 'Transguy'),
              ('transgirl', 'Transgirl'),
              ('other', 'Khác')]
    STAGE_LINE = [('new', 'Được sử dụng'),
                  ('processing', 'Đang xử trí'),
                  ('done', 'Kết thúc'),
                  ('cancel', 'Hủy')]
    type_action = fields.Selection(TYPE_ACTION, 'Hành động')
    booking_id = fields.Many2one('crm.lead')
    name = fields.Char('Tên Booking mới')
    name_customer = fields.Char('Tên Khách hàng mới')
    gender = fields.Selection(GENDER, string='Giới tính')
    stage_id = fields.Many2one('crm.stage', string='Trạng thái')
    crm_line = fields.Many2one('crm.line', domain="[('crm_id','=', booking_id)]")
    stage_line = fields.Selection(STAGE_LINE, 'Trạng thái line dịch vụ')
    booking_source = fields.Many2one('utm.source', 'Nguồn Booking')
    has_group_tool = fields.Boolean(compute='check_user_group_tool')
    customer_source = fields.Many2one('utm.source', 'Nguồn khách hàng')
    line_product = fields.Many2one('crm.line.product', domain="[('booking_id','=', booking_id)]")

    consultants_1 = fields.Many2one('res.users', string='Tư vấn viên 1')
    consulting_role_1 = fields.Selection(CONSULTING_ROLE, string='Vai trò tư vấn viên 1')
    consultants_2 = fields.Many2one('res.users', string='Tư vấn viên 2')
    consulting_role_2 = fields.Selection(CONSULTING_ROLE, string='Vai trò tư vấn viên 2')
    consultants_3 = fields.Many2one('res.users', string='Tư vấn viên 3')
    consulting_role_3 = fields.Selection(CONSULTING_ROLE, string='Vai trò tư vấn viên 3')

    @api.depends('booking_id')
    def check_user_group_tool(self):
        for rec in self:
            rec.has_group_tool = False
            if rec.booking_id and self.env.user.has_group('crm_tool.group_tool'):
                rec.has_group_tool = True

    @api.onchange('has_group_tool')
    def set_type_action(self):
        self.type_action = False
        if not self.has_group_tool:
            self.type_action = 'won'

    def update_booking(self):
        if not self.env.user.has_group('crm_tool.group_tool'):
            if self.type_action != 'won':
                raise ValidationError(
                    'Bạn không có quyền thao tác chức năng này.\nLiên hệ Giám đốc CRM để biết thêm thông tin ^^')
            elif self.type_action == 'won' and str(self.booking_id.name).startswith('BOOK-'):
                raise ValidationError('Bạn chỉ có thể hoàn thành những Booking có mã K-Book, P-Book, D-Book, B-Book')
            else:
                self.booking_id.write({
                    'stage_id': 4
                })
                if self.booking_id.crm_line_ids:
                    lines = self.booking_id.crm_line_ids.filtered(lambda l: l.stage != 'cancel')
                    for line in lines:
                        line.write({'stage': 'done'})
        else:
            if self.type_action == 'effect':
                self.booking_id.write({
                    'effect': 'effect'
                })
            elif self.type_action == 'expire':
                self.booking_id.write({
                    'effect': 'expire'
                })
            elif self.type_action == 'won':
                self.booking_id.write({
                    'stage_id': 4,
                    'effect': 'expire'
                })
                if self.booking_id.crm_line_ids:
                    lines = self.booking_id.crm_line_ids.filtered(lambda l: l.stage != 'cancel')
                    for line in lines:
                        line.write({'stage': 'done'})
            elif self.type_action == 'name' and self.name:
                self.booking_id.write({
                    'name': self.name
                })
            elif self.type_action == 'update_source':
                if self.booking_source:
                    # Đổi nguồn Booking
                    self.booking_id.write({
                        'source_id': self.booking_source,
                        'category_source_id': self.booking_source.category_id
                    })
                    # Đổi nguồn line
                    self.booking_id.crm_line_ids.write({
                        'source_extend_id': self.booking_source
                    })
                    # Đổi nguồn Lead
                    self.booking_id.lead_id.write({
                        'source_id': self.booking_source,
                        'category_source_id': self.booking_source.category_id
                    })
                    # ĐỔi nguồn SO
                    orders = self.env['sale.order'].sudo().search([('booking_id', '=', self.booking_id.id)])
                    if orders:
                        for order in orders:
                            order.source_id = self.booking_source
                if self.customer_source:
                    # Nếu đổi nguồn ban đầu KH sẽ tìm tất cả các lead/booking của KH này để đổi nguồn ban đầu
                    self.booking_id.partner_id.source_id = self.customer_source
                    booking_ids = self.env['crm.lead'].search(
                        [('type', '=', 'opportunity'), ('partner_id', '=', self.booking_id.partner_id.id)])
                    if booking_ids:
                        for booking in booking_ids:
                            booking.write({
                                'original_source_id': self.customer_source
                            })
                    lead_ids = self.env['crm.lead'].search(
                        [('type', '=', 'lead'), ('phone', '=', self.booking_id.partner_id.phone)])
                    if lead_ids:
                        for lead in lead_ids:
                            lead.write({
                                'original_source_id': self.customer_source
                            })
            elif self.type_action == 'name_customer' and self.name_customer:
                self.booking_id.write({
                    'contact_name': self.name_customer
                })
                if self.booking_id.lead_id:
                    self.booking_id.lead_id.write({
                        'contact_name': self.name_customer,
                        'name': self.name_customer
                    })
            elif self.type_action == 'gender':
                self.booking_id.write({
                    'gender': self.gender
                })
                self.booking_id.partner_id.write({
                    'gender': self.gender
                })
                if self.booking_id.lead_id:
                    self.booking_id.lead_id.write({
                        'gender': self.gender
                    })
            elif self.type_action == 'stage':
                self.booking_id.write({
                    'stage_id': self.stage_id.id
                })
            elif self.type_action == 'stage_line':
                self.crm_line.write({
                    'stage': self.stage_line
                })
            elif self.type_action == 'consultant_line_product':
                line_product = self.line_product
                line_product.write({
                    'consultants_1': self.consultants_1 if self.consultants_1 else line_product.consultants_1,
                    'consulting_role_1': self.consulting_role_1 if self.consulting_role_1 else line_product.consulting_role_1,
                    'consultants_2': self.consultants_2 if self.consultants_2 else line_product.consultants_2,
                    'consulting_role_2': self.consulting_role_2 if self.consulting_role_2 else line_product.consulting_role_2,
                })
                sale_payments = self.env['crm.sale.payment'].sudo().search(
                    [('crm_line_product_id', '=', line_product.id)])
                sale_payments.write({
                    'consultants_1': self.consultants_1 if self.consultants_1 else line_product.consultants_1,
                    'consulting_role_1': self.consulting_role_1 if self.consulting_role_1 else line_product.consulting_role_1,
                    'consultants_2': self.consultants_2 if self.consultants_2 else line_product.consultants_2,
                    'consulting_role_2': self.consulting_role_2 if self.consulting_role_2 else line_product.consulting_role_2,
                })
                payment_details = self.env['crm.account.payment.product.detail'].sudo().search(
                    [('crm_line_product_id', '=', line_product.id)])
                payment_details.write({
                    'consultants_1': self.consultants_1 if self.consultants_1 else line_product.consultants_1,
                })
                sols = self.env['sale.order.line'].sudo().search([('line_product', '=', line_product.id)])
                sols.write({
                    'consultants_1': self.consultants_1 if self.consultants_1 else line_product.consultants_1,
                    'consultants_2': self.consultants_2 if self.consultants_2 else line_product.consultants_2,
                })
