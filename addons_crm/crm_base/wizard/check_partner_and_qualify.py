from datetime import datetime, date, timedelta
from odoo import fields, api, models, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
import pytz

class CheckPartnerAndQualify(models.TransientModel):
    _name = 'check.partner.qualify'
    _description = 'Check Partner AndQualify'

    name = fields.Char('Contact name')
    phone = fields.Char('Phone')
    booking_date = fields.Datetime('Booking date')
    lead_id = fields.Many2one('crm.lead', string='Lead')
    company_id = fields.Many2one('res.company', string='Company')
    type = fields.Selection([('lead', 'Lead'), ('opportunity', 'Opportunity')], string='Type record crm')
    partner_id = fields.Many2one('res.partner', string='Partner')
    # code_booking = fields.Char('Mã booking tương ứng')

    # @api.constrains('booking_date')
    # def constrain_booking_date(self):
    #     for record in self:
    #         if record.booking_date.date() < date.today():
    #             raise ValidationError('Ngày hẹn lịch không thể nhỏ hơn ngày hiện tại!!!')
    # @api.onchange('booking_date')
    # def validate_booking_date(self):
    #     """
    #     Trừ User có quyền thiết lập hệ thống, tất cả các user còn lại chỉ dc đặt lịch có BK date lớn hơn hoặc bằng ngày giờ hiện tại
    #     """
    #     if not self.env.user.has_group('base.group_system'):
    #         if self.booking_date and self.booking_date.date() < date.today():
    #             raise ValidationError('Ngày hẹn lịch không thể nhỏ hơn ngày hiện tại')


    def qualify(self):
        self.lead_id.stage_id = self.env.ref('crm_base.crm_stage_booking').id
        self.lead_id.check_booking = True
        if self.partner_id:
            customer = self.partner_id.id
        else:
            # partner = self.env['res.partner'].search(['|', ('phone', '=', self.phone), ('mobile', '=', self.phone)])
            partner = self.env['res.partner'].search([('phone', '=', self.phone)])
            if partner:
                self.lead_id.partner_id = partner.id
                customer = partner.id
            else:
                prt = self.env['res.partner'].create({
                    'name': self.name,
                    'code_customer': self.env['ir.sequence'].next_by_code('res.partner'),
                    'aliases': self.lead_id.aliases,
                    'customer_classification': self.lead_id.customer_classification,
                    'overseas_vietnamese': self.lead_id.overseas_vietnamese,
                    'phone': self.phone,
                    'country_id': self.lead_id.country_id.id,
                    'state_id': self.lead_id.state_id.id,
                    'street': self.lead_id.street,
                    'district_id': self.lead_id.district_id.id,
                    'birth_date': self.lead_id.birth_date,
                    'career': self.lead_id.career,
                    'pass_port': self.lead_id.pass_port,
                    'pass_port_date': self.lead_id.pass_port_date,
                    'pass_port_issue_by': self.lead_id.pass_port_issue_by,
                    'pass_port_address': self.lead_id.pass_port_address,
                    'gender': self.lead_id.gender,
                    'year_of_birth': self.lead_id.year_of_birth,
                    'company_id': False,
                    'source_id': self.lead_id.original_source_id.id,
                    'email': self.lead_id.email_from,
                    'acc_facebook': self.lead_id.facebook_acc,
                    'acc_zalo': self.lead_id.zalo_acc,
                })
                customer = prt.id
                self.lead_id.partner_id = customer
        booking = self.env['crm.lead'].create({
            'name': '/',
            'type_crm_id': self.env.ref('crm_base.type_oppor_new').id,
            'type': 'opportunity',
            'contact_name': self.lead_id.contact_name,
            'partner_id': customer,
            'customer_classification': self.lead_id.customer_classification,
            'aliases': self.lead_id.aliases,
            'stage_id': self.env.ref('crm_base.crm_stage_not_confirm').id,
            'phone': self.lead_id.phone,
            'mobile': self.lead_id.mobile,
            'street': self.lead_id.street,
            'email_from': self.lead_id.email_from,
            'career': self.lead_id.career,
            'lead_id': self.lead_id.id,
            'prg_ids': [(6, 0, self.lead_id.prg_ids.ids)],
            'product_category_ids': [(6, 0, self.lead_id.product_category_ids.ids)],
            'gender': self.lead_id.gender,
            'company_id': self.lead_id.company_id.id,
            'state_id': self.lead_id.state_id.id,
            'district_id': self.lead_id.district_id.id,
            'source_id': self.lead_id.source_id.id,
            'original_source_id': self.lead_id.partner_id.source_id.id,
            'campaign_id': self.lead_id.campaign_id.id,
            'medium_id': self.lead_id.medium_id.id,
            'customer_come': 'no',
            'category_source_id': self.lead_id.category_source_id.id,
            'user_id': self.env.user.id,
            'birth_date': self.lead_id.birth_date,
            'year_of_birth': self.lead_id.year_of_birth,
            'country_id': self.lead_id.country_id.id,
            'facebook_acc': self.lead_id.facebook_acc,
            'zalo_acc': self.lead_id.zalo_acc,
            'send_info_facebook': self.lead_id.send_info_facebook,
            'send_info_zalo': self.lead_id.send_info_zalo,
            'price_list_id': self.lead_id.price_list_id.id,
            'product_ctg_ids': [(6, 0, self.lead_id.product_ctg_ids.ids)],
            'description': self.lead_id.description,
            'special_note': self.lead_id.special_note,
            'pass_port': self.lead_id.pass_port,
            'pass_port_date': self.lead_id.pass_port_date,
            'pass_port_issue_by': self.lead_id.pass_port_issue_by,
            'pass_port_address': self.lead_id.pass_port_address,
            'booking_date': self.booking_date,
            'type_data': self.lead_id.type_data,
            'work_online': self.lead_id.work_online,
            # 'code_booking': self.code_booking,
            'brand_id': self.lead_id.brand_id.id,
            'overseas_vietnamese': self.lead_id.overseas_vietnamese,
            'gclid': self.lead_id.gclid,
            # 'fam_ids': [(6, 0, self.lead_id.fam_ids.ids)],
        })
        # if (booking.create_on + datetime.timedelta(days=30)) < booking.booking_date:
        #     raise ValidationError('Ngày hẹn lịch chỉ được phép trong vòng 30 ngày kể từ ngày tạo Booking')

        if self.lead_id.crm_line_ids:
            self.create_line_booking(self.lead_id.crm_line_ids, booking)


        if self.lead_id.fam_ids:
            for fam in self.lead_id.fam_ids:
                fam_id = self.env['crm.family.info'].create({
                    'crm_id': booking.id,
                    'member_name': fam.member_name,
                    'type_relation_id': fam.type_relation_id.id,
                    'phone': fam.phone,
                })
                fam.sudo().unlink()
        # Tạo phone call sms xác nhận lịch hẹn
        booking.create_phone_call()
        # return {
        #     'name': 'Booking',
        #     'type': 'ir.actions.act_window',
        #     'view_type': 'form',
        #     'view_mode': 'form',
        #     'view_id': self.env.ref('crm_base.crm_lead_form_booking').id,
        #     'res_model': 'crm.lead',
        #     'res_id': booking.id,
        # }
        return self.return_booking_new(booking)

    def return_booking_new(self, booking):
        return {
            'name': 'Booking',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('crm_base.crm_lead_form_booking').id,
            'res_model': 'crm.lead',
            'res_id': booking.id,
        }

    def create_line_booking(self, list_line, booking):
        for rec in list_line:
            line = self.env['crm.line'].create({
                'name': rec.name,
                'quantity': rec.quantity,
                'is_treatment': rec.is_treatment,
                'number_used': rec.number_used,
                'unit_price': rec.unit_price,
                'discount_percent': rec.discount_percent,
                'type': rec.type,
                'discount_cash': rec.discount_cash,
                'sale_to': rec.sale_to,
                'price_list_id': rec.price_list_id.id,
                'total_before_discount': rec.total_before_discount,
                'crm_id': booking.id,
                'company_id': rec.company_id.id,
                'product_id': rec.product_id.id,
                'teeth_ids': [(6, 0, rec.teeth_ids.ids)],
                'source_extend_id': rec.source_extend_id.id,
                'line_booking_date': booking.booking_date,
                'status_cus_come': 'no_come',
                'uom_price': rec.uom_price,
                'prg_ids': [(6, 0, rec.prg_ids.ids)],
                'consultants_1': rec.consultants_1.id,
                'consultants_2': rec.consultants_2.id,
                'consulting_role_1': rec.consulting_role_1,
                'consulting_role_2': rec.consulting_role_2,
                'crm_information_ids': [(6, 0, rec.crm_information_ids.ids)]
            })
            crm_line_discount_history = self.env['crm.line.discount.history'].search(
                [('booking_id', '=', self.lead_id.id), ('crm_line', '=', rec.id)])
            for record in crm_line_discount_history:
                self.env['crm.line.discount.history'].create({
                    'booking_id': booking.id,
                    'discount_program': record.discount_program.id,
                    'type': record.type,
                    'discount': record.discount,
                    'crm_line': line.id,
                    'index': record.index,
                    'type_discount': record.type_discount
                })
