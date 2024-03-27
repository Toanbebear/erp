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
import pyotp
from odoo import http
from odoo.http import request
import requests
from datetime import datetime, date, time, timedelta
from pytz import timezone, utc


class ProductManualController(http.Controller):

    @validate_token
    @http.route("/api/v1/manual/get-data/<booking_code>/<company_code>", type="http", auth="none", methods=["GET"],
                csrf=False)
    def v1_manual_get_data(self, booking_code=None, company_code=None, **payload):
        if booking_code and company_code:
            booking = request.env['crm.lead'].sudo().search(
                [('name', '=', booking_code), ('type', '=', 'opportunity'), ('stage_id', '=', request.env.ref("crm.stage_lead4").id)])
            walkin_ids = booking.walkin_ids

            phieu_pt = []
            phieu_ck = []
            for walkin in walkin_ids:
                for sur in walkin.surgeries_ids:
                    phieu_pt.append(sur)
                for speccialty in walkin.specialty_ids:
                    phieu_ck.append(speccialty)

            data = []
            for pt in phieu_pt:
                for ser in pt.services:
                    data.append({
                        'customer_name': pt.patient.name,
                        'name': pt.name,
                        'date': pt.surgery_date,
                        'service': ser.name,
                        'service_code': ser.default_code,
                    })
            for ck in phieu_ck:
                for ser in ck.services:
                    data.append({
                        'customer_name': ck.patient.name,
                        'name': ck.name,
                        'date': ck.services_date,
                        'service': ser.name,
                        'service_code': ser.default_code,
                    })
            return valid_response(data)
