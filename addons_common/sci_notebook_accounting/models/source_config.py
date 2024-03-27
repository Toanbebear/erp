from odoo import fields, models, api


class SourceConfigAccount(models.Model):
    _name = 'source.config.account'
    _description = 'Nguồn khối'

    name = fields.Char(string='Nguồn/Khối')
