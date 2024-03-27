import datetime
from odoo.exceptions import ValidationError

from odoo import fields, api, models, _
from odoo.exceptions import ValidationError
import datetime


class InheritCRMConvertServiceGuarantee(models.TransientModel):
    _inherit = 'crm.convert.service.guarantee'

    product_incurred = fields.Many2one(string='Dịch vụ thực hiện')
    reason_id = fields.Many2one('crm.guarantee.reason', string='Lí do bảo hành')
    TYPE_GUARANTEE = [('not_totality', 'Một phần'), ('totality', 'Toàn phần')]
    type_guarantee_2 = fields.Selection(TYPE_GUARANTEE,
                                      help='Trường này dành cho Booking bảo hành', string='Loại bảo hành')
    checked = fields.Boolean('T')

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
        else:
            return {
                'domain': {'product_incurred': [('id', '=', 0)]}}
    @api.onchange('type_guarantee_2')
    def onchange_type_guarantee(self):
        domain = []
        if self.type_guarantee_2:
            if self.type_guarantee_2 == 'not_totality':
                domain += [('not_totality', '=', True)]
            elif self.type_guarantee_2 == 'totality':
                domain += [('totality', '=', True)]
            reason_id = self.env['crm.guarantee.reason'].search(domain)
            return {'domain': {'reason_id': [('id', 'in', reason_id.ids)]}}
        else:
            return {'domain': {'reason_id': [('id', 'in', [])]}}

class InheritBookingGuarantee(models.TransientModel):
    _inherit = 'crm.create.guarantee'

    service_new_ids = fields.Many2many('sh.medical.health.center.service', string='Dịch vụ mới')
    note = fields.Char('Ghi chú bảo hành')
    price_list = fields.Many2one(string='Bảng giá niêm yết')
    @api.onchange('price_list')
    def onchange_price_list(self):
        domain = []
        if self.price_list:
            domain += [('id', 'in', self.price_list.item_ids.mapped('product_id').ids)]
            return {
                'domain': {'service_new_ids': [('product_id', 'in', self.env['product.product'].sudo().search(domain).ids)]}}

    def confirm_create(self):
        booking = self.env['crm.lead'].create({
            'name': '/',
            'code_booking': self.code_booking,
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
                crm_information_ids = []
                if booking.brand_id.id == 3:
                    crm_information_id = self.env['crm.information.consultant'].sudo().create(
                        {'role': 'recept', 'user_id': self.env.user.id})
                    crm_information_ids.append(crm_information_id.id)
                if convert_service_id.product_incurred:
                    value = {
                        'product_id': convert_service_id.product_incurred.id,
                        'quantity': 1,
                        'price_list_id': self.price_list.id,
                        'unit_price': self.env['product.pricelist.item'].search([('pricelist_id', '=', self.price_list.id),('product_id', '=', convert_service_id.product_incurred.id)]).fixed_price,
                        'crm_id': booking.id,
                        'company_id': self.env.company.id,
                        'source_extend_id': self.source_id.id if self.source_id else booking.source_id.id,
                        'line_booking_date': self.date_guarantee,
                        'status_cus_come': 'no_come',
                        'initial_product_id': convert_service_id.crm_line_guarantee.product_id.id,
                        'reason_guarantee_id': convert_service_id.reason_id.id,
                        'type_guarantee_2': convert_service_id.type_guarantee_2,
                        'consultants_1': self.env.user.id if booking.company_id.brand_id != 3 else None,
                        'crm_information_ids': [(6, 0, crm_information_ids)]
                    }
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
                else:
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
                        'reason_guarantee_id': convert_service_id.reason_id.id,
                        'type_guarantee_2': convert_service_id.type_guarantee_2,
                        'consultants_1': self.env.user.id if booking.company_id.brand_id != 3 else None,
                        'crm_information_ids': [(6, 0, crm_information_ids)]
                    }
                    if self.brand_id.type == 'hospital':
                        value['service_id'] = convert_service_id.crm_line_guarantee.service_id.id
                    else:
                        value['course_id'] = convert_service_id.crm_line_guarantee.course.id
                    self.env['crm.line'].create(value)
        if self.service_new_ids:
            for service_id in self.service_new_ids:
                crm_information_ids = []
                if booking.brand_id.id == 3:
                    crm_information_id = self.env['crm.information.consultant'].sudo().create(
                        {'role': 'recept', 'user_id': self.env.user.id})
                    crm_information_ids.append(crm_information_id.id)
                value = {
                    'crm_id': booking.id,
                    'product_id': service_id.product_id.id,
                    'quantity': 1,
                    'service_id': service_id.id,
                    'company_id': booking.company_id.id,
                    'price_list_id': self.price_list.id,
                    'unit_price': self.env['product.pricelist.item'].search(
                        [('pricelist_id', '=', self.price_list.id),
                         ('product_id', '=', service_id.product_id.id)]).fixed_price,
                    'source_extend_id': self.source_id.id if self.source_id else booking.source_id.id,
                    'line_booking_date': self.date_guarantee,
                    'status_cus_come': 'no_come',
                    'consultants_1': self.env.user.id if booking.company_id.brand_id == 1 else None,
                    'crm_information_ids': [(6, 0, crm_information_ids)]
                }
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