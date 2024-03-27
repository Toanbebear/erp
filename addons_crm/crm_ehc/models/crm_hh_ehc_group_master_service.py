import logging

import requests

from odoo import fields, models
from odoo.addons.crm_ehc.models.ehc_common import get_token_ehc, get_url_ehc, get_api_code_ehc

_logger = logging.getLogger(__name__)


class GroupMasterServiceEHC(models.Model):
    _name = "crm.hh.ehc.group.master.service"
    _description = 'Group master service'

    group_master_id = fields.Integer('ID nhóm dịch vụ EHC')
    group_master_code = fields.Char('Mã nhóm dịch vụ EHC')
    name = fields.Char('Tên nhóm dịch vụ')
    code = fields.Char('Mã nhóm dịch vụ')
    stage = fields.Selection([('0', 'Đang hoạt động'), ('1', 'Không hoạt động')])


class InheritProductCategory(models.Model):
    _inherit = "product.category"

    type_ehc_id = fields.Integer('ID loại dịch vụ')
    group_master_id = fields.Many2one('crm.hh.ehc.group.master.service')
    stage = fields.Selection([('0', 'Đang hoạt động'), ('1', 'Không hoạt động')], string='Trạng thái')

    def cron_get_type_service_ehc(self):
        token = get_token_ehc()
        url = get_url_ehc()
        api_code = get_api_code_ehc()

        url = url + '/api/typeservice?api=%s' % api_code

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer %s' % token
        }

        r = requests.get(url, headers=headers)
        response = r.json()
        _logger.info('========================= cron get type service ===================================')
        if 'status' in response and int(response['status']) == 0:
            for rec in response['data']:
                # group_master_id = self.env['crm.hh.ehc.group.master.service'].sudo().search(
                #     [('group_master_code', '=', rec['group_master_code']),
                #      ('group_master_id', '=', int(rec['group_master_id']))])
                code = 'EHC-' + rec['type_code']
                product_category_ehc = self.env['product.category'].sudo().search([('code', '=', code)])
                value = {
                    'type_ehc_id': rec['type_id'],
                    'stage': str(rec['stage']),
                    'name': rec['type_name'],
                }
                if product_category_ehc:
                    result = product_category_ehc.sudo().write(value)
                    if result:
                        self.update_type_service_his_erp(type_service=product_category_ehc, type=1)
                    _logger.info("write: %s" % result)
                else:
                    value['code'] = code
                    product_category_ehc = product_category_ehc.sudo().create(value)
                    if product_category_ehc:
                        self.update_type_service_his_erp(type_service=product_category_ehc, type=0)
                    _logger.info("create: %s" % product_category_ehc)

    def update_type_service_his_erp(self, type_service, type):
        # 0: tạo mới
        # khác 0: cập nhật
        if type_service:
            data = {
                'product_cat_id': type_service.id,
                'name': type_service.name,
                'complete_name': type_service.complete_name if type_service.complete_name else type_service.name,
            }
            if type == 0:
                service_category_his = self.env['sh.medical.health.center.service.category'].sudo().create(data)
            else:
                service_category_his = self.env['sh.medical.health.center.service.category'].sudo().write(data)
