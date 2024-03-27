from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = "product.template"

    default_booking_share = fields.Boolean('Dịch vụ thuê phòng mổ', default=False)