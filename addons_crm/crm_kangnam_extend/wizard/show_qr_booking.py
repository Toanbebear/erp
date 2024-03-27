from odoo import models, fields


class ShowQRBooking(models.TransientModel):
    _name = 'show.qr.booking'
    _description = 'Show QR Code của Booking'

    qr_code_id = fields.Binary(string="QR Code")
    crm_name = fields.Char(string="Mã BK")
    partner_name = fields.Char(string="Tên CTV")
    hotline_brand = fields.Char(string="Hotline")
