# -*- coding: utf-8 -*-
import base64
from io import BytesIO

from odoo import models

try:
    import qrcode
except ImportError:
    qrcode = None

class QrcodeMixin(models.AbstractModel):
    """ Mixin class for objects reacting when a qrcode is scanned in their form views
        which contains `<field name="_qrcode_scanned" widget="qrcode_handler"/>`.
        Models using this mixin must implement the method on_qrcode_scanned.
        It works like an onchange and receives the scanned qrcode in parameter.
    """

    _name = 'qrcode.mixin'
    _description = 'Qrcode Mixin'

    def qrcode(self, text):
        qr_code = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=20,
            border=4,
        )
        qr_code.add_data(text)
        qr_code.make(fit=True)
        im = qr_code.make_image()
        temp = BytesIO()
        im.save(temp, format="PNG")
        qr_code = base64.b64encode(temp.getvalue())
        return qr_code
