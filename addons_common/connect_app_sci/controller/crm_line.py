import datetime
import logging

from odoo.addons.restful.controllers.app_member.app_member_common import response
from odoo.addons.restful.common import get_redis
from odoo.addons.connect_app_sci.controller.app_sci_common import validate_token, response, get_user_by_token, \
    extract_arguments
from odoo.http import request
import json

from odoo import http

_logger = logging.getLogger(__name__)
api_access_database = "restful.api_access_database"
expires_in = "restful.access_token_expires_in"
r = get_redis()


class GetCRMLine(http.Controller):

    @http.route("/api/v1/get-crm-line", methods=["GET"], type="http", auth="none", csrf=False)
    def get_crm_line(self, **payload):
        booking_id = payload.get("booking_id", None)
        booking_id = int(booking_id)
        booking_id = request.env['crm.lead'].sudo().search([('id', '=', booking_id)])
        if not booking_id:
            return response({}, message_content='Không tìm thấy Booking', status=2, message_type=1)
        lines = request.env['crm.line'].sudo().search([('crm_id', '=', booking_id.id)], order='create_date asc')
        data = {}
        sell = []
        if booking_id.effect == 'effect':
            data.update({'is_create': True})
        else:
            data.update({'is_create': False})
        for line in lines:
            sell.append({
                'id': line.id,
                'name': line.service_id.name,
                'currency_name': line.currency_id.name,
                'currency_id': line.currency_id.id,
                'unit_price': line.unit_price,
                'uom_price': line.uom_price,
                'quantity': line.quantity,
                'discount_percent': line.discount_percent,
                'discount_cash': line.discount_cash,
                'sale_to': line.sale_to,
                'other_discount': line.other_discount,
                'total_before_discount': line.total_before_discount,
                'total_discount': line.total_discount,
                'total': line.total,
                'company_name': line.company_id.name,
                'company_id': line.company_id.id,
                'pricelist_name': line.price_list_id.name,
                'pricelist_id': line.price_list_id.id,
                'stage': dict(line._fields['stage'].selection).get(line.stage)
            })
        data.update({'sell': sell})

        if data:
            return response(data, message_content='Thành công', status=0, message_type=1)
        else:
            return response({}, message_content='Không có thông tin', status=2, message_type=1)