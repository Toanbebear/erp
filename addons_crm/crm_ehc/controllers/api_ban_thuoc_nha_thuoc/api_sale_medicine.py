# Part of odoo. See LICENSE file for full copyright and licensing details.
import json
import logging

from odoo import http
from odoo.addons.crm_ehc.controllers.crm_hh_ehc_common import ehc_validate_token, get_user_hh, \
    convert_string_to_date, get_company_id_hh, get_price_list_id_hh, get_brand_id_hh
from odoo.http import request

_logger = logging.getLogger(__name__)


class SaleMedicineEHCController(http.Controller):

    @ehc_validate_token
    @http.route("/api/v1/sale-medicine", methods=["POST"], type="json", auth="none", csrf=False)
    def v1_ehc_sale_medicine(self, **payload):
        body = json.loads(request.httprequest.data.decode('utf-8'))
        _logger.info('========================= API bán thuốc nhà thuốc ==================')
        _logger.info(body)
        _logger.info('=================================================================================')
        field_require = [
            'booking_code',
            'patient_code',
            'patient_name',
            'create_date',
            'approval_date',
            'out_date',
            'list_medicine',
        ]
        for field in field_require:
            if field not in body.keys():
                return {
                    'stage': 1,
                    'message': 'Thieu tham so %s!!!' % field
                }
        booking = request.env['crm.lead'].sudo().search([('name', '=', body['booking_code']), ('type', '=', 'opportunity'), '|',('company_id.brand_id.code', '=', 'HH'), ('company2_id.brand_id.code', '=', 'HH')], limit=1)
        if booking:
            patient = request.env['sh.medical.patient'].sudo().search([('code_customer','=',body['patient_code'])])
            if patient:
                value = {'booking_id': booking.id,
                        'patient_id': patient.id}
                field_date_values = {
                    'create_date_ehc': 'create_date',
                    'approval_date': 'approval_date',
                    'out_date': 'out_date'
                }
                for field_date_value in field_date_values:
                    if field_date_values[field_date_value] in body and body[field_date_values[field_date_value]]:
                        if body[field_date_values[field_date_value]] != '000101010000':
                            value['%s' % field_date_value] = convert_string_to_date(body[field_date_values[field_date_value]])
                        else:
                            value['%s' % field_date_value] = False
                sale_medicine = request.env['crm.hh.ehc.sale.medicine'].sudo().create(value)
                if body['list_medicine']:
                    for medicine in body['list_medicine']:
                        product = request.env['product.product'].sudo().search([('default_code','=',medicine['medicine_code'])])
                        if product:
                            value_product = {
                                'booking_id': booking.id,
                                'product_id': product.id,
                                'product_uom_qty': medicine['quantity'],
                                'price_unit': medicine['unit_price'],
                                'product_uom': product.uom_id.id
                            }
                        else:
                            value_line = {'ehc_sale_medicine_id': sale_medicine.id,
                                          'medicine_code': medicine['medicine_code'],
                                          'medicine_name': medicine['medicine_name'],
                                          'unit': medicine['unit'],
                                          'quantity': medicine['quantity'],
                                          'unit_price': medicine['unit_price']}
                            list_medicine = request.env['crm.hh.ehc.sale.medicine'].sudo().create(value_line)

            else:
                pass
        else:
            return {
                'stage': 0,
                'message': 'Khong the tim thay Booking co ma %s!!!' % body['booking_code'],
                'data': {
                    'booking_code': body['booking_code']
                }
            }