from odoo import fields, api, models, _
import requests


class IrSequence(models.Model):
    _inherit = 'ir.sequence'

    def reset_code_booking_by_date(self):
        sequence = self.env.ref('crm_base.seq_crm_opp_sci')
        sequence.number_next_actual = 0
        sequence_bh = self.env.ref('crm_base.seq_crm_guarantee_opp_sci')
        sequence_bh.number_next_actual = 0
        # if self.env['ir.config_parameter'].sudo().get_param('web.base.url') == 'https://erp.scigroup.com.vn':
        #     url = "https://api.telegram.org/bot6480280702:AAEQfjmvu6OudkToWg2jxtEmigGSY7J3ljA/sendMessage?chat_id=-4035923819&text=Đã chạy cron 'Reset code Booking'"
        #     payload = {}
        #     headers = {}
        #     requests.request("GET", url, headers=headers, data=payload)
