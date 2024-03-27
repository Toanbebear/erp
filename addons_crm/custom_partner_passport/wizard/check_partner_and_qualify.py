import datetime
from datetime import date
from odoo import fields, api, models, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta


class CheckPartnerUpdateMethodQualify(models.TransientModel):
    _inherit = 'check.partner.qualify'
    _description = 'Update method qualify'

    # def qualify(self):
    #     self.lead_id.stage_id = self.env.ref('crm_base.crm_stage_booking').id
    #     self.lead_id.check_booking = True
    #     if self.partner_id:
    #         customer = self.partner_id.id
    #     else:
    #         partner = self.env['res.partner'].search([('phone', '=', self.phone)])
    #         if partner:
    #             self.lead_id.partner_id = partner.id
    #             customer = partner.id
    #         else:
    #             prt = self.env['res.partner'].create({
    #                 'name': self.name,
    #                 'customer_classification': self.lead_id.customer_classification,
    #                 'overseas_vietnamese': self.lead_id.overseas_vietnamese,
    #                 'phone': self.phone,
    #                 'country_id': self.lead_id.country_id.id,
    #                 'state_id': self.lead_id.state_id.id,
    #                 'street': self.lead_id.street,
    #                 'district_id': self.lead_id.district_id.id,
    #                 'birth_date': self.lead_id.birth_date,
    #                 'pass_port': self.lead_id.pass_port,
    #                 'pass_port_date': self.lead_id.pass_port_date,
    #                 'pass_port_issue_by': self.lead_id.pass_port_issue_by,
    #                 'gender': self.lead_id.gender,
    #                 'year_of_birth': self.lead_id.year_of_birth,
    #                 'company_id': False,
    #                 'source_id': self.lead_id.source_id.id,
    #                 'email': self.lead_id.email_from,
    #                 'acc_facebook': self.lead_id.facebook_acc,
    #                 'acc_zalo': self.lead_id.zalo_acc,
    #             })
    #             customer = prt.id
    #             self.lead_id.partner_id = customer
    #
    #     booking = self.env['crm.lead'].create({
    #         'type_crm_id': self.env.ref('crm_base.type_oppor_new').id,
    #         'type': 'opportunity',
    #         'contact_name': self.lead_id.contact_name,
    #         'partner_id': customer,
    #         'customer_classification': self.lead_id.customer_classification,
    #         'stage_id': self.env.ref('crm_base.crm_stage_not_confirm').id,
    #         'phone': self.lead_id.phone,
    #         'mobile': self.lead_id.mobile,
    #         'street': self.lead_id.street,
    #         'email_from': self.lead_id.email_from,
    #         'lead_id': self.lead_id.id,
    #         'prg_ids': [(6, 0, self.lead_id.prg_ids.ids)],
    #         'gender': self.lead_id.gender,
    #         'company_id': self.lead_id.company_id.id,
    #         'state_id': self.lead_id.state_id.id,
    #         'district_id': self.lead_id.district_id.id,
    #         'source_id': self.lead_id.source_id.id,
    #         'campaign_id': self.lead_id.campaign_id.id,
    #         'medium_id': self.lead_id.medium_id.id,
    #         'customer_come': 'no',
    #         'category_source_id': self.lead_id.category_source_id.id,
    #         'user_id': self.env.user.id,
    #         'birth_date': self.lead_id.birth_date,
    #         'year_of_birth': self.lead_id.year_of_birth,
    #         'country_id': self.lead_id.country_id.id,
    #         'facebook_acc': self.lead_id.facebook_acc,
    #         'zalo_acc': self.lead_id.zalo_acc,
    #         'send_info_facebook': self.lead_id.send_info_facebook,
    #         'send_info_zalo': self.lead_id.send_info_zalo,
    #         'price_list_id': self.lead_id.price_list_id.id,
    #         'product_ctg_ids': [(6, 0, self.lead_id.product_ctg_ids.ids)],
    #         'description': self.lead_id.description,
    #         'special_note': self.lead_id.special_note,
    #         'pass_port': self.lead_id.pass_port,
    #         'pass_port_date': self.lead_id.pass_port_date,
    #         'pass_port_issue_by': self.lead_id.pass_port_issue_by,
    #         'booking_date': self.booking_date,
    #         'type_data': self.lead_id.type_data,
    #         'work_online': self.lead_id.work_online,
    #         # 'code_booking': self.code_booking,
    #         'brand_id': self.lead_id.brand_id.id,
    #         'overseas_vietnamese': self.lead_id.overseas_vietnamese,
    #         'gclid': self.lead_id.gclid,
    #         # 'fam_ids': [(6, 0, self.lead_id.fam_ids.ids)],
    #     })
    #     # if (booking.create_on + datetime.timedelta(days=30)) < booking.booking_date:
    #     #     raise ValidationError('Ngày hẹn lịch chỉ được phép trong vòng 30 ngày kể từ ngày tạo Booking')
    #
    #     if self.lead_id.crm_line_ids:
    #         for rec in self.lead_id.crm_line_ids:
    #             line = self.env['crm.line'].create({
    #                 'name': rec.name,
    #                 'quantity': rec.quantity,
    #                 'is_treatment': rec.is_treatment,
    #                 'number_used': rec.number_used,
    #                 'unit_price': rec.unit_price,
    #                 'discount_percent': rec.discount_percent,
    #                 'type': rec.type,
    #                 'discount_cash': rec.discount_cash,
    #                 'sale_to': rec.sale_to,
    #                 'price_list_id': rec.price_list_id.id,
    #                 'total_before_discount': rec.total_before_discount,
    #                 'crm_id': booking.id,
    #                 'company_id': rec.company_id.id,
    #                 'product_id': rec.product_id.id,
    #                 'source_extend_id': rec.source_extend_id.id,
    #                 'line_booking_date': booking.booking_date,
    #                 'status_cus_come': 'no_come',
    #                 'uom_price': rec.uom_price,
    #                 'prg_ids': [(6, 0, rec.prg_ids.ids)],
    #             })
    #             crm_line_discount_history = self.env['crm.line.discount.history'].search(
    #                 [('booking_id', '=', self.lead_id.id), ('crm_line', '=', rec.id)])
    #             for record in crm_line_discount_history:
    #                 self.env['crm.line.discount.history'].create({
    #                     'booking_id': booking.id,
    #                     'discount_program': record.discount_program.id,
    #                     'type': record.type,
    #                     'discount': record.discount,
    #                     'crm_line': line.id,
    #                     'index': record.index,
    #                     'type_discount': record.type_discount
    #                 })
    #
    #     if self.lead_id.fam_ids:
    #         for fam in self.lead_id.fam_ids:
    #             fam_id = self.env['crm.family.info'].create({
    #                 'crm_id': booking.id,
    #                 'member_name': fam.member_name,
    #                 'type_relation_id': fam.type_relation_id.id,
    #                 'phone': fam.phone,
    #             })
    #             fam.sudo().unlink()
    #
    #     self.create_phone_call(booking)
    #
    #     return {
    #         'name': 'Booking',
    #         'type': 'ir.actions.act_window',
    #         'view_type': 'form',
    #         'view_mode': 'form',
    #         'view_id': self.env.ref('crm_base.crm_lead_form_booking').id,
    #         'res_model': 'crm.lead',
    #         'res_id': booking.id,
    #     }
