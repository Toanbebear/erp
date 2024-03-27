from datetime import datetime, date
from calendar import monthrange, calendar
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class CrmLeadInherit(models.Model):
    _inherit = 'crm.lead'

    age = fields.Integer('Age', compute='_compute_age')
    walkin_count = fields.Integer('Số lượng phiếu khám', compute='_compute_walkin_count')
    calendar_event_count = fields.Integer('Số lượng lịch hẹn', compute='_compute_event_count')
    survey_count = fields.Integer('Số lượng khảo sát', compute='_compute_survey_count')
    type_lead_id = fields.Selection([('lead', 'Lead'), ('opportunity', 'Cơ hội')], related='lead_id.type')
    day_of_birth = fields.Integer('Ngày sinh')
    month_of_birth = fields.Integer('Tháng sinh')

    @api.model
    def create(self, vals):
        if 'birth_date' in vals and vals['birth_date']:
            if 'partner_id' in vals:
                partner = self.env['res.partner'].sudo().browse(int(vals['partner_id']))
                if partner:
                    partner.birth_date = vals['birth_date']
            if vals['birth_date']:
                if isinstance(vals['birth_date'], str):
                    list = vals['birth_date'].split('-')
                    if 'day_of_birth' not in vals:
                        vals['day_of_birth'] = list[2] if list[2] else ''
                    if 'month_of_birth' not in vals:
                        vals['month_of_birth'] = list[1] if list[1] else ''
                    if 'year_of_birth' not in vals:
                        vals['year_of_birth'] = list[0] if list[0] else ''
                else:
                    if 'day_of_birth' not in vals:
                        vals['day_of_birth'] = vals['birth_date'].day
                    if 'month_of_birth' not in vals:
                        vals['month_of_birth'] = vals['birth_date'].month
                    if 'year_of_birth' not in vals:
                        vals['year_of_birth'] = str(vals['birth_date'].year)
        return super(CrmLeadInherit, self).create(vals)

    @api.onchange('birth_date')
    def set_day_of_birth(self):
        if self.birth_date:
            self.day_of_birth = self.birth_date.day
            self.month_of_birth = self.birth_date.month

    @api.constrains('day_of_birth', 'month_of_birth', 'year_of_birth')
    def constrain_birthday(self):
        for val in self:
            if val.day_of_birth and val.day_of_birth not in range(1, 32):
                raise ValidationError('Ngày sinh chỉ có thể nằm trong khoảng từ 1 - 31')
            if val.month_of_birth and val.month_of_birth not in range(1, 13):
                raise ValidationError('Tháng sinh chỉ có thể nằm trong khoảng từ 1 - 12')
            year_now = datetime.now().year
            if int(val.year_of_birth) and int(val.year_of_birth) not in range(1900, year_now):
                raise ValidationError('Năm sinh chỉ có thể chọn trong khoảng từ 1900 - %s' % year_now)
            if val.day_of_birth and val.month_of_birth and val.year_of_birth and val.day_of_birth > \
                    monthrange(int(val.year_of_birth), val.month_of_birth)[1]:
                raise ValidationError('Tháng %s chỉ có %s ngày, ' % (
                    val.month_of_birth, monthrange(int(val.year_of_birth), val.month_of_birth)[1]))

    @api.onchange('day_of_birth', 'month_of_birth', 'year_of_birth')
    def onchange_birthday(self):
        if self.day_of_birth and self.month_of_birth and self.year_of_birth:
            self.birth_date = date(int(self.year_of_birth), self.month_of_birth, self.day_of_birth)

    @api.onchange('phone')
    def onchange_phone_bd(self):
        if self.phone:
            partner = self.env['res.partner'].search([('phone', '=', self.phone)])
            if partner and partner.birth_date:
                self.day_of_birth = partner.birth_date.day
                self.month_of_birth = partner.birth_date.month

    def _compute_walkin_count(self):
        for record in self:
            record.walkin_count = self.env['sh.medical.appointment.register.walkin'].search_count(
                [('booking_id', '=', record.id)])

    def _compute_event_count(self):
        for record in self:
            record.calendar_event_count = self.env['calendar.event'].search_count(
                [('opportunity_id', '=', record.id)])

    def _compute_survey_count(self):
        for record in self:
            record.survey_count = self.env['survey.user_input'].search_count(
                [('crm_id', '=', record.id)])

    def action_walkin_ids(self):
        return {
            'type': 'ir.actions.act_window',
            'name': ('Lịch sử khám'),
            'res_model': 'sh.medical.appointment.register.walkin',
            'view_mode': 'tree,form',
            'domain': [('booking_id', '=', self.id)],
        }

    def action_event_ids(self):
        return {
            'type': 'ir.actions.act_window',
            'name': ('Lịch hẹn'),
            'res_model': 'calendar.event',
            'view_mode': 'tree,form',
            'domain': [('opportunity_id', '=', self.id)],
        }

    def action_survey_ids(self):
        return {
            'type': 'ir.actions.act_window',
            'name': ('Khảo sát'),
            'res_model': 'survey.user_input',
            'view_mode': 'tree,form',
            'domain': [('crm_id', '=', self.id)],
        }

    def create_phone_call_info(self):
        pc = self.env['crm.phone.call'].create({
            'name': 'Hỏi thêm thông tin - %s' % self.name,
            'subject': 'Hỏi thêm thông tin',
            'partner_id': self.partner_id.id,
            'phone': self.partner_id.phone,
            'direction': 'in',
            'company_id': self.company_id.id,
            'crm_id': self.id,
            'country_id': self.country_id.id,
            'street': self.street,
            'type_crm_id': self.env.ref('crm_base.type_phone_call_customer_ask_info').id,
            # 'booking_date': self.booking_date,
            'call_date': datetime.now(),
        })

        return {
            'name': 'Phone call',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': pc.id,
            'view_id': self.env.ref('crm_base.view_form_phone_call').id,
            'res_model': 'crm.phone.call',
            'context': {},
            'target': 'new',
        }

    @api.depends('partner_id', 'birth_date', 'year_of_birth')
    def _compute_age(self):
        for rec in self:
            if rec.year_of_birth:
                rec.age = datetime.now().year - int(rec.year_of_birth)
            elif rec.partner_id and rec.partner_id.age:
                rec.age = rec.partner_id.age
            else:
                rec.age = 0

    def request_debt_review(self):
        return {
            'name': 'Yêu cầu duyệt nợ',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': self.env.ref('crm_base.debt_view_form').id,
            'res_model': 'crm.debt.review',
            'target': 'current',
            'context': {
                'form_view_initial_mode': 'edit',
                'default_company_id': self.company_id.id,
                'default_booking_id': self.id,
                'default_partner_id': self.partner_id.id,
            },
            'target': 'new',
        }

    def open_case(self):
        self.ensure_one()
        return {
            'name': 'TẠO KHIẾU NẠI',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('crm_base.crm_case_view_form').id,
            'res_model': 'crm.case',
            'context': {
                'default_brand_id': self.brand_id.id,
                'default_company_id': self.company_id.id,
                'default_booking_id': self.id,
                'default_partner_id': self.partner_id.id,
                'default_phone': self.partner_id.phone,
                'default_country_id': self.country_id.id,
                'default_state_id': self.state_id.id,
                'default_street': self.street,
                'default_account_facebook': self.facebook_acc,
            },
        }

    def button_show_qr(self):
        return {
            'name': 'Hiển thị QR',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('crm_kangnam_extend.show_qr_booking_form_view').id,
            'res_model': 'show.qr.booking',
            'context': {'default_qr_code_id': self.qr_code_id,
                        'default_crm_name': self.code_customer,
                        'default_partner_name': self.name,
                        'default_hotline_brand': self.hotline_brand},
            'target': 'new',
        }

    def clone_lead_2(self):
        return {
            'name': 'LEAD',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('crm_kangnam_extend.crm_kangnam_lead_view_form_extend').id,
            'res_model': 'crm.lead',
            'context': {
                'default_phone': self.phone,
                'default_name': self.name,
                'default_contact_name': self.contact_name,
                'default_code_customer': self.code_customer,
                'default_customer_classification': self.customer_classification,
                'default_partner_id': self.partner_id.id,
                'default_aliases': self.aliases,
                'default_type_crm_id': self.type_crm_id.id,
                'default_type': self.type,
                'default_type_data': 'old',
                'default_gender': self.gender,
                'default_birth_date': self.birth_date,
                'default_year_of_birth': self.year_of_birth,
                'default_mobile': self.mobile,
                'default_career': self.career,
                'default_pass_port': self.pass_port,
                'default_pass_port_date': self.pass_port_date,
                'default_pass_port_issue_by': self.pass_port_issue_by,
                'default_pass_port_address': self.pass_port_address,
                'default_country_id': self.country_id.id,
                'default_state_id': self.state_id.id,
                'default_district_id': self.district_id.id,
                'default_street': self.street,
                'default_email_from': self.email_from,
                'default_facebook_acc': self.facebook_acc,
                'default_zalo_acc': self.zalo_acc,
                'default_stage_id': self.env.ref('crm_base.crm_stage_no_process').id,
                'default_company_id': self.company_id.id,
                'default_description': 'COPY',
                'default_special_note': self.special_note,
                'default_price_list_id': self.price_list_id.id if self.price_list_id.active else False,
                'default_currency_id': self.currency_id.id,
                'default_work_online': self.work_online,
                'default_send_info_facebook': self.send_info_facebook,
                'default_online_counseling': self.online_counseling,
                'default_shuttle_bus': self.shuttle_bus,
                'default_is_clone': True,
                'default_day_of_birth': self.day_of_birth,
                'default_month_of_birth': self.month_of_birth,
            },
        }

    def open_booking_new(self):
        return {
            'name': 'Xem BK chi tiết',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': self.id,
            'view_id': self.env.ref('crm_kangnam_extend.crm_kangnam_crm_lead_view_form_extend').id,
            'res_model': 'crm.lead',
            'context': {},
        }

    def open_lead(self):
        return {
            'name': 'Open Lead',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': self.id,
            'view_id': self.env.ref('crm_kangnam_extend.crm_kangnam_lead_view_form_extend').id,
            'res_model': 'crm.lead',
            'context': {},
        }

    def open_booking(self):
        return {
            'name': 'Open Booking',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': self.id,
            'view_id': self.env.ref('crm_kangnam_extend.crm_kangnam_crm_lead_view_form_extend').id,
            'res_model': 'crm.lead',
            'context': {},
        }

    def create_booking_re_exam_ehc(self):
        patient_id = False
        if self.sudo().crm_hh_ehc_medical_record_ids:
            patient_id = self.sudo().crm_hh_ehc_medical_record_ids[0].patient_id
            if not patient_id:
                patient_id = self.env['crm.hh.ehc.patient'].sudo().search([('partner_id', '=', self.partner_id.id)],
                                                                          limit=1)
        return {
            'name': 'Booking',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('crm_kangnam_extend.crm_kangnam_crm_lead_view_form_extend').id,
            'res_model': 'crm.lead',
            'context': {
                'default_phone': self.phone,
                'default_name': self.name,
                'default_contact_name': self.contact_name,
                'default_code_customer': self.code_customer,
                'default_customer_classification': self.customer_classification,
                'default_partner_id': self.partner_id.id,
                'default_aliases': self.aliases,
                'default_type_crm_id': self.env.ref('crm_ehc.type_oppor_re_exam_ehc').id,
                'default_type': self.type,
                'default_type_data': 'old',
                'default_type_data_partner': self.type_data_partner,
                'default_gender': self.gender,
                'default_birth_date': self.birth_date,
                'default_year_of_birth': self.year_of_birth,
                'default_mobile': self.mobile,
                'default_career': self.career,
                'default_pass_port': self.pass_port,
                'default_pass_port_date': self.pass_port_date,
                'default_pass_port_issue_by': self.pass_port_issue_by,
                'default_pass_port_address': self.pass_port_address,
                'default_country_id': self.country_id.id,
                'default_brand_id': self.brand_id.id,
                'default_state_id': self.state_id.id,
                'default_district_id': self.district_id.id,
                'default_street': self.street,
                'default_email_from': self.email_from,
                'default_facebook_acc': self.facebook_acc,
                'default_zalo_acc': self.zalo_acc,
                'default_stage_id': self.env.ref('crm_base.crm_stage_no_process').id,
                'default_company_id': self.company_id.id,
                'default_description': 'COPY',
                'default_special_note': self.special_note,
                'default_price_list_id': self.price_list_id.id,
                'default_currency_id': self.currency_id.id,
                'default_source_id': self.source_id.id,
                'default_collaborators_id': self.collaborators_id.id if self.collaborators_id else False,
                'default_campaign_id': self.campaign_id.id,
                'default_category_source_id': self.category_source_id.id,
                'default_work_online': self.work_online,
                'default_send_info_facebook': self.send_info_facebook,
                'default_online_counseling': self.online_counseling,
                'default_shuttle_bus': self.shuttle_bus,
                'default_root_booking_ehc': self.id,
                'default_customer_come': 'no',
                'default_lead_id': self.id,
                'default_booking_date': datetime.now(),
                'default_product_category_ids': [(6, 0, self.product_category_ids.ids)],
                'default_crm_hh_ehc_medical_record_ids': [(0, 0, {
                    'booking_id': self.id,
                    'patient_id': patient_id.id if patient_id else False,
                    'status': '0',
                })],
            },
        }

    class CrmAdviseLine(models.Model):
        _inherit = 'crm.advise.line'

        def open_advise_line(self):
            return {
                'name': 'Xem dịch vụ tiềm năng chi tiết',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_id': self.id,
                'view_id': self.env.ref('crm_advise.crm_advise_line_potential_form_view').id,
                'res_model': 'crm.advise.line',
                'context': {},
            }

    class CalendarEvent(models.Model):
        _inherit = 'calendar.event'

        def change_calender_evt(self, *args):
            return {
                'name': 'Đi đến Booking',
                'view_mode': 'form',
                'res_model': 'crm.lead',
                'type': 'ir.actions.act_window',
                'target': 'current',
                'res_id': self.opportunity_id.id,
                'views': [(self.env.ref('crm_kangnam_extend.crm_kangnam_crm_lead_view_form_extend').id, 'form')],
            }

    class PhoneCall(models.Model):
        _inherit = "crm.phone.call"

        def return_booking_new(self, booking):
            return {
                'name': 'Booking',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': self.env.ref('crm_kangnam_extend.crm_kangnam_crm_lead_view_form_extend').id,
                'res_model': 'crm.lead',
                'res_id': booking.id,
            }

    class SaleOrder(models.Model):
        _inherit = 'sale.order'

        def open_sale_order_view(self):
            return {
                'name': 'Xem chi tiết đơn hàng',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': self.env.ref('sale.view_order_form').id,
                'res_model': 'sale.order',
                'res_id': self.id,
            }
