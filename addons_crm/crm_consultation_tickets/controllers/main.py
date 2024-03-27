from odoo.http import Controller, request, route
import json
import re
def extract_number_from_string(input_string):
    match = re.search(r'\d+', input_string)
    if match:
        return int(match.group())
    return None

def remove_characters_after_underscore(input_string):
    parts = input_string.split('__')
    return parts[0]

# Nguồn biết đến
KNOW_SOURCE = [
    ('web', 'Website/Facebook'),
    ('hotline', 'Tư vấn Hotline'),
    ('voucher', 'Voucher trải nghiệm'),
    ('ctv', 'Cộng tác viên'),
    ('lcd', 'LCD/Frame/Poster'),
    ('brand', 'Đi ngang chi nhánh'),
    ('friend', 'Người thân/Bạn bè'),
    ('seminor', 'Hội thảo'),
    ('business', 'Nhân viên kinh doanh'),
    ('qc', 'Quảng các TV'),
    ('other', 'Khác')
]


class ConsultationController(Controller):

    @route(['/phieu-tu-van/<int:booking_id>'], type='http', auth='user', website=True)
    def consultation(self, booking_id, **post):
        # uid = request.session.uid
        company = request.env.company
        allowed_company_ids = [cid.id for cid in request.env.user.company_ids]
        booking = request.env['crm.lead'].with_context(allowed_company_ids=allowed_company_ids).browse(booking_id)
        pricelist_item_ids = request.env['product.pricelist.item'].sudo().search(
            [('pricelist_id', '=', booking.price_list_id.id)])
        service = request.env['sh.medical.health.center.service'].sudo().search(
            [('product_id', 'in', pricelist_item_ids.mapped('product_id').ids)])

        consulting_doctor = request.env['sh.medical.physician'].sudo().search(
            [('company_id', '=', booking.company_id.id)])
        source_id = request.env['utm.source'].sudo().search([])

        list_service = []
        for rec in service:
            list_service.append({'id': rec.id, 'name': rec.name})

        json_service = json.dumps(list_service)

        company_booking = booking.company_id

        if booking.brand_id and booking.brand_id.code:
            brand_code = booking.brand_id.code.lower()
        else:
            brand_code = ''

        data = {
            'company': company,
            'booking': booking,
            'crm_line_ids': booking.crm_line_ids,
            'user': request.env.user,
            'company_booking': company_booking,
            'service': service,
            'json_service': json_service,
            'consulting_doctor': consulting_doctor,
            'brand_code': brand_code,
            'know_source': KNOW_SOURCE,
            'source_id': source_id
        }

        return request.render('crm_consultation_tickets.consultation_ticket', data)

    @route(['/phieu-tu-van-submit/<int:booking_id>'], type='http',
           methods=['POST'], csrf=False, auth='public', website=True)
    def consultation_submit(self, booking_id, **post):
        booking = request.env['crm.lead'].sudo().search([('id', '=', booking_id)])
        source_id = request.env['utm.source']
        if 'source_id' in post:
            source_id += request.env['utm.source'].search([('id', '=', int(post['source_id']))])
        address = []
        partner = booking.partner_id
        if partner.street:
            address.append(partner.street)
        if partner.district_id:
            address.append(partner.district_id.name)
        if partner.state_id:
            address.append(partner.state_id.name)
        if partner.country_id:
            address.append(partner.country_id.name)

        # Bác sĩ tư vấn: consulting_doctor
        consulting_doctor = request.env['sh.medical.physician']
        if 'consulting_doctor' in post:
            consulting_doctor += request.env['sh.medical.physician'].search(
                [('id', '=', int(post['consulting_doctor']))])
        # Xử lý để tạo các detail_ticket
        dict_key = []  # Lấy ra danh sách key của detail ticket
        list_result = []  # Danh sách tất cả các detail ticket
        for key in post:
            if '__' in key:
                dict_key.append(key)

        for i in range(1, int(extract_number_from_string(dict_key[-1])) + 1):
            dict_result = {}  # dict detail ticket hoàn chỉnh
            for key in post:
                if extract_number_from_string(key) == i:
                    key_dict_result = remove_characters_after_underscore(key)
                    dict_result[key_dict_result] = post[key]
                    if key_dict_result == 'service':
                        service_id = request.env['sh.medical.health.center.service'].sudo().search(
                            [('id', '=', int(dict_result['service']))])
                        if service_id:
                            dict_result['service_id'] = service_id.id
                            dict_result.pop('service')

                    confirm_service = False
                    if ('confirm_service' in dict_result) and dict_result['confirm_service'] == 'on':
                        confirm_service = True
                    dict_result['confirm_service'] = confirm_service
            if dict_result:
                list_result.append((0, 0, dict_result))
        # Tạo ra 1 bản ghi phiếu tư vấn
        request.env['consultation.ticket'].sudo().create({
            'booking_id': booking.id,
            'partner_id': partner.id,
            'allergy_history': partner.allergy_history,
            'name_customer': partner.name,
            'code_customer': partner.code_customer,
            'gender_customer': partner.gender,
            'birth_date_customer': partner.gender,
            'passport_customer': partner.pass_port,
            'passport_date_customer': partner.pass_port_date,
            'address_customer': address,
            'phone_customer': partner.phone,
            'emergency_phone_customer': partner.emergency_phone,
            'email_customer': partner.email,
            'know_source': post['know_source'] if ('know_source' in post) else False,
            'source_id': source_id.id if source_id else False,
            'sh_medical_physician_id': consulting_doctor.id if ('consulting_doctor' in post) else False,
            'consultation_detail_ticket_ids': list_result,
        })
        return request.render('crm_consultation_tickets.sfinished')

