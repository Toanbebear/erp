# Part of odoo. See LICENSE file for full copyright and licensing details.
import json
import logging

from odoo import http
from odoo.addons.crm_ehc.controllers.crm_hh_ehc_common import ehc_validate_token, get_user_hh
from odoo.http import request

_logger = logging.getLogger(__name__)


class UpdateServiceBookingEHCController(http.Controller):
    @ehc_validate_token
    @http.route("/api/v1/update-material-booking", methods=["POST"], type="json", auth="none", csrf=False)
    def v1_ehc_update_material_booking(self, **payload):
        body = json.loads(request.httprequest.data.decode('utf-8'))
        _logger.info('========================= API thuốc vật tư sử dụng ===================================')
        _logger.info(body)
        _logger.info('======================================================================================')
        field_require = [
            'booking_code',
            'service_order_form_id',
            'service_order_form_code',
            'medical_examination_stage',
            "key_data_master",
            "key_data",
            "service_code",
            "service_quantity",
            "service_unit_price",
            "service_discount",
            "service_source",
            "service_object",
            "service_designated_date",
            "service_date",
            "service_result_day",
            "service_designator",
            "service_executor",
            "service_result_payer",
            "service_designated_room",
            "service_implementation_room",
            "service_result_room",
            "service_status",
        ]
        for field in field_require:
            if field not in body.keys():
                return {
                    'stage': 1,
                    'message': 'Thieu tham so %s!!!' % field
                }
        # search booking
        booking = request.env['crm.lead'].sudo().search(
            [('name', '=', body['booking_code']), ('brand_id.code', '=', 'HH')], limit=1)
        if 'service_code' in body and body['service_code']:
            if booking:
                dict_check_material = {}
                for service_booking_erp in booking.material_ehc_ids:
                    dict_check_material[service_booking_erp.material_id.default_code] = service_booking_erp.key_data
                service_code_check = 'EHC-' + body['service_code']
                product_erp = request.env['product.product'].sudo().search(
                    [('default_code', '=', service_code_check), ('active', '=', False)])
                if product_erp:
                    if "stage" in body and str(body["stage"]) == '0':
                        # check nếu tồn tại 1 cặp giá trị service & key_data trên ERP thì cập nhật và ko có thì tạo mới
                        if service_code_check in dict_check_material and int(body['key_data']) == int(
                                dict_check_material[service_code_check]):
                            line = booking.material_ehc_ids.filtered(
                                lambda s: s.key_data == int(
                                    body['key_data']) and s.material_id.default_code == service_code_check)
                            line.with_user(get_user_hh()).sudo().write({
                                'booking_id': booking.id,
                                'material_id': product_erp.id,
                                'quantity': body['service_quantity'],
                                'unit_price': body['service_unit_price'],
                                'total_discount': body['service_discount'],
                                'total': int(body['service_unit_price']) * int(body['service_quantity']) - int(
                                    body['service_discount']),
                                'key_data': body['key_data']
                            })
                            return {
                                'stage': 0,
                                'message': 'Cap nhat thuoc /vat tu vao Booking thanh cong!'
                            }
                        else:
                            booking.material_ehc_ids.with_user(get_user_hh()).sudo().create(
                                {
                                    'booking_id': booking.id,
                                    'material_id': product_erp.id,
                                    'quantity': body['service_quantity'],
                                    'unit_price': body['service_unit_price'],
                                    'total_discount': body['service_discount'],
                                    'total': int(body['service_unit_price']) * int(body['service_quantity']) - int(
                                        body['service_discount']),
                                    'key_data': body['key_data']
                                }
                            )
                            return {
                                'stage': 0,
                                'message': 'Them thuoc/ vat tu vao Booking thanh cong!'
                            }
                    elif "stage" in body and str(body["stage"]) == '1':
                        if service_code_check in dict_check_material and int(body['key_data']) == int(
                                dict_check_material[service_code_check]):
                            line = booking.material_ehc_ids.filtered(
                                lambda s: s.key_data == int(
                                    body['key_data']) and s.material_id.default_code == service_code_check)
                            if line:
                                line.unlink()
                                return {
                                    'stage': 0,
                                    'message': 'Cap nhat thuoc /vat tu vao Booking thanh cong!'
                                }
                    else:
                        # check nếu tồn tại 1 cặp giá trị service & key_data trên ERP thì cập nhật và ko có thì tạo mới
                        if service_code_check in dict_check_material and int(body['key_data']) == int(
                                dict_check_material[service_code_check]):
                            line = booking.material_ehc_ids.filtered(
                                lambda s: s.key_data == int(
                                    body['key_data']) and s.material_id.default_code == service_code_check)
                            line.with_user(get_user_hh()).sudo().write({
                                'booking_id': booking.id,
                                'material_id': product_erp.id,
                                'quantity': body['service_quantity'],
                                'unit_price': body['service_unit_price'],
                                'total_discount': body['service_discount'],
                                'total': int(body['service_unit_price']) * int(body['service_quantity']) - int(
                                    body['service_discount']),
                                'key_data': body['key_data']
                            })
                            return {
                                'stage': 0,
                                'message': 'Cap nhat thuoc /vat tu vao Booking thanh cong!'
                            }
                        else:
                            booking.material_ehc_ids.with_user(get_user_hh()).sudo().create(
                                {
                                    'booking_id': booking.id,
                                    'material_id': product_erp.id,
                                    'quantity': body['service_quantity'],
                                    'unit_price': body['service_unit_price'],
                                    'total_discount': body['service_discount'],
                                    'total': int(body['service_unit_price']) * int(body['service_quantity']) - int(
                                        body['service_discount']),
                                    'key_data': body['key_data']
                                }
                            )
                            return {
                                'stage': 0,
                                'message': 'Them thuoc/ vat tu vao Booking thanh cong!'
                            }
                else:
                    return {
                        'stage': 1,
                        'message': 'Khong tim thay san pham co ma %s!!!' % body['service_code']
                    }
            else:
                return {
                    'stage': 1,
                    'message': 'Khong tim thay Booking co ma %s!!!' % body['booking_code']
                }
        else:
            return {
                'stage': 1,
                'message': 'service_code dang truyen vao la %s bi loi, lien he admin de kiem tra!!!' % body[
                    'booking_code']
            }
