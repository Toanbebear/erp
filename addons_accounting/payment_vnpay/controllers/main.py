# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http
from odoo.http import *

_logger = logging.getLogger(__name__)


def error_response(status, error, error_descrip):
    return werkzeug.wrappers.Response(
        status=status,
        content_type='application/json; charset=utf-8',
        # headers = None,
        response=json.dumps({
            'error': error,
            'error_descrip': error_descrip,
        }),
    )


class ApiRequest(WebRequest):
    _request_type = "json"

    def __init__(self, *args):
        super(ApiRequest, self).__init__(*args)
        params = collections.OrderedDict(self.httprequest.args)
        params.update(self.httprequest.form)
        params.update(self.httprequest.files)
        params.pop('session_id', None)
        self.params = params

    def _response(self, result=None, error=None):
        if error is not None:
            return error

        elif result is not None:
            return result

    def dispatch(self):
        try:
            result = self._call_function()
            return self._json_response(result)
        except Exception as exception:
            # Rollback
            if self._cr:
                self._cr.rollback()
            # End Rollback
            error = {
                'code': 500,
                'message': "Odoo Server Error",
                'data': False
            }
            if not isinstance(exception,
                              (odoo.exceptions.Warning, SessionExpiredException, odoo.exceptions.except_orm)):
                _logger.exception("Exception during JSON request handling.")
            error = {
                'code': 500,
                'message': "Odoo Server Error",
                'data': serialize_exception(exception)
            }
            if isinstance(exception, SessionExpiredException):
                error['code'] = 400
                error['message'] = "Odoo Session Expired"
            return error_response(error['code'], error['message'], error['data'] or error['message'])

    def _json_response(self, result=None, error=None):
        mime = 'application/json'
        body = json.dumps(result, default=date_utils.json_default)

        return Response(
            body, status=error and error.pop('http_status', 200) or 200,
            headers=[('Content-Type', mime), ('Content-Length', len(body))]
        )


def vnpay_api_get_request(self, httprequest):
    # deduce type of request
    if ('/payment/vnpayqr/notify' in httprequest.path) and (httprequest.mimetype == "application/json"):
        return ApiRequest(httprequest)
    if httprequest.args.get('jsonp') or httprequest.mimetype in ("application/json", "application/json-rpc"):
        return JsonRequest(httprequest)
    else:
        return HttpRequest(httprequest)


Root.get_request = vnpay_api_get_request


class VnpayqrController(http.Controller):
    _notify_url = '/payment/vnpayqr/notify'

    # key abc@123
    def _vnpayqr_validate_data(self, values):
        # Xử lý dữ liệu
        # {
        #     "code": "00",
        #     "message": "Tru tien thanh cong, so trace 100550",
        #     "msgType": "1",
        #     "txnId": "50141",
        #     "qrTrace": "000098469",
        #     "bankCode": "VIETCOMBANK",
        #     "mobile": "0989511021",
        #     "accountNo": "",
        #     "amount": "1000000",
        #     "payDate": "20180807164732",
        #     "masterMerCode": "A000000775",
        #     "merchantCode": "0311609355",
        #     "terminalId": "FPT02",
        #     "addData": [{
        #         "merchantType": "5045",
        #         "serviceCode": "06",
        #         "masterMerCode": "A000000775",
        #         "merchantCode": "0311609355",
        #         "terminalId": "FPT02",
        #         "productId": "",
        #         "amount": "100000",
        #         "ccy": "704",
        #         "qty": "1",
        #         "note": ""
        #     }],
        #     "checksum": "81F77683FEA4EBE2CE748AFC99CC3AE9",
        #     "ccy": "704",
        #     "secretKey": "VNPAY"
        # }
        # Mã đơn hàng
        _logger.info(values)
        txn_id = values.get('txnId')
        qr_trace = values.get('qrTrace')
        amount = values.get('amount')
        if txn_id:
            account_payment = request.env['account.payment'].sudo().browse(int(txn_id))
            company = account_payment.company_id
            _logger.info(company)
            _logger.info(account_payment)
            if account_payment:
                amount_vnd = str(int(account_payment.amount_vnd))

                if amount_vnd == amount:
                    _logger.info('Chay ham post payment')
                    account_payment.with_context(force_company=company.id).post()
                    _logger.info('---------------> Chay xong post payment')
                    transaction = account_payment.payment_transaction_id
                    _logger.info(transaction)
                    transaction._set_transaction_done()
                    _logger.info('_set_transaction_done')
                    if transaction.state == 'done':
                        _logger.info(transaction.state)
                        account_payment.with_context(force_company=company.id).post()
                    _logger.info(transaction)
                    return {
                        "code": "00",
                        "message": "đặt hàng thành công",
                        "data": {
                            "txnId": str(txn_id)
                        }
                    }
                else:
                    return {
                        "code": "07",
                        "message": "số tiền không chính xác",
                        "data": {
                            "amount": amount_vnd
                        }
                    }
            else:
                return {
                    "code": "01",
                    "message": "Không tìm thấy giao dịch",
                    "data": {
                        "txnId": "5014233"
                    }
                }

    def _vnpayqr_validate_notification(self, post):
        # Check IP của VNPAYQR
        ip = request.httprequest.environ['REMOTE_ADDR'] if request else 'n/a'
        accept_ips = ['127.0.0.1']
        _logger.info("IP: %s" % ip)
        # if ip not in accept_ips:
        #     return {
        #         "code": "10",
        #         "message": "IP không được truy cập",
        #         "data": {
        #         }
        #     }
        # Check sum
        # TODO cấu hình secretKey trong config
        if post.get('secretKey') and post.get('secretKey') == 'VNPAY':
            return self._vnpayqr_validate_data(post)
        else:
            return {
                "code": "06",
                "message": "sai thông tin xác thực",
                "data": {
                }
            }

    @http.route('/payment/vnpayqr/notify', type="json", auth='public', methods=['POST'], csrf=False)
    def vnpayqr_notify(self):
        """ VNPAY-QR Notify """
        # key abc@123
        values = json.loads(request.httprequest.data.decode('utf-8'))
        _logger.info('Beginning VNPAY-QR notification with post data %s', pprint.pformat(request.httprequest.data.decode('utf-8')))
        return self._vnpayqr_validate_notification(values)
