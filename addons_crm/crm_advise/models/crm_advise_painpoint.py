from odoo import fields, models


class AdvisePainPoint(models.Model):
    _name = 'crm.advise.painpoint'
    _description = 'Điểm đau'

    name = fields.Char(string='Nội dung điểm đau')
    service_group = fields.Many2one('sh.medical.health.center.service.category', string='Nhóm dịch vụ', domain="[('brand_id', '=', brand_id)]")
    brand_id = fields.Many2one('res.brand', string='Thương hiệu')
    sequence = fields.Integer(string='Thứ tự')
    active = fields.Boolean('Active', default=True)