from calendar import monthrange
from datetime import date, timedelta, datetime

from odoo.addons.sci_seeding.controllers.common import seeding_validate_token
from odoo.addons.restful.common import (
    extract_arguments,
    invalid_response,
    valid_response,
)
import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class CheckSeedingController(http.Controller):
    @seeding_validate_token
    @http.route("/api/v1/check-seeding", methods=["GET"], type="http", auth="none", csrf=False)
    def v1_get_report_seeding(self, **payload):
        """ Truy vấn báo cáo doanh thu theo nhóm dịch vụ"""
        domain, fields, offset, limit, order = extract_arguments(payload)
        data = []
        if payload.get('list_phone'):
            list_phone = payload.get('list_phone').split(", ")
            for phone in list_phone:
                bookings = request.env['crm.lead'].sudo().search(['|', ('phone', '=', phone), ('mobile', '=', phone),('source_id.code','not in',eval(payload.get('list_source'))), ('type','=','opportunity')])
                if bookings:
                    for booking in bookings:
                        if booking.crm_line_ids:
                            dv = []
                            doanh_so = []
                            for line in booking.crm_line_ids:
                                dv.append(line.service_id.name)
                        crm_sale_payment = request.env['crm.sale.payment'].sudo().search([('booking_id','=',booking.id)])
                        if crm_sale_payment:
                            for sp in crm_sale_payment:
                                doanh_so.append({
                                    'dich_vu': sp.service_id.name,
                                    'tien': sp.amount_proceeds,
                                    'ngay_thanh_toan': str(sp.account_payment_id.payment_date)
                                })
                        value = {
                            'name': booking.contact_name,
                            'bk_code': booking.name,
                            'phone_1': booking.phone if booking.phone else '',
                            'phone_2': booking.mobile if booking.mobile else '',
                            'booking_date': str(booking.booking_date) if booking.booking_date else '',
                            'day_expire': str(booking.day_expire) if booking.day_expire else '',
                            'dich_vu': dv,
                            'doanh_so': doanh_so,
                            'sale_create': booking.create_by.name
                        }
                        data.append(value)
            if data:
                return valid_response(data)
            else:
                return invalid_response('Error')
        else:
            return invalid_response('Error')