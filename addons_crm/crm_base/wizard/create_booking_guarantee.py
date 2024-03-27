from odoo import fields, api, models, _
from odoo.exceptions import ValidationError


class CRMConvertServiceGuarantee(models.TransientModel):
    _name = 'crm.convert.service.guarantee'
    _description = 'Convert service guarantee'

    crm_create_guarantee_id = fields.Many2one('crm.create.guarantee')
    crm_id = fields.Many2one('crm.lead', related='crm_create_guarantee_id.crm_id', string='Related booking', store=True)
    TYPE_GUARANTEE = [('1', 'Một phần trước 01/06/2020'), ('2', 'Một phần trước 01/10/2020'),
                      ('3', 'Một phần sau 01/06/2020'), ('4', 'Một phần sau 01/10/2020'),
                      ('5', 'Toàn phần trước 01/06/2020'), ('6', 'Toàn phần trước 01/10/2020'),
                      ('7', 'Toàn phần sau 01/06/2020'), ('8', 'Toàn phần sau 01/10/2020'), ('9', 'Bảo hành không do lỗi chuyên môn'), ('10', 'Bảo hành chung (TH Paris)')]
    type_guarantee = fields.Selection(TYPE_GUARANTEE,
                                      help='Trường này dành cho Booking bảo hành', string='Loại bảo hành')
    crm_line_guarantee = fields.Many2one('crm.line', string='Dịch vụ bảo hành',
                                         domain="[('crm_id','=',crm_id), ('stage', '=', 'done')]")
    product_incurred = fields.Many2one('product.product', string='Dịch vụ phát sinh', domain="[('type','=','service'), ('type_product_crm', '=', 'course')]")

    # @api.constrains('crm_line_guarantee')
    # def validate_line_guarantee(self):
    #     """
    #     Dịch vụ được bảo hành đi kèm loại bảo hành
    #     """
    #     if self.crm_line_guarantee and not self.type_guarantee:
    #         raise ValidationError('Bạn cần chọn loại bảo hành cho dịch vụ này')

    @api.onchange('crm_create_guarantee_id')
    def onchange_brand_id(self):
        domain = []
        brand_id = self.crm_create_guarantee_id.brand_id
        price_list = self.crm_create_guarantee_id.price_list
        # if brand_id.type == 'hospital':
        #     domain += [('type', '=', 'service_crm')]
        # elif brand_id.type == 'academy':
        #     domain += [('type', '=', 'course')]
        if price_list:
            domain += [('id', 'in', price_list.item_ids.mapped('product_id').ids)]
        # print(domain)
        # product_ids = self.env['product.product'].sudo().search(domain)
        # print(product_ids)
        return {'domain': {'product_incurred': [('id', 'in', self.env['product.product'].sudo().search(domain).ids)]}}


class BookingGuarantee(models.TransientModel):
    _name = 'crm.create.guarantee'
    _description = 'wizard create booking guarantee'

    crm_id = fields.Many2one('crm.lead', string='Related booking')
    partner_id = fields.Many2one('res.partner', string='Customer')
    brand_id = fields.Many2one('res.brand', string='Brand')
    price_list_id = fields.Many2one('product.pricelist', string='price list',
                                    domain="[('brand_id','=',brand_id),('type','=','guarantee')]")
    date_guarantee = fields.Datetime('Date guarantee')
    code_booking = fields.Char('Mã booking tương ứng')  # Todo Bỏ
    source_id = fields.Many2one('utm.source', string='Nguồn', domain="[('extend_source', '=', True)]")
    convert_service_guarantee_ids = fields.One2many('crm.convert.service.guarantee', 'crm_create_guarantee_id',
                                                    string='Dich vụ')
    price_list = fields.Many2one('product.pricelist', string='Bảng giá',
                                 help='Bảng giá này dành cho dịch vụ phát sinh cần thu tiền(nếu có)',
                                 domain="[('brand_id','=',brand_id),('type','=','service')]")
    price_list_guarantee = fields.Many2one('product.pricelist', string='Bảng giá bảo hành',
                                           domain="[('brand_id','=',brand_id),('type','=','guarantee')]")
    note = fields.Char('Lý do bảo hành')

    # def confirm(self):
    #     print('33333333333')
    #     # Todo : Phần tạo BK bảo hành này còn thiếu 1 số trường ở lead mới thêm ở module
    #     booking = self.env['crm.lead'].create({
    #         'name': '/',
    #         # 'code_booking': self.code_booking,
    #         'type_crm_id': self.env.ref('crm_base.type_oppor_guarantee').id,
    #         'type': 'opportunity',
    #         'contact_name': self.partner_id.name,
    #         'partner_id': self.partner_id.id,
    #         'stage_id': self.env.ref('crm_base.crm_stage_not_confirm').id,
    #         'phone': self.partner_id.phone,
    #         'mobile': self.partner_id.mobile,
    #         'street': self.partner_id.street,
    #         'overseas_vietnamese': self.partner_id.overseas_vietnamese,
    #         'district_id': self.partner_id.district_id.id,
    #         'email_from': self.partner_id.email,
    #         'lead_id': self.crm_id.id if self.crm_id else False,
    #         'online_counseling': self.crm_id.online_counseling if self.crm_id else False,
    #         'shuttle_bus': self.crm_id.shuttle_bus if self.crm_id else False,
    #         'work_online': self.crm_id.work_online if self.crm_id else False,
    #         'gender': self.partner_id.gender,
    #         'company_id': self.env.company.id,
    #         'state_id': self.partner_id.state_id.id,
    #         'source_id': self.crm_id.source_id.id if self.crm_id else self.source_id.id,
    #         'campaign_id': self.crm_id.campaign_id.id if self.crm_id else False,
    #         'medium_id': self.crm_id.medium_id.id if self.crm_id else False,
    #         'customer_come': 'no',
    #         'user_id': self.env.user.id,
    #         'birth_date': self.partner_id.birth_date,
    #         'year_of_birth': self.partner_id.year_of_birth,
    #         'country_id': self.partner_id.country_id.id,
    #         'facebook_acc': self.crm_id.facebook_acc if self.crm_id else False,
    #         'price_list_id': self.price_list_guarantee.id,
    #         'pass_port': self.partner_id.pass_port,
    #         'pass_port_date': self.partner_id.pass_port_date,
    #         'pass_port_issue_by': self.partner_id.pass_port_issue_by,
    #         'booking_date': self.date_guarantee,
    #         'type_data': 'old',
    #         'note': self.note,
    #         'category_source_id': self.crm_id.category_source_id.id if self.crm_id
    #         else self.source_id.category_id.id,
    #     })
    #
    #     if self.convert_service_guarantee_ids:
    #         for convert_service_id in self.convert_service_guarantee_ids:
    #             if convert_service_id.product_incurred:
    #                 value = {
    #                     'product_id': convert_service_id.product_incurred.id,
    #                     'quantity': 1,
    #                     'price_list_id': self.price_list.id,
    #                     'unit_price': self.env['product.pricelist.item'].search(
    #                         [('pricelist_id', '=', self.price_list.id),
    #                          ('product_id', '=', convert_service_id.product_incurred.id)]).fixed_price,
    #                     'crm_id': booking.id,
    #                     'company_id': self.env.company.id,
    #                     'source_extend_id': self.source_id.id,
    #                     'line_booking_date': self.date_guarantee,
    #                     'status_cus_come': 'no_come',
    #                 }
    #                 if convert_service_id.crm_line_guarantee:
    #                     value['initial_product_id'] = convert_service_id.crm_line_guarantee.product_id.id
    #                     value['type_guarantee'] = convert_service_id.type_guarantee
    #
    #                 if self.brand_id.type == 'hospital':
    #                     service_id = self.env['sh.medical.health.center.service'].search(
    #                         [('product_id', '=', convert_service_id.product_incurred.id)])
    #                     if service_id:
    #                         value['service_id'] = service_id.id
    #                 else:
    #                     course_id = self.env['op.course'].search(
    #                         [('product_id', '=', convert_service_id.product_incurred.id)])
    #                     if course_id:
    #                         value['course_id'] = course_id.id
    #                 self.env['crm.line'].create(value)
    #             else:
    #                 value = {
    #                     'product_id': convert_service_id.crm_line_guarantee.product_id.id,
    #                     'quantity': 1,
    #                     'price_list_id': self.price_list_guarantee.id,
    #                     'unit_price': self.env['product.pricelist.item'].search(
    #                         [('pricelist_id', '=', self.price_list_guarantee.id),
    #                          ('product_id', '=', convert_service_id.crm_line_guarantee.product_id.id)]).fixed_price,
    #                     'crm_id': booking.id,
    #                     'company_id': self.env.company.id,
    #                     'source_extend_id': self.source_id.id,
    #                     'line_booking_date': self.date_guarantee,
    #                     'status_cus_come': 'no_come',
    #                     'uom_price': convert_service_id.crm_line_guarantee.uom_price,
    #                     'initial_product_id': convert_service_id.crm_line_guarantee.product_id.id,
    #                     'type_guarantee': convert_service_id.type_guarantee
    #
    #                 }
    #                 if self.brand_id.type == 'hospital':
    #                     value['service_id'] = convert_service_id.crm_line_guarantee.service_id.id
    #                 else:
    #                     value['course_id'] = convert_service_id.crm_line_guarantee.course.id
    #                 self.env['crm.line'].create(value)
    #
    #     return {
    #         'name': 'Booking guarantee',
    #         'type': 'ir.actions.act_window',
    #         'view_type': 'form',
    #         'view_mode': 'form',
    #         'view_id': self.env.ref('crm_base.crm_lead_form_booking').id,
    #         'res_model': 'crm.lead',
    #         'res_id': booking.id,
    #     }
