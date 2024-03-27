from odoo import api, models, fields


class NextCLoudWalkinInherit(models.Model):
    _inherit = 'sh.medical.appointment.register.walkin'

    nc_image_ids = fields.One2many("sh.medical.appointment.register.walkin.image", "walkin_id", 'Hình ảnh mô tả')
