import json
import logging
from odoo.addons.restful.common import (
    get_redis,
    get_redis_server
)
from odoo import models
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from datetime import timedelta, datetime

_logger = logging.getLogger(__name__)

DICT_TRANSPORT = {
    'bicycle': 'Xe đạp',
    'scooter': 'Xe máy',
    'bus': 'Xe Bus',
    'car': 'Ô tô',
    'other': 'Khác',
}

DICT_GENDER = {
    'male': 'Nam',
    'female': 'Nữ',
    'transguy': 'Transguy',
    'transgirl': 'Transgirl',
    'other': 'Khác',
}

CUSTOMER_CLASSIFICATION_DICT = {
    '1': 'Bình thường',
    '2': 'Quan tâm',
    '3': 'Quan tâm hơn',
    '4': 'Đặc biệt',
    '5': 'Khách hàng V.I.P',
}


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def view_customer_persona(self):
        domain = self.env['ir.config_parameter'].sudo().get_param('domain_customer_persona_extend')

        url = domain + '/app/customer-portrait/profile?company_id=%s&partner_id=%s' % (
            self.env.company.id, self.id)
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }

    def write(self, vals):
        res = super(ResPartner, self).write(vals)
        fields_customer_portraits = ['affected_by', 'behavior_on_the_internet', 'break_end_time', 'break_start_time',
                                     'customer_personas', 'hobby', 'revenue_source', 'term_goals', 'transport',
                                     'work_start_time', 'work_end_time']
        field_personal_information = ['name', 'street', 'street2', 'country_id', 'state_id', 'contact_address', 'email',
                                      'phone', 'mobile', 'birth_date', 'year_of_birth', 'age', 'gender',
                                      'code_customer']
        redis_client = get_redis()
        if redis_client:
            partner = self.env['res.partner'].sudo().search([('phone', '=', self.phone)], limit=1)
            partner_action_id = self.env.ref('contacts.action_contacts').id
            partner_menu_id = self.env.ref('contacts.menu_contacts').id
            if any(key in vals for key in fields_customer_portraits):
                key = self.phone
                datas = self._get_customer_portrait(partner, partner_action_id, partner_menu_id)
                redis_client.hset(key, 'portraits', json.dumps(datas, indent=4, sort_keys=True, default=str))
            elif any(key in vals for key in field_personal_information):
                key = self.phone
                datas = self._get_personal_information(partner, partner_action_id, partner_menu_id)
                redis_client.hset(key, 'personal', json.dumps(datas, indent=4, sort_keys=True, default=str))

        return res

    def partner_get_personal_information(self, phone=None, phone_2=None, phone_3=None, offset=0, limit=10, order=None):
        """ Method phục vụ cho API 1.16"""
        # key = '%s_personal' % phone
        key = phone
        sub_key = 'personal'

        redis_client = get_redis_server()
        if key and redis_client:
            # data = redis_client.get(key)
            data = redis_client.hget(key, sub_key)
            if data:
                _logger.info('REDIS: %s-personal get from cache' % key)
                return json.loads(data)
        result = {}
        domain = [('active', '=', True)]
        # if phone:
        #     domain = domain + [('phone', '=', phone)]
        # else:
        #     return result
        #
        # if phone_2:
        #     domain = domain + ['|', ('phone', '=', phone), ('phone_2', '=', phone_2)]
        #
        # if phone_3:
        #     domain = domain + ['|', '|', ('phone', '=', phone), ('phone_2', '=', phone_2), ('phone_3', '=', phone_3)]

        if phone:
            phones = [phone]
            if phone_2:
                phones.append(phone_2)
            if phone_3:
                phones.append(phone_3)

            domain.append(('phone', 'in', phones))
        else:
            return result

        partners = self.env['res.partner'].sudo().search(domain, limit=1)

        partner_action_id = self.env.ref('contacts.action_contacts').id
        partner_menu_id = self.env.ref('contacts.menu_contacts').id

        for partner in partners:
            result = self._get_personal_information(partner, partner_action_id, partner_menu_id)

        # Có redis thì set lại
        if key and redis_client:
            if result:
                # redis_client.set(key, json.dumps(result, indent=4, sort_keys=True, default=str))
                redis_client.hset(key, sub_key, json.dumps(result, indent=4, sort_keys=False, default=str))
        return result

    def partner_get_customer_portrait(self, phone=None, phone_2=None, phone_3=None, offset=0, limit=10, order=None):
        """ Method phục vụ cho API 1.17"""
        # key = '%s_portraits' % phone
        key = phone
        sub_key = 'portraits'
        redis_client = get_redis_server()
        if key and redis_client:
            # data = redis_client.get(key)
            data = redis_client.hget(key, sub_key)
            if data:
                _logger.info('REDIS: %s-portraits get from cache' % key)
                return json.loads(data)

        result = {}
        domain = [('active', '=', True)]
        # if phone:
        #     domain = domain + [('phone', '=', phone)]
        # else:
        #     return result
        #
        # if phone_2:
        #     domain = domain + ['|', ('phone', '=', phone), ('phone_2', '=', phone_2)]
        #
        # if phone_3:
        #     domain = domain + ['|', '|', ('phone', '=', phone), ('phone_2', '=', phone_2), ('phone_3', '=', phone_3)]

        if phone:
            phones = [phone]
            if phone_2:
                phones.append(phone_2)
            if phone_3:
                phones.append(phone_3)

            domain.append(('phone', 'in', phones))
        else:
            return result
        partners = self.env['res.partner'].sudo().search(domain, limit=1)
        partner_action_id = self.env.ref('contacts.action_contacts').id
        partner_menu_id = self.env.ref('contacts.menu_contacts').id

        for partner in partners:
            result = self._get_cdkh(partner, partner_action_id, partner_menu_id)

        # Có redis thì set lại
        if key and redis_client:
            if result:
                redis_client.hset(key, sub_key, json.dumps(result, indent=4, sort_keys=False, default=str))
        return result

    def _get_cdkh(self, partner, partner_action_id, partner_menu_id):
        # hobby
        hobby = []
        for rec in partner.hobby:
            hobby.append(rec.name)
        customer_personas = {'desires': [], 'pain_point': []}
        for desire in partner.desires:
            customer_personas['desires'].append({
                'id': desire.id,
                'name': desire.name,
            })
        for point in partner.pain_point:
            customer_personas['pain_point'].append({
                'id': point.id,
                'name': point.name,
            })
        return {'hobby': hobby, 'revenue_source': partner.revenue_source, 'term_goals': partner.term_goals,
                'behavior_on_the_internet': partner.behavior_on_the_internet, 'affected_by': partner.affected_by,
                'work_start_time': partner.work_start_time, 'work_end_time': partner.work_end_time,
                'break_start_time': partner.break_start_time, 'break_end_time': partner.break_end_time,
                'transport': DICT_TRANSPORT[partner.transport] if partner.transport else '',
                'customer_personas': customer_personas,
                'account_url': "%s/web#id=%d&action=%d&model=res.partner&view_type=form&cids=%d&menu_id=%d" % (
                    self.env['ir.config_parameter'].sudo().get_param('web.base.url'),
                    partner.id,
                    partner_action_id,
                    partner.company_id.id,
                    partner_menu_id)}

    def partner_get_cases(self, phone=None, phone_2=None, phone_3=None, offset=0, limit=5, order=None):
        """ Method phục vụ cho API 1.19"""
        # key = '%s_cases' % phone
        key = phone
        sub_key = 'cases'
        if not order:
            order = 'create_date desc'

        # Phân trang thì lấy luôn trong db
        redis_client = get_redis_server()
        if key and redis_client:
            # data = redis_client.get(key)
            data = redis_client.hget(key, sub_key)
            if data:
                _logger.info('REDIS: %s-cases get from cache' % key)
                return json.loads(data)

        result = []
        domain = [('active', '=', True)]
        # if phone:
        #     domain = domain + [('phone', '=', phone)]
        # else:
        #     return result
        #
        # if phone_2:
        #     domain = domain + ['|', ('phone', '=', phone), ('phone_2', '=', phone_2)]
        #
        # if phone_3:
        #     domain = domain + ['|', '|', ('phone', '=', phone), ('phone_2', '=', phone_2), ('phone_3', '=', phone_3)]

        if phone:
            phones = [phone]
            if phone_2:
                phones.append(phone_2)
            if phone_3:
                phones.append(phone_3)

            domain.append(('phone', 'in', phones))
        else:
            return result

        partners = self.env['res.partner'].search(domain, limit=1)

        case_action_id = self.env.ref('crm_base.action_complain_case_view').id
        case_menu_id = self.env.ref('crm_base.crm_menu_case').id

        result = self._get_cases(partners, case_action_id, case_menu_id, offset, limit, order)

        # Có redis thì set lại
        if key and redis_client:
            # Khi không phân trang mới set vào cache, còn phân trang tính sau
            redis_client.hset(key, sub_key, json.dumps(result, indent=4, sort_keys=False, default=str))
        return result

    def partner_phones_calls(self, phone=None, phone_2=None, phone_3=None, offset=0, limit=5, order=None):
        if not order:
            order = 'call_date desc'
        """ Method phục vụ cho API 1.20"""
        # key = '%s_phone_calls' % phone
        key = phone
        sub_key = 'phone_calls'
        redis_client = get_redis_server()
        if key and redis_client:
            # # Phân trang thì lấy luôn trong db
            # if not offset:
            # data = redis_client.get(key)
            # Hiện tại api gọi không có phân trang, load tất cả phonecall của khách hàng
            data = redis_client.hget(key, sub_key)
            if data:
                _logger.info('REDIS: %s-phone_calls get from cache' % key)
                return json.loads(data)

        result = []
        domain = [('active', '=', True)]
        # if phone:
        #     domain = domain + [('phone', '=', phone)]
        # else:
        #     return result
        #
        # if phone_2:
        #     domain = domain + ['|', ('phone', '=', phone), ('phone_2', '=', phone_2)]
        #
        # if phone_3:
        #     domain = domain + ['|', '|', ('phone', '=', phone), ('phone_2', '=', phone_2), ('phone_3', '=', phone_3)]

        if phone:
            phones = [phone]
            if phone_2:
                phones.append(phone_2)
            if phone_3:
                phones.append(phone_3)

            domain.append(('phone', 'in', phones))
        else:
            return result

        partners = self.env['res.partner'].search(domain, limit=1)

        actions_phone_call_id = self.env.ref('crm_base.action_open_view_phone_call').id
        menu_phone_call_id = self.env.ref('crm_base.crm_menu_phone_call').id

        result = self._get_phone_calls(partners, actions_phone_call_id, menu_phone_call_id, offset, limit, order)

        # Có redis thì set lại
        if key and redis_client:
            # Khi không phân trang mới set vào cache, còn phân trang tính sau
            # if not offset:
            redis_client.hset(key, sub_key, json.dumps(result, indent=4, sort_keys=False, default=str))
        return result

    def partner_get_loyalty(self, phone=None, phone_2=None, phone_3=None, offset=0, limit=5, order=None):
        """ Method phục vụ cho API """
        # key = '%s_loyalty' % phone
        key = phone
        sub_key = 'loyalty'
        redis_client = get_redis_server()
        if key and redis_client:
            # data = redis_client.get(key)
            data = redis_client.hget(key, sub_key)
            if data:
                _logger.info('REDIS: %s-loyalty get from cache' % key)
                return json.loads(data)
        result = []
        domain = [('active', '=', True)]
        # if phone:
        #     domain = domain + [('phone', '=', phone)]
        # else:
        #     return result
        #
        # if phone_2:
        #     domain = domain + ['|', ('phone', '=', phone), ('phone_2', '=', phone_2)]
        #
        # if phone_3:
        #     domain = domain + ['|', '|', ('phone', '=', phone), ('phone_2', '=', phone_2), ('phone_3', '=', phone_3)]
        if phone:
            phones = [phone]
            if phone_2:
                phones.append(phone_2)
            if phone_3:
                phones.append(phone_3)

            domain.append(('phone', 'in', phones))
        else:
            return result

        partners = self.env['res.partner'].search(domain, limit=1)
        result = self._get_loyalty(partners)

        # Có redis thì set lại
        if key and redis_client:
            redis_client.hset(key, sub_key, json.dumps(result, indent=4, sort_keys=False, default=str))
        return result

    def partner_get_walkin(self, phone=None, phone_2=None, phone_3=None, offset=0, limit=5, order=None):
        """ Method phục vụ cho API """
        # key = '%s_walkin' % phone
        key = phone
        sub_key = 'walkin'
        if not order:
            order = 'create_date desc'

        redis_client = get_redis_server()
        if key and redis_client:
            # Phân trang thì lấy luôn trong db
            # if not offset:
            # data = redis_client.get(key)
            data = redis_client.hget(key, sub_key)
            if data:
                _logger.info('REDIS: %s-walkin get from cache' % key)
                return json.loads(data)

        result = []
        domain = [('active', '=', True)]
        # if phone:
        #     domain = domain + [('phone', '=', phone)]
        # else:
        #     return result
        #
        # if phone_2:
        #     domain = domain + ['|', ('phone', '=', phone), ('phone_2', '=', phone_2)]
        #
        # if phone_3:
        #     domain = domain + ['|', '|', ('phone', '=', phone), ('phone_2', '=', phone_2), ('phone_3', '=', phone_3)]

        if phone:
            phones = [phone]
            if phone_2:
                phones.append(phone_2)
            if phone_3:
                phones.append(phone_3)

            domain.append(('phone', 'in', phones))
        else:
            return result

        partners = self.env['res.partner'].search(domain, limit=1)

        walkin_action_id = self.env.ref('shealth_all_in_one.sh_medical_register_for_walkin_action_tree').id
        walkin_menu_id = self.env.ref('shealth_all_in_one.sh_medical_menu').id

        result = self._get_walkin(partners, walkin_action_id, walkin_menu_id, offset, limit, order)

        # Có redis thì set lại
        if key and redis_client:
            # Khi không phân trang mới set vào cache, còn phân trang tính sau
            # if not offset:
            redis_client.hset(key, sub_key, json.dumps(result, indent=4, sort_keys=False, default=str))
        return result

    def partner_get_bookings_by_phone(self, phone=None, phone_2=None, phone_3=None, offset=0, limit=5, order=None):
        """ Method phục vụ cho API """
        # key = '%s_bookings' % phone
        key = phone
        sub_key = 'bookings'
        if not order:
            order = 'create_on desc'

        redis_client = get_redis_server()
        if redis_client:
            # Phân trang thì lấy luôn trong db
            if not offset:
                data = redis_client.hget(key, sub_key)
                if data:
                    _logger.info('REDIS: %s-bookings get from cache' % key)
                    return json.loads(data)

        result = []
        domain = [('active', '=', True), ('type', '=', 'opportunity')]
        if phone:
            phones = [phone]
            if phone_2:
                phones.append(phone_2)
            if phone_3:
                phones.append(phone_3)

            domain.append(('phone', 'in', phones))
        else:
            return result

        booking_action_id = self.env.ref('crm.crm_lead_action_pipeline').id
        booking_menu_id = self.env.ref('crm.crm_menu_root').id

        bookings = self.env['crm.lead'].search_read(domain=domain,
                                                    fields=['id', 'name', 'stage_id', 'create_on', 'company_id',
                                                            'effect', 'booking_date', 'arrival_date', 'phone',
                                                            'customer_classification', 'crm_line_ids'],
                                                    offset=offset,
                                                    limit=limit,
                                                    order=order)

        # line_ids = []
        # for book in bookings:
        #     line_ids += book['crm_line_ids']
        #
        # crm_lines = self.env['crm.line'].search_read(domain=[('id', 'in', line_ids)],
        #                                              fields=['id', 'service_id', 'crm_id'])
        #
        # map_crm_lines = {}
        # for crm_line in crm_lines:
        #     crm_id = crm_line['crm_id'][0]
        #     if crm_id in map_crm_lines:
        #         map_crm_lines[crm_id].append(crm_line)
        #     else:
        #         map_crm_lines[crm_id] = [crm_line]
        for booking in bookings:
            result.append(self._get_booking_detail(booking, booking_action_id, booking_menu_id))

        # Có redis thì set lại
        if redis_client:
            # Khi không phân trang mới set vào cache, còn phân trang tính sau
            if not offset:
                redis_client.hset(key, sub_key, json.dumps(result, indent=4, sort_keys=False, default=str))
        return result

    def action_recache(self):
        # Re cache lại tất cả subkey của 1 số điện thoại
        redis_client = get_redis_server()
        if redis_client:
            partner_action_id = self.env.ref('contacts.action_contacts').id
            partner_menu_id = self.env.ref('contacts.menu_contacts').id

            case_action_id = self.env.ref('crm_base.action_complain_case_view').id
            case_menu_id = self.env.ref('crm_base.crm_menu_case').id

            actions_phone_call_id = self.env.ref('crm_base.action_open_view_phone_call').id
            menu_phone_call_id = self.env.ref('crm_base.crm_menu_phone_call').id

            walkin_action_id = self.env.ref('shealth_all_in_one.sh_medical_register_for_walkin_action_tree').id
            walkin_menu_id = self.env.ref('shealth_all_in_one.sh_medical_menu').id

            booking_action_id = self.env.ref('crm.crm_lead_action_pipeline').id
            booking_menu_id = self.env.ref('crm.crm_menu_root').id

            for partner in self:
                key = partner.phone
                if key:
                    personal = self._get_personal_information(partner, partner_action_id, partner_menu_id)
                    redis_client.hset(key, 'personal', json.dumps(personal, indent=4, sort_keys=False, default=str))

                    portraits = self._get_customer_portrait(partner, partner_action_id, partner_menu_id)
                    redis_client.hset(key, 'portraits',
                                      json.dumps(portraits, indent=4, sort_keys=False, default=str))

                    cases = self._get_cases([partner], case_action_id, case_menu_id)
                    redis_client.hset(key, 'cases', json.dumps(cases, indent=4, sort_keys=False, default=str))

                    phone_calls = self._get_phone_calls([partner], actions_phone_call_id, menu_phone_call_id)
                    redis_client.hset(key, 'phone_calls',
                                      json.dumps(phone_calls, indent=4, sort_keys=False, default=str))

                    loyalty = self._get_loyalty([partner])
                    redis_client.hset(key, 'loyalty', json.dumps(loyalty, indent=4, sort_keys=False, default=str))

                    walkin = self._get_walkin([partner], walkin_action_id, walkin_menu_id)
                    redis_client.hset(key, 'walkin', json.dumps(walkin, indent=4, sort_keys=False, default=str))

                    bookings = self._get_bookings([partner], booking_action_id, booking_menu_id)
                    redis_client.hset(key, 'bookings', json.dumps(bookings, indent=4, sort_keys=False, default=str))

                    _logger.info('REDIS: %s get from cache' % key)

    def cron_job_sync_redis(self):
        # Lưu 1 key lưu tất
        redis_client = get_redis()
        if redis_client:
            partner_ids = self.env['sale.order'].sudo().search(
                [('state', 'in', ['sale', 'done']), ('date_order', '>=', '2023/05/01')]).mapped('partner_id').ids

            partners = self.env['res.partner'].search([('id', 'in', partner_ids)])

            partner_action_id = self.env.ref('contacts.action_contacts').id
            partner_menu_id = self.env.ref('contacts.menu_contacts').id

            case_action_id = self.env.ref('crm_base.action_complain_case_view').id
            case_menu_id = self.env.ref('crm_base.crm_menu_case').id

            actions_phone_call_id = self.env.ref('crm_base.action_open_view_phone_call').id
            menu_phone_call_id = self.env.ref('crm_base.crm_menu_phone_call').id

            walkin_action_id = self.env.ref('shealth_all_in_one.sh_medical_register_for_walkin_action_tree').id
            walkin_menu_id = self.env.ref('shealth_all_in_one.sh_medical_menu').id

            booking_action_id = self.env.ref('crm.crm_lead_action_pipeline').id
            booking_menu_id = self.env.ref('crm.crm_menu_root').id
            for partner in partners:
                key = partner.phone
                if key:
                    personal = self._get_personal_information(partner, partner_action_id, partner_menu_id)
                    redis_client.hset(key, 'personal', json.dumps(personal, indent=4, sort_keys=True, default=str))

                    portraits = self._get_customer_portrait(partner, partner_action_id, partner_menu_id)
                    redis_client.hset(key, 'portraits', json.dumps(portraits, indent=4, sort_keys=True, default=str))

                    cases = self._get_cases([partner], case_action_id, case_menu_id)
                    redis_client.hset(key, 'cases', json.dumps(cases, indent=4, sort_keys=True, default=str))

                    phone_calls = self._get_phone_calls([partner], actions_phone_call_id, menu_phone_call_id)
                    redis_client.hset(key, 'phone_calls',
                                      json.dumps(phone_calls, indent=4, sort_keys=True, default=str))

                    loyalty = self._get_loyalty([partner])
                    redis_client.hset(key, 'loyalty', json.dumps(loyalty, indent=4, sort_keys=True, default=str))

                    walkin = self._get_walkin([partner], walkin_action_id, walkin_menu_id)
                    redis_client.hset(key, 'walkin', json.dumps(walkin, indent=4, sort_keys=True, default=str))

                    bookings = self._get_bookings([partner], booking_action_id, booking_menu_id)
                    redis_client.hset(key, 'bookings', json.dumps(bookings, indent=4, sort_keys=False, default=str))

    def _get_bookings(self, partners, booking_action_id, booking_menu_id, offset=0, limit=5, order=None):
        p = []
        for rec in partners:
            p.append(rec.id)

        domain = [('active', '=', True), ('type', '=', 'opportunity'), ('partner_id', 'in', p)]

        bookings = self.env['crm.lead'].search_read(domain=domain,
                                                    fields=['id', 'name', 'stage_id', 'create_on', 'company_id',
                                                            'effect', 'booking_date', 'arrival_date', 'phone',
                                                            'customer_classification', 'crm_line_ids'],
                                                    offset=offset,
                                                    limit=limit,
                                                    order=order)
        result = []
        for booking in bookings:
            result.append(self._get_booking_detail(booking, booking_action_id, booking_menu_id))
        return result

    def _get_booking_detail(self, booking, booking_action_id, booking_menu_id):
        crm_line_ids = []
        for line in booking['crm_line_ids']:
            crm_line = self.env['crm.line'].browse(int(line))
            crm_line_ids.append({
                'id': crm_line.id,
                'service_name': crm_line.service_id.name,
            })

        record_url = "%s/web#id=%d&model=crm.lead&view_type=form&action=%d&menu_id=%d" % (
            self.env['ir.config_parameter'].sudo().get_param('web.base.url'),
            booking['id'], booking_action_id, booking_menu_id)
        if booking['effect'] == 'effect':
            effect = 'Hiệu lực'
        elif booking['effect'] == 'expire':
            effect = 'Hết hiệu lực'
        else:
            effect = 'Chưa hiệu lực'

        return {
            'id': booking['id'],
            'name': booking['name'],
            'stage': booking['stage_id'][1],
            'booking_date': booking['booking_date'].strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            'create_on': booking['create_on'].strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            'effect': effect,
            'link_detail': record_url,
            'company_id': booking['company_id'],
            'arrival_date': (booking['arrival_date'] + timedelta(hours=7, minutes=00)).strftime(
                DEFAULT_SERVER_DATETIME_FORMAT) if booking['arrival_date'] else '',
            'customer_classification': CUSTOMER_CLASSIFICATION_DICT[booking['customer_classification']],
            'services': crm_line_ids
        }

    def _get_personal_information(self, partner, partner_action_id, partner_menu_id):
        if partner.birth_date:
            birth_date = partner.birth_date.strftime(DEFAULT_SERVER_DATE_FORMAT)
        else:
            birth_date = partner.birth_date
        return {'id': partner.id,
                'name': partner.name,
                'street': partner.street,
                'street2': partner.street2 if partner.street2 else '',
                'country_id': partner.country_id.id,
                'country_name': partner.country_id.name,
                'state_id': partner.state_id.id,
                'state_name': partner.state_id.name,
                'contact_address': partner.contact_address,
                'email': partner.email,
                'phone': partner.phone,
                'mobile': partner.mobile,
                'birth_date': birth_date,
                'year_of_birth': partner.year_of_birth,
                'age': partner.age,
                'gender': DICT_GENDER[partner.gender] if partner.gender else '',
                'code_customer': partner.code_customer,
                'account_url': "%s/web#id=%d&action=%d&model=res.partner&view_type=form&cids=%d&menu_id=%d" % (
                    self.env['ir.config_parameter'].sudo().get_param('web.base.url'),
                    partner.id,
                    partner_action_id,
                    partner.company_id.id,
                    partner_menu_id)
                }

    def _get_customer_portrait(self, partner, partner_action_id, partner_menu_id):
        result = {}
        # hobby
        hobby = []
        for rec in partner.hobby:
            hobby.append(rec.name)
        result['hobby'] = hobby

        # revenue_source
        result['revenue_source'] = partner.revenue_source

        # term_goals
        result['term_goals'] = partner.term_goals

        # behavior_on_the_internet
        result['behavior_on_the_internet'] = partner.behavior_on_the_internet

        # affected_by
        result['affected_by'] = partner.affected_by

        # work_start_time
        result['work_start_time'] = partner.work_start_time

        # work_end_time
        result['work_end_time'] = partner.work_end_time

        # break_start_time
        result['break_start_time'] = partner.break_start_time

        # break_end_time
        result['break_end_time'] = partner.break_end_time

        # transport
        result['transport'] = DICT_TRANSPORT[partner.transport] if partner.transport else ''

        # Chân dung Customer Personas
        customer_personas = {'desires': [], 'pain_point': []}
        for desire in partner.desires:
            customer_personas['desires'].append({
                'id': desire.id,
                'name': desire.name,
            })
        for point in partner.pain_point:
            customer_personas['pain_point'].append({
                'id': point.id,
                'name': point.name,
            })
        result['customer_personas'] = customer_personas

        result['account_url'] = "%s/web#id=%d&action=%d&model=res.partner&view_type=form&cids=%d&menu_id=%d" % (
            self.env['ir.config_parameter'].sudo().get_param('web.base.url'),
            partner.id,
            partner_action_id,
            partner.company_id.id,
            partner_menu_id)
        return result

    def _get_cases(self, partners, case_action_id, case_menu_id, offset=0, limit=5, order=None):
        result = []
        p = []
        for rec in partners:
            p.append(rec.id)
        domain_c = [('crm_case.partner_id', 'in', p)]

        cases = self.env['crm.content.complain'].search_read(domain=domain_c,
                                                             fields=['id', 'crm_case', 'complain_id', 'stage',
                                                                     'priority', 'create_date'],
                                                             limit=limit,
                                                             offset=offset,
                                                             order=order)

        for case in cases:
            # get stage
            if case['stage'] == 'new':
                stage = 'Mới'
            elif case['stage'] == 'processing':
                stage = 'Đang xử trí'
            elif case['stage'] == 'finding':
                stage = 'Tìm thêm thông tin'
            elif case['stage'] == 'waiting_response':
                stage = 'Chờ phản hồi'
            elif case['stage'] == 'need_to_track':
                stage = 'Cần theo dõi'
            elif case['stage'] == 'resolve':
                stage = 'Giải quyết'
            else:
                stage = 'Hoàn thành'

            # get priority
            if case['priority'] == '0':
                priority = 'Thấp'
            elif case['priority'] == '1':
                priority = 'Bình thường'
            elif case['priority'] == '2':
                priority = 'Cao'
            else:
                priority = 'Khẩn cấp'

            record_url = "%s/web#id=%d&action=%d&model=crm.case&view_type=form&menu_id=%d" % (
                self.env['ir.config_parameter'].sudo().get_param('web.base.url'),
                int(case['crm_case'][0]),
                case_action_id, case_menu_id)
            result.append({
                'id': case['id'] if case['id'] else None,
                'name': case['complain_id'][1] if case['complain_id'] else None,
                'stage': stage if stage else None,
                'priority': priority if priority else None,
                'case_url': record_url,
                'create_date': case['create_date'].strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            })
        return result

    def _get_phone_calls(self, partners, actions_phone_call_id, menu_phone_call_id, offset=0, limit=5, order=None):
        result = []
        p = []
        for rec in partners:
            p.append(rec.id)
        domain_p = [('partner_id', 'in', p)]
        phones_call = self.env['crm.phone.call'].search_read(domain=domain_p,
                                                             fields=['id', 'name', 'type_crm_id', 'state',
                                                                     'support_rating', 'call_date'],
                                                             offset=offset,
                                                             limit=limit,
                                                             order='id desc')

        for phone_call in phones_call:
            record_url = "%s/web#id=%d&action=%d&model=crm.phone.call&view_type=form&menu_id=%d" % (
                self.env['ir.config_parameter'].sudo().get_param('web.base.url'),
                phone_call['id'],
                actions_phone_call_id, menu_phone_call_id)
            # get stage phone call
            if phone_call['state'] == 'draft':
                stage = 'Chưa xử lý'
            elif phone_call['state'] == 'not_connect':
                stage = 'Chưa kết nối'
            elif phone_call['state'] == 'connected':
                stage = 'Đã xử lý'
            elif phone_call['state'] == 'later':
                stage = 'Hẹn gọi lại sau'
            else:
                stage = 'Huỷ'

            result.append({
                'id': phone_call['id'],
                'name': phone_call['name'],
                'type_crm_id': phone_call['type_crm_id'][1],
                'stage_id': stage,
                'support_rating': phone_call['support_rating'],
                'call_date': phone_call['call_date'].strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                'phone_call_url': record_url,
            })
        return result

    def _get_loyalty(self, partners):
        result = []
        for partner in partners:
            # Thẻ thành viên loyalty_card_ids   crm.loyalty.card
            for loyalty_card_id in partner.loyalty_card_ids:
                for reward_id in loyalty_card_id.reward_ids:
                    if reward_id.stage == 'allow':
                        result.append({
                            'reward_name': reward_id.name,
                            'stage': 'Được sử dụng',
                            'expiration_date': loyalty_card_id.due_date,
                        })
        return result

    def _get_walkin(self, partners, walkin_action_id, walkin_menu_id, offset=0, limit=5, order=None):
        result = []
        p = []
        for rec in partners:
            p.append(rec.id)
        domain_w = [('partner_id', 'in', p)]

        walkin_ids = self.env['sh.medical.appointment.register.walkin'].search(domain_w,
                                                                               offset=offset,
                                                                               limit=limit,
                                                                               order=order)
        for walkin_id in walkin_ids:
            services = []
            for service in walkin_id.service:
                services.append(service.name)
            record_url = "%s/web#id=%d&model=sh.medical.appointment.register.walkin&view_type=form&action=%d&menu_id=%d" % (
                self.env['ir.config_parameter'].sudo().get_param('web.base.url'),
                walkin_id.id, walkin_action_id, walkin_menu_id)
            result.append({
                'id': walkin_id.id,
                'name': walkin_id.name,
                'date': walkin_id.date.strftime("%Y-%m-%d"),
                'department_id': walkin_id.service_room.id,
                'department_name': walkin_id.service_room.name,
                'services': services,
                'link_detail': record_url
            })
        return result

    def cron_sync_redis(self):
        ''' Cron chạy lúc 1h sáng: check tất cả các bản ghi có write_date là ngày hôm trước => gom theo partner  '''
        redis_client = get_redis_server()
        if redis_client:
            date_from = datetime.now() - timedelta(days=1)
            date_to = datetime.now()
            # lấy menu
            partner_action_id = self.env.ref('contacts.action_contacts').id
            partner_menu_id = self.env.ref('contacts.menu_contacts').id

            case_action_id = self.env.ref('crm_base.action_complain_case_view').id
            case_menu_id = self.env.ref('crm_base.crm_menu_case').id

            actions_phone_call_id = self.env.ref('crm_base.action_open_view_phone_call').id
            menu_phone_call_id = self.env.ref('crm_base.crm_menu_phone_call').id

            walkin_action_id = self.env.ref('shealth_all_in_one.sh_medical_register_for_walkin_action_tree').id
            walkin_menu_id = self.env.ref('shealth_all_in_one.sh_medical_menu').id

            booking_action_id = self.env.ref('crm.crm_lead_action_pipeline').id
            booking_menu_id = self.env.ref('crm.crm_menu_root').id

            # ============================================== truy vấn ==================================================
            query = f''' select distinct rp.id from res_partner rp
            left join crm_lead cl on rp.id = cl.partner_id
            left join crm_case cc on cc.id = cc.partner_id
            left join crm_phone_call cpc  on cpc.id = cpc.partner_id
            left join crm_loyalty_card clc  on clc.id = clc.partner_id
            left join sh_medical_appointment_register_walkin smarw  on smarw.id = smarw.partner_id
            where (cl.write_date  >= '{date_from}' AND cl.write_date <= '{date_to}')
            or (cc.write_date  >= '{date_from}' AND cc.write_date <= '{date_to}')
            or (clc.write_date  >= '{date_from}' AND clc.write_date <= '{date_to}')
            or (cpc.write_date  >= '{date_from}' AND cpc.write_date <= '{date_to}')
            or (smarw.write_date  >= '{date_from}' AND smarw.write_date <= '{date_to}') '''
            self.env.cr.execute(query)
            result_query = self.env.cr.fetchall()
            datas = []
            for rec in result_query:
                datas.append(rec[0])
            for data in datas:
                partner = self.env['res.partner'].browse(int(data))
                key = partner.phone
                if key:
                    personal = self._get_personal_information(partner, partner_action_id, partner_menu_id)
                    redis_client.hset(key, 'personal', json.dumps(personal, indent=4, sort_keys=True, default=str))

                    portraits = self._get_customer_portrait(partner, partner_action_id, partner_menu_id)
                    redis_client.hset(key, 'portraits', json.dumps(portraits, indent=4, sort_keys=True, default=str))

                    cases = self._get_cases([partner], case_action_id, case_menu_id)
                    redis_client.hset(key, 'cases', json.dumps(cases, indent=4, sort_keys=True, default=str))

                    phone_calls = self._get_phone_calls([partner], actions_phone_call_id, menu_phone_call_id)
                    redis_client.hset(key, 'phone_calls',
                                      json.dumps(phone_calls, indent=4, sort_keys=True, default=str))

                    loyalty = self._get_loyalty([partner])
                    redis_client.hset(key, 'loyalty', json.dumps(loyalty, indent=4, sort_keys=True, default=str))

                    walkin = self._get_walkin([partner], walkin_action_id, walkin_menu_id)
                    redis_client.hset(key, 'walkin', json.dumps(walkin, indent=4, sort_keys=True, default=str))

                    bookings = self._get_bookings([partner], booking_action_id, booking_menu_id)
                    redis_client.hset(key, 'bookings', json.dumps(bookings, indent=4, sort_keys=False, default=str))