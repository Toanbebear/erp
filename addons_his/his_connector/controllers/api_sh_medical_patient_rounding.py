from calendar import monthrange
from datetime import date, timedelta, datetime
from odoo.addons.restful.common import (
    extract_arguments,
    invalid_response,
    valid_response,
    valid_response_once
)
import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class ShMedicalPatientRounding83Controller(http.Controller):

    @http.route("/api/83/v1/get-patient-rounding-ids/<phone>", methods=["GET"], type="http", auth="none", csrf=False)
    def v1_83_get_lab_test_ids(self, phone=None, **payload):
        if phone:
            partner = request.env['res.partner'].sudo().search([('phone', '=', phone)], limit=1)
            if partner:
                patient = request.env['sh.medical.patient'].sudo().search([('partner_id', '=', partner.id)], limit=1)
                if patient:
                    patient_rounding_ids = request.env['sh.medical.patient.rounding'].sudo().search(
                        [('patient', '=', patient.id), ('state', '=', 'Completed')])
                    if patient_rounding_ids:
                        data = []
                        for patient_rounding_id in patient_rounding_ids:
                            data.append({
                                'walkin_id': patient_rounding_id.walkin.id,
                                'walkin_name': patient_rounding_id.walkin.name,
                                'rounding_test_id': patient_rounding_id.id,
                                'rounding_test_name': patient_rounding_id.name,
                            })
                        return valid_response(data)
                    else:
                        return valid_response([])
                else:
                    return invalid_response("ERROR", "Khong tim thay benh nhan !!!")
            else:
                return invalid_response("ERROR", "Khong tim thay khach hang !!!")
        else:
            return invalid_response("ERROR", "Khong nhan duoc so dien thoai !!!")

    @http.route("/api/83/v1/get-patient-rounding/<id>", methods=["GET"], type="http", auth="none", csrf=False)
    def v1_83_get_surgery(self, id=None, **payload):
        if id:
            rounding = request.env['sh.medical.patient.rounding'].sudo().browse(int(id))
            if rounding:
                data = {
                    'id': rounding.id,
                    'name': rounding.name,
                    'evaluation_start_date': rounding.evaluation_start_date.strftime('%Y-%m-%d %H:%M:%S') if rounding.evaluation_start_date else '',
                    'evaluation_end_date': rounding.evaluation_end_date.strftime('%Y-%m-%d %H:%M:%S') if rounding.evaluation_end_date else '',
                }

                supplies = []
                supplies_code = []
                for sup in rounding.medicaments:
                    if sup.medicine.default_code:
                        supplies_code.append(sup.medicine.default_code)
                    supplies.append({
                        'supply_name': sup.medicine.name_use if sup.medicine else '',
                        'supply_code': sup.medicine.default_code if sup.medicine else '',
                        'qty': sup.qty if sup.qty else '',
                        'uom_id': sup.uom_id.name if sup.uom_id else '',
                    })
                data['supplies'] = supplies
                data['supplies_code'] = supplies_code

                return valid_response_once(data)
            else:
                return invalid_response("ERROR", "Khong tim thay phieu CSHP co id = %s !!!" % id)
        else:
            return invalid_response("ERROR", "Khong nhan duoc id !!!")
