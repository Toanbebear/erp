import logging
from datetime import datetime, timedelta

import jwt

from odoo import fields, models
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

_logger = logging.getLogger(__name__)


def nonce(phone, access_key, expired, call_out_id=None):
    try:
        payload = {
            "ipphone": phone,
            'expired': expired.strftime('%Y-%m-%d 00:00:00'),
        }
        return jwt.encode(
            payload,
            access_key,
            algorithm='HS256'
        )
    except Exception as e:
        return e


class APIVoiceAccessTokenCs(models.Model):
    _name = "api.caresoft.voice.access.token"
    _description = "API Caresoft Voice Access Token"

    token = fields.Char("Access Token", required=True)
    phone = fields.Char("Phone")
    brand_code = fields.Char("Brand code")
    user_id = fields.Many2one("res.users", string="User", required=True)
    expires = fields.Datetime(string="Expires", required=True)

    def find_one_or_create_token(self, user_id=None, access_key=None, brand_code=None, ip_phone=None, create=False):
        if not user_id:
            user_id = self.env.user.id

        if not access_key and self.env.company.brand_id.cs_access_token:
            access_key = self.env.company.brand_id.cs_access_token

        phone = ip_phone

        access_token = self.sudo().search([('user_id', '=', user_id),('brand_code', '=', brand_code)],order="id DESC", limit=1)

        if access_token:
            access_token = access_token[0]
            if access_token.has_expired():
                access_token = None
        if not access_token and create:
            expires = datetime.utcnow() + timedelta(days=50, seconds=0)
            vals = {
                "user_id": user_id,
                "phone": phone,
                "expires": expires.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                "token": nonce(phone, access_key, expires),
                "brand_code": brand_code,
            }
            access_token = self.sudo().create(vals)
        if not access_token:
            return None
        return access_token.token

    def has_expired(self):
        self.ensure_one()
        if self.expires:
            return datetime.now() > fields.Datetime.from_string(self.expires)
        else:
            return True


