import json
import re
from datetime import datetime, timedelta, date, time
import requests
from odoo import models, fields
import logging

_logger = logging.getLogger(__name__)


class SurveyRuleSMS(models.Model):
    _name = 'survey.survey.rule.sms'
    _description = 'Cấu hình gửi tin nhắn khảo sát tự động cho khách'
    _rec_name = 'name'

    survey_type = fields.Selection([('pk', 'Phiếu khám'), ('tk', 'Tái khám'), ('bk', 'Booking')], 'Loại phiếu ghi')
    survey_time_id = fields.Many2one('survey.survey.type', string='Tiêu chí')
    sent_time = fields.Float('Thời gian gửi')
    stage_id = fields.Many2many('crm.stage',
                                'survey_survey_rule_sms_rel',
                                'survey_rule_id',
                                'stage_id',
                                string='Trạng thái booking',
                                help="Tin nhắn sẽ tự động gửi cho các booking có trạng thái đã chọn")
    state_pk = fields.Selection([('Scheduled', 'Khám'), ('WaitPayment', 'Chờ thu tiền'), ('Payment', 'Đã thu tiền'),
                                 ('InProgress', 'Đang thực hiện'), ('Completed', 'Hoàn thành'),
                                 ('Cancelled', 'Đã hủy')], string='Trạng thái phiếu khám',
                                help="Tin nhắn sẽ tự động gửi cho các booking có trạng thái đã chọn")
    state_tk = fields.Selection([('InProgress', 'Đang thực hiện'), ('Completed', 'Đã hoàn thành')],
                                string='Trạng thái phiếu tái khám',
                                help="Tin nhắn sẽ tự động gửi cho các booking có trạng thái đã chọn")

    name = fields.Char('Tên của tiêu chí',
                       help="Mỗi một tiêu chí để gửi SMS sẽ có 1 tên khác nhau, phụ thuộc vào tiêu chí được chọn")

    after_date_out = fields.Integer('Số ngày sau khi đóng phiếu')

    def cron_job_survey_sms(self):
        rules = self.env['survey.survey.rule.sms'].sudo().search([])
        config = self.env['ir.config_parameter'].sudo()
        now = datetime.now()
        content_sms = None
        list_value = []
        for rule in rules:
            # Nếu Loại phiếu là booking
            if rule.survey_type == 'bk':
                list_stage_id = []
                for stage in rule.stage_id:
                    list_stage_id.append(stage.id)
                date_closed = now.replace(hour=0, minute=0, second=0,microsecond=0) - timedelta(days=int(rule.after_date_out))
                start_date = date_closed + timedelta(days=1)
                end_date = date_closed - timedelta(days=1)
                bookings = self.env['crm.lead'].sudo().search(
                    [('stage_id', 'in', list_stage_id), ('date_closed', '<', start_date), ('date_closed', '>', end_date)])
                for booking in bookings:
                    send_date = datetime.strftime(
                        fields.Datetime.context_timestamp(self.with_context(tz=self.env.user.tz),now.replace(hour=0, minute=0, second=0,microsecond=0)) + timedelta(seconds=rule.sent_time * 60 * 60), "%Y-%m-%d %H:%M:%S")
                    if not booking.survey_answer_ids:
                        surveys = self.env['survey.survey'].sudo().search(
                            [('brand_id', '=', booking.brand_id.id), ('state', '=', 'open')])
                        for survey in surveys:
                            list_company = []
                            list_group_service = []
                            list_survey_time = []
                            for company in survey.company_ids:
                                list_company.append(company.id)
                            for group_service in survey.group_service_ids:
                                list_group_service.append(group_service.id)
                            for time in survey.survey_time_ids:
                                list_survey_time.append(time.id)
                            if booking.crm_line_ids.service_id.service_category and booking.company_id.id in list_company and rule.survey_time_id.id in list_survey_time:
                                for group_service in booking.crm_line_ids.service_id.service_category:
                                    if group_service.id in list_group_service:
                                        value = {
                                            'survey_id': survey.id,
                                            'partner_phone': booking.phone,
                                            'partner_name': booking.partner_id.name,
                                            'group_service_id': group_service.id,
                                            'time': rule.survey_time_id.id,
                                            'booking_id': booking.id,
                                            'walkin_id': None,
                                            'evaluation_id': None,
                                            'send_date': str(send_date)
                                        }
                                        list_value.append(value)
                                        break

            # Nếu Loại phiếu là pk
            elif rule.survey_type == 'pk':
                date_closed = now.replace(hour=0, minute=0, second=0,microsecond=0) - timedelta(days=int(rule.after_date_out))
                start_date = date_closed + timedelta(days=1)
                end_date = date_closed - timedelta(days=1)
                walkins = self.env['sh.medical.appointment.register.walkin'].sudo().search(
                    [('state', '=', rule.state_pk), ('date_out', '<', start_date), ('date_out', '>', end_date)])
                for walkin in walkins:
                    send_date = datetime.strftime(
                        fields.Datetime.context_timestamp(self.with_context(tz=self.env.user.tz),now.replace(hour=0, minute=0, second=0,microsecond=0)) + timedelta(seconds=rule.sent_time * 60 * 60), "%Y-%m-%d %H:%M:%S")
                    if not walkin.survey_answer_ids:
                        surveys = self.env['survey.survey'].sudo().search(
                            [('brand_id', '=', walkin.booking_id.brand_id.id), ('state', '=', 'open')])
                        for survey in surveys:
                            list_company = []
                            list_group_service = []
                            list_survey_time = []
                            for company in survey.company_ids:
                                list_company.append(company.id)
                            for group_service in survey.group_service_ids:
                                list_group_service.append(group_service.id)
                            for time in survey.survey_time_ids:
                                list_survey_time.append(time.id)

                            if walkin.booking_id.crm_line_ids.service_id.service_category and walkin.booking_id.company_id.id in list_company and rule.survey_time_id.id in list_survey_time:
                                for group_service in walkin.booking_id.crm_line_ids.service_id.service_category:
                                    if group_service.id in list_group_service:
                                        value = {
                                            'survey_id': survey.id,
                                            'partner_phone': walkin.booking_id.phone,
                                            'partner_name': walkin.booking_id.partner_id.name,
                                            'group_service_id': group_service.id,
                                            'time': rule.survey_time_id.id,
                                            'booking_id': walkin.booking_id.id,
                                            'walkin_id': walkin.id,
                                            'evaluation_id': None,
                                            'send_date': str(send_date)
                                        }
                                        list_value.append(value)
                                        break

            # Nếu Loại phiếu là tk
            elif rule.survey_type == 'tk':
                date_closed = now.replace(hour=0, minute=0, second=0,microsecond=0) - timedelta(days=int(rule.after_date_out))
                start_date = date_closed + timedelta(days=1)
                end_date = date_closed - timedelta(days=1)
                evaluations = self.env['sh.medical.evaluation'].sudo().search([('state', '=', rule.state_tk),('evaluation_end_date','<',start_date),('evaluation_end_date','>',end_date)])
                for evaluation in evaluations:
                    send_date = datetime.strftime(fields.Datetime.context_timestamp(self.with_context(tz=self.env.user.tz),now.replace(hour=0, minute=0, second=0, microsecond=0)) + timedelta(
                        seconds=rule.sent_time * 60 * 60),"%Y-%m-%d %H:%M:%S")
                    if not evaluation.survey_answer_ids:
                        surveys = self.env['survey.survey'].sudo().search(
                            [('brand_id', '=', evaluation.walkin.booking_id.brand_id.id), ('state', '=', 'open')])
                        for survey in surveys:
                            list_company = []
                            list_group_service = []
                            list_survey_time = []
                            for company in survey.company_ids:
                                list_company.append(company.id)
                            for group_service in survey.group_service_ids:
                                list_group_service.append(group_service.id)
                            for time in survey.survey_time_ids:
                                list_survey_time.append(time.id)
                            if evaluation.walkin.booking_id.crm_line_ids.service_id.service_category and evaluation.walkin.booking_id.company_id.id in list_company and rule.survey_time_id.id in list_survey_time:
                                for group_service in evaluation.walkin.booking_id.crm_line_ids.service_id.service_category:
                                    if group_service.id in list_group_service:
                                        value = {
                                            'survey_id': survey.id,
                                            'partner_phone': evaluation.walkin.booking_id.phone,
                                            'partner_name': evaluation.walkin.booking_id.partner_id.name,
                                            'group_service_id': group_service.id,
                                            'time': rule.survey_time_id.id,
                                            'booking_id': evaluation.walkin.booking_id.id,
                                            'walkin_id': None,
                                            'evaluation_id': evaluation.id,
                                            'send_date': str(send_date)
                                        }
                                        list_value.append(value)
                                        break

        brands = self.env['survey.brand.config'].sudo().search([])
        for brand_config in brands:
            list_payload = []
            for payload in list_value:
                booking = self.env['crm.lead'].sudo().browse(int(payload.get('booking_id')))
                if brand_config.brand_id == booking.brand_id:
                    list_payload.append(payload)
            token = brand_config.survey_brand_token
            url = brand_config.survey_brand_url + 'api/v1/get-multi-link-survey'
            headers = {
                'Authorization': token
            }
            data = {'data': str(list_payload)}
            response = requests.get(url, headers=headers, data=data)
            response = response.json()
            if response['status'] == 0:
                datas = response['data']
                for data in datas:
                    if 'url' and 'send_date' and 'booking_id' in data:
                        link_survey = data['url']
                        date_send = data['send_date']
                        booking = self.env['crm.lead'].sudo().browse(int(data['booking_id']))
                        if link_survey:
                            content_sms = brand_config.survey_sms
                            if '[NAME]' in brand_config.survey_sms:
                                # Loại bỏ dấu trong tên khách hàng
                                if brand_config.is_remove_vietnamese:
                                    name = self._convert(booking.partner_id.name)
                                content_sms = content_sms.replace('[NAME]', name)
                            if '[LINK]' in content_sms:
                                content_sms = content_sms.replace('[LINK]', link_survey)
                            # Tạo sẵn SMS để đợi đến giờ gửi cho khách hàng
                            if booking.brand_id.id and booking.phone and content_sms:
                                partner = self.env['res.partner'].sudo().search([('phone', '=', booking.phone)])
                                sms = self.env['crm.sms'].sudo().create({
                                    'name': "SMS gửi link khảo sát",
                                    'partner_id': partner.id,
                                    'contact_name': partner.name,
                                    'phone': partner.phone,
                                    'company_id': booking.company_id.id,
                                    'send_date': date_send,
                                    'state': 'draft',
                                    'desc': content_sms
                                })



    def send_auto_sms_survey(self):
        config = self.env['ir.config_parameter'].sudo()
        # Lấy account thương hiệu và token bên caresoft
        cs_account = {}
        brands = self.env['res.brand'].search([])
        for brand in brands:
            cs_account[brand.id] = {
                'domain': config.get_param('domain_caresoft_%s' % (brand.code.lower())),
                'token': config.get_param('domain_caresoft_token_%s' % (brand.code.lower())),
                'service_id': config.get_param('domain_caresoft_service_id_%s' % (brand.code.lower()))
            }
        rules = self.env['survey.survey.rule.sms'].sudo().search([])
        for rule in rules:
            send_time = datetime.now().replace(hour=0, minute=0, second=0) + timedelta(seconds=rule.sent_time * 60 * 60)
            start_time = send_time - timedelta(minutes=10)
            end_time = send_time + timedelta(minutes=10)

            sms_lines = self.env['crm.sms'].sudo().search([('active', '=', True),
                                                           ('state', '=', 'draft'),
                                                           ('send_date', '>=', start_time),
                                                           ('send_date', '<=', end_time),
                                                           ('name', '=', 'SMS gửi link khảo sát'),
                                                           ('phone', '!=', False),
                                                           ('desc', '!=', False)],
                                                          order='send_date asc')
            for sms in sms_lines:
                brand_id = sms.brand_id.id
                if brand_id in cs_account:
                    domain = cs_account[brand_id]['domain']
                    service_id = cs_account[brand_id]['service_id']
                    token = cs_account[brand_id]['token']
                    content = sms.desc
                    phone = sms.phone
                    if phone and content:
                        res = self._sms_cs(domain, token, service_id, content, phone)
                        if res['code'] == 'OK':
                            sms.write({
                                'state': 'sent',
                                'cs_response': json.dumps(res),
                            })
                        else:
                            sms.write({
                                'state': 'error',
                                'cs_response': json.dumps(res),
                            })

    def _convert(self, text):
        patterns = {
            '[àáảãạăắằẵặẳâầấậẫẩ]': 'a',
            '[đ]': 'd',
            '[èéẻẽẹêềếểễệ]': 'e',
            '[ìíỉĩị]': 'i',
            '[òóỏõọôồốổỗộơờớởỡợ]': 'o',
            '[ùúủũụưừứửữự]': 'u',
            '[ỳýỷỹỵ]': 'y'
        }
        output = text
        for regex, replace in patterns.items():
            output = re.sub(regex, replace, output)

            # deal with upper case
            output = re.sub(regex.upper(), replace.upper(), output)
        return output

    def _sms_cs(self, domain, token, service_id, content, phone):
        headers = {
            'Authorization': 'Bearer ' + token,
            'Content-Type': 'application/json'
        }

        data = {
            "sms": {
                "service_id": service_id,
                "content": content,
                "phone": phone,
            }
        }

        url = "%s/api/v1/sms" % domain

        _logger.info("Survey....Send headers %s data %s", headers, data)
        res = requests.post(url, headers=headers, data=json.dumps(data))
        if res.status_code == 200:
            return {'code': 'OK', 'message': 'Đã gửi SMS cho khách hàng'}
        else:
            return {'code': 'error', 'message': 'Chưa gửi được'}
