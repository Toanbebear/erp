"""Part of odoo. See LICENSE file for full copyright and licensing details."""
import logging
from datetime import timedelta

from odoo import http
from odoo.addons.restful.common import (
    extract_arguments,
    valid_response,
    valid_response_once,
    invalid_response,
    get_redis
)
from odoo.addons.restful.controllers.main import (
    get_url_base,
    validate_token,
)
from odoo.http import request
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT

_logger = logging.getLogger(__name__)


class AccountController(http.Controller):

    @validate_token
    @http.route("/api/v1/personal-information", type="http", auth="none", methods=["GET"], csrf=False)
    def get_personal_information(self, **payload):
        """ API 1.16 Lấy thông tin cá nhân khách hàng"""
        domain, fields, offset, limit, order = extract_arguments(payload)
        phone = payload.get("phone", None)
        phone_2 = payload.get("phone_2", None)
        phone_3 = payload.get("phone_3", None)
        data = request.env['res.partner'].partner_get_personal_information(phone=phone,
                                                                        phone_2=phone_2,
                                                                        phone_3=phone_3,
                                                                        offset=offset,
                                                                        limit=limit,
                                                                        order=order)
        return valid_response_once(data)

    @validate_token
    @http.route("/api/v1/customer-portrait", type="http", auth="none", methods=["GET"], csrf=False)
    def get_customer_portrait(self, **payload):
        """ API Lấy thông tin chân dung khách hàng"""
        domain, fields, offset, limit, order = extract_arguments(payload)
        phone = payload.get("phone", None)
        phone_2 = payload.get("phone_2", None)
        phone_3 = payload.get("phone_3", None)
        data = request.env['res.partner'].partner_get_customer_portrait(phone=phone,
                                                                        phone_2=phone_2,
                                                                        phone_3=phone_3,
                                                                        offset=offset,
                                                                        limit=limit,
                                                                        order=order)
        return valid_response_once(data)

    @validate_token
    @http.route("/api/v1/bookings1", type="http", auth="none", methods=["GET"], csrf=False)
    def get_all_bookings(self, **payload):
        """ API Lấy danh sách booking của khách hàng"""
        domain, fields, offset, limit, order = extract_arguments(payload)
        phone = payload.get("phone", None)
        phone_2 = payload.get("phone_2", None)
        phone_3 = payload.get("phone_3", None)
        data = request.env['res.partner'].partner_get_bookings_by_phone(phone=phone, phone_2=phone_2, phone_3=phone_3,
                                                                      offset=offset, limit=limit, order=order)
        return valid_response(data)

    @validate_token
    @http.route("/api/v1/cases", type="http", auth="none", methods=["GET"], csrf=False)
    def get_cases(self, **payload):
        """ API 1.19 Lấy danh sách case khiếu nại """
        domain, fields, offset, limit, order = extract_arguments(payload)
        phone = payload.get("phone", None)
        phone_2 = payload.get("phone_2", None)
        phone_3 = payload.get("phone_3", None)
        data = request.env['res.partner'].partner_get_cases(phone=phone,
                                                         phone_2=phone_2,
                                                         phone_3=phone_3,
                                                         offset=offset,
                                                         limit=limit,
                                                         order=order)
        return valid_response(data)

    @validate_token
    @http.route("/api/v1/phones-call", type="http", auth="none", methods=["GET"], csrf=False)
    def get_phones_call(self, **payload):
        """ API 1.20 Lấy danh sách phone call của khách hàng"""
        domain, fields, offset, limit, order = extract_arguments(payload)
        phone = payload.get("phone", None)
        phone_2 = payload.get("phone_2", None)
        phone_3 = payload.get("phone_3", None)
        data = request.env['res.partner'].partner_phones_calls(phone=phone,
                                                         phone_2=phone_2,
                                                         phone_3=phone_3,
                                                         offset=offset,
                                                         limit=limit,
                                                         order=order)
        return valid_response(data)

    @validate_token
    @http.route("/api/v1/walkin", type="http", auth="none", methods=["GET"], csrf=False)
    def get_walkin(self, **payload):
        """ API 1.21 Lấy danh sách phiếu khám của khách hàng"""
        domain, fields, offset, limit, order = extract_arguments(payload)
        phone = payload.get("phone", None)
        phone_2 = payload.get("phone_2", None)
        phone_3 = payload.get("phone_3", None)
        data = request.env['res.partner'].partner_get_walkin(phone=phone,
                                                         phone_2=phone_2,
                                                         phone_3=phone_3,
                                                         offset=offset,
                                                         limit=limit,
                                                         order=order)
        return valid_response(data)

    @validate_token
    @http.route("/api/v1/loyalty", type="http", auth="none", methods=["GET"], csrf=False)
    def get_loyalty(self, **payload):
        """ API 1.22 thông tin thẻ thành viên của khách hàng"""
        domain, fields, offset, limit, order = extract_arguments(payload)
        phone = payload.get("phone", None)
        phone_2 = payload.get("phone_2", None)
        phone_3 = payload.get("phone_3", None)
        data = request.env['res.partner'].partner_get_loyalty(phone=phone,
                                                         phone_2=phone_2,
                                                         phone_3=phone_3,
                                                         offset=offset,
                                                         limit=limit,
                                                         order=order)
        return valid_response(data)

    @validate_token
    @http.route("/api/v1/leads", type="http", auth="none", methods=["GET"], csrf=False)
    def get_leads(self, **payload):
        """ API Lấy danh sách leads của khách hàng """
        domain, fields, offset, limit, order = extract_arguments(payload)
        phone = payload.get("phone", None)
        phone_2 = payload.get("phone_2", None)
        phone_3 = payload.get("phone_3", None)
        data = request.env['crm.lead'].crm_lead_get_leads(phone=phone,
                                                         phone_2=phone_2,
                                                         phone_3=phone_3,
                                                         offset=offset,
                                                         limit=limit,
                                                         order=order)
        return valid_response_once(data)

    @validate_token
    @http.route("/api/v1/account", type="http", auth="none", methods=["GET"], csrf=False)
    def get_account(self, **payload):
        """ API 4.1 Lấy thông tin khách hàng"""
        domain, fields, offset, limit, order = extract_arguments(payload)

        if payload.get("phone", None):
            phones = [payload.get("phone")]
            phone_2 = payload.get("phone_2", None)
            phone_3 = payload.get("phone_3", None)

            if phone_2:
                phones.append(payload.get("phone_2"))
            if phone_3:
                phones.append(payload.get("phone_3"))

            domain = [('active', '=', True), ('phone', 'in', phones)]

            partners = request.env['res.partner'].search(domain, limit=10)
            datas = []
            for partner in partners:
                data = {}
                data['id'] = partner.id
                data['name'] = partner.name
                data['street'] = partner.street
                data['street2'] = partner.street2 if partner.street2 else ''
                data['country_id'] = partner.country_id.id
                data['country_name'] = partner.country_id.name
                data['state_id'] = partner.state_id.id
                data['state_name'] = partner.state_id.name
                data['contact_address'] = partner.contact_address
                data['email'] = partner.email
                data['phone'] = partner.phone
                data['mobile'] = partner.mobile
                if partner.birth_date:
                    data['birth_date'] = partner.birth_date.strftime(DEFAULT_SERVER_DATE_FORMAT)
                else:
                    data['birth_date'] = partner.birth_date
                data['year_of_birth'] = partner.year_of_birth
                data['age'] = partner.age
                data['gender'] = partner.gender
                data['code_customer'] = partner.code_customer
                # data['pricelist'] = partner.property_product_pricelist
                # data['invoice_ids'] = partner.invoice_ids
                # data['opportunity_ids'] = partner.opportunity_ids
                # data['sale_order_ids'] = partner.sale_order_ids
                # data['sale_order_count'] = partner.sale_order_count
                # data['crm_ids'] = partner.sale_order_count

                price_list = []
                for product_pricelist in partner.property_product_pricelist:
                    price_list.append({
                        'id': product_pricelist.id,
                        'name': product_pricelist.name,
                    })
                data['price_list'] = price_list

                bookings = []
                # examinations = []
                booking_action_id = request.env.ref('crm.crm_lead_action_pipeline').id
                booking_menu_id = request.env.ref('crm.crm_menu_root').id
                for booking in partner.opportunity_ids:
                    record_url = get_url_base() + "/web#id=%d&model=crm.lead&view_type=form&action=%d&menu_id=%d" % (
                        booking.id,
                        booking_action_id, booking_menu_id)

                    if booking.effect == 'effect':
                        effect = 'Hiệu lực'
                    elif booking.effect == 'expire':
                        effect = 'Hết hiệu lực'
                    else:
                        effect = 'Chưa hiệu lực'

                    bookings.append({
                        'id': booking.id,
                        'name': booking.name,
                        'stage': booking.stage_id.name,
                        # 'booking_date': booking.booking_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                        'create_on': booking.create_on.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                        'effect': effect,
                        'link_detail': record_url,
                        'company_id': booking.company_id.id
                    })

                    # # Phiếu khám
                    # for walkin_id in booking.walkin_ids:
                    #     # examinations.append({'date': walkin_id.date.strftime("%d-%m-%Y"),})
                data['bookings'] = bookings
                # data['examinations'] = examinations

                # Case
                cases = []
                for crm_case_id in partner.crm_case_ids:
                    cases.append({
                        'id': crm_case_id.id,
                        'code': crm_case_id.code,
                        'name': crm_case_id.name,
                        'user_id': crm_case_id.user_id.id,
                        'user_name': crm_case_id.user_id.name,
                        'create_on': crm_case_id.create_on.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                        'write_date': crm_case_id.write_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                    })

                data['cases'] = cases

                # Lịch sử khám 1
                examinations = []
                walkin_action_id = request.env.ref('shealth_all_in_one.sh_medical_register_for_walkin_action_tree').id
                walkin_menu_id = request.env.ref('shealth_all_in_one.sh_medical_menu').id
                for walkin_id in partner.walkin_ids:
                    services = []
                    for service in walkin_id.service:
                        services.append(service.name)

                    record_url = get_url_base() + "/web#id=%d&model=sh.medical.appointment.register.walkin&view_type" \
                                                  "=form&action=%d&menu_id=%d" % (
                                     walkin_id.id, walkin_action_id, walkin_menu_id)

                    examinations.append({
                        'id': walkin_id.id,
                        'name': walkin_id.name,
                        'date': walkin_id.date.strftime("%Y-%m-%d"),
                        'department_id': walkin_id.service_room.id,
                        'department_name': walkin_id.service_room.name,
                        'services': services,
                        'link_detail': record_url
                    })
                data['examinations'] = examinations

                # Thẻ thành viên loyalty_card_ids   crm.loyalty.card
                loyalty_cards = []
                for loyalty_card_id in partner.loyalty_card_ids:
                    if loyalty_card_id.rank_id:
                        rank = loyalty_card_id.rank_id.name
                    else:
                        rank = ''
                    if loyalty_card_id.date_interaction:
                        date_interaction = loyalty_card_id.date_interaction.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                    else:
                        date_interaction = loyalty_card_id.date_interaction

                    if loyalty_card_id.due_date:
                        due_date = loyalty_card_id.due_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                    else:
                        due_date = loyalty_card_id.due_date

                    loyalty_cards.append({
                        'id': loyalty_card_id.id,
                        'name': loyalty_card_id.name,
                        'rank': rank,
                        'date_interaction': date_interaction,
                        'validity_card': loyalty_card_id.validity_card,
                        'due_date': due_date,
                    })
                data['loyalty_cards'] = loyalty_cards

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
                data['customer_personas'] = customer_personas

                # Đơn hàng
                orders = []
                for sale_order_id in partner.sale_order_ids:
                    orders.append({
                        'id': sale_order_id.id,
                        'name': sale_order_id.name,
                        'amount_total': sale_order_id.amount_total,
                        'state': sale_order_id.state,
                        'create_date': sale_order_id.create_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                    })
                data['orders'] = orders
                datas.append(data)
        return valid_response(datas)

    # @validate_token
    # @http.route("/api/v1/personal-information", type="http", auth="none", methods=["GET"], csrf=False)
    # def get_personal_information(self, **payload):
    #     """ API Lấy thông tin cá nhân khách hàng"""
    #     if payload.get("phone", None):
    #         phones = [payload.get("phone")]
    #         phone_2 = payload.get("phone_2", None)
    #         phone_3 = payload.get("phone_3", None)
    #
    #         if phone_2:
    #             phones.append(payload.get("phone_2"))
    #         if phone_3:
    #             phones.append(payload.get("phone_3"))
    #
    #         domain = [('active', '=', True), ('phone', 'in', phones)]
    #
    #         partners = request.env['res.partner'].search(domain, limit=10)
    #         data = {}
    #
    #         partner_action_id = request.env.ref('contacts.action_contacts').id
    #         partner_menu_id = request.env.ref('contacts.menu_contacts').id
    #
    #         for partner in partners:
    #             data['id'] = partner.id
    #             data['name'] = partner.name
    #             data['street'] = partner.street
    #             data['street2'] = partner.street2 if partner.street2 else ''
    #             data['country_id'] = partner.country_id.id
    #             data['country_name'] = partner.country_id.name
    #             data['state_id'] = partner.state_id.id
    #             data['state_name'] = partner.state_id.name
    #             data['contact_address'] = partner.contact_address
    #             data['email'] = partner.email
    #             data['phone'] = partner.phone
    #             data['mobile'] = partner.mobile
    #             if partner.birth_date:
    #                 data['birth_date'] = partner.birth_date.strftime(DEFAULT_SERVER_DATE_FORMAT)
    #             else:
    #                 data['birth_date'] = partner.birth_date
    #             data['year_of_birth'] = partner.year_of_birth
    #             data['age'] = partner.age
    #             data['gender'] = partner.gender
    #             data['code_customer'] = partner.code_customer
    #             data[
    #                 'account_url'] = get_url_base() + "/web#id=%d&action=%d&model=res.partner&view_type=form&cids=%d&menu_id=%d" % (
    #                 partner.id, partner_action_id, partner.company_id.id, partner_menu_id)
    #         return valid_response_once(data)

    # @validate_token
    # @http.route("/api/v1/customer-portrait", type="http", auth="none", methods=["GET"], csrf=False)
    # def get_customer_portrait(self, **payload):
    #     """ API Lấy thông tin chân dung khách hàng"""
    #     if payload.get("phone", None):
    #         phones = [payload.get("phone")]
    #         phone_2 = payload.get("phone_2", None)
    #         phone_3 = payload.get("phone_3", None)
    #
    #         if phone_2:
    #             phones.append(payload.get("phone_2"))
    #         if phone_3:
    #             phones.append(payload.get("phone_3"))
    #
    #         request.env['res.partner'].search(domain, limit=10)
    #
    #         domain = [('active', '=', True), ('phone', 'in', phones)]
    #
    #         partners = request.env['res.partner'].search(domain, limit=10)
    #         data = {}
    #
    #         partner_action_id = request.env.ref('contacts.action_contacts').id
    #         partner_menu_id = request.env.ref('contacts.menu_contacts').id
    #
    #         for partner in partners:
    #             # hobby
    #             hobby = []
    #             for rec in partner.hobby:
    #                 hobby.append(rec.name)
    #             data['hobby'] = hobby
    #
    #             # revenue_source
    #             data['revenue_source'] = partner.revenue_source
    #
    #             # term_goals
    #             data['term_goals'] = partner.term_goals
    #
    #             # behavior_on_the_internet
    #             data['behavior_on_the_internet'] = partner.behavior_on_the_internet
    #
    #             # affected_by
    #             data['affected_by'] = partner.affected_by
    #
    #             # work_start_time
    #             data['work_start_time'] = partner.work_start_time
    #
    #             # work_end_time
    #             data['work_end_time'] = partner.work_end_time
    #
    #             # break_start_time
    #             data['break_start_time'] = partner.break_start_time
    #
    #             # break_end_time
    #             data['break_end_time'] = partner.break_end_time
    #
    #             # transport
    #             data['transport'] = partner.transport
    #
    #             # Chân dung Customer Personas
    #             customer_personas = {'desires': [], 'pain_point': []}
    #             for desire in partner.desires:
    #                 customer_personas['desires'].append({
    #                     'id': desire.id,
    #                     'name': desire.name,
    #                 })
    #             for point in partner.pain_point:
    #                 customer_personas['pain_point'].append({
    #                     'id': point.id,
    #                     'name': point.name,
    #                 })
    #             data['customer_personas'] = customer_personas
    #             data[
    #                 'account_url'] = get_url_base() + "/web#id=%d&action=%d&model=res.partner&view_type=form&cids=%d&menu_id=%d" % (
    #                 partner.id, partner_action_id, partner.company_id.id, partner_menu_id)
    #         return valid_response_once(data)
    #
    # @validate_token
    # @http.route("/api/v1/leads", type="http", auth="none", methods=["GET"], csrf=False)
    # def get_leads(self, **payload):
    #     """ API Lấy danh sách leads của khách hàng"""
    #     if payload.get("phone", None):
    #         # set default offset, limit
    #
    #         phones = [payload.get("phone")]
    #         phone_2 = payload.get("phone_2", None)
    #         phone_3 = payload.get("phone_3", None)
    #         offset = int(payload.get("offset")) if payload.get("offset") else 0
    #         limit = int(payload.get("limit")) if payload.get("limit") else 5
    #
    #         if phone_2:
    #             phones.append(payload.get("phone_2"))
    #         if phone_3:
    #             phones.append(payload.get("phone_3"))
    #         # search partner
    #         domain = [('active', '=', True), ('phone', 'in', phones), ('type', '=', 'lead')]
    #
    #         leads = request.env['crm.lead'].search_read(domain=domain,
    #                                                     fields=['id', 'name', 'stage_id', 'create_on', 'company_id',
    #                                                             'effect'], offset=offset, limit=limit,
    #                                                     order='create_on desc')
    #
    #         lead_action_id = request.env.ref('crm.crm_lead_all_leads').id
    #         lead_menu_id = request.env.ref('crm.crm_menu_root').id
    #
    #         data = []
    #         for lead in leads:
    #             record_url = get_url_base() + "/web#id=%d&model=crm.lead&view_type=form&action=%d&menu_id=%d" % (
    #                 lead['id'], lead_action_id, lead_menu_id)
    #
    #             data.append({
    #                 'id': lead['id'],
    #                 'name': lead['name'],
    #                 'stage': lead['stage_id'][1],
    #                 # 'booking_date': booking.booking_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
    #                 'create_on': lead['create_on'].strftime(DEFAULT_SERVER_DATETIME_FORMAT),
    #                 'link_detail': record_url,
    #                 'company_id': lead['company_id'],
    #             })
    #         return valid_response(data)


    @validate_token
    @http.route("/api/v1/bookings", type="http", auth="none", methods=["GET"], csrf=False)
    def get_bookings(self, **payload):
        """ API 1.18 Lấy danh sách booking của khách hàng"""
        if payload.get("phone", None):
            phones = [payload.get("phone")]
            phone_2 = payload.get("phone_2", None)
            phone_3 = payload.get("phone_3", None)
            offset = int(payload.get("offset")) if payload.get("offset") else 0
            limit = int(payload.get("limit")) if payload.get("limit") else 5

            if phone_2:
                phones.append(payload.get("phone_2"))
            if phone_3:
                phones.append(payload.get("phone_3"))
            # search partner
            domain = [('active', '=', True), ('phone', 'in', phones), ('type', '=', 'opportunity')]

            bookings = request.env['crm.lead'].search_read(domain=domain,
                                                           fields=['id', 'name', 'stage_id', 'create_on', 'company_id',
                                                                   'effect', 'booking_date', 'arrival_date',
                                                                   'customer_classification', 'crm_line_ids'],
                                                           offset=offset,
                                                           limit=limit,
                                                           order='create_on desc')
            booking_action_id = request.env.ref('crm.crm_lead_action_pipeline').id
            booking_menu_id = request.env.ref('crm.crm_menu_root').id

            customer_classification_dict = {
                '1': 'Bình thường',
                '2': 'Quan tâm',
                '3': 'Quan tâm hơn',
                '4': 'Đặc biệt',
                '5': 'Khách hàng V.I.P',
            }

            data = []
            for booking in bookings:
                crm_line_ids = []
                for line in booking['crm_line_ids']:
                    crm_line = request.env['crm.line'].browse(int(line))
                    crm_line_ids.append({
                        'id': crm_line.id,
                        'service_name': crm_line.service_id.name,
                    })
                record_url = get_url_base() + "/web#id=%d&model=crm.lead&view_type=form&action=%d&menu_id=%d" % (
                    booking['id'],
                    booking_action_id, booking_menu_id)

                if booking['effect'] == 'effect':
                    effect = 'Hiệu lực'
                elif booking['effect'] == 'expire':
                    effect = 'Hết hiệu lực'
                else:
                    effect = 'Chưa hiệu lực'

                data.append({
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
                    'customer_classification': customer_classification_dict[booking['customer_classification']] if booking['customer_classification'] else '',
                    'services': crm_line_ids
                })
            return valid_response(data)
        else:
            return invalid_response("Phone not found", "Vui lòng nhập số điện thoại tham số phone")
    # @validate_token
    # @http.route("/api/v1/phones-call", type="http", auth="none", methods=["GET"], csrf=False)
    # def get_phones_call(self, **payload):
    #     """ API Lấy danh sách phone call của khách hàng"""
    #     if payload.get("phone", None):
    #         phones = [payload.get("phone")]
    #         phone_2 = payload.get("phone_2", None)
    #         phone_3 = payload.get("phone_3", None)
    #         offset = int(payload.get("offset")) if payload.get("offset") else 0
    #         limit = int(payload.get("limit")) if payload.get("limit") else 5
    #
    #         if phone_2:
    #             phones.append(payload.get("phone_2"))
    #         if phone_3:
    #             phones.append(payload.get("phone_3"))
    #
    #         domain = [('active', '=', True), ('phone', 'in', phones)]
    #         partners = request.env['res.partner'].search(domain, limit=10)
    #
    #         p = []
    #         for rec in partners:
    #             p.append(rec.id)
    #         domain_p = [('partner_id', 'in', p)]
    #         phones_call = request.env['crm.phone.call'].search_read(domain=domain_p,
    #                                                                 fields=['id', 'name', 'type_crm_id', 'state',
    #                                                                         'support_rating', 'call_date'],
    #                                                                 offset=offset, limit=limit, order='call_date desc')
    #         call = request.env['crm.phone.call'].search(domain_p)
    #         data = []
    #         actions_phone_call_id = request.env.ref('crm_base.action_open_view_phone_call').id
    #         menu_phone_call_id = request.env.ref('crm_base.crm_menu_phone_call').id
    #         for phone_call in phones_call:
    #             record_url = get_url_base() + "/web#id=%d&action=%d&model=crm.phone.call&view_type=form&menu_id=%d" % (
    #                 phone_call['id'],
    #                 actions_phone_call_id, menu_phone_call_id)
    #             # get stage phone call
    #             if phone_call['state'] == 'draft':
    #                 stage = 'Chưa xử lý'
    #             elif phone_call['state'] == 'not_connect':
    #                 stage = 'Chưa kết nối'
    #             elif phone_call['state'] == 'connected':
    #                 stage = 'Đã xử lý'
    #             elif phone_call['state'] == 'later':
    #                 stage = 'Hẹn gọi lại sau'
    #             else:
    #                 stage = 'Huỷ'
    #
    #             data.append({
    #                 'id': phone_call['id'],
    #                 'name': phone_call['name'],
    #                 'type_crm_id': phone_call['type_crm_id'][1],
    #                 'stage_id': stage,
    #                 'support_rating': phone_call['support_rating'],
    #                 'call_date': phone_call['call_date'].strftime(DEFAULT_SERVER_DATETIME_FORMAT),
    #                 'phone_call_url': record_url,
    #             })
    #         return valid_response(data)

    # @validate_token
    # @http.route("/api/v1/walkin", type="http", auth="none", methods=["GET"], csrf=False)
    # def get_walkin(self, **payload):
    #     """ API Lấy danh sách phiếu khám của khách hàng"""
    #     if payload.get("phone", None):
    #         phones = [payload.get("phone")]
    #         phone_2 = payload.get("phone_2", None)
    #         phone_3 = payload.get("phone_3", None)
    #         offset = int(payload.get("offset")) if payload.get("offset") else 0
    #         limit = int(payload.get("limit")) if payload.get("limit") else 5
    #
    #         if phone_2:
    #             phones.append(payload.get("phone_2"))
    #         if phone_3:
    #             phones.append(payload.get("phone_3"))
    #
    #         domain = [('phone', 'in', phones)]
    #         partners = request.env['res.partner'].search(domain, limit=10)
    #         p = []
    #         for rec in partners:
    #             p.append(rec.id)
    #         domain_w = [('partner_id', 'in', p)]
    #         data = []
    #         # for partner in partners:
    #         #     walkin_action_id = request.env.ref('shealth_all_in_one.sh_medical_register_for_walkin_action_tree').id
    #         #     walkin_menu_id = request.env.ref('shealth_all_in_one.sh_medical_menu').id
    #         #     for walkin_id in partner.walkin_ids:
    #         #         services = []
    #         #         for service in walkin_id.service:
    #         #             services.append(service.name)
    #         #
    #         #         record_url = get_url_base() + "/web#id=%d&model=sh.medical.appointment.register.walkin&view_type" \
    #         #                                       "=form&action=%d&menu_id=%d" % (
    #         #                          walkin_id.id, walkin_action_id, walkin_menu_id)
    #         #
    #         #         examinations.append({
    #         #             'id': walkin_id.id,
    #         #             'name': walkin_id.name,
    #         #             'date': walkin_id.date.strftime("%Y-%m-%d"),
    #         #             'department_id': walkin_id.service_room.id,
    #         #             'department_name': walkin_id.service_room.name,
    #         #             'services': services,
    #         #             'link_detail': record_url
    #         #         })
    #         walkin_action_id = request.env.ref('shealth_all_in_one.sh_medical_register_for_walkin_action_tree').id
    #         walkin_menu_id = request.env.ref('shealth_all_in_one.sh_medical_menu').id
    #         walkin_ids = request.env['sh.medical.appointment.register.walkin'].search(domain_w, offset=offset,
    #                                                                                   limit=limit,
    #                                                                                   order='create_date desc')
    #         for walkin_id in walkin_ids:
    #             services = []
    #             for service in walkin_id.service:
    #                 services.append(service.name)
    #             record_url = get_url_base() + "/web#id=%d&model=sh.medical.appointment.register.walkin&view_type" \
    #                                           "=form&action=%d&menu_id=%d" % (
    #                              walkin_id.id, walkin_action_id, walkin_menu_id)
    #             data.append({
    #                 'id': walkin_id.id,
    #                 'name': walkin_id.name,
    #                 'date': walkin_id.date.strftime("%Y-%m-%d"),
    #                 'department_id': walkin_id.service_room.id,
    #                 'department_name': walkin_id.service_room.name,
    #                 'services': services,
    #                 'link_detail': record_url
    #             })
    #         return valid_response(data)

    # @validate_token
    # @http.route("/api/v1/cases", type="http", auth="none", methods=["GET"], csrf=False)
    # def get_cases(self, **payload):
    #     """ API Lấy danh sách case của khách hàng"""
    #     if payload.get("phone", None):
    #         phones = [payload.get("phone")]
    #         phone_2 = payload.get("phone_2", None)
    #         phone_3 = payload.get("phone_3", None)
    #         offset = int(payload.get("offset")) if payload.get("offset") else 0
    #         limit = int(payload.get("limit")) if payload.get("limit") else 5
    #
    #         if phone_2:
    #             phones.append(payload.get("phone_2"))
    #         if phone_3:
    #             phones.append(payload.get("phone_3"))
    #
    #         domain = [('active', '=', True), ('phone', 'in', phones)]
    #         partners = request.env['res.partner'].search(domain, limit=10)
    #
    #         # cases = []
    #         # for partner in partners:
    #         #     for crm_case_id in partner.crm_case_ids:
    #         #         cases.append({
    #         #             'id': crm_case_id.id,
    #         #             'code': crm_case_id.code,
    #         #             'name': crm_case_id.name,
    #         #             'user_id': crm_case_id.user_id.id,
    #         #             'user_name': crm_case_id.user_id.name,
    #         #             'create_on': crm_case_id.create_on.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
    #         #             'write_date': crm_case_id.write_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
    #         #         })
    #
    #         p = []
    #         for rec in partners:
    #             p.append(rec.id)
    #         domain_c = [('crm_case.partner_id', 'in', p)]
    #
    #         cases = request.env['crm.content.complain'].search_read(domain=domain_c,
    #                                                     fields=['id', 'crm_case', 'complain_id', 'stage', 'priority', 'create_date'],
    #                                                     limit=limit, offset=offset, order='create_date desc')
    #
    #         data = []
    #
    #         case_action_id = request.env.ref('crm_base.action_complain_case_view').id
    #         case_menu_id = request.env.ref('crm_base.crm_menu_case').id
    #
    #         for case in cases:
    #             # get stage
    #             if case['stage'] == 'new':
    #                 stage = 'Mới'
    #             elif case['stage'] == 'processing':
    #                 stage = 'Đang xử trí'
    #             elif case['stage'] == 'finding':
    #                 stage = 'Tìm thêm thông tin'
    #             elif case['stage'] == 'waiting_response':
    #                 stage = 'Chờ phản hồi'
    #             elif case['stage'] == 'need_to_track':
    #                 stage = 'Cần theo dõi'
    #             elif case['stage'] == 'resolve':
    #                 stage = 'Giải quyết'
    #             else:
    #                 stage = 'Hoàn thành'
    #
    #             # get priority
    #             if case['priority'] == '0':
    #                 priority = 'Thấp'
    #             elif case['priority'] == '1':
    #                 priority = 'Bình thường'
    #             elif case['priority'] == '2':
    #                 priority = 'Cao'
    #             else:
    #                 priority = 'Khẩn cấp'
    #
    #             record_url = get_url_base() + "/web#id=%d&action=%d&model=crm.case&view_type=form&menu_id=%d" % (
    #                 int(case['crm_case'][0]),
    #                 case_action_id, case_menu_id)
    #             data.append({
    #                 'id': case['id'] if case['id'] else None,
    #                 'name': case['complain_id'][1] if case['complain_id'] else None,
    #                 'stage': stage if stage else None,
    #                 'priority': priority if priority else None,
    #                 'case_url': record_url,
    #                 'create_date': case['create_date'].strftime(DEFAULT_SERVER_DATETIME_FORMAT),
    #             })
    #         return valid_response(data)

    # @validate_token
    # @http.route("/api/v1/loyalty", type="http", auth="none", methods=["GET"], csrf=False)
    # def get_loyalty(self, **payload):
    #     """ API thông tin thẻ thành viên của khách hàng"""
    #     if payload.get("phone", None):
    #         phones = [payload.get("phone")]
    #         phone_2 = payload.get("phone_2", None)
    #         phone_3 = payload.get("phone_3", None)
    #         # offset = int(payload.get("offset")) if payload.get("offset") else 0
    #         # limit = int(payload.get("limit")) if payload.get("offset") else 10
    #         if phone_2:
    #             phones.append(payload.get("phone_2"))
    #         if phone_3:
    #             phones.append(payload.get("phone_3"))
    #
    #         domain = [('active', '=', True), ('phone', 'in', phones)]
    #         partners = request.env['res.partner'].search(domain, limit=10)
    #         data = []
    #         for partner in partners:
    #             # Thẻ thành viên loyalty_card_ids   crm.loyalty.card
    #             for loyalty_card_id in partner.loyalty_card_ids:
    #                 for reward_id in loyalty_card_id.reward_ids:
    #                     if reward_id.stage == 'allow':
    #                         data.append({
    #                             'reward_name': reward_id.name,
    #                             'stage': 'Được sử dụng',
    #                             'expiration_date': loyalty_card_id.due_date,
    #                         })
    #         return valid_response(data)
