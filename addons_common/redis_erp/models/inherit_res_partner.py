import json
from datetime import datetime
from odoo.addons.restful.controllers.main import (
    get_url_base,
    validate_token,
    get_redis
)
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from odoo import models, fields

dict_gender = {
    'male': 'Nam',
    'female': 'Nữ',
    'transguy': 'Transguy',
    'transgirl': 'Transgirl',
    'other': 'Khác'
}
dict_stage = {
    'draft': 'Chưa xử lý',
    'not_connect': 'Chưa kết nối',
    'connected': 'Đã xử lý',
    'later': 'Hẹn gọi lại sau'
}
stage_case = {
    'new': 'Mới',
    'processing': 'Đang xử trí',
    'finding': 'Tìm thêm thông tin',
    'waiting_response': 'Chờ phản hồi',
    'need_to_track': 'Cần theo dõi',
    'resolve': 'Giải quyết'
}
dict_priority = {
    '0': 'Thấp',
    '1': 'Bình thường',
    '2': 'Cao'
}
stage_phonecall = {
    'draft': 'Chưa xử lý',
    'not_connect': 'Chưa kết nối',
    'connected': 'Đã xử lý',
    'later': 'Hẹn gọi lại sau'
}
class InheritResPartner(models.Model):
    _inherit = 'res.partner'

    def cron_job_sync_redis(self):
        redis_client = get_redis()
        booking_action_id = self.env.ref('crm.crm_lead_action_pipeline').id
        booking_menu_id = self.env.ref('crm.crm_menu_root').id
        partner_action_id = self.env.ref('contacts.action_contacts').id
        partner_menu_id = self.env.ref('contacts.menu_contacts').id
        actions_phone_call_id = self.env.ref('crm_base.action_open_view_phone_call').id
        menu_phone_call_id = self.env.ref('crm_base.crm_menu_phone_call').id
        walkin_action_id = self.env.ref('shealth_all_in_one.sh_medical_register_for_walkin_action_tree').id
        walkin_menu_id = self.env.ref('shealth_all_in_one.sh_medical_menu').id
        now = datetime.now()
        dict_loyalty = {}
        # querry_loyalty = """
        # select clc.phone, cllw.name, clc.due_date
        # from crm_loyalty_card clc
        # full join crm_loyalty_line_reward cllw on cllw.loyalty_id = clc.id
        # where cllw.stage = 'allow'
        # """
        # self.env.cr.execute(querry_loyalty)
        # loyaltys = self.env.cr.fetchall()
        # for loyalty in loyaltys:
        #     if loyalty[0] not in dict_loyalty:
        #         dict_loyalty[loyalty[0]] = []
        #     dict_loyalty[loyalty[0]].append({
        #         'reward_name': loyalty[1],
        #         'stage': 'Được sử dụng',
        #         'expiration_date': loyalty[2],
        #     })
        # querry_bk = """
        # select rp.phone, cl.id, cl.name, cl.contact_name, cl.gender, cl.pass_port, cl.phone, cl.mobile, cl.birth_date, cl.year_of_birth, cl.email_form,
        # rc.id, rc.name, rs.id, rs.name, rd.id, rd.name, rc.id, rc.name, cl.facebook_acc, cl.send_info_facebook, cl.zalo_acc, rb.id, rb.name, pp.id, pp.name,
        # ccs.id, ccs.name, cl.overseas_vietnamese, cl.work_online, cl.shuttle_bus, uc.id, uc.name, cl.amount_total, cl.create_on
        # from crm_lead cl
        # left join res_partner rp on rp.id = cl.partner_id
        # full join res_country rc on rc.id = cl.country_id
        # full join res_country_state rs on rs.id = cl.state_id
        # full join res_country_district rd on rd.id = cl.district_id
        # full join res_company rc on rc.id = cl.company_id
        # full join res_brand rb on rb.id = cl.brand_id
        # full join product_pricelist pp on pp.id = cl.price_list_id
        # full join crm_category_source ccs on ccs.id = cl.category_source_id
        # full join utm_campaign uc on uc.id = cl.campaign_id
        # where cl.type = %s and cl.active = true
        # """
        # self.env.cr.execute(querry_bk, 'opportunity')
        # bookings = self.env.cr.fetchall()

        # querry_pc = """
        # select pc.phone, pc.id, pc.name, ct.name, pc.state, pc.support_rating, pc.call_date
        # from phone_call pc
        # left join crm_type ct on ct.id = pc.type_crm_id
        # """
        # self.env.cr.execute(querry_pc)
        # phone_calls = self.env.cr.fetchall()
        # for pc in phone_calls:
        #     record_url = get_url_base() + "/web#id=%d&action=%d&model=crm.phone.call&view_type=form&menu_id=%d" % (
        #                     pc['id'],
        #                     actions_phone_call_id, menu_phone_call_id)
        #     key = '%s_phone_calls' % pc[0]
        #     dict_phone_call = {
        #         'id': pc[1],
        #         'name': pc[2],
        #         'type_crm_id': pc[3],
        #         'stage_id': stage_phonecall[pc[4]] if pc[4] in stage_phonecall else 'Hủy',
        #         'support_rating': pc['5'],
        #         'call_date': pc['6'].strftime(DEFAULT_SERVER_DATETIME_FORMAT),
        #         'phone_call_url': record_url,
        #     }
        #     if redis_client:
        #         redis_client.set(key, json.dumps(dict_phone_call, indent=4, sort_keys=True, default=str))
        # querry_partner = """
        # select rp.phone, rp.revenue_source, rp.term_goals, rp.behavior_on_the_internet, rp.affected_by, rp.work_start_time, rp.work_end_time,
        # rp.break_start_time, rp.break_end_time, rp.transport
        # from res_partner rp
        # where rp.active = true
        # """
        # self.env.cr.execute(querry_partner)
        # partner_ids = self.env.cr.fetchall()
        # for partner in partner_ids:
        #     key = '%s_portraits' % partner[0]
        #     parter_id = self.env['res.partner'].sudo().browse(partner[0])
        #     hobby = []
        #     for rec in partner.hobby:
        #         hobby.append(rec.name)
        #     customer_personas = {'desires': [], 'pain_point': []}
        #     for desire in parter_id.desires:
        #         customer_personas['desires'].append({
        #             'id': desire.id,
        #             'name': desire.name,
        #         })
        #     for point in parter_id.pain_point:
        #         customer_personas['pain_point'].append({
        #             'id': point.id,
        #             'name': point.name,
        #         })
        #     if partner[0] not in dict_partner:
        #         dict_partner[partner[0]] = {}
        #     if 'customer_portrait' not in dict_partner[partner[1]]:
        #         dict_partner = {
        #             'hobby': hobby,
        #             'revenue_source': partner[1],
        #             'term_goals': partner[2],
        #             'behavior_on_the_internet': partner[3],
        #             'affected_by': partner[4],
        #             'work_start_time': partner[5],
        #             'work_end_time': partner[6],
        #             'break_start_time': partner[7],
        #             'break_end_time': partner[8],
        #             'transport': partner[9],
        #             'customer_personas': customer_personas,
        #             'account_url': get_url_base() + "/web#id=%d&action=%d&model=res.partner&view_type=form&menu_id=%d" % (
        #                 partner[0], partner_action_id, partner_menu_id)
        #         }
        #     if redis_client:
        #         redis_client.set(key, json.dumps(dict_partner, indent=4, sort_keys=True, default=str))
        #
        # for booking in bookings:
        #     if booking[0] not in dict_partner:
        #         dict_partner[booking[0]] = {}
        #     if 'booking' not in dict_partner[booking[0]]:
        #         dict_partner[booking[0]]['booking'] = []
        #     dict_partner[booking[0]]['booking'].append({
        #         'id': booking[1],
        #         'link_booking_detail': get_url_base() + "/web#id=%d&model=crm.lead&view_type=form&action=%d&menu_id=%d" % (
        #             booking[1], booking_action_id, booking_menu_id),
        #         'name': booking[2],
        #         'contact_name': booking[3],
        #         'gender': dict_gender[booking[4]] if booking[4] in dict_gender else '',
        #         'pass_port': booking[5],
        #         'phone': booking[6],
        #         'mobile': booking[7],
        #         'birth_date': booking[8],
        #         'year_of_birth': booking[9],
        #         'email_from': booking[10],
        #         'country_id': booking[11],
        #         'country_name': booking[12],
        #         'state_id': booking[13],
        #         'state_name': booking[14],
        #         'district_id': booking[15],
        #         'district_name': booking[16],
        #         'street': booking[17],
        #         'company_id': booking[18],
        #         'company_name': booking[19],
        #         'facebook_acc': booking[20],
        #         'send_info_facebook': booking[21],
        #         'zalo_acc': booking[22],
        #         'send_info_zalo': booking[23],
        #         'brand_id': booking[24],
        #         'brand_name': booking[25],
        #         'price_list_id': booking[26],
        #         'price_list_name': booking[27],
        #         'category_source_id': booking[28],
        #         'category_source_name': booking[29],
        #         'overseas_vietnamese': booking[30],
        #         'work_online': booking[31],
        #         'online_counseling': booking[32],
        #         'shuttle_bus': booking[33],
        #         'campaign_id': booking[34],
        #         'campaign_name': booking[35],
        #         'amount_total': booking[36],
        #         'create_on': booking[37]
        #     })
        # self.env.cr.execute(querry_bk, 'lead')
        # lead_action_id = self.env.ref('crm.crm_lead_all_leads').id
        # lead_menu_id = self.env.ref('crm.crm_menu_root').id
        # leads = self.env.cr.fetchall()
        # for lead in leads:
        #     if lead[0] not in dict_partner:
        #         dict_partner[lead[0]] = {}
        #     if 'lead' not in dict_partner[lead[0]]:
        #         dict_partner[lead[0]]['lead'] = []
        #     dict_partner[lead[0]]['lead'].append({
        #         'id': lead[1],
        #         'link_lead_detail': get_url_base() + "/web#id=%d&model=crm.lead&view_type=form&action=%d&menu_id=%d" % (
        #             lead[1], lead_action_id, lead_menu_id),
        #         'name': lead[2],
        #         'contact_name': lead[3],
        #         'gender': dict_gender[lead[4]] if lead[4] in dict_gender else '',
        #         'pass_port': lead[5],
        #         'phone': lead[6],
        #         'mobile': lead[7],
        #         'birth_date': lead[8],
        #         'year_of_birth': lead[9],
        #         'email_from': lead[10],
        #         'country_id': lead[11],
        #         'country_name': lead[12],
        #         'state_id': lead[13],
        #         'state_name': lead[14],
        #         'district_id': lead[15],
        #         'district_name': lead[16],
        #         'street': lead[17],
        #         'company_id': lead[18],
        #         'company_name': lead[19],
        #         'facebook_acc': lead[20],
        #         'send_info_facebook': lead[21],
        #         'zalo_acc': lead[22],
        #         'send_info_zalo': lead[23],
        #         'brand_id': lead[24],
        #         'brand_name': lead[25],
        #         'price_list_id': lead[26],
        #         'price_list_name': lead[27],
        #         'category_source_id': lead[28],
        #         'category_source_name': lead[29],
        #         'overseas_vietnamese': lead[30],
        #         'work_online': lead[31],
        #         'online_counseling': lead[32],
        #         'shuttle_bus': lead[33],
        #         'campaign_id': lead[34],
        #         'campaign_name': lead[35],
        #         'amount_total': lead[36],
        #         'create_on': lead[37]
        #     })
        index = 1
        pipe = redis_client.pipeline()
        querry = """
        select rp.id, rp.name, rp.street, rp.street2, rc.id, rc.name, rs.id, rs.name, rp.contact_address_complete, rp.email,
        rp.phone, rp.mobile, rp.birth_date, rp.year_of_birth,extract(year from age(birth_date)), rp.gender, rp.code_customer,
        rp.revenue_source, rp.term_goals, rp.behavior_on_the_internet, rp.affected_by, rp.work_start_time, rp.work_end_time,
        rp.break_start_time, rp.break_end_time, rp.transport
        from res_partner rp
        full join res_country rc on rc.id = rp.country_id
        full join res_country_state rs on rs.id = rp.state_id
        where rp.active = true
        """
        self.env.cr.execute(querry)
        partners = self.env.cr.fetchall()
        for partner in partners:
            index += 1
            phone = partner[10]
            partner_id = self.env['res.partner'].sudo().browse(partner[0])
            key = '%s_personal' % phone
            key_pc = '%s_phone_calls' % phone
            key_pt = '%s_portraits' % phone
            dict_partner = {
                'id': partner[0],
                'name': partner[1],
                'street': partner[2],
                'street_2': partner[3] if partner[3] else '',
                'country_id': partner[4],
                'country_name': partner[5],
                'state_id': partner[6],
                'state_name': partner[7],
                'contact_address': partner[8],
                'email': partner[9],
                'phone': partner[10],
                'mobile': partner[11],
                'birth_date': str(partner[12]) if partner[12] else '',
                'year_of_birth': partner[13],
                'age': partner[14] if partner else '',
                'gender': dict_gender[partner[15]] if partner[15] in dict_gender else '',
                'code_customer': partner[16],
                'account_url': get_url_base() + "/web#id=%d&action=%d&model=res.partner&view_type=form&menu_id=%d" % (
                    partner[0], partner_action_id, partner_menu_id)
            }
            hobby = []
            for rec in partner_id.hobby:
                hobby.append(rec.name)
            customer_personas = {'desires': [], 'pain_point': []}
            for desire in partner_id.desires:
                customer_personas['desires'].append({
                    'id': desire.id,
                    'name': desire.name,
                })
            for point in partner_id.pain_point:
                customer_personas['pain_point'].append({
                    'id': point.id,
                    'name': point.name,
                })
            dict_partner_portrait = {
                'hobby': hobby,
                'revenue_source': partner[17],
                'term_goals': partner[18],
                'behavior_on_the_internet': partner[19],
                'affected_by': partner[20],
                'work_start_time': partner[21],
                'work_end_time': partner[22],
                'break_start_time': partner[23],
                'break_end_time': partner[24],
                'transport': partner[25],
                'customer_personas': customer_personas,
                'account_url': get_url_base() + "/web#id=%d&action=%d&model=res.partner&view_type=form&menu_id=%d" % (
                    partner[0], partner_action_id, partner_menu_id)
            }
            domain_p = [('partner_id', '=', partner_id.id)]
            phones_call = self.env['crm.phone.call'].search_read(domain=domain_p,
                                                                    fields=['id', 'name', 'type_crm_id', 'state',
                                                                    'support_rating', 'call_date'],order='call_date desc')
            data = []
            for phone_call in phones_call:
                record_url = get_url_base() + "/web#id=%d&action=%d&model=crm.phone.call&view_type=form&menu_id=%d" % (
                phone_call['id'],
                actions_phone_call_id, menu_phone_call_id)
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

                data.append({
                    'id': phone_call['id'],
                    'name': phone_call['name'],
                    'type_crm_id': phone_call['type_crm_id'][1],
                    'stage_id': stage,
                    'support_rating': phone_call['support_rating'],
                    'call_date': phone_call['call_date'].strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                    'phone_call_url': record_url,
                })
            pipe.set(key, json.dumps(dict_partner))
            pipe.set(key_pc, json.dumps(data))
            pipe.set(key_pt, json.dumps(dict_partner_portrait))
            if index > 1000:
                break
        pipe.execute()
        # case_action_id = self.env.ref('crm_base.action_complain_case_view').id
        # case_menu_id = self.env.ref('crm_base.crm_menu_case').id
        # querry_cases = """
        # select cc.phone, cc.id, cc.name, cc.stage, cc.priority, cc.create_date
        # from crm.case cc
        # """
        # self.env.cr.execute(querry_cases)
        # cases = self.env.cr.fetchall()
        # for case in cases:
        #     record_url = get_url_base() + "/web#id=%d&action=%d&model=crm.case&view_type=form&menu_id=%d" % (
        #         int(case[1]),
        #         case_action_id, case_menu_id)
        #     key = '%s_case' % case[0]
        #     dict_case = {
        #         'id': case[1],
        #         'name': case[2],
        #         'stage': stage_case[case[3]] if case[3] in stage_case else 'Hoàn thành',
        #         'priority': dict_priority[case[4]] if case[4] in dict_priority else 'Khẩn cấp',
        #         'case_url': record_url,
        #         'create_date': case[5].strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        #     }
        #     if redis_client:
        #         redis_client.set(key, json.dumps(dict_case, indent=4, sort_keys=True, default=str))
