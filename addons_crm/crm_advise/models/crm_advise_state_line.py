from odoo import fields, models


class ModelName(models.Model):
    _name = 'crm.advise.state.line'
    _description = 'Nội dung tình trạng'

    name = fields.Char(string='Nội dung tình trạng')
    brand_id = fields.Many2one('res.brand', string='Thương hiệu')
    servicegroup = fields.Many2one('sh.medical.health.center.service.category', string='Nhóm dịch vụ',
                                   domain="[('brand_id','=',brand_id)]")
