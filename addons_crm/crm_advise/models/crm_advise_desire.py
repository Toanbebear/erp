from odoo import fields, models


class AdviseDesire(models.Model):
    _name = 'crm.advise.desire'
    _description = 'Mong muốn'

    name = fields.Char(string='Nội dung mong muốn')
    service_group = fields.Many2one('sh.medical.health.center.service.category', string='Nhóm dịch vụ', domain="[('brand_id', '=', brand_id)]")
    brand_id = fields.Many2one('res.brand', string='Thương hiệu')
    sequence = fields.Integer(string='Thứ tự')
    active = fields.Boolean('Active', default=True)
    # company = fields.Many2one('res.company', string='Công ty')
