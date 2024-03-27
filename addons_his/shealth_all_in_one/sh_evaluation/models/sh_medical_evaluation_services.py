from odoo import fields, models


class SHealthEvaluationServices(models.Model):
    _name = 'sh.medical.evaluation.services'
    _description = "Loại tái khám bệnh nhân"

    _order = 'sequence'

    name = fields.Char(string='Tên', required=True)
    has_supply = fields.Boolean(string='Có VTTH?')
    sequence = fields.Integer('Thứ tự', default=10)
    brand_id = fields.Many2one('res.brand', 'Thương hiệu')