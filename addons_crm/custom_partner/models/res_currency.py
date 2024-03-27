from odoo import fields, models, api


class CurrencyRateInherit(models.Model):
    _inherit = 'res.currency.rate'

    currency_id = fields.Many2one('res.currency', string='Currency', readonly=False)

    def name_get(self):
        result = super(CurrencyRateInherit, self).name_get()
        if self.env.context.get('currency_rate_date'):
            return [(record.id, '1 {currency} = {rate:,.0f} VNĐ - Ngày cập nhật : {name}'.format(currency=record.currency_id.name, rate=round(1/record.rate), name=record.name)) for record in self]
        return result