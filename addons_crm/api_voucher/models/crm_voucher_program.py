import json

import requests

from odoo import fields, api, models, _
from odoo.exceptions import ValidationError
from odoo.addons.queue_job.job import job
import logging
_logger = logging.getLogger(__name__)

class CrmVoucherProgram(models.Model):
    _inherit = 'crm.voucher.program'

    is_accesstrade = fields.Boolean('Voucher Accesstrade', default=False)

    def check_sequence(self):
        if not self.prefix:
            raise ValidationError('Vui lòng nhập tiền tố của Voucher')
        if not self.quantity:
            raise ValidationError('Vui lòng nhập số lượng voucher cần tạo')
        code_exit = self.voucher_ids.mapped('name')
        list_code = self.create_code(self.prefix, self.quantity, code_exit)
        if self.is_accesstrade:
            self.sudo().with_delay(priority=0, channel='sync_voucher_accesstrade').sync_record(self.prefix, list_code, self.end_date.strftime("%d/%m/%Y"))
        if list_code:
            for code in list_code:
                self.env['crm.voucher'].create({'voucher_program_id': self.id,
                                                'name': code,
                                                'stage_voucher': self.stage_prg_voucher
                                                })
                self.current_number_voucher += 1

            view = self.env.ref('sh_message.sh_message_wizard')
            view_id = view and view.id or False
            context = dict(self._context or {})
            context['message'] = '%s Voucher đã được tạo thành công!!' % self.quantity
            return {
                'name': 'Success',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'sh.message.wizard',
                'views': [(view_id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'context': context,
            }


    @job
    def sync_record(self, prefix, vals, date_end):
        config = self.env['ir.config_parameter'].sudo()

        url_root = config.get_param('voucher_url')
        token = config.get_param('token_voucher')
        url = url_root + '/create_voucher'
        body = {
            'prefix': prefix,
            'name': vals,
            'date_end': date_end
        }
        headers = {
            'Content-Type':'application/json',
            'Authorization': token
        }
        response = requests.request('POST', url=url, data=json.dumps(body), headers=headers)