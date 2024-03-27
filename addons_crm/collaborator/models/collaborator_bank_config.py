from odoo import fields, models


class CollaboratorBankConfig(models.Model):
    _name = 'collaborator.bank.config'
    _description = 'Ngân hàng'
    _order = 'sequence asc'

    name = fields.Char(string='Ngân hàng')
    logo = fields.Binary(string="Logo")
    code = fields.Char(string='Mã')
    sequence = fields.Integer(string='Thứ tự', default=10)
    active = fields.Boolean(string='Active', default=True)
