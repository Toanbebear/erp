import json

import requests

from odoo import fields, api, models, _
from odoo.exceptions import ValidationError


class SyncHis83Wizard(models.TransientModel):
    _name = 'sync.his.83.wizard'
    _description = 'Tạo hồ sơ 83 TC'

    company_id = fields.Many2one('res.company', string='Công ty', )
    booking_id = fields.Many2one('crm.lead', string='Booking')

    @api.onchange('company_id')
    def domain_company_id(self):
        domain = []
        if self.booking_id:
            return {
                'domain': {
                    'company_id': [('id', 'in', self.booking_id.company2_id.ids + [self.booking_id.company_id.id])]}
            }
        return {'domain': {'company_id': []}}

    def post(self):
        view = self.env.ref('sh_message.sh_message_wizard')
        view_id = view and view.id or False
        context = dict(self._context or {})
        for rec in self.booking_id:
            if self.company_id.token_his:
                if rec.birth_date:
                    url = self.company_id.url_his_83 + "/api/create-patient"
                    access_token = self.company_id.token_his
                    payload = json.dumps({
                        "year_of_birth": str(rec.birth_date) if rec.birth_date else '',
                        "gender": rec.gender if rec.gender else '',
                        "name": rec.contact_name if rec.contact_name else '',
                        "phone": rec.phone if rec.phone else '',
                        "career": rec.career if rec.career else '',
                        "country_id": rec.country_id.code if rec.country_id else '',
                        "street": rec.street if rec.street else '',
                        "state_id": rec.state_id.cs_id if rec.state_id else '',
                        "district_id": rec.district_id.cs_id if rec.district_id else '',
                        "ward_id": rec.ward_id.id_dvhc if rec.ward_id else '',
                        'weight': rec.partner_id.weight if rec.partner_id.weight else '',
                        'height': rec.partner_id.height if rec.partner_id.height else '',
                    })
                    headers = {
                        'access-token': access_token,
                        'Content-Type': 'application/json',
                    }
                    response = requests.request("POST", url, headers=headers, data=payload)
                    response = response.json()
                    if 'stage' in response and response['stage'] == 1:
                        context['message'] = 'Tạo hồ sơ thành công !!!'
                        return {
                            'name': 'THÔNG BÁO THÀNH CÔNG',
                            'type': 'ir.actions.act_window',
                            'view_type': 'form',
                            'view_mode': 'form',
                            'res_model': 'sh.message.wizard',
                            'views': [(view_id, 'form')],
                            'view_id': view.id,
                            'target': 'new',
                            'context': context,
                        }
                    else:
                        context['message'] = 'Tạo hồ sơ thất bại !!! Liên hệ IT để nhận được hỗ trợ'
                        return {
                            'name': 'THÔNG BÁO THẤT BẠI',
                            'type': 'ir.actions.act_window',
                            'view_type': 'form',
                            'view_mode': 'form',
                            'res_model': 'sh.message.wizard',
                            'views': [(view_id, 'form')],
                            'view_id': view.id,
                            'target': 'new',
                            'context': context,
                        }
                else:
                    raise ValidationError(_('Bạn cần nhập ngày sinh để có thể tạo hồ sơ 83'))
            else:
                raise ValidationError(
                    _('Hiện tại, chưa cấu hình cho công ty %s, liên hệ IT để được hỗ trợ') % self.company_id.name)

