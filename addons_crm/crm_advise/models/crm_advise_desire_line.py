from odoo import fields, models, api


class ModelName(models.Model):
    _name = 'crm.advise.desire.line'
    _description = 'Nội dung mong muốn'

    name = fields.Char(string='Nội dung mong muốn')
    service_group = fields.Many2one('sh.medical.health.center.service.category', string='Nhóm dịch vụ')
