"""Part of odoo. See LICENSE file for full copyright and licensing details."""
import logging
from datetime import datetime, date

from odoo import http
from odoo.addons.restful.common import (
    invalid_response,
    valid_response_once,
)
from odoo.addons.restful.controllers.main import (
    get_url_base,
    validate_token
)
from odoo.http import request

_logger = logging.getLogger(__name__)


class LeadController(http.Controller):

    @validate_token
    @http.route("/api/v1/lead", type="http", auth="none", methods=["POST"], csrf=False)
    def create_lead(self, **payload):
        """ API 2.1 Tạo lead"""
        """
            payload = {   
                'country_id': '241',
                'state_id': '',
                'company_id': '2',
                'price_list_id': '14',
                'category_source_id': '21',
                'source_id': '178',
                'campaign_id': '7',
                'crm_line_ids': '[12553,12554]',
                'email_from': 'sondoan_026',
                'facebook_acc': '',
                'zalo_acc': '',
                'send_info_facebook': 'sent',
                'send_info_zalo': 'sent',
                'overseas_vietnamese': 'no',
                'work_online': '',
                'online_counseling': '',
                'shuttle_bus': '',
                'account_id': '80806',
                'phone_no1': '096801111110111',
                'phone_no2': '1',
                'contact_name': 'mimi111',
                'gender': 'male',
                'account_id': '',
                'ticket_id': '229149',
                'agent_email': 'chinh@scigroup.com.vn',
                'district_id': '',
                'birth_date': '',
                'street': '',
                'email_from': '',
                'customer_portrait': {
                            'hobby':[2,4],
                            'revenue_source':10000,
                            'term_goals':'test',
                            'social_influence':'test',
                            'behavior_on_the_internet':'test',
                            'affected_by':'family',
                            'work_start_time':2,
                            'work_end_time':2,
                            'break_start_time':2,
                            'break_end_time':2,
                            'transport':'bicycle',
                            'pain_point':['point 1','point 2'],
                            'desires':['desires 1','desires 2']
                                }
                }
        """
        values = {}

        # get brand
        brand_id = request.brand_id
        brand_type = request.brand_type
        brand_code = request.brand_code
        # check các trường require
        field_require = [
            'contact_name',
            'gender',
            'company_id',
            'category_source_id',
            'source_id',
            'price_list_id',
            # 'crm_line_ids',
        ]
        for rec in field_require:
            if rec not in payload.keys():
                return invalid_response(
                    "Missing",
                    "The parameter %s is missing!!!" % rec)
        # changing IDs from string to int.
        try:
        # if 1 == 1:
            # changing IDs from string to int.
            for k, v in payload.items():
                values[k] = v
            # ghi nhận data chưa xử lý từ CS
            values_cs = values.copy()

            # check user tạo lead
            if 'booking_date' in values and values['booking_date']:
                return invalid_response("Error",
                                        "Tạo Lead không chọn ngày đặt lịch !!!")

            user = request.env['res.users'].search([('login', '=', values['agent_email'])])
            _logger.info("============================== values =======================================")
            _logger.info(values)
            _logger.info("=============================================================================")
            if user:
                values['create_by'] = user.id
                values['assign_person'] = user.id
            # check phone_no2
            if 'phone_no2' in values and values['phone_no2']:
                values['mobile'] = values['phone_no2']
            else:
                values['mobile'] = False

            # check country
            if 'country_id' in values and values['country_id']:
                country = request.env['res.country'].search([('id', '=', values['country_id'])])
                if country:
                    values['country_id'] = int(values['country_id'])
                else:
                    return invalid_response("ID Country not found",
                                            "The ID %s not found in system !!!" % int(values['country_id']))
            else:
                values.pop('country_id')

            # check gclid
            if 'comment' in values:
                if values['comment']:
                    values['gclid'] = values['comment']
                    values.pop('comment')
                else:
                    values.pop('comment')

            # check state_id
            if 'state_id' in values and len(values['state_id']) != 0:
                state = request.env['res.country.state'].search([('cs_id', '=', int(values['state_id']))], limit=1)
                if state:
                    values['state_id'] = state.id
                else:
                    return invalid_response("ID State not found",
                                            "The ID CS %s not found in system !!!" % int(values['state_id']))
            else:
                values.pop('state_id')

            # check district_id
            if 'district_id' in values and len(values['district_id']) != 0:
                district = request.env['res.country.district'].search([('cs_id', '=', int(values['district_id']))],
                                                                      limit=1)
                if district:
                    values['district_id'] = district.id
                else:
                    return invalid_response("ID District not found",
                                            "The ID CS %s not found in system !!!" % int(values['district_id']))
            else:
                values.pop('district_id')

            # require check source_id
            if 'source_id' in values and values['source_id']:
                field_id_cs_source = "id" + "_" + "%s" % (brand_code.lower())
                domain = [(field_id_cs_source, '=', int(values['source_id']))]
                source = request.env['utm.source'].search(domain)
                if source:
                    values['source_id'] = source.id
                    values['category_source_id'] = source.category_id.id
                else:
                    return invalid_response("ID Source CS not found",
                                            "The ID CS %s not found in system !!!" % int(values['source_id']))

            # check customer_portrait
            customer_portrait_partner = dict()
            if 'customer_portrait' in values and len(values['customer_portrait']):
                customer_portrait = eval(values['customer_portrait'])
                if 'pain_point' in customer_portrait and len(customer_portrait['pain_point']):
                    list_pain_point = []
                    for point in customer_portrait['pain_point']:
                        if point:
                            # old_point = request.env['pain.point.and.desires'].sudo().search(
                            #     [('name', '=', point.lower()), ('type', '=', 'pain_point')], limit=1)
                            # if old_point:
                            #     list_pain_point.append((4, old_point.id))
                            # else:
                            list_pain_point.append((0, 0, {
                                'name': point.lower(),
                                'type': 'pain_point',
                                'create_by': user.id,
                                'create_on': datetime.now(),
                                'phone': values['phone_no1'] if values['phone_no1'] else False
                            }))
                        values['pain_point'] = list_pain_point
                        customer_portrait_partner['pain_point'] = list_pain_point

                if 'desires' in customer_portrait and customer_portrait['desires']:
                    list_desire = []
                    for desire in customer_portrait['desires']:
                        if desire:
                            list_desire.append((0, 0, {
                                'name': desire.lower(),
                                'type': 'desires',
                                'create_by': user.id,
                                'create_on': datetime.now(),
                                'phone': values['phone_no1'] if values['phone_no1'] else False
                            }))
                        values['desires'] = list_desire
                        customer_portrait_partner['desires'] = list_desire
                if 'hobby' in customer_portrait and customer_portrait['hobby']:
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
                    values['hobby'] = list_hobby
                    customer_portrait_partner['hobby'] = list_hobby
                values.pop('customer_portrait')

            # =================================== check partner ==============================
            if 'account_id' in values and len(values['account_id']) != 0:
                partner = request.env['res.partner'].search([('id', '=', values['account_id'])])
                if partner:
                    if customer_portrait_partner:
                        partner.sudo().write(customer_portrait_partner)
                    values['partner_id'] = partner.id
                    values['contact_name'] = partner.name
                    values['gender'] = partner.gender if partner.gender else values['gender']
                    values['phone'] = partner.phone
                    values['original_source_id'] = partner.source_id.id if partner.source_id else values['source_id']
                else:
                    values['type_data_partner'] = 'new'
            if 'phone_no1' in values and len(values['phone_no1']) != 0:
                partner = request.env['res.partner'].search([('phone', '=', values['phone_no1'])])
                if partner:
                    if customer_portrait_partner:
                        partner.sudo().write(customer_portrait_partner)
                    values['type_data_partner'] = partner.type_data_partner
                    values['partner_id'] = partner.id
                    values['contact_name'] = partner.name
                    values['gender'] = partner.gender if partner.gender else values['gender']
                    values['phone'] = partner.phone
                    values['original_source_id'] = partner.source_id.id if partner.source_id else values['source_id']
                else:
                    values['type_data_partner'] = 'new'

            # require check company_id & set brand_id
            if 'company_id' in values:
                company = request.env['res.company'].search(
                    [('code', '=', values['company_id']), ('brand_id', '=', brand_id)])
                if company:
                    values['company_id'] = company.id
                    values['brand_id'] = brand_id
                else:
                    return invalid_response("Code Company not found",
                                            "The Code %s not found in system !!!" % values['company_id'])

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
                if len(values['product_category_ids']) and brand_code.lower() == 'hh':
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
            if 'crm_line_ids' in values and len(values['crm_line_ids']) != 0:
                crm_line_ids = eval(values['crm_line_ids'])
                list_product = []
                # check dịch vụ học viện
                if brand_type == 'academy':
                    for line in values['crm_line_ids']:
                        # search service
                        service = request.env['op.course'].search([('product_id', '=', line)])
                        # search item_price
                        item_price = request.env['product.pricelist.item'].search(
                            [('pricelist_id', '=', values['price_list_id']),
                             ('product_id', '=', line)])
                        if service:
                            list_product.append((0, 0, {
                                'course_id': service.id,
                                'product_id': line,
                                'unit_price': item_price.fixed_price,
                                'quantity': 1,
                                'company_id': values['company_id'],
                                'price_list_id': values['price_list_id'],
                                'source_extend_id': values['source_id'],
                            }))
                        else:
                            return invalid_response("ID Service not found",
                                                    "The ID %s not found in system !!!" % int(line))

                else:
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
                                'consultants_1': user.id,
                            }))
                        else:
                            return invalid_response("ID Service not found",
                                                    "The ID %s not found in system !!!" % int(line))
                values['crm_line_ids'] = list_product

            if 'campaign_id' in values:
                if len(values['campaign_id']) != 0:
                    campaign = request.env['utm.campaign'].browse(values['campaign_id'])
                    if campaign:
                        values['campaign_id'] = int(values['campaign_id'])
                    else:
                        return invalid_response("ID Campaign not found",
                                                "The ID %s not found in system !!!" % int(values['campaign_id']))
                else:
                    values.pop('campaign_id')

            # add year of birth
            if 'birth_date' in values and len(values['birth_date']) > 0:
                year_birth_date = values['birth_date'].split('-')[0]
                if int(year_birth_date) < 1900:
                    return invalid_response("Invalid Birth date",
                                            "The Birth date %s is invalid !!!" % values['birth_date'])
                else:
                    if int(values['birth_date'].split('-', 1)[0]) < date.today().year:
                        values['year_of_birth'] = values['birth_date'].split('-', 1)[0]
                    else:
                        values.pop('birth_date')
                        return invalid_response("Năm sinh không hợp lệ", "Năm sinh phải nhỏ hơn năm hiện tại")
            else:
                values.pop('birth_date')

            # check stage
            if 'stage_id' in values and values['stage_id']:
                stage = request.env['crm.stage'].search([('name', '=', values['stage_id'])])
                if stage:
                    values['stage_id'] = stage.id
                else:
                    values['stage_id'] = False
            else:
                values['stage_id'] = False

            # check type_data
            domain = [('type', '=', 'lead'), ('brand_id', '=', brand_id)]
            if 'account_id' in values and len(values['account_id']) != 0:
                domain += [('partner_id', '=', values['partner_id'])]
            else:
                domain += [('phone', '=', values['phone_no1'])]
                values['phone'] = values['phone_no1']
            lead = request.env['crm.lead'].search(domain, limit=1)
            if lead:
                values['type_data'] = 'old'
            else:
                values['type_data'] = 'new'

            # set type = lead, phone
            values['type'] = 'lead'
            values['type_crm_id'] = request.env.ref('crm_base.type_lead_new').id
            values['name'] = values['contact_name'] if 'contact_name' in values else False

            # check ngày cấp CMND
            if 'pass_port_date' in values and values['pass_port_date']:
                values['pass_port_date'] = datetime.strptime(values['pass_port_date'], '%Y-%m-%d')
            else:
                values['pass_port_date'] = False

            # loại bỏ trường ko dùng
            # TODO: xử lý các trường thông tin chưa dùng tới ở dưới
            if 'account_id' in values:
                values.pop('account_id')
            if 'user_ctv_code' in values:
                values.pop('user_ctv_code')
            if 'user_seeding_code' in values:
                values.pop('user_seeding_code')
            if 'phone_no1' in values:
                values.pop('phone_no1')
            if 'phone_no2' in values:
                values['mobile'] = values['phone_no2']
                values.pop('phone_no2')
            if 'phone_no3' in values:
                values.pop('phone_no3')
            if 'agent_email' in values:
                values.pop('agent_email')
            if 'aliases' in values:
                values.pop('aliases')
            if 'booking_date' in values:
                values.pop('booking_date')
            if 'user_seeding_code' in values:
                values.pop('user_seeding_code')
            if 'user_ctv_code' in values:
                values.pop('user_ctv_code')
            if 'seminar_customer' in values:
                values.pop('seminar_customer')
            # tạo lead
            _logger.info('========================= create lead ======================================================')
            _logger.info(values)
            _logger.info('============================================================================================')
            # values['log_api_erp'] = values
            # values['log_api_cs'] = values_cs
            record_lead = request.env['crm.lead'].with_user(user.id).sudo().create(values)

            data = {}
            if record_lead:
                customer_portrait = {}
                customer_portrait['revenue_source'] = record_lead.revenue_source if record_lead.revenue_source else None
                customer_portrait['term_goals'] = record_lead.term_goals if record_lead.term_goals else None
                customer_portrait[
                    'social_influence'] = record_lead.social_influence if record_lead.social_influence else None
                customer_portrait[
                    'behavior_on_the_internet'] = record_lead.behavior_on_the_internet if record_lead.behavior_on_the_internet else None
                customer_portrait['affected_by'] = record_lead.affected_by if record_lead.affected_by else None
                customer_portrait[
                    'work_start_time'] = record_lead.work_start_time if record_lead.work_start_time else None
                customer_portrait['work_end_time'] = record_lead.work_end_time if record_lead.work_end_time else None
                customer_portrait[
                    'break_start_time'] = record_lead.break_start_time if record_lead.break_start_time else None
                customer_portrait['break_end_time'] = record_lead.break_end_time if record_lead.break_end_time else None
                customer_portrait['transport'] = record_lead.transport if record_lead.transport else None
                if record_lead.hobby:
                    list_hobby = []
                    for rec in record_lead.hobby:
                        list_hobby.append(rec.name)
                    customer_portrait['hobby'] = list_hobby
                if record_lead.pain_point:
                    list_pain_point = []
                    for point in record_lead.pain_point:
                        list_pain_point.append(point.name)
                    customer_portrait['pain_point'] = list_pain_point
                if record_lead.desires:
                    list_desires = []
                    for desire in record_lead.desires:
                        list_desires.append(desire.name)
                    customer_portrait['desires'] = list_desires
                lead_action_id = request.env.ref('crm.crm_lead_all_leads').id
                lead_menu_id = request.env.ref('crm.crm_menu_root').id
                data['customer_portrait'] = customer_portrait
                data['id_lead'] = record_lead.id
                data[
                    'link_lead_detail'] = get_url_base() + "/web#id=%d&model=crm.lead&view_type=form&action=%d&menu_id=%d" % (
                    record_lead.id,
                    lead_action_id, lead_menu_id)
            # return valid_response_once(data)
        except Exception as e:
            request.env.cr.rollback()
            return invalid_response("params", e)
        else:
            # data = record.read()
            if record_lead:
                return valid_response_once(data)
            else:
                return valid_response_once(data)

    @validate_token
    @http.route("/api/v1/lead/<id>", type="http", auth="none", methods=["GET"], csrf=False)
    def get_lead_by_id(self, id=None, **payload):
        """ API 2.3 lấy thông tin Lead qua id của Lead"""

        try:
            _id = int(id)
        except Exception as e:
            return invalid_response("invalid object id", "invalid literal %s for id with base " % id)

        domain = [("id", "=", _id), ('type', '=', 'lead')]
        record = request.env['crm.lead'].search(domain)
        data = {}
        if record:
            data['id'] = record.id
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
                        'course_id': line.course_id.id,
                        'course_name': line.course_id.name,
                        'quantity': line.quantity,
                        'source_extend_id': line.source_extend_id,
                        'total_before_discount': line.total_before_discount,
                        'total_after_discount': 0,
                    })
                else:
                    crm_line_ids.append({
                        'id': line.id,
                        'service_id': line.service_id.id,
                        'service_name': line.service_id.name,
                        'quantity': line.quantity,
                        'source_extend_id': line.source_extend_id.id,
                        'source_extend_name': line.source_extend_id.name,
                        'total_before_discount': line.total_before_discount,
                        'total_after_discount': 0,
                    })
            data['crm_line_ids'] = crm_line_ids
        if data:
            return valid_response_once(data)
        else:
            # return valid_response(record.read())
            return valid_response_once(data)
