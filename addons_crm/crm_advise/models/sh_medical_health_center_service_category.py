from odoo import fields, models


class ServiceCategory(models.Model):
    _inherit = 'sh.medical.health.center.service.category'
    _description = 'Mong muốn'

    advise_required = fields.Boolean('Mong muốn, điểm đau', help='Nếu chọn thì nhóm dịch vụ này sẽ bắt buộc phải nhập mong muốn, điểm đau, tình trạng bên phiếu tư vấn')