from calendar import monthrange
from datetime import date, timedelta, datetime
from odoo.addons.restful.common import (
    extract_arguments,
    invalid_response,
    valid_response,
    valid_response_once,
)
import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class ShMedicalPrescription83Controller(http.Controller):

    @http.route("/api/83/v1/get-prescription-ids/<phone>", methods=["GET"], type="http", auth="none", csrf=False)
    def v1_83_get_prescription_ids(self, phone=None, **payload):
        if phone:
            partner = request.env['res.partner'].sudo().search([('phone', '=', phone)], limit=1)
            if partner:
                patient = request.env['sh.medical.patient'].sudo().search([('partner_id', '=', partner.id)], limit=1)
                if patient:
                    prescription_ids = request.env['sh.medical.prescription'].sudo().search([('patient', '=', patient.id), ('state', '=', 'Đã xuất thuốc')])
                    if prescription_ids:
                        data = []
                        for prescription_id in prescription_ids:
                            data.append({
                                'walkin_id': prescription_id.walkin.id,
                                'walkin_name': prescription_id.walkin.name,
                                'prescription_id': prescription_id.id,
                                'prescription_name': prescription_id.name,
                                'service_patient_erp': ', '.join(prescription_id.services.mapped('name')),
                                'name_patient_erp': prescription_id.patient.name + '' + '-' + '' + (prescription_id.patient.birth_date and prescription_id.patient.birth_date.strftime('%Y') or ''),
                                'prescription_date': prescription_id.date,
                            })
                        return valid_response(data)
                    else:
                        return valid_response([])
                else:
                    return invalid_response("ERROR", "Khong tim thay benh nhan !!!")
            else:
                return invalid_response("ERROR", "Khong tim thay khach hang !!!")
        else:
            return invalid_response("ERROR", "Khong tim thay so dien thoai !!!")

    @http.route("/api/83/v1/get-prescription/<id>", methods=["GET"], type="http", auth="none", csrf=False)
    def v1_83_get_prescription(self, id=None, **payload):
        if id:
            prescription = request.env['sh.medical.prescription'].sudo().browse(int(id))
            if prescription:
                data = {
                    'id': prescription.id,
                    'name': prescription.name,
                    'date': prescription.date.strftime('%Y-%m-%d %H:%M:%S') if prescription.date else '',   # Ngày làm dịch vụ
                    'date_out': prescription.date_out.strftime('%Y-%m-%d %H:%M:%S') if prescription.date_out else '', # Ngày xuất thuốc
                    'diagnose': prescription.diagnose if prescription.diagnose else '',  # Ngày xuất thuốc
                }
                supplies = []
                supplies_code = []
                for sup in prescription.prescription_line:
                    if sup.name.default_code:
                        supplies_code.append(sup.name.default_code)
                    supplies.append({
                        'supply_name': sup.name.name_use if sup.name else '',
                        'supply_code': sup.name.default_code if sup.name else '',
                        'qty_used': sup.qty if sup.qty else '',
                        'info': sup.info if sup.info else '',
                        'uom': sup.dose_unit_related.name if sup.dose_unit_related else '',
                    })
                data['supplies'] = supplies
                data['supplies_code'] = supplies_code

                return valid_response_once(data)
            else:
                return invalid_response("ERROR", "Không tìm thấy đơn thuốc co id = %s !!!" % id)
        else:
            return invalid_response("ERROR", "không nhận được id !!!")
