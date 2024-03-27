from odoo import fields, models


class ModelName(models.Model):
    _name = 'crm.advise.painpoint.line'
    _description = 'Nội dung điểm đau'

    name = fields.Char(string='Nội dung điểm đau')
    servicegroup = fields.Many2one('sh.medical.health.center.service.category', string='Nhóm dịch vụ')
