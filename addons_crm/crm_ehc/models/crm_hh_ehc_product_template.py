import logging

import requests

from odoo import fields, models
from odoo.addons.crm_ehc.controllers.crm_hh_ehc_common import get_user_hh
from odoo.addons.crm_ehc.models.ehc_common import get_token_ehc, get_url_ehc, get_api_code_ehc

_logger = logging.getLogger(__name__)


class ProductEHC(models.Model):
    _inherit = 'product.template'

    # thông tin dịch vụ EHC
    service_id_ehc = fields.Integer('ID dịch vụ EHC')
    service_code_ehc = fields.Char('Mã dịch vụ EHC')
    service_price_bhyt = fields.Monetary('Giá BHYT')
    service_code_bhyt = fields.Char('Mã BHYT')
    service_type = fields.Char('Loại phẫu thuật')
    service_unit = fields.Char('Đơn vị tính')
    stage = fields.Selection([('0', 'Đang hoạt động'), ('1', 'Không hoạt động')])
    service_room_ids = fields.Many2many('crm.hh.ehc.department', 'crm_hh_ehc_product_template_rel', 'service_id', 'room_id',
                                        string='Phòng')

    # thông tin cho thuốc - vật tư EHC
    material_id = fields.Integer('ID th/vt EHC')
    master_id = fields.Integer('Master ID')
    group_id = fields.Integer('Group ID')
    material_code = fields.Char('Mã th/vt EHC')
    material_unit = fields.Char('Đơn vị tính')
    material_content = fields.Char('Hàm lượng')
    material_category = fields.Selection([('1', 'Bán lẻ'), ('0', 'Sử dụng trong bệnh viện')], string='Loại')
    material_specifications = fields.Char('Quy cách')
    material_route_of_use = fields.Char('Đường dùng')
    material_brand_name = fields.Char('Biệt dược')
    material_active_ingredient = fields.Char('Tên hoạt chất')
    type_material_ehc = fields.Selection([('th', 'Thuốc'), ('vt', 'Vật tư')])

    # phân loại dịch vụ
    vs_hm = fields.Boolean('VSHM', default=False)
    pttm = fields.Boolean('PTTM', default=False)
    da_khoa = fields.Boolean('DAKHOA', default=False)

    def cron_get_material_ehc(self):
        token = get_token_ehc()
        url = get_url_ehc()
        api_code = get_api_code_ehc()

        url = url + '/api/material?api=%s' % api_code

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer %s' % token
        }

        r = requests.get(url, headers=headers)
        response = r.json()
        i = 0
        if 'status' in response and int(response['status']) == 0:
            for rec in response['data']:
                material_code = 'EHC-' + rec['material_code']
                if int(rec['master_id']) == 7:
                    master_id = 'th'
                else:
                    master_id = 'vt'
                data = {
                    'name': rec['material_name'],
                    'default_code': material_code,
                    'material_id': rec['material_id'],
                    'material_code': rec['material_code'],
                    'type_material_ehc': master_id,
                    'group_id': rec['group_id'],
                    'material_unit': rec['material_unit'],
                    'material_content': rec['material_content'],
                    'material_category': str(rec['material_category']),
                    'material_specifications': rec['material_specifications'],
                    'material_route_of_use': rec['material_route_of_use'],
                    'material_brand_name': rec['material_brand_name'],
                    'material_active_ingredient': rec['material_active_ingredient'],
                    'active': False
                }
                exits_product = self.env['product.product'].sudo().search(
                    [('default_code', '=', material_code), ('active', '=', False)], limit=1)
                _logger.info("prd: %s" % exits_product)
                _logger.info("stt: %s" % i)
                i += 1
                if exits_product:
                    _logger.info("write")
                    exits_product.product_tmpl_id.with_user(get_user_hh()).sudo().write(data)
                    # exits_product.with_user(get_user_hh()).sudo().write(data)
                    # exits_product.product_tmpl_id.with_user(get_user_hh()).write({'default_code': material_code})
                else:
                    _logger.info("create")
                    data['type'] = 'consu'
                    product_template = self.env['product.template'].with_user(get_user_hh()).sudo().create(data)
                    # product = self.env['product.product'].with_user(get_user_hh()).sudo().search(
                    #     [('product_tmpl_id', '=', product_template.id)], limit=1)
                    # product.with_user(get_user_hh()).sudo().write(data)
