# Part of odoo. See LICENSE file for full copyright and licensing details.
import json
import logging

from odoo.addons.crm_ehc.controllers.crm_hh_ehc_common import ehc_validate_token, get_user_hh

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class SupplyMedicineEHCController(http.Controller):
    @ehc_validate_token
    @http.route("/api/v1/update-material", methods=["POST"], type="json", auth="none", csrf=False)
    def v1_ehc_update_supply_medicine(self, **payload):
        """
            7.2 API cập nhật thuốc - vật tư EHC-HIS
        """
        # get body
        body = json.loads(request.httprequest.data.decode('utf-8'))
        _logger.info('========================= 7.2 API cập nhật thuốc - vật tư EHC-HIS ==================')
        _logger.info(body)
        _logger.info('=================================================================================')

        field_require = [
            'material_id',
            'material_code',
            'material_name',
            'master_id',
            'group_id',
            'material_unit',
            'material_content',
            'material_category',
            'material_specifications',
            'material_route_of_use',
            'material_brand_name',
            'material_active_ingredient'
        ]
        for field in field_require:
            if field not in body.keys():
                return {
                    'stage': 1,
                    'message': 'Thieu tham so %s!!!' % field
                }

        if body['material_code']:
            default_code_ehc = 'EHC-' + body['material_code']
            data = {
                'name': body['material_name'],
                'default_code': default_code_ehc,
                'material_id': body['material_id'],
                'material_code': body['material_code'],
                'master_id': body['master_id'],
                'group_id': body['group_id'],
                'material_unit': body['material_unit'],
                'material_content': body['material_content'],
                'material_category': str(body['material_category']),
                'material_specifications': body['material_specifications'],
                'material_route_of_use': body['material_route_of_use'],
                'material_brand_name': body['material_brand_name'],
                'material_active_ingredient': body['material_active_ingredient'],
                'active': False
            }
            if body['master_id'] in [7, 8]:
                if int(body['master_id']) == 7:
                    data['type_material_ehc'] = 'th'
                else:
                    data['type_material_ehc'] = 'vt'
            else:
                return {
                    'stage': 1,
                    'message': 'Truong master_id chi nhan 2 gia tri: 7- Thuoc và 8- Vat tu!!!'
                }
            exits_product = request.env['product.product'].sudo().search(
                [('default_code', '=', default_code_ehc), ('active', '=', False)], limit=1)
            if exits_product:
                exits_product.product_tmpl_id.with_user(get_user_hh()).sudo().write(data)
                exits_product.with_user(get_user_hh()).sudo().write(data)
                exits_product.product_tmpl_id.write({'default_code': default_code_ehc})
                return {
                    'stage': 0,
                    'message': 'Cap nhat thuoc/ vat tu thanh cong!!!'
                }
            else:
                data['type'] = 'consu'
                product_template = request.env['product.template'].with_user(get_user_hh()).sudo().create(data)
                product = request.env['product.product'].sudo().search(
                    [('product_tmpl_id', '=', product_template.id), ('active', '=', False)], limit=1)
                product.sudo().write({
                    'default_code': default_code_ehc,
                    'material_id': body['material_id'],
                    'material_code': body['material_code'],
                    'master_id': body['master_id'],
                    'group_id': body['group_id'],
                    'material_unit': body['material_unit'],
                    'material_content': body['material_content'],
                    'material_category': str(body['material_category']),
                    'material_specifications': body['material_specifications'],
                    'material_route_of_use': body['material_route_of_use'],
                    'material_brand_name': body['material_brand_name'],
                    'material_active_ingredient': body['material_active_ingredient'],
                })
                return {
                    'stage': 0,
                    'message': 'Cap nhat thuoc/ vat tu thanh cong!!!'
                }