# -*- coding: utf-8 -*-
import base64
import hashlib
import json
from io import BytesIO

import qrcode
import requests

from odoo import _
from odoo import models, fields, api
from odoo.exceptions import UserError

ROUNDING_FACTOR = 16


class AccountPayment(models.Model):
    _name = "account.payment"
    _inherit = ['account.payment', 'qrcode.mixin', 'money.mixin']

    @api.depends('qr_code_data')
    def _get_image(self):
        for record in self:
            record.qr_code_image = self.qrcode(record.qr_code_data)

    qr_code_data = fields.Text(string='QRCode')
    qr_code_image = fields.Binary(string='QrCode', compute='_get_image')

    # Có công ty, có thương hiệu, có kiểu thanh toán lấy ra thông số thanh toán
    def generate_vnpay_qr_code(self):
        for payment in self:
            # Gọi tạo mã QR

            # - merchantCode: 41
            # A8047564
            # - merchantName: NHAKHOAPARIS
            # - merchantType: 0763

            # - terminalId: NKPARIS1 cty
            # - appId: MERCHANT
            # - seckey: vnpay @ MERCHANT

            # Người dùng ở công ty, thuộc thương hiệu gì
            # Lấy merchantName của thương hiệu

            if payment.company_id:
                # Lấy terminalId từ company
                terminal_id = payment.company_id.terminal_id
                if not terminal_id:
                    raise UserError(
                        _('Chưa cấu hình điểm bán Terminal ID cho chi nhánh. Vui lòng liên hệ quản trị line 888'))

                if payment.company_id.brand_id:
                    master_merchant_code = payment.company_id.brand_id.master_merchant_code

                    app_id = payment.company_id.brand_id.app_id

                    secret_key = payment.company_id.brand_id.secret_key

                    merchant_name = payment.company_id.brand_id.merchant_name
                    merchant_code = payment.company_id.brand_id.merchant_code
                    merchant_type = payment.company_id.brand_id.merchant_type
                    if not merchant_name or not merchant_code or not merchant_type:
                        raise UserError(
                            _('Chưa cấu hình thông tin tài khoản merchant cho thương hiệu. Vui lòng liên hệ quản trị line 888'))

                    if not payment.amount or payment.amount < 0:
                        raise UserError(
                            _('Số tiền thanh toán phải lớn hơn 0'))

                    # Xử lý số tiền thanh toán, không tính sau dấu phẩy
                    amount = str(int(payment.amount_vnd))
                    try:
                        # appId = self.env["ir.config_parameter"].sudo().get_param("vnpay_qrcode_app_id") or ''
                        # TODO lưu trong payment_transaction và truyền id của payment_transaction sang Vnpay
                        txn_id = str(payment._origin.id)  # Mã payment
                        # booking = payment.crm_id.name if payment.crm_id else 'NO_BOOKING'
                        booking = txn_id
                        serviceCode = "03"
                        countryCode = "VN"
                        payType = "03"
                        productId = ""
                        tipAndFee = ""
                        ccy = "704"
                        # TODO ngày giờ hết hạn giao dịch dựa vào gì?
                        expDate = "2112291225"
                        # secretKey = self.env["ir.config_parameter"].sudo().get_param("vnpay_qrcode_secret_key") or ''

                        checksum = "%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s" % (
                            app_id,
                            merchant_name,
                            serviceCode,
                            countryCode,
                            master_merchant_code,
                            merchant_type,
                            merchant_code,
                            terminal_id,
                            payType,
                            productId,
                            txn_id,
                            amount,
                            tipAndFee,
                            ccy,
                            expDate,
                            secret_key
                        )

                        data = {
                            'appId': app_id,
                            'merchantName': merchant_name,
                            'serviceCode': serviceCode,
                            'countryCode': countryCode,
                            'merchantCode': merchant_code,
                            'terminalId': terminal_id,  # Lấy mã của cty
                            'payType': payType,
                            'productId': productId,  # Mã sản phẩm
                            'txnId': txn_id,
                            'billNumber': booking,  # Mã đơn hàng SO
                            'amount': amount,  # Số tiền
                            'ccy': ccy,
                            'expDate': expDate,
                            'desc': "Thanh toán đơn hàng",
                            'masterMerCode': master_merchant_code,
                            'merchantType': merchant_type,  # Loại hình doanh nghiệp
                            'tipAndFee': tipAndFee,  # Tiền tip and fee
                            'consumerID': "",
                            'purpose': "",
                            'checksum': hashlib.md5(checksum.encode('utf-8')).hexdigest()
                        }
                        headerVal = {'Content-Type': 'text/plain'}
                        url = self.sudo().env['ir.config_parameter'].get_param('payment_vnpay.vnpay_qrcode_url_create_qr')
                        if url:
                            resp = requests.post(url=url, data=json.dumps(data), headers=headerVal, timeout=30)
                            resp_json = resp.json()
                        else:
                            raise UserError(_('Hệ thống chưa cấu hình VNPAY-QR URL'))
                    except requests.exceptions.Timeout:
                        raise UserError(_('Timeout: Hệ thống VNPAY-QR không phản hồi trong 60s'))
                    except (ValueError, requests.exceptions.ConnectionError):
                        raise UserError(_('Hệ thống VNPAY-QR có lỗi, vui lòng thử lại sau'))

                    result = resp_json  # json.dumps(resp_json)
                    if result:
                        code = result.get('code')
                        result_url = result.get('url') or 'null'
                        result_checksum_data = "%s|%s|%s|%s|%s" % (
                            result.get('code'), result.get('message'), result.get('data'), result_url, secret_key)
                        result_checksum = hashlib.md5(result_checksum_data.encode('utf-8')).hexdigest()
                        self.qr_code_data = ''
                        if result.get('checksum').upper() == result_checksum.upper():
                            # TT 1 00 Success
                            if code == '00':
                                self.qr_code_data = result['data']
                            elif code == '01':
                                raise UserError('Dữ liệu không đúng định dạng')
                            elif code == '04':
                                raise UserError('Dữ liệu QRCode lỗi')
                            elif code == '05':
                                raise UserError('IP bị từ chối')
                            elif code == '06':
                                raise UserError('IP bị từ chối')
                            elif code == '07':
                                raise UserError('Lỗi checkSum')
                            elif code == '09':
                                raise UserError('Service code không chính xác')
                            elif code == '10':
                                raise UserError('AppId không chính xác')
                            elif code == '11':
                                raise UserError('Merchant không tồn tại')
                            elif code == '12':
                                raise UserError('Mã Master merchant rỗng')
                            elif code == '15':
                                raise UserError('ConsumerID rỗng')
                            elif code == '16':
                                raise UserError('Purpose rỗng')
                            elif code == '21':
                                raise UserError('Terminal - Điểm thanh toán không chính xác')
                            elif code == '24':
                                raise UserError('Terminal - Điểm thanh toán không hoạt động')
                            elif code == '99':
                                raise UserError('Internal errors')
                            elif code == '96':
                                raise UserError('System is maintaining')
                            else:
                                self.qr_code_data = ''
                        else:
                            raise UserError('Sai mã Checksum')

                    # Hiển thị mã

    def check_transaction(self):
        """ Yêu cầu kiểm tra giao dịch(CheckTrans)"""
        for payment in self:
            if payment.company_id:
                # Lấy terminalId từ company
                terminal_id = payment.company_id.terminal_id
                if not terminal_id:
                    raise UserError(
                        _('Chưa cấu hình điểm bán Terminal ID cho chi nhánh. Vui lòng liên hệ quản trị line 888'))

                if payment.company_id.brand_id:
                    master_merchant_code = payment.company_id.brand_id.master_merchant_code
                    app_id = payment.company_id.brand_id.app_id

                    secret_key = payment.company_id.brand_id.secret_key

                    merchant_name = payment.company_id.brand_id.merchant_name
                    merchant_code = payment.company_id.brand_id.merchant_code
                    merchant_type = payment.company_id.brand_id.merchant_type
                    if not merchant_name or not merchant_code or not merchant_type:
                        raise UserError(
                            _('Chưa cấu hình thông tin tài khoản merchant cho thương hiệu. Vui lòng liên hệ quản trị line 888'))

                    try:
                        txn_id = str(payment.id)  # Mã payment
                        pay_date = "2112291225"

                        checksum = "%s|%s|%s|%s|%s" % (
                            pay_date,
                            app_id,
                            merchant_code,
                            terminal_id,
                            secret_key
                        )
                        print(checksum)
                        data = {
                            'txnId': txn_id,
                            'payDate': pay_date,
                            'merchantCode': merchant_code,
                            'terminalID': terminal_id,  # Lấy mã của cty
                            'checksum': hashlib.md5(checksum.encode('utf-8')).hexdigest()
                        }
                        print('data', data)
                        headerVal = {'Content-Type': 'application/json'}
                        url = self.sudo().env['ir.config_parameter'].get_param('payment_vnpay.vnpay_qrcode_check_trans_url')
                        print('resp_json', url)
                        if url:
                            resp = requests.post(url=url, data=json.dumps(data), headers=headerVal, timeout=30)
                            resp_json = resp.json()
                            print('resp_json', resp_json)
                        else:
                            raise UserError(_('Hệ thống chưa cấu hình VNPAY-QR URL'))
                    except requests.exceptions.Timeout:
                        raise UserError(_('Timeout: Hệ thống VNPAY-QR không phản hồi trong 60s'))
                    except (ValueError, requests.exceptions.ConnectionError):
                        raise UserError(_('Hệ thống VNPAY-QR có lỗi, vui lòng thử lại sau'))

                    result = resp_json  # json.dumps(resp_json)
                    if result:
                        code = result.get('code')
                        result_checksum_data = "%s|%s|%s|%s|%s|%s|%s|%s|%s|%s" % (master_merchant_code,
                                                                                  merchant_code,
                                                                                  result.get('terminalID'),
                                                                                  result.get('txnId'),
                                                                                  result.get('payDate'),
                                                                                  result.get('bankCode'),
                                                                                  result.get('qrTrace'),
                                                                                  result.get('debitAmount'),
                                                                                  result.get('realAmount'),
                                                                                  secret_key)

                        result_checksum = hashlib.md5(result_checksum_data.encode('utf-8')).hexdigest()
                        print('---------------->result:', result)
                        print('---------------->result_checksum:', result_checksum)
                        if result.get('checkSum').upper() == result_checksum.upper():
                            # TT 1 00 Success
                            if code == '00':
                                # Xử lý dữ liệu, cập nhật lại trạng thái của account.payment
                                code = 0
                                # {
                                #     "code": "00",
                                #     "message": "Giao dich thanh cong.",
                                #     "masterMerchantCode": "A000000775",
                                #     "merchantCode": "0314438965",
                                #     "terminalID": "ILOGIC01",
                                #     "billNumber": "317",
                                #     "txnId": "317",
                                #     "payDate": "19/12/2018 11:20:39",
                                #     "qrTrace": "000134800",
                                #     "bankCode": "VIETCOMBANK",
                                #     "debitAmount": "18500",
                                #     "realAmount": "18500",
                                #     "checkSum": "83299B0E97CBCF411C22C51AA141E427"
                                # }
                                payment.write({'state': 'posted'})

                            elif code == '01':
                                raise UserError('Không tìm thấy giao dịch')
                            elif code == '02':
                                raise UserError('PayDate không đúng định dạng')
                            elif code == '03':
                                raise UserError('TxnId không được null hoặc empty')
                            elif code == '04':
                                raise UserError('Giao dịch thất bại')
                            elif code == '05':
                                raise UserError('Giao dịch nghi vấn')
                            elif code == '11':
                                raise UserError('Dữ liệu đầu vào không đúng định dạng')
                            elif code == '14':
                                raise UserError('IP bị khóa')
                            elif code == '99':
                                raise UserError('Internal errors')
                        else:
                            raise UserError('Sai mã Checksum')

    def print_vnpay_qr_code(self):
        print('in phiếu')

    @api.model
    def create(self, vals_list):
        if vals_list.get('payment_method') == 'vdt':
            payment_token = self._get_payment_token(self._context.get('allowed_company_ids')[0])
            if not vals_list.get('payment_token_id') and payment_token:
                vals_list['payment_token_id'] = payment_token.id
            if not vals_list.get('journal_id') and payment_token:
                vals_list['journal_id'] = payment_token.acquirer_id.journal_id
        res = super(AccountPayment, self).create(vals_list)
        if vals_list.get('payment_method') == 'vdt':
            res.generate_vnpay_qr_code()
        return res

    def write(self, values):
        res = super(AccountPayment, self).write(values)
        return res

    # Thay đổi hình thức thanh toán, số tiền sẽ cập nhật lại QR code
    @api.onchange('company_id', 'amount_vnd')
    def _get_qr_code_data_onchange(self):
        self.ensure_one()
        if self.company_id and self.amount_vnd != 0 and self.payment_method == 'vdt':
            self.generate_vnpay_qr_code()

    @api.onchange('payment_token_id')
    def _get_journal(self):
        self.ensure_one()
        if self.payment_token_id:
            self.journal_id = self.payment_token_id.acquirer_id.journal_id

    def _get_payment_token(self, company_id):
        result = None
        payment_acquirer = self.env['payment.acquirer'].search([('company_id', '=', company_id)], limit=1)
        if payment_acquirer:
            result = self.env['payment.token'].search([('acquirer_id', '=', payment_acquirer.id)], limit=1)
        return result

    @api.onchange('payment_method')
    def _get_payment_token_id(self):
        self.ensure_one()
        if self.payment_method == 'vdt' and self.payment_type == 'inbound':
            payment_token_id = self._get_payment_token(self.company_id.id)
            if payment_token_id:
                self.payment_token_id = payment_token_id
            else:
                raise UserError(_('Chưa cấu hình payment token'))