from odoo import fields, api, models, _
from odoo.exceptions import ValidationError
from odoo import modules
from odoo.tools.safe_eval import safe_eval
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta

try:
    import qrcode
except ImportError:
    qrcode = None
try:
    import base64
except ImportError:
    base64 = None
from io import BytesIO
from pytz import timezone, utc
from calendar import monthrange

class InheritLoyaltyCard(models.Model):
    _inherit = 'crm.loyalty.card'

    # Lịch sử sử dụng của người thân
    relative_reward = fields.One2many('history.relative.reward', 'loyalty', string='Người thân')

    def cron_job_set_rank_paris(self):
        loyalties = self.env['crm.loyalty.card'].sudo().search([('brand_id.code', '=', 'PR')])
        for loyalty in loyalties:
            rank_id = self.env['crm.loyalty.rank'].sudo().search(
                [('brand_id.code', '=', 'PR'), ('money_fst', '<=', loyalty.amount), ('money_end', '>', loyalty.amount)])
            loyalty.rank_id = rank_id.id if rank_id else None

    def cron_job_birth_day_reward(self):
        local_tz = timezone(self.env.user.tz or 'Etc/GMT+7')
        today_utc = local_tz.localize(datetime.now(), is_dst=None)
        today = today_utc.astimezone(utc).replace(tzinfo=None)
        month = today.month
        last_day = date(today.year, today.month, monthrange(today.year, month)[1])
        voucher_ids = self.env['voucher.loyalty'].sudo().search([('is_birth_day', '=', True)])
        if voucher_ids:
            for voucher in voucher_ids:
                loyalties = self.env['crm.loyalty.card'].sudo().search([('rank_id', '=', voucher.rank.id)])
                if loyalties:
                    for loyalty in loyalties:
                        if loyalty.partner_id.birth_date and loyalty.partner_id.birth_date.month == month:
                            name = voucher.name + 'Tháng %s năm %s' %(month, today.year)
                            self.env['crm.loyalty.line.reward'].sudo().create({
                                'name': name,
                                'brand_id': voucher.rank.brand_id.id,
                                'rank_id': voucher.rank.id,
                                'type_reward': voucher.type,
                                'product_ids': voucher.product_ids.ids,
                                'preferential_method': voucher.method,
                                'quantity': voucher.number,
                                'number_use': 0,
                                'discount_percent': voucher.percent if voucher.method == 'discount' else 100,
                                'stage': 'allow',
                                'loyalty_id': loyalty.id,
                                'voucher_loyalty_id': voucher.id,
                                'end_date': last_day
                            })

    def cron_job_cancel_reward(self):
        # local_tz = timezone(self.env.user.tz or 'Etc/GMT+7')
        # today_utc = local_tz.localize(datetime.now(), is_dst=None)
        # today = today_utc.astimezone(utc).replace(tzinfo=None)
        today = datetime.now() + timedelta(hours=7)
        rewards = self.env['crm.loyalty.line.reward'].sudo().search([('end_date', '<', today)])
        if rewards:
            for reward in rewards:
                reward.sudo().write({'stage':'not_allow'})

