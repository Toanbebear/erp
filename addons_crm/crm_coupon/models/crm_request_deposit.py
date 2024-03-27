from odoo import fields, models, api, _
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
STAGE = [('new', 'Mới'), ('used', 'Đã dùng'), ('out_date', 'Hết hạn')]


class RequestDepositInherit(models.Model):
    _inherit = 'crm.request.deposit'

    used = fields.Boolean(string='Đã sử dụng', default=False, readonly=True)
    status = fields.Selection(STAGE, string='Tình trạng', default='new', readonly=True, compute='compute_status', store=True)
    campaign_id = fields.Many2one('utm.campaign', string='Chiến dịch', required=True)

    @api.depends('used', 'payment_date')
    def compute_status(self):
        for rec in self:
            if rec.payment_date:
                today = datetime.today().strftime('%Y-%m-%d')
                date = rec.payment_date + relativedelta(months=+6)
                end_date = date.strftime('%Y-%m-%d')
                if rec.used is True:
                    rec.status = 'used'
                else:
                    if today > end_date:
                        rec.status = 'out_date'
                    else:
                        rec.status = 'new'
            else:
                rec.status = 'new'







