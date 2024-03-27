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

DEFAULT_SERVER_DATE_FORMAT = "%Y-%m-%d"
DEFAULT_SERVER_TIME_FORMAT = "%H:%M:%S"
DEFAULT_SERVER_DATETIME_FORMAT = "%s %s" % (
    DEFAULT_SERVER_DATE_FORMAT,
    DEFAULT_SERVER_TIME_FORMAT)


class BookingController(http.Controller):
    @http.route("/api/v1/fe/bookings", type="http", auth="none", methods=["GET"], csrf=False)
    def get_bookings(self, **payload):
        domain, fields, offset, limit, order = extract_arguments(payload)
        count = request.env['crm.lead'].sudo().search_count([])
        domain = [('active', '=', True), ('type', '=', 'opportunity')]
        if 'company_id' in payload:
            domain.append(('company_id', 'in', [com for com in eval(payload.get('company_id'))]))
        bookings = request.env['crm.lead'].sudo().search_read(domain=domain,
                                                              fields=['id', 'name', 'customer_classification',
                                                                      'contact_name',
                                                                      'phone', 'source_id', 'booking_date',
                                                                      'arrival_date', 'company_id',
                                                                      'stage_id', 'effect'],
                                                              offset=offset,
                                                              limit=limit,
                                                              order='create_date desc')

        customer_classification = {
            '1': 'Bình thường',
            '2': 'Quan tâm',
            '3': 'Quan tâm hơn',
            '4': 'Đặc biệt',
            '5': 'Khách hàng V.I.P',
        }

        effect = {
            'not_valid': 'Chưa hiệu lực',
            'effect': 'Hiệu lực',
            'expire': 'Hết hiệu lực',
        }

        booking = []
        for book in bookings:
            booking.append([
                book['id'],
                customer_classification[book['customer_classification']] if book['customer_classification'] and book['customer_classification'] in customer_classification else '',
                book['name'],
                book['contact_name'],
                book['phone'],
                book['source_id'][1],
                book['booking_date'].strftime(DEFAULT_SERVER_DATETIME_FORMAT) if book[
                    'booking_date'] else '',
                book['arrival_date'].strftime(DEFAULT_SERVER_DATETIME_FORMAT) if book[
                    'arrival_date'] else '',
                book['stage_id'][1],
                book['company_id'][1],
                effect[book['effect']] if book['effect'] and book['effect'] in effect else '',
            ])
        data = {
                'iTotalRecords': count,
                'iTotalDisplayRecords': count,
                'data': booking
            }
        return valid_response(data)
