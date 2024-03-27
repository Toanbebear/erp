# Part of odoo. See LICENSE file for full copyright and licensing details.
import json
import logging

from odoo.addons.crm_ehc.controllers.crm_hh_ehc_common import ehc_validate_token

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class GetPaymentEHCController(http.Controller):
    @ehc_validate_token
    @http.route("/api/v1/get-payment-booking", methods=["POST"], type="json", auth="none", csrf=False)
    def v1_ehc_get_payment_booking(self, **payload):
        body = json.loads(request.httprequest.data.decode('utf-8'))
        _logger.info('=============== 12.1 API lấy danh sách cập nhật thanh toán của booking =======================')
        _logger.info(body)
        _logger.info('==============================================================================================')
        field_require = [
            'booking_code',
        ]
        for field in field_require:
            if field not in body.keys():
                return {
                    'stage': 1,
                    'message': 'Thieu tham so %s!!!' % field
                }
            if not body[field]:
                return {
                    'stage': 1,
                    'message': 'Tham so %s dang rong !!!' % field
                }
        # search booking
        booking = request.env['crm.lead'].sudo().search([('name', '=', body['booking_code'])], limit=1)
        if booking:
            # search payment
            list_payment = request.env['account.payment'].sudo().search([('crm_id', '=', booking.id)])
            if list_payment:
                data = []
                for payment in list_payment:
                    internal_payment_type_dict = {
                        'tai_don_vi': 'Tại đơn vị',
                        'thu_ho': 'Thu hộ',
                        'chi_ho': 'Chi hộ',
                    }
                    payment_type_dict = {
                        'inbound': 'Nhận tiền',
                        'outbound': 'Hoàn tiền',
                        'transfer': 'Giao dịch nội bộ'
                    }
                    payment_method_dict = {
                        'tm': 'Tiền mặt',
                        'ck': 'Chuyển khoản',
                        'nb': 'Thanh toán nôi bộ',
                        'pos': 'Quẹt thử qua POS',
                        'vdt': 'Thanh toán qua ví điện tử',
                    }
                    data.append({
                        'booking_code': payment.crm_id.name,
                        'payment_code': payment.name,
                        'internal_payment_type': internal_payment_type_dict[payment.internal_payment_type],
                        'payment_type': payment_type_dict[payment.payment_type],
                        'payment_method': payment_method_dict[payment.payment_method],
                        'customer_name': payment.partner_id.name,
                        'customer_code': payment.partner_id.code_customer,
                        'amount': payment.amount,
                        'currency_id': payment.currency_id.name,
                        'payment_date': payment.payment_date,
                        'communication': payment.communication,
                        'user_name': payment.user.name,
                        'user_code': payment.user.employee_ids[0].employee_code if payment.user.employee_ids else '',
                    })
                return {
                    'stage': 0,
                    'message': 'Thanh cong !!!',
                    'data': data
                }
            else:
                return {
                    'stage': 0,
                    'message': 'Booking co ma %s khong co thong tin thanh toan !!!' % body['booking_code'],
                    'data': ''
                }
        else:
            return {
                'stage': 1,
                'message': 'Khong tim thay Booking co ma %s !!!' % body['booking_code']
            }
