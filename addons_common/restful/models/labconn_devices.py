from odoo import fields, models


class LabDevices(models.Model):
    _name = 'lab.devices'
    _description = 'Danh mục thiết bị xét nghiệm'

    name = fields.Char('Tên thiết bị')
    code = fields.Char('Mã thiết bị')
    company = fields.Many2one('res.company', 'Chi nhánh')