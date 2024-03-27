import logging

import requests

from odoo import fields, models
from odoo.addons.crm_ehc.models.ehc_common import get_token_ehc, get_url_ehc, get_api_code_ehc

_logger = logging.getLogger(__name__)


class ServiceDepartmentEHC(models.Model):
    _name = "crm.hh.ehc.department"
    _description = 'Department EHC'
    _rec_name = "room_name"

    room_id = fields.Integer('ID EHC')
    room_code = fields.Char('Mã')
    room_name = fields.Char('Tên phòng khám')
    id_department_room = fields.Integer('ID khoa EHC')
    code_department_room = fields.Char('Mã khoa')
    # room_type_id
    room_stage = fields.Selection([('0', 'Đang hoạt động'), ('1', 'Không hoạt động')],'Trạng thái', default=0)
    faculty_id = fields.Many2one('crm.hh.ehc.faculty', 'Khoa')

    def cron_get_department_ehc(self):
        token = get_token_ehc()
        url = get_url_ehc()
        api_code = get_api_code_ehc()

        url = url + '/api/department?api=%s' % api_code

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer %s' % token
        }

        r = requests.get(url, headers=headers)
        response = r.json()
        if 'status' in response and int(response['status']) == 0:
            for rec in response['data']:
                value = {
                    'room_id': rec['room_id'],
                    'room_code': rec['room_code'],
                    'room_name': rec['room_name'],
                    'id_department_room': rec['id_department_room'],
                    'code_department_room': rec['code_department_room'],
                    # 'room_type_id': rec['room_type_id'],
                    'room_stage': rec['stage']
                }
                # search khoa
                if 'id_department_room' in rec and rec['id_department_room']:
                    faculty_id = self.env['crm.hh.ehc.faculty'].search(
                        [('id_ehc', '=', int(rec['id_department_room']))])
                    if faculty_id:
                        value['faculty_id'] = faculty_id.id
                    else:
                        value['faculty_id'] = False

                room_ehc = self.env['crm.hh.ehc.department'].sudo().search([('room_id', '=', rec['room_id'])], limit=1)
                if room_ehc:
                    room_ehc.sudo().write(value)
                else:
                    room_ehc.sudo().create(value)
