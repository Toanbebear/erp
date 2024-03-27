from odoo import api, models, fields


class NextCLoudBookingInherit(models.Model):
    _inherit = 'crm.lead'

    nc_image_ids = fields.One2many("crm.lead.image", "booking_id", "Hình ảnh mô tả")
