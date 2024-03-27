# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import models, _, fields, api

_logger = logging.getLogger(__name__)


class PhieuKham(models.Model):
    _inherit = 'sh.medical.appointment.register.walkin'

    address = fields.Char('Địa chỉ', compute='_compute_set_address')

    @api.depends('partner_id')
    def _compute_set_address(self):
        for rec in self:
            if rec.partner_id:
                address = []
                if rec.partner_id.street:
                    address.append(rec.partner_id.street)
                if rec.partner_id.district_id:
                    address.append(rec.partner_id.district_id.name)
                if rec.partner_id.state_id:
                    address.append(rec.partner_id.state_id.name)
                if address:
                    rec.address = ','.join(address)
                else:
                    rec.address = 'Chưa có thông tin địa chỉ'
            else:
                rec.address = 'Chưa có thông tin địa chỉ'

    def his_extend_action_view_walkin(self):
        domain = ['|', ('company_id', 'in', self.env.companies.ids), ('company2_id', 'in', self.env.companies.ids)]
        room_type_dict = {'shealth_all_in_one.group_sh_medical_physician_surgery': 'Surgery',
                          'shealth_all_in_one.group_sh_medical_physician_odontology': 'Odontology',
                          'shealth_all_in_one.group_sh_medical_physician_spa': 'Spa',
                          'shealth_all_in_one.group_sh_medical_physician_laser': 'Laser'}
        room_types = []
        for grp, rt in room_type_dict.items():
            if self.env.user.has_group(grp):
                room_types.append(rt)
        if room_types:
            domain = [('room_type', 'in', room_types)] + domain
        return {'type': 'ir.actions.act_window',
                'name': _('Phiếu khám bệnh'),
                'res_model': 'sh.medical.appointment.register.walkin',
                'view_mode': 'tree,form',
                'domain': domain,
                'context': {'search_default_group_date': True},
                'views': [(self.env.ref('his_extend.phieu_kham_tree_view_extend').id, 'tree'),
                          (self.env.ref('his_extend.phieu_kham_form_view_extend').id, 'form')],
                }
