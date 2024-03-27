import datetime
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api
from odoo.exceptions import ValidationError
import pytz
import requests
from datetime import date, datetime, timedelta


class CrmLead(models.Model):
    _inherit = "crm.lead"

    recare = fields.Boolean('Booking tái khai thác')

    def create_phonecall_recare(self):
        timezone = pytz.timezone('Asia/Ho_Chi_Minh')
        now = datetime.now(timezone)
        date_check = now.date()
        # Sinh PC đối với Booking Outsold trong ngày
        outsold_booking = self.env['crm.lead'].search(
            [('type', '=', 'opportunity'), ('stage_id', '=', self.env.ref('crm_base.crm_stage_out_sold').id),
             ('date_out_sold', '=', date_check)])
        if outsold_booking:
            for booking in outsold_booking:
                default_user = booking.crm_line_ids.mapped('crm_information_ids')[
                    0].user_id if booking.crm_line_ids.mapped('crm_information_ids') else self.env.user
                self.env['crm.phone.call'].with_user(default_user.id).sudo().create({
                    'name': 'Chăm sóc khách hàng Outsold - %s' % (booking.name),
                    'subject': 'Chăm sóc khách hàng Outsold',
                    'partner_id': booking.partner_id.id,
                    'phone': booking.partner_id.phone,
                    'direction': 'out',
                    'company_id': booking.company_id.id,
                    'crm_id': booking.id,
                    'country_id': booking.country_id.id,
                    'street': booking.street,
                    'type_crm_id': self.env.ref('crm_recare.phone_call_out_sold').id,
                    'care_type': 'LT',
                    # 'create_uid': consultants_1[0].user_id.id,
                    'call_date': now.date() + timedelta(days=1)
                })

        # Sinh PC đối với Booking khách không đến trong ngày
        start_datetime = datetime(date_check.year, date_check.month, date_check.day, 00, 00, 00, 0)
        end_datetime = datetime(date_check.year, date_check.month, date_check.day, 23, 59, 59, 0)
        # no_come_booking = self.env['crm.lead'].search(
        #     [('type', '=', 'opportunity'), ('stage_id', '=', self.env.ref('crm_base.crm_stage_no_come').id),
        #      ('booking_date', '>=', start_datetime), ('booking_date', '<=', end_datetime)])
        no_come_booking = self.env['crm.lead'].search(
            [('type', '=', 'opportunity'), ('customer_come', '!=', 'yes'),
             ('booking_date', '>=', start_datetime), ('booking_date', '<=', end_datetime)])
        if no_come_booking:
            for booking in no_come_booking:
                self.env['crm.phone.call'].with_user(booking.create_uid.id).sudo().create({
                    'name': 'Chăm sóc khách hàng không đến theo lịch - %s' % (booking.name),
                    'subject': 'Chăm sóc khách hàng không đến theo lịch',
                    'partner_id': booking.partner_id.id,
                    'phone': booking.partner_id.phone,
                    'direction': 'out',
                    'company_id': booking.company_id.id,
                    'crm_id': booking.id,
                    'country_id': booking.country_id.id,
                    'street': booking.street,
                    'type_crm_id': self.env.ref('crm_recare.phone_call_khach_khong_den').id,
                    'care_type': 'DVKH',
                    'call_date': booking.booking_date.replace(hour=1, minute=0, second=0) + timedelta(days=1)
                })
        # if self.env['ir.config_parameter'].sudo().get_param('web.base.url') == 'https://erp.scigroup.com.vn':
        #     body = 'Đã chạy cron Sinh PC tái chăm sóc, Ngày kiểm tra: %s' % date_check
        #     url = "https://api.telegram.org/bot6480280702:AAEQfjmvu6OudkToWg2jxtEmigGSY7J3ljA/sendMessage?chat_id=-4035923819&text=%s" % body
        #     payload = {}
        #     headers = {}
        #     requests.request("GET", url, headers=headers, data=payload)


class PhoneCall(models.Model):
    _inherit = "crm.phone.call"

    booking_recare = fields.Many2one('crm.lead', string='Booking tái khai thác Outsold')
    CONTENT_RECARE = [('1', 'Chưa sắp xếp được thời gian'),
                      ('2', 'Đã làm dịch vụ tại cơ sở khác'),
                      ('3', 'Không có nhu cầu'),
                      ('4', 'Chưa đủ chi phí'),
                      ('5', 'Chi phí quá cao'),
                      ('6', 'Chưa tin tưởng về chuyên môn'),
                      ('7', 'Tư vấn không đồng nhất'),
                      ('8', 'Hỏi ý kiến người thân'),
                      ('9', 'Đang điều trị bệnh lý'),
                      ('10', 'Bác sĩ tư vấn không cải thiện'),
                      ('11', 'Phát sinh chi phí do thêm gói dịch vụ hoặc nâng gói dịch vụ hoặc thay đổi phương án'),
                      ('12', 'Khách hàng lớn tuổi'),
                      ('13', 'Khách hàng không đủ thời gian ở Việt Nam (Việt kiều'),
                      ('14', 'Khách hàng tư vấn với mục đích nhận quà/ giải thưởng')]
    content_recare = fields.Selection(CONTENT_RECARE, string='Lý do KH không đến/Outsold')

    @api.onchange('booking_date')
    def set_call_date_1(self):
        if self.booking_date and (self.type_crm_id not in [self.env.ref('crm_recare.phone_call_out_sold'),
                                                           self.env.ref('crm_recare.phone_call_khach_khong_den')]):
            self.call_date = self.booking_date - relativedelta(days=+1)

    def create_booking(self):
        if not self.booking_date:
            raise ValidationError('Hệ thống kiểm tra bạn chưa điền giá trị Ngày hẹn lịch trên PC này')
        if self.state not in ['connected_2', 'later_1']:
            raise ValidationError('Hệ thống kiểm tra trạng thái của PC này không là Xác nhận lịch hoặc Hẹn lịch')
        booking = self.env['crm.lead'].sudo().create({
            'name': self.env['ir.sequence'].next_by_code('crm.lead'),
            'type_crm_id': self.env.ref('crm_base.type_oppor_new').id,
            'type': 'opportunity',
            'contact_name': self.crm_id.contact_name,
            'recare': True,
            'partner_id': self.partner_id.id,
            'customer_classification': self.crm_id.customer_classification,
            'aliases': self.crm_id.aliases,
            'stage_id': self.env.ref('crm_base.crm_stage_not_confirm').id,
            'phone': self.crm_id.phone,
            'mobile': self.crm_id.mobile,
            'street': self.crm_id.street,
            'email_from': self.crm_id.email_from,
            'career': self.crm_id.career,
            'lead_id': self.crm_id.id,
            'gender': self.crm_id.gender,
            'company_id': self.crm_id.company_id.id,
            'state_id': self.crm_id.state_id.id,
            'district_id': self.crm_id.district_id.id,
            'source_id': self.crm_id.source_id.id,
            'original_source_id': self.crm_id.partner_id.source_id.id,
            'campaign_id': self.crm_id.campaign_id.id,
            'customer_come': 'no',
            'category_source_id': self.crm_id.category_source_id.id,
            'user_id': self.env.user.id,
            'birth_date': self.crm_id.birth_date,
            'year_of_birth': self.crm_id.year_of_birth,
            'country_id': self.crm_id.country_id.id,
            'facebook_acc': self.crm_id.facebook_acc,
            'zalo_acc': self.crm_id.zalo_acc,
            'send_info_facebook': self.crm_id.send_info_facebook,
            'send_info_zalo': self.crm_id.send_info_zalo,
            'price_list_id': self.crm_id.price_list_id.id,
            'pass_port': self.crm_id.pass_port,
            'pass_port_date': self.crm_id.pass_port_date,
            'pass_port_issue_by': self.crm_id.pass_port_issue_by,
            'pass_port_address': self.crm_id.pass_port_address,
            'booking_date': self.booking_date,
            'type_data': self.crm_id.type_data,
            'brand_id': self.crm_id.brand_id.id,
            'overseas_vietnamese': self.crm_id.overseas_vietnamese,
        })
        self.booking_recare = booking.id
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
