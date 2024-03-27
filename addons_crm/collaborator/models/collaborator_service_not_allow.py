from odoo import fields, models


class CollaboratorServiceNotAllowConfig(models.Model):
    _name = 'collaborator.service.not.allow.config'
    _description = 'Danh sách dịch vụ không tính hoa hồng'

    service_id = fields.Many2one('product.product', string='Dịch vụ loại trừ')
    brand_id = fields.Many2one('res.brand', string='Thương hiệu')
