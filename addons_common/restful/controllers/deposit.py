"""Part of odoo. See LICENSE file for full copyright and licensing details."""
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


class DepositController(http.Controller):

    @validate_token
    @http.route('/api/v1/account-journal', type="http", auth="none", methods=["GET"], csrf=False)
    def get_journal_id(self, company_id=None, payment_method=None, **payload):
        """ API 1.12 Danh sách sổ nhật ký"""
        domain, fields, offset, limit, order = extract_arguments(payload)
        domain = []
        _logger.info(payment_method)
        if company_id:
            domain += [("company_id", "=", int(company_id))]
        method = 'cash'
        if payment_method:
            payment_method = int(payment_method)
            if payment_method == 2:
               method = 'bank'
            domain += [("type", "=", method)]
        return valid_response(request.env['account.journal'].api_get_data(company_id=int(company_id), type=method))
        fields = ['id', 'name']
        data = request.env['account.journal'].search_read(domain=domain, fields=fields)
        if data:
            return valid_response(data)
        else:
            return invalid_response('Not found account journal')

    @validate_token
    @http.route('/api/v1/crm-request-deposit/create', type="http", auth="none", methods=["POST"], csrf=False)
    def request_deposit(self, **payload):
        """API 1.15 Tạo phiếu đặt cọc"""

        """
        data = {
            'partner_id': '514183',
            'brand_id':'1',
            'company_id':'2',
            'booking_id': '818344',
            'discount_program_id':'67',
            'payment_date':'2021-07-26',
            'payment_method':'1',
            'currency':'3',
            'amount':'2000000',
            'journal_id':'121',
            'note':'Tài khoản 1241xxxx525341 Ngân hàng BIDV đặt cọc dịch vụ Bấm mí mắt',
        }
        """
        _logger.info('========================= Payload ======================================================')
        _logger.info(payload)
        _logger.info('=========================================================================================')
        field_required = ['booking_id', 'company_id', 'payment_date', 'payment_method',
                          'amount', 'journal_id', 'note']
        data = {}
        for field in field_required:
            if field not in payload:
                return invalid_response(
                    "Missing",
                    "The parameter %s is missing." % field,
                )
        brand_id = request.brand_id
        data['brand_id'] = brand_id
        # Lấy ra Chi nhánh
        company = request.env['res.company'].search(
            [('id', '=', int(payload['company_id'])), ('brand_id', '=', brand_id)])
        if company:
            data['company_id'] = company.id
        else:
            return invalid_response(
                "Missing",
                "This Company does not exist",
            )

        # Lấy ra booking
        domain = [('id', '=', int(payload['booking_id'])), ('effect', '=', 'effect'), ('company_id', '=', company.id)]
        booking = request.env['crm.lead'].search(domain)
        if booking:
            data['booking_id'] = booking.id
            data['partner_id'] = booking.partner_id.id
        else:
            return invalid_response(
                "Missing",
                "Mã Booking này hiện không tồn tại trên hệ thống hoặc đã hết hiệu lực!!!" % company.name,
            )
        # Chuyển đổi payment_method
        if payload['payment_method'] == '2':
            method = 'ck'
        elif payload['payment_method'] == '3':
            method = 'nb'
        elif payload['payment_method'] == '4':
            method = 'pos'
        elif payload['payment_method'] == '5':
            method = 'vdt'
        else:
            method = 'tm'
        data['payment_method'] = method

        # Lấy ra sổ nhật ký
        journal = request.env['account.journal'].sudo().search([('id', '=', int(payload['journal_id']))])
        if journal:
            data['journal_id'] = journal.id
        else:
            return invalid_response(
                "Missing",
                "This Journal does not exist",
            )

        # Lấy ra currency_id
        currency_name = 'VND'
        if 'currency' in payload:
            if int(payload['currency']) == 1:
                currency_name = 'EUR'
            elif int(payload['currency']) == 2:
                currency_name = 'EUR'
        currency_id = request.env['res.currency'].sudo().search([('name', '=', currency_name)])
        if journal:
            data['currency_id'] = currency_id.id
        # Lấy ra chương trình Khuyến mại
        if 'discount_program_id' in payload:
            discount_program = request.env['crm.discount.program'].search(
                [('id', '=', int(payload['discount_program_id']))])
            if discount_program:
                data['discount_program_id'] = discount_program.id

        data['payment_date'] = payload['payment_date']
        data['amount'] = int(payload['amount'])
        data['name'] = payload['note']
        request_deposit = request.env['crm.request.deposit'].sudo().create(data)
        request_deposit.sudo().with_context(communication=data['name']).convert_payment()

        _logger.info('========================= Data ======================================================')
        _logger.info(data)
        _logger.info('=========================================================================================')
        return valid_response('Đã tạo phiếu và hóa đơn duyệt nợ')
