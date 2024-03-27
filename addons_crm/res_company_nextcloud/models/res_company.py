from odoo import fields, api, models, _


class QueueSpecialty(models.Model):
    _inherit = "res.company"

    url_image = fields.Char('Link ảnh khách hàng')

