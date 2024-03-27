"""Part of odoo. See LICENSE file for full copyright and licensing details."""
import ast
import logging

from odoo import http
from odoo.addons.restful.common import (
    extract_arguments,
    invalid_response,
    valid_response,
)
from odoo.addons.restful.controllers.main import (
    validate_token
)
from odoo.http import request

_logger = logging.getLogger(__name__)


class CaseController(http.Controller):

    @validate_token
    @http.route("/api/v1/crm-complain-group", type="http", auth="none", methods=["GET"], csrf=False)
    def get_complain_group(self, id=None, **payload):
        """ API 7.1 lấy danh sách nhóm complain"""
        #Todo: Trên CS không tạo Case
        try:
            _id = int(id)
        except Exception as e:
            return invalid_response("invalid object id", "invalid literal %s for id with base " % id)

        domain, fields, offset, limit, order = extract_arguments(payload)
        domain = [("id", "=", _id)]
        fields = ['id', 'name']
        data = request.env['crm.complain.group'].search_read(
            domain=domain, fields=fields, offset=offset, limit=limit, order=order,
        )
        if data:
            return valid_response(data)
        else:
            return invalid_response('Error')

    _routes = ['/api/v1/crm-complain', '/api/v1/crm-complain?complain_group={id}']

    @validate_token
    @http.route(_routes, type="http", auth="none", methods=["GET"], csrf=False)
    def get_complain(self, id=None, **payload):
        """ API 7.2 Danh sách khiếu nại"""
        # Todo: Trên CS không tạo Case
        domain, fields, offset, limit, order = extract_arguments(payload)
        if id:
            domain = [("id", "=", id)]
        else:
            domain = []
        fields = ['id', 'name']
        data = request.env['crm.complain'].search_read(
            domain=domain, fields=fields, offset=offset, limit=limit, order=order,
        )
        if data:
            return valid_response(data)
        else:
            return invalid_response('Error')

    @validate_token
    @http.route('/api/v1/crm-case/create', type="http", auth="none", methods=["POST"], csrf=False)
    def create_case_complain(self, **payload):
        """API 7.3.1 Tạo Case khiếu nại"""
        """
        data = {
            'name': Khách hàng phàn nàn chất lượng dịch vụ Cắt mí,
            'phone': 0963227022,
            'type_case':1,
            'start_date':'2021-08-14 00:00:00',
            'receive_source':1,
            'booking_id':818512,
            'brand_id':1,
            'company_id':2,
            'crm_content_complain': [
                {
                    'complain_group_id':13,
                    'complain_id':388,
                    'product_ids': ['28730','28658'],
                    'department_ids': ['204','221'],
                    'priority':3,
                    'stage':2,
                    'desc': 'Khách tham khảo thấy khuyến mãi 25% nhưng lễ tân chỉ báo là 15%',
                    'note': 'cần gọi lại cho khách'
                },
                {
                    'complain_group_id':10,
                    'complain_id':368,
                    'department_ids': ['204','221'],
                    'priority':3,
                    'desc': 'chảy máu',
                    'solution': 'Hỏi thăm và hỗ trợ chính sách giảm giá dịch vụ sau này',
                }
            ]
        }
        """
        # field_required = ['name', 'phone','type_case', 'start_date', 'receive_source', 'user_id', 'brand_id', 'company_id','create_by']
        field_required = ['name', 'phone', 'type_case', 'receive_source', 'brand_id', 'company_id']
        data = {}
        for field in field_required:
            if field not in payload:
                return invalid_response(
                    "Missing",
                    "The parameter %s is missing." % field,
                )
        values = {}
        for k, v in payload.items():
            if "__api__" in k:
                values[k[7:]] = ast.literal_eval(v)
            else:
                values[k] = v
        data['name'] = values['name']
        # Lấy ra thông tin khách hàng có SDT trong values
        phone_values = values['phone']
        partner = request.env['res.partner'].search([('phone', '=', phone_values)], limit=1)
        if not partner:
            return invalid_response(
                "Missing",
                "No customer proudly owns phone number %s on ERP system." % phone_values,
            )
        else:
            data['phone'] = phone_values
            data['partner_id'] = partner.id
            data['country_id'] = partner.country_id.id
            data['state_id'] = partner.state_id.id
            data['street'] = partner.street

        # Lấy ra Thương hiệu
        brand_id = request.env['res.brand'].search([('id', '=', int(values['brand_id']))])
        if brand_id:
            data['brand_id'] = brand_id.id
        else:
            return invalid_response(
                "Missing",
                "This Brand does not exist",
            )
        # Lấy ra Chi nhánh
        company_id = request.env['res.company'].search(
            [('id', '=', int(values['company_id'])), ('brand_id', '=', brand_id.id)])
        if company_id:
            data['company_id'] = company_id.id
        else:
            return invalid_response(
                "Missing",
                "This Company does not exist",
            )
        # Lấy ra Booking(nếu có)
        if 'booking_id' in values:
            booking_id = request.env['crm.lead'].search(
                [('id', '=', int(values['booking_id'])), ('type', '=', 'opportunity'), ('partner_id', '=', partner.id)])
            if booking_id:
                data['booking_id'] = booking_id.id
            else:
                return invalid_response('Booking does not exist')
        # Todo: xem có cần thiết cả phonecall không
        # # Lấy ra PhoneCall(nếu có)
        # Lấy ra người xử lý
        user = request.env['res.users'].search([('id', '=', int(values['user_id']))])
        # if user:
        #     data['user_id'] = user.id
        # else:
        #     return invalid_response(
        #         "Missing",
        #         "This Company does not exist",
        #     )

        case_complain = request.env['crm.case'].sudo().create(data)
        # Thêm chi tiết khiếu nại
        if 'crm_content_complain' in values:
            content_complain = eval(values['crm_content_complain'])
            content_field_required = ['complain_id', 'priority']
            for content in content_complain:
                if set(content_field_required).issubset(set(content)):
                    value = {
                        'priority': str(content['priority']),
                        'desc': content['desc'] if ('desc' in content) else False,
                        'note': content['note'] if ('note' in content) else False,
                        'solution': content['solution'] if ('solution' in content) else False,
                    }
                    complain_group_id = request.env['crm.complain.group'].search(
                        [('id', '=', int(content['complain_group_id']))])
                    value['complain_group_id'] = complain_group_id.id
                    complain_id = request.env['crm.complain'].search(
                        [('id', '=', int(content['complain_id'])), ('complain_group_id', '=', complain_group_id.id)])
                    if complain_id:
                        value['complain_id'] = complain_id.id
                    else:
                        return invalid_response(
                            "Missing",
                            "This Complain does not exist",
                        )
                    if 'stage' in content:
                        if content['stage'] == 2:
                            value['stage'] = 'processing'
                        elif content['stage'] == 3:
                            value['stage'] = 'finding'
                        elif content['stage'] == 4:
                            value['stage'] = 'waiting_response'
                        elif content['stage'] == 5:
                            value['stage'] = 'need_to_track'
                        elif content['stage'] == 6:
                            value['stage'] = 'resolve'
                        elif content['stage'] == 7:
                            value['stage'] = 'complete'
                    else:
                        value['stage'] = 'new'
                    if 'product_ids' in content:
                        domain = [('id', 'in', list(map(int, content['product_ids'])))]
                        if brand_id.type == 'hospital':
                            domain += [('type_product_crm', '=', 'service_crm')]
                        elif brand_id.type == 'academy':
                            domain += [('type_product_crm', '=', 'course')]
                        value['product_ids'] = [(6, 0, request.env['product.product'].sudo().search(domain).ids)]

                    if 'department_ids' in content:
                        department_ids = request.env['hr.department'].sudo().search([('id', 'in', list(map(int, content[
                                                                                         'department_ids'])))])

                        department_ids_valid = []
                        for department in department_ids:
                            if department in complain_id.department_ids:
                                department_ids_valid.append(department.id)
                            else:
                                return invalid_response(
                                    "Missing",
                                    "Phòng %s không được khai báo trong Mã khiếu nại %s" % (
                                        department.name, complain_id.name),
                                )
                        value['department_ids'] = [(6, 0, department_ids_valid)]

                    case_complain.write({
                        'crm_content_complain': [(0, 0, value)]
                    })
        data = case_complain.read()
        if case_complain:
            return valid_response(data)
        else:
            return valid_response(data)

    @validate_token
    @http.route("/api/v1/crm-case/<id>", type="http", auth="none", methods=["PUT"], csrf=False)
    def update_case_complain(self, id=None, **payload):
        """ API 7.3.2 Cập nhật Case khiếu nại"""
        """
        data = {
            'user_id':1815,
            'crm_content_complain': [
                {
                    'complain_group_id':13,
                    'complain_id':388,
                    'priority':3,
                    'stage':7,
                    'desc': 'Khách tham khảo thấy khuyến mãi 25% nhưng lễ tân chỉ báo là 15%',
                    'note': 'cần gọi lại cho khách',
                    'solution': 'Xin lỗi và giải thích cho khách',
                    'product_ids': ['28730','28658']
                },
                {
                    'complain_group_id':10,
                    'complain_id':368,
                    'priority':3,
                    'desc': 'chảy máu, khách yêu cầu bồi thường',
                    'note': 'KHách yêu cầu bồi thường',
                }
            ]
        }
        """
        brand_id = request.brand_id
        case = request.env['crm.case'].sudo().browse(int(id))
        value = {}
        if 'user_id' in payload:
            user = request.env['res.users'].search([('id', '=', int(payload['user_id']))])
            if user:
                value['user_id'] = user.id
            else:
                return invalid_response(
                    "Missing",
                    "Không tìm thấy 'Người xử lý'",
                )
        case.write(value)
        if 'crm_content_complain' in payload:
            case.crm_content_complain.unlink()
            content_complain = eval(payload['crm_content_complain'])
            for content in content_complain:
                value = {
                    'priority': str(content['priority']),
                    'desc': content['desc'] if ('desc' in content) else False,
                    'note': content['note'] if ('note' in content) else False,
                    'solution': content['solution'] if ('solution' in content) else False,
                }
                complain_group_id = request.env['crm.complain.group'].search(
                    [('id', '=', int(content['complain_group_id']))])
                value['complain_group_id'] = complain_group_id.id
                complain_id = request.env['crm.complain'].search(
                    [('id', '=', int(content['complain_id'])), ('complain_group_id', '=', complain_group_id.id)])
                if complain_id:
                    value['complain_id'] = complain_id.id
                else:
                    return invalid_response(
                        "Missing",
                        "This Complain does not exist",
                    )
                if 'stage' in content:
                    if content['stage'] == 2:
                        value['stage'] = 'processing'
                    elif content['stage'] == 3:
                        value['stage'] = 'finding'
                    elif content['stage'] == 4:
                        value['stage'] = 'waiting_response'
                    elif content['stage'] == 5:
                        value['stage'] = 'need_to_track'
                    elif content['stage'] == 6:
                        value['stage'] = 'resolve'
                    elif content['stage'] == 7:
                        value['stage'] = 'complete'
                else:
                    value['stage'] = 'new'

                if 'product_ids' in content:
                    domain = ('id', 'in', list(map(int, content['product_ids'])))
                    if brand_id.type == 'hospital':
                        domain += [('type_product_crm', '=', 'service_crm')]
                    elif brand_id.type == 'academy':
                        domain += [('type_product_crm', '=', 'course')]
                    value['product_ids'] = [(0, 0, request.env['product.product'].search(domain).ids)]

                case.write({
                    'crm_content_complain': [(0, 0, value)]
                })
        return valid_response(case.read())
