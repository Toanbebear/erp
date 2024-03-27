from datetime import datetime, timedelta
import json
import logging

from odoo.addons.restful.common import (
    valid_response,
    valid_response_once,
    invalid_response
)
from odoo.addons.restful.controllers.main import (
    get_url_base,
    validate_token,
)
from odoo import fields
# import pyotp
from odoo import http
from odoo.http import request
import requests
from datetime import datetime, date, time, timedelta
from pytz import timezone, utc

_logger = logging.getLogger(__name__)
STAGE = {
    'cho_tu_van': 'Chờ tư vấn',
    'dang_tu_van': 'Đang tư vấn',
    'hoan_thanh': 'Hoàn thành',
    'huy': 'Hủy',
    '': ''
}


class CheckinController(http.Controller):

    @http.route("/datatable/print-data-checkin/<id>", type="http")
    def print_data_checkin(self, id=None, **payload):
        booking_id = request.env['crm.lead'].sudo().browse(int(id))
        r = request.env.ref('check_in_app.action_customer_info_sheet_qr')
        pdf = r.sudo().render_qweb_pdf([int(booking_id.id)])[0]
        pdfhttpheaders = [('Content-Type', 'application/pdf'),
                          ('Content-Length', len(pdf)), ]
        return request.make_response(pdf, headers=pdfhttpheaders)

    @http.route("/datatable/get-data-checkin", type="http", methods=["POST"], csrf=False)
    def get_data_checkin(self, **payload):
        local_tz = timezone('Etc/GMT+7')
        now = datetime.now()
        today = now.date()
        domain = [('create_date', '>=', datetime.combine(today, time(0, 0, 0)) - timedelta(hours=7)),
                  ('create_date', '<=', datetime.combine(today, time(23, 59, 59)) - timedelta(hours=7)),
                  ('create_uid', '=', request.env.user.id), ('booking', '!=', False)]
        if 'query' in payload:
            domain.extend(['|', '|', ('booking.name', 'ilike', "%" + payload.get('query') + "%"),
                          ('partner.name', 'ilike', "%" + payload.get('query') + "%"),
                          ('partner.phone', 'ilike', "%" + payload.get('query') + "%")])
        checkin = request.env['crm.check.in'].sudo().search(domain,
                                                            order='create_date desc', limit=int(payload.get('length')),
                                                            offset=int(payload.get('start'))
                                                            )
        count_checkin = request.env['crm.check.in'].sudo().search_count(domain)
        data = []
        if checkin:
            stt = int(payload.get('start')) + 1
            booking_action_id = request.env.ref('crm.crm_lead_action_pipeline').id
            booking_menu_id = request.env.ref('crm.crm_menu_root').id
            for rec in checkin:
                url = get_url_base() + "/web#id=%d&model=crm.lead&view_type=form&action=%d&menu_id=%d" % (
                    rec.booking.id, booking_action_id, booking_menu_id)
                data.append([
                    stt,
                    local_tz.localize(rec.create_date, is_dst=None).astimezone(utc).replace(tzinfo=None).strftime(
                        "%d-%m-%Y %H:%M:%S"),
                    "<a href='" + url + "' target='new'>" + rec.booking.name + "</a>",
                    rec.booking.company_id.name,
                    rec.partner.name,
                    STAGE[rec.stage],
                    "<a href='/datatable/print-data-checkin/" + str(
                        rec.booking.id) + "' class='btn btn-primary' target='new'>" + "<i class='fa fa-print'></i>  In phiếu</span></a>"
                ])
                stt += 1

        return json.dumps({
            'iTotalRecords': count_checkin,
            'iTotalDisplayRecords': count_checkin,
            'data': data
        })
