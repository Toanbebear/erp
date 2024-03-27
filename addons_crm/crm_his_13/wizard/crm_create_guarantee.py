import datetime
from odoo.exceptions import ValidationError

from odoo import fields, api, models, _
from odoo.exceptions import ValidationError
import datetime


class InheritBookingGuarantee(models.TransientModel):
    _inherit = 'crm.create.guarantee'

    # service_incurred = fields.Boolean(string='Phát sinh dịch vụ')
    # product_ids = fields.Many2many('product.product', 'create_guarantee_product_ref', 'create_guarantee_ids',
    #                                'product_ids', string='Dịch vụ phát sinh')
    # price_list = fields.Many2one('product.pricelist', string='Bảng giá',
    #                              domain="[('brand_id','=',brand_id),('type','=','service')]")

    @api.onchange('brand_id', 'price_list')
    def onchange_brand_id(self):
        domain = []
        if self.brand_id.type == 'hospital':
            domain += [('type_product_crm', '=', 'service_crm')]
            if self.price_list:
                domain += [('id', 'in', self.price_list.item_ids.mapped('product_id').ids)]
        elif self.brand_id.type == 'academy':
            domain += [('type_product_crm', '=', 'course')]
            if self.price_list:
                domain += [('id', 'in', self.price_list.item_ids.mapped('product_id').ids)]
        product_ids = self.env['product.product'].search(domain)
        return {'domain': {'product_ids': [('id', 'in', product_ids.ids)]}}

    def confirm(self):
        booking = self.env['crm.lead'].create({
            'name': '/',
            # 'code_booking': self.code_booking,
            'type_crm_id': self.env.ref('crm_base.type_oppor_guarantee').id,
            'type': 'opportunity',
            'contact_name': self.partner_id.name,
            'partner_id': self.partner_id.id,
            'stage_id': self.env.ref('crm_base.crm_stage_not_confirm').id,
            'phone': self.partner_id.phone,
            'mobile': self.partner_id.mobile,
            'street': self.partner_id.street,
            'overseas_vietnamese': self.partner_id.overseas_vietnamese,
            'district_id': self.partner_id.district_id.id,
            'email_from': self.partner_id.email,
            'lead_id': self.crm_id.id if self.crm_id else False,
            'online_counseling': self.crm_id.online_counseling if self.crm_id else False,
            'shuttle_bus': self.crm_id.shuttle_bus if self.crm_id else False,
            'work_online': self.crm_id.work_online if self.crm_id else False,
            'gender': self.partner_id.gender,
            'company_id': self.env.company.id,
            'state_id': self.partner_id.state_id.id,
            'source_id': self.crm_id.source_id.id,
            'original_source_id': self.partner_id.source_id.id if self.partner_id else self.crm_id.original_source_id.id,
            'campaign_id': self.crm_id.campaign_id.id if self.crm_id else False,
            'medium_id': self.crm_id.medium_id.id if self.crm_id else False,
            'customer_come': 'no',
            'user_id': self.env.user.id,
            'birth_date': self.partner_id.birth_date,
            'year_of_birth': self.partner_id.year_of_birth,
            'country_id': self.partner_id.country_id.id if self.partner_id.country_id.id else self.crm_id.country_id.id,
            'facebook_acc': self.crm_id.facebook_acc if self.crm_id else False,
            'price_list_id': self.price_list_guarantee.id,
            'pass_port': self.partner_id.pass_port,
            'pass_port_date': self.partner_id.pass_port_date,
            'pass_port_issue_by': self.partner_id.pass_port_issue_by,
            'booking_date': self.date_guarantee,
            'type_data': 'old',
            'note': self.note,
            'category_source_id': self.crm_id.source_id.category_id.id,
            # 'category_source_id': self.source_id.category_id.id if self.source_id else self.crm_id.source_id.category_id.id,
        })
        if self.convert_service_guarantee_ids:
            for convert_service_id in self.convert_service_guarantee_ids:
                if convert_service_id.product_incurred:
                    value = {
                        'product_id': convert_service_id.product_incurred.id,
                        'quantity': 1,
                        'price_list_id': self.price_list.id,
                        'unit_price': self.env['product.pricelist.item'].search(
                            [('pricelist_id', '=', self.price_list.id),
                             ('product_id', '=', convert_service_id.product_incurred.id)]).fixed_price,
                        'crm_id': booking.id,
                        'company_id': self.env.company.id,
                        'source_extend_id': self.source_id.id if self.source_id else booking.source_id.id,
                        'line_booking_date': self.date_guarantee,
                        'status_cus_come': 'no_come',
                        'consultants_1': self.env.user.id,
                    }
                    if convert_service_id.crm_line_guarantee:
                        value['initial_product_id'] = convert_service_id.crm_line_guarantee.product_id.id
                        value['type_guarantee'] = convert_service_id.type_guarantee

                    if self.brand_id.type == 'hospital':
                        service_id = self.env['sh.medical.health.center.service'].search(
                            [('product_id', '=', convert_service_id.product_incurred.id)])
                        if service_id:
                            value['service_id'] = service_id.id
                    else:
                        course_id = self.env['op.course'].search(
                            [('product_id', '=', convert_service_id.product_incurred.id)])
                        if course_id:
                            value['course_id'] = course_id.id
                    self.env['crm.line'].create(value)
                elif convert_service_id.crm_line_guarantee:
                    value = {
                        'product_id': convert_service_id.crm_line_guarantee.product_id.id,
                        'quantity': 1,
                        'price_list_id': self.price_list_guarantee.id,
                        'unit_price': self.env['product.pricelist.item'].search(
                            [('pricelist_id', '=', self.price_list_guarantee.id),
                             ('product_id', '=', convert_service_id.crm_line_guarantee.product_id.id)]).fixed_price,
                        'crm_id': booking.id,
                        'company_id': self.env.company.id,
                        'source_extend_id': self.source_id.id if self.source_id else booking.source_id.id,
                        'line_booking_date': self.date_guarantee,
                        'status_cus_come': 'no_come',
                        'uom_price': convert_service_id.crm_line_guarantee.uom_price,
                        'initial_product_id': convert_service_id.crm_line_guarantee.product_id.id,
                        'type_guarantee': convert_service_id.type_guarantee,
                        'consultants_1': self.env.user.id,
                    }
                    if self.brand_id.type == 'hospital':
                        value['service_id'] = convert_service_id.crm_line_guarantee.service_id.id
                    else:
                        value['course_id'] = convert_service_id.crm_line_guarantee.course.id
                    self.env['crm.line'].create(value)

        return self.return_booking_new(booking)

    def return_booking_new(self, booking):
        return {
            'name': 'Booking guarantee',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('crm_base.crm_lead_form_booking').id,
            'res_model': 'crm.lead',
            'res_id': booking.id,
        }


class AddServiceGuaranteeLine(models.TransientModel):
    _name = 'add.service.guarantee.line'
    _description = 'Add service guaranteee line'

    def _get_product_incurred_domain(self):
        pricelist_incurred = self.env['product.pricelist'].search(
            [('type', '=', 'service'), ('brand_id', '=', self.env.context.get('default_brand_id'))])
        product_id = self.env['product.pricelist.item'].search([('pricelist_id', 'in', pricelist_incurred.ids)]).mapped(
            'product_id')
        return [('id', 'in', product_id.ids)]

    add_service_guarantee_id = fields.Many2one('add.service.guarantee')
    TYPE_GUARANTEE = [('1', 'Một phần trước 01/06/2020'), ('2', 'Một phần trước 01/10/2020'),
                      ('3', 'Một phần sau 01/06/2020'), ('4', 'Một phần sau 01/10/2020'),
                      ('5', 'Toàn phần trước 01/06/2020'), ('6', 'Toàn phần trước 01/10/2020'),
                      ('7', 'Toàn phần sau 01/06/2020'), ('8', 'Toàn phần sau 01/10/2020'), ('9', 'Bảo hành không do lỗi chuyên môn'), ('10', 'Bảo hành chung (TH Paris)')]
    type_guarantee = fields.Selection(TYPE_GUARANTEE,
                                      help='Trường này dành cho Booking bảo hành', string='Loại bảo hành')
    crm_line_guarantee = fields.Many2one('crm.line', string='Dịch vụ bảo hành')
    product_incurred = fields.Many2one('product.product', string='Dịch vụ phát sinh',
                                       domain=_get_product_incurred_domain)

    @api.onchange('add_service_guarantee_id')
    def get_domain_line_guarantee(self):
        if self.add_service_guarantee_id:
            return {'domain': {
                'crm_line_guarantee': [('id', 'in', self.add_service_guarantee_id.service_guarantee_line.ids)]}}


class AddServiceGuarantee(models.TransientModel):
    _name = 'add.service.guarantee'
    _description = 'Add service guarantee'

    def domain_booking_guarantee(self):
        partner = self.env.context.get('default_partner')
        booking = self.env.context.get('default_crm_id')
        booking_ids = self.env['crm.lead'].sudo().search([('type', '=', 'opportunity'), ('partner_id', '=', partner), ('id', '!=', booking),
                                                          ('stage_id', 'not in', [self.env.ref('crm_base.crm_stage_cancel').id, self.env.ref('crm_base.crm_stage_out_sold').id])])
        return [('id', 'in', booking_ids.ids)]

    partner = fields.Many2one('res.partner', string='Khách hàng')
    crm_id = fields.Many2one('crm.lead', string='Booking hiện tại')
    brand_id = fields.Many2one('res.brand', string='Thương hiệu')
    # booking_ids = fields.Many2many('crm.lead',
    #                                domain="[('type', '=', 'opportunity'),"
    #                                       " ('partner_id', '=', partner),"
    #                                       " ('id', '!=', crm_id),"
    #                                       " ('stage_id', 'not in', [self.env.ref('crm_base.crm_stage_cancel').id, self.env.ref('crm_base.crm_stage_out_sold').id])]",
    #                                string='Booking chứa dịch vụ muốn bảo hành')
    booking_ids = fields.Many2many('crm.lead',
                                   domain=domain_booking_guarantee,
                                   string='Booking chứa dịch vụ muốn bảo hành')
    service_guarantee_line = fields.Many2many('crm.line',
                                              string='Dịch vụ', compute='_get_service_guarantee_line')
    add_service_line_guarantee = fields.One2many('add.service.guarantee.line', 'add_service_guarantee_id')
    pricelist_incurred = fields.Many2one('product.pricelist', string='Bảng giá cho dịch vụ phát sinh',
                                         domain="[('brand_id', '=', brand_id), ('type', '=', 'service')]")

    @api.depends('booking_ids')
    def _get_service_guarantee_line(self):
        for record in self:
            record.service_guarantee_line = False
            line_guarantee = self.env['crm.line'].search(
                [('stage', '=', 'done'), ('crm_id', 'in', record.booking_ids.ids)])
            record.service_guarantee_line = [(6, 0, line_guarantee.ids)]

    def action_add_service_guarantee(self):
        if self.add_service_line_guarantee:
            for service_line in self.add_service_line_guarantee:
                if service_line.product_incurred and self.pricelist_incurred:
                    value = {
                        'product_id': service_line.product_incurred.id,
                        'quantity': 1,
                        'price_list_id': self.pricelist_incurred.id,
                        'unit_price': self.env['product.pricelist.item'].search(
                            [('pricelist_id', '=', self.pricelist_incurred.id),
                             ('product_id', '=', service_line.product_incurred.id)]).fixed_price,
                        'crm_id': self.crm_id.id,
                        'company_id': self.crm_id.company_id.id,
                        'source_extend_id': self.crm_id.source_id.id,
                        'line_booking_date': datetime.datetime.now(),
                        'status_cus_come': 'no_come',
                        'consultants_1': self.env.user.id,
                    }
                    if service_line.crm_line_guarantee:
                        value['initial_product_id'] = service_line.crm_line_guarantee.product_id.id
                        value['type_guarantee'] = service_line.type_guarantee

                    if self.brand_id.type == 'hospital':
                        service_id = self.env['sh.medical.health.center.service'].search(
                            [('product_id', '=', service_line.product_incurred.id)])
                        if service_id:
                            value['service_id'] = service_id.id
                    self.env['crm.line'].create(value)
                elif service_line.product_incurred and not self.pricelist_incurred:
                    raise ValidationError('Bạn chưa chọn bảng giá')
                elif service_line.crm_line_guarantee:
                    value = {
                        'product_id': service_line.crm_line_guarantee.product_id.id,
                        'quantity': 1,
                        'price_list_id': self.crm_id.price_list_id.id,
                        'unit_price': self.env['product.pricelist.item'].search(
                            [('pricelist_id', '=', self.crm_id.price_list_id.id),
                             ('product_id', '=', service_line.crm_line_guarantee.product_id.id)]).fixed_price,
                        'crm_id': self.crm_id.id,
                        'company_id': self.crm_id.company_id.id,
                        'source_extend_id': self.crm_id.source_id.id,
                        'line_booking_date': datetime.datetime.now(),
                        'status_cus_come': 'no_come',
                        'uom_price': service_line.crm_line_guarantee.uom_price,
                        'initial_product_id': service_line.crm_line_guarantee.product_id.id,
                        'type_guarantee': service_line.type_guarantee,
                        'consultants_1': self.env.user.id,
                    }
                    if self.brand_id.type == 'hospital':
                        value['service_id'] = service_line.crm_line_guarantee.service_id.id
                    self.env['crm.line'].create(value)
        else:
            raise ValidationError('Chưa có giá trị tại bảng quy đổi dịch vụ bảo hành')
