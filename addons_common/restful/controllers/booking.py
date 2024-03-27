"""Part of odoo. See LICENSE file for full copyright and licensing details."""
import logging
from datetime import datetime, date, timedelta
from odoo.exceptions import AccessError, MissingError, ValidationError, UserError
from odoo import http
from odoo.addons.restful.common import (
    invalid_response,
    valid_response,
    valid_response_once,
)
from odoo.addons.restful.controllers.main import (
    get_url_base,
    validate_token
)
from odoo.http import request

_logger = logging.getLogger(__name__)


def create_log(model_name, input, id_record, response, type_log, name_log, status_code, url, header):
    model = request.env['ir.model'].sudo().search([('model', '=', model_name)])
    if model:
        request.env['api.log'].sudo().create({
            "name": name_log,
            "type_log": type_log,
            "model_id": model.id,
            "id_record": id_record,
            "input": input,
            "response": response,
            "url": url,
            "status_code": status_code,
            "header": header,
        })


class BookingController(http.Controller):

    @validate_token
    @http.route("/api/v1/booking/<id>", type="http", auth="none", methods=["GET"], csrf=False)
    def get_booking_by_id(self, id=None, **payload):
        """ API 3.4 lấy thông tin booking qua id của booking"""

        try:
            _id = int(id)
        except Exception as e:
            return invalid_response("invalid object id", "invalid literal %s for id with base " % id)

        domain = [("id", "=", _id), ('type', '=', 'opportunity')]
        record = request.env['crm.lead'].search(domain)
        data = {}
        booking_action_id = request.env.ref('crm.crm_lead_action_pipeline').id
        booking_menu_id = request.env.ref('crm.crm_menu_root').id
        if record:
            data['id'] = record.id
            data[
                'link_booking_detail'] = get_url_base() + "/web#id=%d&model=crm.lead&view_type=form&action=%d&menu_id=%d" % (
                record.id,
                booking_action_id, booking_menu_id)
            data['name'] = record.name
            data['contact_name'] = record.contact_name
            data['gender'] = record.gender
            data['pass_port'] = record.pass_port
            data['phone'] = record.phone
            data['mobile'] = record.mobile
            data['birth_date'] = record.birth_date
            data['year_of_birth'] = record.year_of_birth
            data['email_from'] = record.email_from
            data['country_id'] = record.country_id.id
            data['country_name'] = record.country_id.name
            data['state_id'] = record.state_id.id
            data['state_name'] = record.state_id.name
            data['district_id'] = record.district_id.id
            data['district_name'] = record.district_id.name
            data['street'] = record.street
            data['company_id'] = record.company_id.id
            data['company_name'] = record.company_id.name
            data['facebook_acc'] = record.facebook_acc
            data['send_info_facebook'] = record.send_info_facebook
            data['zalo_acc'] = record.zalo_acc
            data['send_info_zalo'] = record.send_info_zalo
            data['brand_id'] = record.brand_id.id
            data['brand_name'] = record.brand_id.name
            data['price_list_id'] = record.price_list_id.id
            data['price_list_name'] = record.price_list_id.name
            data['category_source_id'] = record.category_source_id.id
            data['category_source_name'] = record.category_source_id.name
            data['overseas_vietnamese'] = record.overseas_vietnamese
            data['work_online'] = record.work_online
            data['online_counseling'] = record.work_online
            data['shuttle_bus'] = record.work_online
            data['campaign_id'] = record.campaign_id.id
            data['campaign_name'] = record.campaign_id.name
            data['amount_total'] = record.amount_total
            data['create_on'] = record.create_on
            crm_line_ids = []
            for line in record.crm_line_ids:
                if record.brand_id.code == "HV":
                    crm_line_ids.append({
                        'id': line.id,
                        'service_id': line.course_id.id,
                        'course_name': line.course_id.name,
                        'quantity': line.quantity,
                        'source_extend_id': line.source_extend_id.id,
                        'source_extend_name': line.source_extend_id.name,
                    })
                else:
                    crm_line_ids.append({
                        'id': line.id,
                        'service_id': line.service_id.id,
                        'service_name': line.service_id.name,
                        'quantity': line.quantity,
                        'source_extend_id': line.source_extend_id.id,
                        'source_extend_name': line.source_extend_id.name,
                    })
            data['crm_line_ids'] = crm_line_ids
        if data:
            return valid_response(data)
        else:
            return valid_response(data)

    @validate_token
    @http.route("/api/v1/booking-name/<name>", type="http", auth="none", methods=["GET"], csrf=False)
    def get_booking_by_name(self, name=None, **payload):
        """ API 3.4 lấy thông tin booking qua name của booking"""

        try:
            _name = name
        except Exception as e:
            return invalid_response("invalid object name", "invalid literal %s for id with base " % name)

        domain = [("name", "=", _name), ('type', '=', 'opportunity')]
        record = request.env['crm.lead'].search(domain)
        data = {}
        booking_action_id = request.env.ref('crm.crm_lead_action_pipeline').id
        booking_menu_id = request.env.ref('crm.crm_menu_root').id
        if record:
            data['id'] = record.id
            data[
                'link_booking_detail'] = get_url_base() + "/web#id=%d&model=crm.lead&view_type=form&action=%d&menu_id=%d" % (
                record.id,
                booking_action_id, booking_menu_id)
            data['name'] = record.name
            data['contact_name'] = record.contact_name
            data['gender'] = record.gender
            data['pass_port'] = record.pass_port
            data['phone'] = record.phone
            data['mobile'] = record.mobile
            data['birth_date'] = record.birth_date
            data['year_of_birth'] = record.year_of_birth
            data['email_from'] = record.email_from
            data['country_id'] = record.country_id.id
            data['country_name'] = record.country_id.name
            data['state_id'] = record.state_id.id
            data['state_name'] = record.state_id.name
            data['district_id'] = record.district_id.id
            data['district_name'] = record.district_id.name
            data['street'] = record.street
            data['company_id'] = record.company_id.id
            data['company_name'] = record.company_id.name
            data['facebook_acc'] = record.facebook_acc
            data['send_info_facebook'] = record.send_info_facebook
            data['zalo_acc'] = record.zalo_acc
            data['send_info_zalo'] = record.send_info_zalo
            data['brand_id'] = record.brand_id.id
            data['brand_name'] = record.brand_id.name
            data['price_list_id'] = record.price_list_id.id
            data['price_list_name'] = record.price_list_id.name
            data['category_source_id'] = record.category_source_id.id
            data['category_source_name'] = record.category_source_id.name
            data['overseas_vietnamese'] = record.overseas_vietnamese
            data['work_online'] = record.work_online
            data['online_counseling'] = record.work_online
            data['shuttle_bus'] = record.work_online
            data['campaign_id'] = record.campaign_id.id
            data['campaign_name'] = record.campaign_id.name
            data['amount_total'] = record.amount_total
            data['create_on'] = record.create_on
            crm_line_ids = []
            for line in record.crm_line_ids:
                if record.brand_id.code == "HV":
                    crm_line_ids.append({
                        'id': line.id,
                        'service_id': line.course_id.id,
                        'course_name': line.course_id.name,
                        'source_extend_id': line.source_extend_id.id,
                        'source_extend_name': line.source_extend_id.name,
                    })
                else:
                    crm_line_ids.append({
                        'id': line.id,
                        'service_id': line.service_id.id,
                        'service_name': line.service_id.name,
                        'quantity': line.quantity,
                        'source_extend_id': line.source_extend_id.id,
                        'source_extend_name': line.source_extend_id.name,
                    })
            data['crm_line_ids'] = crm_line_ids
        if data:
            return valid_response(data)
        else:
            return invalid_response("Booking not found", "Booking %s not found in system" % _name)

    @validate_token
    @http.route("/api/v1/booking", type="http", auth="none", methods=["POST"], csrf=False)
    def create_booking(self, **payload):
        """ API 1.13 tạo booking"""
        """
            payload={
                'country_id': '1',
                'state_id': '1',
                'company_id': '2',
                'price_list_id': '1',
                'category_source_id': '1',
                'source_id': '1',
                'campaign_id': '22',
                'crm_line_ids': '[28546,28547,28548]',
                'email_from': 'sondoan_026',
                'facebook_acc': 'abc',
                'zalo_acc': '1111',
                'send_info_facebook': 'sent',
                'send_info_zalo': 'sent',
                'overseas_vietnamese': 'no',
                'work_online': 'no',
                'booking_date': '2021-08-31',
                'online_counseling': 'yes',
                'shuttle_bus': 'no',
                'account_id': '514433',
                'phone_no1': '0363788103',
                'phone_no2': '0363788101',
                'phone_no3': '0363788102',
                'contact_name': 'Nguyễn Văn A',
                'gender': 'male',
            }
        """

        values = {}

        # get brand
        brand_id = request.brand_id
        brand_code = request.brand_code
        # check các trường require
        field_require = [
            'contact_name',
            'gender',
            'company_id',
            'source_id',
            'price_list_id',
            'crm_line_ids',
            'booking_date',
        ]

        location_unknow = ['KN.KXD.00', 'DA.KXD.00', 'PR.KXD.00', 'HH.KXD.00']
        for field in field_require:
            if field not in payload.keys():
                return invalid_response(
                    "Missing",
                    "The parameter %s is missing!!!" % field)

        # try:
        if 1 == 1:
            # changing IDs from string to int.
            for k, v in payload.items():
                values[k] = v
            # require check company_id & set brand_id
            if 'company_id' in values:
                if values['company_id'] in location_unknow:
                    return invalid_response("Chọn sai công ty",
                                            "Khi tạo Booking không chọn chi nhánh không xác định !!!")
                else:
                    company = request.env['res.company'].search(
                        [('code', '=', values['company_id']), ('brand_id', '=', brand_id)])
                    if company:
                        values['company_id'] = company.id
                        values['brand_id'] = brand_id
                    else:
                        return invalid_response("Code Company not found",
                                                "The Code %s not found in system !!!" % values['company_id'])

            # ghi nhận data chưa xử lý từ CS
            values_cs = values.copy()

            # check user tạo lead + bk
            user = request.env['res.users'].search([('login', '=', values['agent_email'])])
            if user:
                values['create_by'] = user.id
                values['assign_person'] = user.id
            else:
                user = request.env.user
            # check booking_date
            if 'booking_date' in values and values['booking_date']:
                year_booking_date = values['booking_date'].split("-")[0]
                if int(year_booking_date) < 1900:
                    return invalid_response("Invalid Booking Date",
                                            "Booking date %s is invalid !!!" % values['booking_date'])
                else:
                    booking_date = datetime.strptime(values['booking_date'], '%Y-%m-%d %H:%M')
                    booking_date = booking_date - timedelta(hours=7, minutes=00)
                    if booking_date.hour == 17:
                        booking_date = booking_date + timedelta(hours=9, minutes=00)
                    if booking_date.date() < datetime.now().date():
                        return invalid_response("Invalid Booking Date",
                                                "Ngày hẹn lịch không được phép nhỏ hơn ngày hiện tại !!!")
                    values['booking_date'] = booking_date

            # chân dung khách hàng
            customer_portrait_partner = dict()

            check_vn = True
            # check country
            if 'country_id' in values and values['country_id']:
                country = request.env['res.country'].search([('id', '=', values['country_id'])], limit=1)
                if country:
                    values['country_id'] = int(values['country_id'])
                    customer_portrait_partner['country_id'] = values['country_id']
                    if country.code != 'VN':
                        check_vn = False
                else:
                    return invalid_response("ID Country not found",
                                            "The ID %s not found in system !!!" % int(values['country_id']))
            else:
                country = request.env['res.country'].search([('name', '=', 'Việt nam')], limit=1)
                if country:
                    values['country_id'] = country.id

            # check state_id
            if 'state_id' in values and values['state_id']:
                state = request.env['res.country.state'].search([('cs_id', '=', int(values['state_id']))], limit=1)
                if state:
                    values['state_id'] = state.id
                    customer_portrait_partner['state_id'] = values['state_id']
                else:
                    return invalid_response("ID State not found",
                                            "The ID CS %s not found in system !!!" % int(values['state_id']))
            else:
                values['state_id'] = False

            # check district_id
            if 'district_id' in values and values['district_id']:
                district = request.env['res.country.district'].search([('cs_id', '=', int(values['district_id']))],
                                                                      limit=1)
                if district:
                    values['district_id'] = district.id
                    customer_portrait_partner['district_id'] = values['district_id']
                else:
                    return invalid_response("ID District not found",
                                            "The ID CS %s not found in system !!!" % int(values['district_id']))
            else:
                values['state_id'] = False
            # =================================== check partner ======================================================
            if 'customer_portrait' in values and values['customer_portrait']:
                partner = request.env['res.partner'].search([('phone', '=', values['phone_no1'])])
                pp_ds_check = partner.pain_point_and_desires.mapped('name')
                customer_portrait = eval(values['customer_portrait'])
                if 'hobby' in customer_portrait and len(customer_portrait['hobby']):
                    list_hobby = []
                    for rec in customer_portrait['hobby']:
                        hobby = request.env['hobbies.interest'].sudo().search([('name', '=', rec.lower())])
                        if hobby:
                            list_hobby.append(hobby.id)
                        else:
                            hobby = request.env['hobbies.interest'].sudo().create({
                                'name': rec.lower(),
                                'desc': rec.lower(),
                            })
                            list_hobby.append(hobby.id)
                    customer_portrait_partner['hobby'] = list_hobby
                if 'desires' in customer_portrait and customer_portrait['desires']:
                    list_desire = []
                    for desire in customer_portrait['desires']:
                        if desire and desire.lower() not in pp_ds_check:
                            list_desire.append((0, 0, {
                                'name': desire.lower(),
                                'type': 'desires',
                                'create_by': user.id,
                                'create_on': datetime.now(),
                                'phone': values['phone_no1'] if values['phone_no1'] else False
                            }))
                        values['desires'] = list_desire
                    customer_portrait_partner['desires'] = list_desire
                if 'pain_point' in customer_portrait and len(customer_portrait['pain_point']):
                    list_pain_point = []
                    for point in customer_portrait['pain_point']:
                        if point and point not in pp_ds_check:
                            list_pain_point.append((0, 0, {
                                'name': point.lower(),
                                'type': 'pain_point',
                                'create_by': user.id,
                                'create_on': datetime.now(),
                                'phone': values['phone_no1'] if values['phone_no1'] else False
                            }))
                        values['pain_point'] = list_pain_point
                        customer_portrait_partner['pain_point'] = list_pain_point
            # -----------------------------
            # check phone_no1
            if 'phone_no1' in values and values['phone_no1']:
                if values['phone_no1'].isdigit() is False:
                    return invalid_response("Loi SDT", "SDT khach hang chi nhan gia tri so")
                if check_vn:
                    if (10 > len(values['phone_no1'])) or (len(values['phone_no1']) > 10):
                        return invalid_response("Loi SDT", "SDT VN chi chap nhan 10 ki tu")

            # add year of birth
            if 'birth_date' in values:
                if values['birth_date']:
                    year_birth_date = values['birth_date'].split('-')[0]
                    if int(year_birth_date) < 1900:
                        return invalid_response("Invalid Birth date",
                                                "The Birth date %s is invalid !!!" % values['birth_date'])
                    else:
                        if int(values['birth_date'].split('-', 1)[0]) < date.today().year:
                            values['year_of_birth'] = values['birth_date'].split('-', 1)[0]
                            customer_portrait_partner['birth_date'] = values['birth_date']
                            customer_portrait_partner['year_of_birth'] = values['birth_date'].split('-', 1)[0]
                        else:
                            values.pop('birth_date')
                            return invalid_response("Năm sinh không hợp lệ", "Năm sinh phải nhỏ hơn năm hiện tại")
                else:
                    values.pop('birth_date')
            # check phone_no2
            if 'phone_no2' in values and values['phone_no2']:
                values['mobile'] = values['phone_no2']
            else:
                values['mobile'] = False

            # check phone_no3
            if 'phone_no3' in values and values['phone_no3']:
                values['phone_no_3'] = values['phone_no3']
            else:
                values['phone_no_3'] = False

            # require check source_id
            if 'source_id' in values and values['source_id']:
                field_id_cs_source = "id" + "_" + "%s" % (brand_code.lower())
                domain = [(field_id_cs_source, '=', int(values['source_id'])), ('brand_id.code', '=', brand_code)]
                source = request.env['utm.source'].search(domain, limit=1)
                if source:
                    values['source_id'] = source.id
                    values['category_source_id'] = source.category_id.id
                else:
                    return invalid_response("ID Source CS not found",
                                            "The ID CS %s not found in system !!!" % int(values['source_id']))

            # tìm chân dung
            pain_point = request.env['pain.point.and.desires'].search(
                [('phone', '=', values['phone_no1']), ('partner_id', '=', False)])
            partner = request.env['res.partner'].search([('phone', '=', values['phone_no1'])])
            if pain_point and partner:
                for pain in pain_point:
                    pain.write({
                        'partner_id': partner.id,
                    })

            # tạo acc
            if 'account_id' in values and values['account_id']:
                partner = request.env['res.partner'].search([('id', '=', values['account_id'])])
                if partner:
                    values['partner_id'] = partner.id
                    values['contact_name'] = partner.name
                    values['gender'] = partner.gender if partner.gender else values['gender']
                    values['phone'] = partner.phone
                    values['original_source_id'] = partner.source_id.id if partner.source_id else values['source_id']
                    if 'customer_portrait' in values and values['customer_portrait']:
                        partner.sudo().write(customer_portrait_partner)
            else:
                if 'phone_no1' in values:
                    partner = request.env['res.partner'].search([('phone', '=', values['phone_no1'])])
                    if partner:
                        values['partner_id'] = partner.id
                        values['original_source_id'] = partner.source_id.id if partner.source_id else values[
                            'source_id']
                        values['gender'] = partner.gender if partner.gender else values['gender']
                        if partner.type_data_partner == 'new':
                            if partner.sudo().sale_order_ids:
                                for rec in partner.sudo().sale_order_ids:
                                    if rec.state in ['sale', 'done']:
                                        customer_portrait_partner['type_data_partner'] = 'old'
                                        break
                        elif not partner.type_data_partner:
                            if partner.sudo().sale_order_ids:
                                for rec in partner.sudo().sale_order_ids:
                                    if rec.state in ['sale', 'done']:
                                        customer_portrait_partner['type_data_partner'] = 'old'
                                        break
                                    else:
                                        customer_portrait_partner['type_data_partner'] = 'new'
                            else:
                                customer_portrait_partner['type_data_partner'] = 'new'
                        else:
                            customer_portrait_partner['type_data_partner'] = 'old'
                        partner.sudo().write(customer_portrait_partner)
                        values['type_data_partner'] = partner.type_data_partner
                    else:
                        customer_portrait_partner['name'] = values['contact_name']
                        customer_portrait_partner['phone'] = values['phone_no1']
                        customer_portrait_partner['mobile'] = values['phone_no2']
                        customer_portrait_partner['phone_no_3'] = values['phone_no3']
                        customer_portrait_partner['gender'] = values['gender']
                        customer_portrait_partner['source_id'] = values['source_id']
                        customer_portrait_partner['customer_rank'] = 1
                        customer_portrait_partner['code_customer'] = request.env['ir.sequence'].next_by_code(
                            'res.partner')
                        customer_portrait_partner['type_data_partner'] = 'new'
                        partner = request.env['res.partner'].with_user(user.id).sudo().create(customer_portrait_partner)
                        values['partner_id'] = partner.id
                        values['type_data_partner'] = 'new'
                        values['original_source_id'] = partner.source_id.id if partner.source_id else values[
                            'source_id']
            # =============================== chech values ============================================================

            # require check price_list_id
            if 'price_list_id' in values and brand_code.lower() != 'hh':
                price_list = request.env['product.pricelist'].search(
                    [('id', '=', values['price_list_id']), ('brand_id', '=', brand_id)])
                if price_list:
                    values['price_list_id'] = int(values['price_list_id'])
                else:
                    return invalid_response("ID Price list not found",
                                            "The ID %s not found in system !!!" % int(values['price_list_id']))

            # check product_category_ids
            if 'product_category_ids' in values:
                if values['product_category_ids'] and brand_code.lower() == 'hh':
                    product_category_ids = eval(values['product_category_ids'])
                    list_product_category_id = []
                    for rec in product_category_ids:
                        prd_cate = request.env['product.category'].search(
                            [('brand_id', '=', brand_id), ('code', '=', rec)])
                        if prd_cate:
                            list_product_category_id.append(prd_cate.id)
                        else:
                            return invalid_response("Code Service Category not found",
                                                    "The Code Service Category %s not found in system !!!" % rec)
                    values.pop('product_category_ids')
                    values['product_category_ids'] = list_product_category_id
                else:
                    values.pop('product_category_ids')

            # require check crm_line_ids
            if 'crm_line_ids' in values and values['crm_line_ids']:
                crm_line_ids = eval(values['crm_line_ids'])
                list_product = []
                for line in crm_line_ids:
                    # search service
                    service = request.env['sh.medical.health.center.service'].search([('product_id', '=', line)])
                    # search item_price
                    item_price = request.env['product.pricelist.item'].search(
                        [('pricelist_id', '=', values['price_list_id']), ('product_id', '=', line)])
                    if service:
                        list_product.append((0, 0, {
                            'service_id': service.id,
                            'product_id': line,
                            'unit_price': item_price.fixed_price,
                            'quantity': 1,
                            'company_id': values['company_id'],
                            'price_list_id': values['price_list_id'],
                            'source_extend_id': values['source_id'],
                            'status_cus_come': 'no_come',
                            'line_booking_date': values['booking_date'],
                            'consultants_1': user.id,
                            # 'create_uid': user.id,
                        }))
                    else:
                        return invalid_response("ID Service not found",
                                                "The ID %s not found in system !!!" % int(line))
                values['crm_line_ids'] = list_product

            # check campaign_id
            if 'campaign_id' in values:
                if values['campaign_id']:
                    campaign = request.env['utm.campaign'].browse(values['campaign_id'])
                    if campaign:
                        values['campaign_id'] = int(values['campaign_id'])
                    else:
                        return invalid_response("ID Campaign not found",
                                                "The ID %s not found in system !!!" % int(values['campaign_id']))
                else:
                    values.pop('campaign_id')

            # check gclid
            if 'comment' in values:
                if values['comment'] and 'gclid' in values['comment']:
                    values['gclid'] = values['comment'].strip("[gclid]")
                    values.pop('comment')
                else:
                    values.pop('comment')

            # pop stage_id
            if 'stage_id' in values:
                values.pop('stage_id')

            # ========================== check hiệu lực booking ===================================
            booking_effect = request.env['crm.lead'].search(
                [('type', '=', 'opportunity'), ('partner_id', '=', values['partner_id']),
                 ('brand_id', '=', brand_id), ('effect', '=', 'effect')])
            if booking_effect:
                booking_name = []
                for booking in booking_effect:
                    booking_name.append(booking.name)
                return invalid_response("Không thể tạo Booking mới do còn Booking vẫn còn hiêu lực",
                                        "Hãy vào Booking có mã %s của thương hiệu %s để thao tác tiếp" % (
                                            ','.join(booking_name), booking_effect.brand_id.name))
            else:
                # ============================ tạo lead ===============================================================
                values_lead = values.copy()
                # check type_data
                lead = request.env['crm.lead'].search(
                    [('partner_id', '=', values_lead['partner_id']), ('type', '=', 'lead'),
                     ('brand_id', '=', brand_id)], limit=1)
                if lead:
                    values_lead['type_data'] = 'old'
                else:
                    values_lead['type_data'] = 'new'

                # set type = lead, phone
                values_lead['type'] = 'lead'
                values_lead['name'] = values_lead['contact_name']
                values_lead['type_crm_id'] = request.env.ref('crm_base.type_lead_new').id
                values_lead['stage_id'] = request.env.ref('crm_base.crm_stage_booking').id

                # check ngày cấp CMND
                if 'pass_port_date' in values_lead and values_lead['pass_port_date']:
                    values_lead['pass_port_date'] = datetime.strptime(values['pass_port_date'], '%Y-%m-%d')
                else:
                    values_lead['pass_port_date'] = False

                # loại bỏ trường ko dùng
                # TODO: xử lý các trường thông tin chưa dùng tới ở dưới
                if 'account_id' in values_lead:
                    values_lead.pop('account_id')
                if 'phone_no1' in values_lead:
                    values_lead.pop('phone_no1')
                if 'phone_no2' in values_lead:
                    values_lead.pop('phone_no2')
                if 'phone_no3' in values_lead:
                    values_lead.pop('phone_no3')
                if 'agent_email' in values_lead:
                    values_lead.pop('agent_email')
                if 'booking_date' in values_lead:
                    values_lead.pop('booking_date')
                if 'customer_portrait' in values_lead:
                    values_lead.pop('customer_portrait')
                if 'mobile' in values_lead:
                    values_lead.pop('mobile')
                if 'reason_not_booking_date' in values_lead:
                    values_lead.pop('reason_not_booking_date')
                if 'aliases' in values_lead:
                    values_lead.pop('aliases')
                if 'user_seeding_code' in values_lead:
                    values_lead.pop('user_seeding_code')
                if 'user_ctv_code' in values_lead:
                    values_lead.pop('user_ctv_code')
                if 'seminar_customer' in values_lead:
                    values_lead['seminar_customers'] = values_lead['seminar_customer']
                    values_lead.pop('seminar_customer')

                # ghi nhận booking seeding
                user_seeding = False
                if 'user_seeding_code' in values and values['user_seeding_code']:
                    user_seeding = request.env['seeding.user'].sudo().search(
                        [('code_user', '=', values['user_seeding_code'])])
                    if not user_seeding:
                        return invalid_response("Lỗi",
                                                "Không tìm thấy User seeding có mã %s" % values[
                                                    'user_seeding_code'])
                # tạo lead
                _logger.info('========================= create lead ==================================================')
                _logger.info(values_lead)
                _logger.info('========================================================================================')
                record_lead = request.env['crm.lead'].with_user(user.id).sudo().create(values_lead)
                if record_lead:
                    create_log(model_name=record_lead._name, input=values_cs, id_record=record_lead.id,
                               response=False,
                               type_log=str(0),
                               name_log='Tạo lead từ CS',
                               url=False,
                               header=False, status_code=False)

                # tạo booking
                _logger.info('===================== create booking ===================================================')
                record_booking_qualify = request.env['check.partner.qualify'].sudo().create({
                    'name': 'test',
                    'phone': record_lead.phone,
                    'booking_date': values['booking_date'],
                    'lead_id': record_lead.id,
                    'company_id': record_lead.company_id.id,
                    'type': 'opportunity',
                    'partner_id': values['partner_id']
                })
                try:
                    record = record_booking_qualify.with_user(user.id).sudo().qualify()
                    record_booking = request.env['crm.lead'].browse(record['res_id'])
                    if record_booking:
                        create_log(model_name=record_booking._name, input=values_cs, id_record=record_booking.id,
                                   response=False,
                                   type_log=str(0),
                                   name_log='Tạo BK từ CS',
                                   url=False,
                                   header=False, status_code=False)
                    # ============== trả ouput ===========================
                    data = {}
                    if record_booking:
                        record_booking.sudo().write({
                            'ticket_id': values['ticket_id']
                        })
                        if user_seeding:
                            record_seeding_booking = request.env['seeding.booking'].sudo().create({
                                'crm_id': record_booking.id,
                                'seeding_user_id': user_seeding.id,
                            })

                        customer_portrait = {}
                        customer_portrait[
                            'revenue_source'] = record_booking.partner_id.revenue_source if record_booking.partner_id.revenue_source else None
                        customer_portrait[
                            'term_goals'] = record_booking.partner_id.term_goals if record_booking.partner_id.term_goals else None
                        customer_portrait[
                            'social_influence'] = record_booking.partner_id.social_influence if record_booking.partner_id.social_influence else None
                        customer_portrait[
                            'behavior_on_the_internet'] = record_booking.partner_id.behavior_on_the_internet if record_booking.partner_id.behavior_on_the_internet else None
                        customer_portrait[
                            'affected_by'] = record_booking.partner_id.affected_by if record_booking.partner_id.affected_by else None
                        customer_portrait[
                            'work_start_time'] = record_booking.partner_id.work_start_time if record_booking.partner_id.work_start_time else None
                        customer_portrait[
                            'work_end_time'] = record_booking.partner_id.work_end_time if record_booking.partner_id.work_end_time else None
                        customer_portrait[
                            'break_start_time'] = record_booking.partner_id.break_start_time if record_booking.partner_id.break_start_time else None
                        customer_portrait[
                            'break_end_time'] = record_booking.partner_id.break_end_time if record_booking.partner_id.break_end_time else None
                        customer_portrait[
                            'transport'] = record_booking.partner_id.transport if record_booking.partner_id.transport else None
                        if record_booking.partner_id.hobby:
                            list_hobby = []
                            for rec in record_booking.partner_id.hobby:
                                list_hobby.append(rec.name)
                            customer_portrait['hobby'] = list_hobby
                        if record_booking.partner_id.pain_point:
                            list_pain_point = []
                            for point in record_booking.partner_id.pain_point:
                                list_pain_point.append(point.name)
                            customer_portrait['pain_point'] = list_pain_point
                        if record_booking.partner_id.desires:
                            list_desires = []
                            for desire in record_booking.partner_id.desires:
                                list_desires.append(desire.name)
                            customer_portrait['desires'] = list_desires

                        booking_action_id = request.env.ref('crm.crm_lead_action_pipeline').id
                        booking_menu_id = request.env.ref('crm.crm_menu_root').id
                        data['account_id'] = record_booking.partner_id.id
                        data['customer_portrait'] = customer_portrait
                        data['id_booking'] = record_booking.id
                        data[
                            'link_booking_detail'] = get_url_base() + "/web#id=%d&model=crm.lead&view_type=form&action=%d&menu_id=%d" % (
                            record_booking.id,
                            booking_action_id, booking_menu_id)
                    return valid_response_once(data)
                except Exception as e:
                    return invalid_response("Lỗi", e)
# except Exception as e:
#     request.env.cr.rollback()
#     return invalid_response("params", e)
