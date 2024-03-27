from odoo import fields, models, api


class ConfigSource(models.Model):
    _name = 'config.source.revenue'
    _description = 'Cấu hình nguồn doanh thu'

    name = fields.Char(string='Tên nguồn')
