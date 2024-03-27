from odoo import fields, models

class DepartmentSector(models.Model):
    _name = "hr.department.sector"
    _description = 'HR department sector'

    name = fields.Char("Tên Khối", required=True)
    code = fields.Char("Mã Khối", required=True)
    active = fields.Boolean('Lưu trữ', default=True)
    sequence = fields.Integer('Sequence', default=20)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Tên khối đã tồn tại!"),
    ]