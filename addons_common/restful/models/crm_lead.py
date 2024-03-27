import json
import logging
import threading
import time
from datetime import datetime
from datetime import timedelta

import requests
from odoo import fields, models, api, tools
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.addons.queue_job.job import job

from odoo.addons.restful.common import (
    get_redis,
    get_redis_server
)

_logger = logging.getLogger(__name__)

CUSTOMER_CLASSIFICATION_DICT = {
    '1': 'Bình thường',
    '2': 'Quan tâm',
    '3': 'Quan tâm hơn',
    '4': 'Đặc biệt',
    '5': 'Khách hàng V.I.P',
}


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    ticket_id = fields.Integer('Lead/Booking ticket id')

    marital_status = fields.Selection(
        [('single', 'Single'), ('in_love', 'In love'), ('engaged', 'Engaged'), ('married', 'Married'),
         ('divorce', 'Divorce'), ('other', 'Other')], string='Marital status', tracking=True)
    # hobby = fields.Many2many('hobbies.interest', 'partner_hobbies_rel', 'partner_ids', 'hobbies_ids',
    #                          string='Hobbies and Interests', tracking=True)
    revenue_source = fields.Char('Revenue Source/Income', tracking=True)
    term_goals = fields.Char('Personal plan/Term goals', tracking=True)
    social_influence = fields.Char('Social Influence', tracking=True)
    behavior_on_the_internet = fields.Char('Behavior on the Internet', tracking=True)
    affected_by = fields.Selection(
        [('family', 'Family'), ('friend', 'Friend'), ('co_worker', 'Co-Worker'), ('community', 'Community'),
         ('electronic_media', 'Electronic media'), ('other', 'Other')], string='Affected by...', tracking=True)
    work_start_time = fields.Float('Work start time', tracking=True)
    work_end_time = fields.Float('Work end time', tracking=True)
    break_start_time = fields.Float('Break start time', tracking=True)
    break_end_time = fields.Float('Break end time', tracking=True)
    transport = fields.Selection(
        [('bicycle', 'Bicycle'), ('scooter', 'Scooter'), ('bus', 'Bus'), ('car', 'Car'), ('other', 'Other')],
        string='Transport', tracking=True)
    pain_point_and_desires = fields.One2many('pain.point.and.desires', 'lead_id', string='Pain point and desires',
                                             tracking=True)
    pain_point = fields.One2many('pain.point.and.desires', 'lead_id', string='Pain point',
                                 domain=[('type', '=', 'pain_point')], tracking=True)
    desires = fields.One2many('pain.point.and.desires', 'lead_id', string='Desires',
                              domain=[('type', '=', 'desires')], tracking=True)
    hobby = fields.Many2many('hobbies.interest', 'lead_hobbies_rel', 'lead_ids', 'hobbies_ids',
                             string='Hobbies and Interests', tracking=True)

    def action_open_ticket(self):
        """ Open the website page with the survey form """
        self.ensure_one()
        if self.ticket_id:
            config = self.env['ir.config_parameter'].sudo()
            key = 'domain_caresoft_%s' % self.brand_id.code.lower()
            domain = config.get_param(key)
            domain = domain.replace('api', 'web55')
            domain = domain + '#/index?type=ticket&id=%s' % self.ticket_id

            threaded_update_account = threading.Thread(target=self._update_account, args=([self.id]))
            threaded_update_account.start()
            time.sleep(1)
            return {
                'type': 'ir.actions.act_url',
                'name': "Open ticket",
                'target': 'new',
                'url': domain
            }
        else:
            raise ValidationError("Booking này không có ticket tương ứng!")

    def _update_account(self, id):
        try:
            # if 1 == 1:
            with api.Environment.manage():
                new_cr = self.pool.cursor()
                self = self.with_env(self.env(cr=new_cr))
                booking = self.env['crm.lead'].browse(int(id))
                if booking:
                    brand_code = booking.brand_id.code.lower()
                    params = self.env['ir.config_parameter'].sudo()
                    domain_config = 'domain_caresoft_%s' % (brand_code)
                    token_config = 'domain_caresoft_token_%s' % (brand_code)

                    headers = {
                        'Authorization': 'Bearer ' + params.get_param(token_config),
                        'Content-Type': 'application/json'
                    }
                    # lấy thông tin acc
                    response = requests.get(
                        '%s/api/v1/tickets/%s' % (params.get_param(domain_config), booking.ticket_id), headers=headers)
                    response = response.json()
                    if 'ticket' in response and 'requester_id' in response['ticket'] and response['ticket'][
                        'requester_id']:
                        account_id = response['ticket']['requester_id']
                        # lấy thông tin account
                        response = requests.get(
                            '%s/api/v1/contacts/%s' % (params.get_param(domain_config), account_id), headers=headers)
                        response = response.json()
                        if response['code'] == 'ok':
                            if not response['contact']['phone_no2'] or response['contact']['phone_no3']:
                                if booking.mobile or booking.phone_no_3:
                                    data = {
                                        "contact": {
                                            "phone_no2": booking.mobile if booking.mobile else response['contact'][
                                                'phone_no2'],
                                            "phone_no3": booking.phone_no_3 if booking.phone_no_3 else
                                            response['contact']['phone_no3']
                                        }
                                    }
                                    response = requests.put(
                                        '%s/api/v1/contacts/%s' % (params.get_param(domain_config), account_id),
                                        headers=headers,
                                        data=json.dumps(data))
        except Exception as e:
            _logger.info('>' * 100)
            _logger.info(e)
            _logger.info('>' * 100)

    def write(self, vals):
        res = super(CrmLead, self).write(vals)

        # Update redis cache
        redis_client = get_redis()
        if redis_client:
            fields = ['id', 'name', 'phone', 'stage_id', 'create_on', 'company_id', 'effect', 'create_on', 'type',
                      'booking_date', 'arrival_date', 'customer_classification', 'crm_line_ids']
            lead_action_id = self.env.ref('crm.crm_lead_all_leads').id
            lead_menu_id = self.env.ref('crm.crm_menu_root').id

            booking_action_id = self.env.ref('crm.crm_lead_action_pipeline').id
            booking_menu_id = self.env.ref('crm.crm_menu_root').id
            crm_leads = self.env['crm.lead'].search_read(domain=[('active', '=', True), ('id', '=', self.id)],
                                                         fields=fields)
            for crm_lead in crm_leads:
                key = crm_lead['phone']
                if crm_lead['type'] == 'opportunity':
                    bookings = self._get_booking(crm_lead['phone'], booking_action_id, booking_menu_id)
                    redis_client.hset(key, 'bookings', json.dumps(bookings, indent=4, sort_keys=False, default=str))
                else:
                    leads = self._get_lead(crm_lead['phone'], lead_action_id, lead_menu_id)
                    redis_client.hset(key, 'leads', json.dumps(leads, indent=4, sort_keys=False, default=str))

        params = self.env['ir.config_parameter'].sudo()
        if 'sms_care_soft_enable' in tools.config.options \
                and tools.config['sms_care_soft_enable'] == 'production' \
                and 'production' == params.get_param('environment'):
            try:

                check_sync = params.get_param('config_sync_data_care_soft')
                # Câu hình là True
                if check_sync == 'True':
                    for rec in self:
                        if rec.type == 'opportunity' and rec.ticket_id:
                            domain_config = 'domain_caresoft_%s' % (rec.brand_id.code.lower())
                            token_config = 'domain_caresoft_token_%s' % (rec.brand_id.code.lower())
                            author_config = 'config_author_id_care_soft_%s' % (rec.brand_id.code.lower())

                            token = params.get_param(token_config)
                            author_id = params.get_param(author_config)
                            cs_custom_fields = eval(params.get_param('cs_custom_fields'))

                            # get url of brand
                            url = params.get_param(domain_config)

                            headers = {
                                'Authorization': 'Bearer ' + token,
                                'Content-Type': 'application/json'
                            }

                            # check thay đổi trạng thái
                            if vals.get('stage_id'):
                                stage_id_care_soft_config = 'config_stage_id_care_soft_%s' % (rec.brand_id.code.lower())
                                stage_id_care_soft = params.get_param(stage_id_care_soft_config)
                                stage_id_care_soft_values = \
                                    cs_custom_fields['%s' % rec.brand_id.code.upper()][int(stage_id_care_soft)][
                                        'values']

                                stage_erp = self.env['crm.stage'].browse(vals.get('stage_id'))
                                for stage_id_care_soft_value in stage_id_care_soft_values:
                                    if stage_id_care_soft_value['lable'] == stage_erp.name:
                                        # if rec['lable'] == 'Thành công':
                                        data = {
                                            "ticket": {
                                                "ticket_comment": {
                                                    "body": "Cập nhật trạng thái Booking: %s" % stage_erp.name,
                                                    "author_id": int(author_id),
                                                    "type": 0,
                                                    "is_public": 1
                                                },
                                                "custom_fields": [
                                                    {
                                                        "id": int(stage_id_care_soft),
                                                        "value": int(stage_id_care_soft_value['id'])
                                                    },
                                                ]
                                            }
                                        }
                                        response = requests.put('%s/api/v1/tickets/%s' % (url, rec.ticket_id),
                                                                headers=headers,
                                                                data=json.dumps(data))
                            # check thay đổi dịch vụ trên booking
                            if vals.get('crm_line_ids'):
                                list_service_cs = eval(params.get_param('cs_service_code_custom_fields_id_dict'))
                                list_service_erp = ','
                                list_service_hh = []
                                for crm_line_id in rec.crm_line_ids:
                                    if crm_line_id.stage != 'cancel':
                                        code_service = crm_line_id.service_id.default_code.replace('Đ', 'D')
                                        list_service_erp = list_service_erp + str(
                                            list_service_cs['%s' % code_service]) + ','
                                        list_service_hh.append(crm_line_id.service_id.name)
                                if list_service_erp:
                                    service_id_care_soft_config = 'config_service_care_soft_%s' % (
                                        rec.brand_id.code.lower())
                                    config_service_id_care_soft = params.get_param(service_id_care_soft_config)
                                    if rec.brand_id.code.lower() == 'hh':
                                        data = {
                                            "ticket": {
                                                "ticket_comment": {
                                                    "body": "Cập nhật dịch vụ Booking: %s" % ', '.join(list_service_hh),
                                                    "author_id": int(author_id),
                                                    "type": 0,
                                                    "is_public": 1
                                                },
                                            }
                                        }
                                    else:
                                        data = {
                                            "ticket": {
                                                "ticket_comment": {
                                                    "body": "Cập nhật dịch vụ Booking",
                                                    "author_id": int(author_id),
                                                    "type": 0,
                                                    "is_public": 1
                                                },
                                                "custom_fields": [
                                                    {
                                                        "id": int(config_service_id_care_soft),
                                                        "value": list_service_erp
                                                    },
                                                ]
                                            }
                                        }
                                    response = requests.put('%s/api/v1/tickets/%s' % (url, rec.ticket_id),
                                                            headers=headers,
                                                            data=json.dumps(data))
                                    # response = requests.put('https://api.caresoft.vn/kangnam/api/v1/tickets/306563535', headers=headers,
                                    #                         data=json.dumps(data))
                            # check thay đổi ngày đến cửa
                            if vals.get('arrival_date'):
                                arrival_date_id_care_soft_config = 'config_arrival_date_id_care_soft_%s' % (
                                    rec.brand_id.code.lower())
                                arrival_date_id_care_soft = params.get_param(arrival_date_id_care_soft_config)
                                # TODO cap nhat lai
                                if rec.brand_id.code.lower() != 'kn':
                                    data = {
                                        "ticket": {
                                            "ticket_comment": {
                                                "body": "Cập nhật Ngày đến cửa",
                                                "author_id": int(author_id),
                                                "type": 0,
                                                "is_public": 1
                                            },
                                            "custom_fields": [
                                                {
                                                    "id": int(arrival_date_id_care_soft),
                                                    "value": "%s" % (datetime.strptime(vals.get('arrival_date'),
                                                                                       '%Y-%m-%d %H:%M:%S')).strftime(
                                                        '%Y/%m/%d'),
                                                },
                                            ]
                                        }
                                    }
                                else:
                                    data = {
                                        "ticket": {
                                            "ticket_comment": {
                                                "body": "Cập nhật Ngày đến cửa",
                                                "author_id": int(author_id),
                                                "type": 0,
                                                "is_public": 1
                                            },
                                            "custom_fields": [
                                                {
                                                    "id": int(arrival_date_id_care_soft),
                                                    "value": "%s" % (datetime.strptime(vals.get('arrival_date'),
                                                                                       '%Y-%m-%d %H:%M:%S')).strftime(
                                                        '%Y/%m/%d'),
                                                },
                                                {
                                                    "id": 8939,
                                                    "value": 137482,
                                                }
                                            ]
                                        }
                                    }
                                response = requests.put('%s/api/v1/tickets/%s' % (url, rec.ticket_id),
                                                        headers=headers,
                                                        data=json.dumps(data))

                            _logger.info('========================== update ticket success ===========================')
            except Exception as e:
                _logger.info('====================================== update ticket error =============================')
                _logger.info(e)
                _logger.info('========================================================================================')

        return res

    def crm_lead_get_leads(self, phone=None, phone_2=None, phone_3=None, offset=0, limit=5, order=None):
        """ Method phục vụ cho API """
        # key = '%s_leads' % phone
        key = phone
        sub_key = 'leads'
        if not order:
            order = 'create_on desc'

        redis_client = get_redis()
        if redis_client:
            # Phân trang thì lấy luôn trong db
            if not offset:
                data = redis_client.hget(key, sub_key)
                if data:
                    return json.loads(data)

        result = []
        domain = [('active', '=', True), ('type', '=', 'lead')]
        if phone:
            phones = [phone]
            if phone_2:
                phones.append(phone_2)
            if phone_3:
                phones.append(phone_3)

            domain.append(('phone', 'in', phones))
        else:
            return result

        lead_action_id = self.env.ref('crm.crm_lead_all_leads').id
        lead_menu_id = self.env.ref('crm.crm_menu_root').id

        leads = self.env['crm.lead'].search_read(domain=domain,
                                                 fields=['id', 'name', 'stage_id', 'create_on', 'company_id',
                                                         'effect'],
                                                 offset=offset,
                                                 limit=limit,
                                                 order=order)

        for lead in leads:
            result.append(self._get_lead(lead, lead_action_id, lead_menu_id))

        # Có redis thì set lại
        if redis_client:
            # Khi không phân trang mới set vào cache, còn phân trang tính sau
            if not offset:
                redis_client.hset(key, sub_key, json.dumps(result, indent=4, sort_keys=True, default=str))
        return result

    def _get_lead(self, phone, lead_action_id, lead_menu_id):
        data = []
        leads = self.env['crm.lead'].search([('active', '=', True), ('phone', '=', phone), ('type', '=', 'lead')])
        if leads:
            for lead in leads:
                data.append({
                    'id': lead.id,
                    'name': lead.name,
                    'stage': lead.stage_id.name if lead.stage_id else '',
                    # 'booking_date': booking.booking_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                    'create_on': lead.create_on.strftime(DEFAULT_SERVER_DATETIME_FORMAT) if lead.create_on else '',
                    'link_detail': "%s/web#id=%d&model=crm.lead&view_type=form&action=%d&menu_id=%d" % (
                        self.env['ir.config_parameter'].sudo().get_param('web.base.url'), lead.id, lead_action_id,
                        lead_menu_id),
                    'company_id': lead.company_id.name,
                })
        return data

    def _get_booking(self, phone, booking_action_id, booking_menu_id):
        data = []
        bookings = self.env['crm.lead'].search(
            [('active', '=', True), ('phone', '=', phone), ('type', '=', 'opportunity')])
        if bookings:
            for booking in bookings:
                crm_line_ids = []
                for line in booking.crm_line_ids:
                    crm_line = self.env['crm.line'].browse(int(line))
                    crm_line_ids.append({
                        'id': crm_line.id,
                        'service_name': crm_line.service_id.name,
                    })
                record_url = "%s/web#id=%d&model=crm.lead&view_type=form&action=%d&menu_id=%d" % (
                    self.env['ir.config_parameter'].sudo().get_param('web.base.url'),
                    booking.id, booking_action_id, booking_menu_id)
                if booking.effect == 'effect':
                    effect = 'Hiệu lực'
                elif booking.effect == 'expire':
                    effect = 'Hết hiệu lực'
                else:
                    effect = 'Chưa hiệu lực'
                data.append({
                    'id': booking.id,
                    'name': booking.name,
                    'stage': booking.stage_id.name if booking.stage_id else '',
                    'booking_date': booking.booking_date.strftime(
                        DEFAULT_SERVER_DATETIME_FORMAT) if booking.booking_date else '',
                    'create_on': booking.create_on.strftime(
                        DEFAULT_SERVER_DATETIME_FORMAT) if booking.create_on else '',
                    'effect': effect,
                    'link_detail': record_url,
                    'company_id': booking.company_id.name,
                    'arrival_date': (booking.arrival_date + timedelta(hours=7, minutes=00)).strftime(
                        DEFAULT_SERVER_DATETIME_FORMAT) if booking.arrival_date else '',
                    'customer_classification': CUSTOMER_CLASSIFICATION_DICT[booking.customer_classification] if
                    booking.customer_classification else '',
                    'services': crm_line_ids
                })
        return data

    def cron_job_sync_redis(self):
        # Lưu 1 key lưu tất
        redis_client = get_redis()
        if redis_client:
            domain = [('active', '=', True)]
            fields = ['id', 'name', 'phone', 'stage_id', 'create_on', 'company_id', 'effect', 'create_on', 'type',
                      'booking_date', 'arrival_date', 'customer_classification', 'crm_line_ids']
            offset = 0
            # limit = 50000
            # order = None
            crm_leads = self.env['crm.lead'].search_read(domain=domain, fields=fields, offset=offset)

            lead_action_id = self.env.ref('crm.crm_lead_all_leads').id
            lead_menu_id = self.env.ref('crm.crm_menu_root').id

            booking_action_id = self.env.ref('crm.crm_lead_action_pipeline').id
            booking_menu_id = self.env.ref('crm.crm_menu_root').id

            for crm_lead in crm_leads:
                key = crm_lead['phone']
                if key:
                    if crm_lead['type'] == 'opportunity':
                        bookings = self._get_booking(crm_lead, booking_action_id, booking_menu_id)
                        redis_client.hset(key, 'bookings', json.dumps(bookings, indent=4, sort_keys=True, default=str))
                    else:
                        leads = self._get_lead(crm_lead, lead_action_id, lead_menu_id, )
                        redis_client.hset(key, 'leads', json.dumps(leads, indent=4, sort_keys=True, default=str))

    def lich_su_tham_kham(self):
        list_val = []
        data = {'name': 'Lịch sử thăm khám'}
        if self.partner_id:
            walkin = self.env['sh.medical.appointment.register.walkin'].sudo().search(
                [('partner_id', '=', self.partner_id.id), ('state', '=', 'Completed')])
            walkin = walkin.filtered(
                lambda w: (w.company_id == self.env.company) or (self.env.company in w.company2_id))
            sorted_walkin = sorted(walkin, key=lambda x: (x['booking_id']['create_date'], x['create_date']))

            for record in sorted_walkin:
                booking = record.booking_id
                service = record.service
                ngay_tu_van = []
                tinh_trang = []
                noi_dung_tu_van = []
                # Xử lý : Ngày tư vấn + tình trạng + nội dung tư vấn
                if booking.consultation_ticket_ids:
                    for line in booking.consultation_ticket_ids:
                        service_consultations = line.consultation_detail_ticket_ids.mapped('service_id')
                        if any(service in service for service in service_consultations):
                            ngay_tu_van.append(line.create_date.strftime('%d-%m-%Y'))
                            tinh_trang.append(
                                line.consultation_detail_ticket_ids.filtered(lambda c: c.service_id in service).mapped(
                                    'health_status'))
                            noi_dung_tu_van.append(
                                line.consultation_detail_ticket_ids.filtered(lambda c: c.service_id in service).mapped(
                                    'schedule'))

                # Xử lý phần BS tư vấn và lễ tân tư vấn
                bsi_tu_van = []
                letan_tu_van = []
                employees = (record.sale_order_id.order_line.mapped('crm_line_id').mapped(
                    'consultants_1') + record.sale_order_id.order_line.mapped('crm_line_id').mapped(
                    'consultants_2')).mapped('employee_ids')

                for employee in employees:
                    name = str(employee.job_id.name)
                    if 'bác sĩ' in name.lower():
                        bsi_tu_van.append(employee.name.title())
                    else:
                        letan_tu_van.append(employee.name.title())

                # Xử lý phần bác sĩ thực hiện
                if record.surgeries_ids and record.surgeries_ids.surgery_team:
                    bac_si_thuc_hien = record.surgeries_ids.surgery_team.filtered(
                        lambda st: "bác sĩ" in str(st.role.name).lower()).mapped('team_member').mapped('name')
                else:
                    bac_si_thuc_hien = record.specialty_ids.specialty_team.filtered(
                        lambda st: "bác sĩ" in str(st.role.name).lower()).mapped('team_member').mapped('name')
                list_val.append({
                    'booking': record.booking_id.name,
                    'ngay_tu_van': ', '.join(ngay_tu_van) if ngay_tu_van else 'Chưa tư vấn',
                    'ngay_thuc_hien': record.service_date_start.strftime(
                        '%d-%m-%Y') if record.service_date_start else 'Chưa thực hiện',
                    'dich_vu': ', '.join(service.mapped('name')),
                    'tinh_trang': ', '.join(tinh_trang) if tinh_trang else '',
                    'noi_dung_tu_van': ', '.join(noi_dung_tu_van) if noi_dung_tu_van else '',
                    'le_tan_tu_van': ', '.join(letan_tu_van),
                    'bsi_tu_van': ', '.join(bsi_tu_van) if bsi_tu_van else '',
                    'bac_si_thuc_hien': ', '.join(bac_si_thuc_hien).title()
                })

                # Kiểm tra xem có tái khám nào gán với PK này không

                evaluations = self.env['sh.medical.evaluation'].sudo().search([('walkin', '=', record.id)],
                                                                              order='create_date asc')
                if evaluations:
                    for evaluation in evaluations:
                        list_val.append({
                            'booking': record.booking_id.name,
                            'ngay_tu_van': '',
                            'ngay_thuc_hien': evaluation.evaluation_start_date.strftime('%d-%m-%Y'),
                            'dich_vu': ', '.join(evaluation.services.mapped('name')),
                            'tinh_trang': evaluation.info_diagnosis or evaluation.notes_complaint,
                            'noi_dung_tu_van': '',
                            'le_tan_tu_van': '',
                            'bsi_tu_van': '',
                            'bac_si_thuc_hien': ', '.join(evaluation.evaluation_team.filtered(
                                lambda et: 'bác sĩ' in str(et.role.name).lower()).mapped('team_member').mapped(
                                'name')).title()
                        })

        data.update({'data': list_val})
        return data

    def get_customer_persona(self):
        dict_val = {}
        data = {'name': 'Chân dung khách hàng'}
        if self.partner_id:
            persona = self.partner_id.persona
            list_mong_muon = self.partner_id.desires.filtered(lambda p: p.type == 'desires').mapped('name')
            if list_mong_muon:
                dict_val.update({'mong_muon': list_mong_muon})
            list_noi_lo_lang = self.partner_id.pain_point.filtered(lambda p: p.type == 'pain_point').mapped('name')
            if list_noi_lo_lang:
                dict_val.update({'lo_lang': list_noi_lo_lang})
            list_tinh_cach = persona.filtered(lambda p: p.type == '3').mapped('description')
            if list_tinh_cach:
                dict_val.update({'tinh_cach': list_tinh_cach})
            list_gia_dinh = persona.filtered(lambda p: p.type == '4').mapped('description')
            if list_gia_dinh:
                dict_val.update({'gia_dinh': list_gia_dinh})
            list_tai_chinh = persona.filtered(lambda p: p.type == '5').mapped('description')
            if list_tai_chinh:
                dict_val.update({'tai_chinh': list_tai_chinh})
            list_so_thich = persona.filtered(lambda p: p.type == '6').mapped('description')
            if list_so_thich:
                dict_val.update({'so_thich': list_so_thich})
            list_muc_tieu = persona.filtered(lambda p: p.type == '7').mapped('description')
            if list_muc_tieu:
                dict_val.update({'muc_tieu': list_muc_tieu})
            list_thuong_hieu = persona.filtered(lambda p: p.type == '8').mapped('description')
            if list_thuong_hieu:
                dict_val.update({'thuong_hieu': list_thuong_hieu})
            list_anh_huong = persona.filtered(lambda p: p.type == '9').mapped('description')
            if list_anh_huong:
                dict_val.update({'anh_huong': list_anh_huong})
            list_hanh_vi = persona.filtered(lambda p: p.type == '10').mapped('description')
            if list_hanh_vi:
                dict_val.update({'anh_huong': list_anh_huong})
            list_hoat_dong = persona.filtered(lambda p: p.type == '11').mapped('description')
            if list_hoat_dong:
                dict_val.update({'hoat_dong': list_hoat_dong})
            list_other = persona.filtered(lambda p: p.type == '12').mapped('description')
            if list_other:
                dict_val.update({'other': list_other})
        data.update({'data': dict_val})
        return data

    def view_customer_persona(self):
        domain = self.env['ir.config_parameter'].sudo().get_param('domain_customer_persona_extend')
        url = domain + '/app/customer-portrait/profile?company_id=%s&partner_id=%s' % (
            self.env.company.id, self.partner_id.id)
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }

    # @job
    # def sync_booking_redis(self, id, redis_client):
    #     fields = ['id', 'name', 'phone', 'stage_id', 'create_on', 'company_id', 'effect', 'create_on', 'type',
    #               'booking_date', 'arrival_date', 'customer_classification', 'crm_line_ids']
    #     lead_action_id = self.env.ref('crm.crm_lead_all_leads').id
    #     lead_menu_id = self.env.ref('crm.crm_menu_root').id
    #
    #     booking_action_id = self.env.ref('crm.crm_lead_action_pipeline').id
    #     booking_menu_id = self.env.ref('crm.crm_menu_root').id
    #     record = self.env['crm.lead'].search_read(domain=[('active', '=', True), ('id', '=', self.id)],
    #                                               fields=fields)
    #     key = record['phone']
    #     if record['type'] == 'opportunity':
    #         bookings = self._get_booking(record['phone'], booking_action_id, booking_menu_id)
    #         redis_client.hset(key, 'bookings', json.dumps(bookings, indent=4, sort_keys=False, default=str))
    #     else:
    #         leads = self._get_lead(record['phone'], lead_action_id, lead_menu_id)
    #         redis_client.hset(key, 'leads', json.dumps(leads, indent=4, sort_keys=False, default=str))
    #
    # @api.model
    # def create(self, vals):
    #     res = super(CrmLead, self).create(vals)
    #     redis_client = get_redis()
    #     if redis_client and res:
    #         self.sudo().with_delay(priority=0, channel='sync_seeding_crm_lead').sync_booking_redis(id=res.id,
    #                                                                                                redis_client=redis_client)
    #     return res
    #
    # def write(self, vals):
    #     res = super(CrmLead, self).create(vals)
    #     redis_client = get_redis()
    #     if redis_client and res:
    #         for crm in self:
    #             func_string = f"{crm._name}({crm.id},).sync_record({crm.id})"
    #             existing_job = self.env['queue.job'].sudo().search([
    #                 ('func_string', '=', func_string),
    #                 ('channel', '=', 'sync_seeding_crm_lead'),
    #                 ('state', '=', 'pending')
    #             ])
    #             if crm.id and not existing_job:
    #                 crm.sudo().with_delay(priority=0, channel='sync_seeding_crm_lead').sync_booking_redis(id=crm.id,
    #                                                                                                       redis_client=redis_client)
    #             else:
    #                 pass
    #     return res
