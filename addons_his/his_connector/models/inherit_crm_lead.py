import json

import requests

from odoo import fields, api, models, _
from odoo.exceptions import ValidationError


class InheritCrmLead(models.Model):
    _inherit = 'crm.lead'

    sync_his_83 = fields.Boolean('Đã tạo hồ sơ HIS83')

    def action_sync_his_83(self):
        return {
            'name': 'Thông tin cập nhật 83',
            'view_mode': 'form',
            'res_model': 'sync.his.83.wizard',
            'type': 'ir.actions.act_window',
            'view_id': self.env.ref('his_connector.sync_his_83_wizard_form_view').id,
            'context': {
                'default_booking_id': self.id,
                'default_company_id': self.company_id.id,
            },
            'target': 'new'
        }
