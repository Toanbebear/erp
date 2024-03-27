import logging
from datetime import datetime, timedelta

import jwt
from odoo import api, models
from odoo import fields, models
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

_logger = logging.getLogger(__name__)


def nonce(phone, access_key, expired, call_out_id=None):
    try:
        payload = {
            "ipphone": phone,
            'expired': expired.strftime('%Y-%m-%d 00:00:00'),
            'callout_id': call_out_id
        }
        return jwt.encode(
            payload,
            access_key,
            algorithm='HS256'
        )
    except Exception as e:
        return e


# def nonce_voice(phone, access_key, expired):
#     try:
#         payload = {
#             "ipphone": phone,
#             'expired': expired.strftime('%Y-%m-%d 00:00:00'),
#         }
#         return jwt.encode(
#             payload,
#             access_key,
#             algorithm='HS256'
#         )
#     except Exception as e:
#         return e


class APIAccessTokenCs(models.Model):
    _name = "api.access.token.cs"
    _description = "API Access Token Caresoft"

    token = fields.Char("Access Token", required=True)
    phone = fields.Char("Phone")
    brand_code = fields.Char("Brand code")
    user_id = fields.Many2one("res.users", string="User", required=True)
    expires = fields.Datetime(string="Expires", required=True)
    token_type = fields.Selection([('voice', 'Voice'),
                                   ('click2call', 'Click2Call')],
                                  string='Kiểu token', default='click2call')

    def find_one_or_create_token(self, user_id=None, access_key=None, brand_code=None, ip_phone=None,create=False):
        if not user_id:
            user_id = self.env.user.id

        if not access_key and self.env.company.brand_id.cs_access_token:
            access_key = self.env.company.brand_id.cs_access_token

        phone = ip_phone

        access_token = self.env["api.access.token.cs"].sudo().search([('user_id', '=', user_id),
                                                                      ('brand_code', '=', brand_code),
                                                                      ('token_type', '=', 'click2call')],
                                                                     order="id DESC", limit=1)

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
            access_token = self.env["api.access.token.cs"].sudo().create(vals)
        if not access_token:
            return None
        return access_token.token

    def has_expired(self):
        self.ensure_one()
        if self.expires:
            return datetime.now() > fields.Datetime.from_string(self.expires)
        else:
            return True

    # # def get_token_cs_voice(self, user_id=None, access_key=None, brand_code=None):
    # @api.model
    # def get_token_cs_voice(self):
    #     access_key = self.env.company.brand_id.cs_access_token
    #     # Check key
    #     user_id = self.env.user.id
    #     phone = self.env.user.cs_ip_phone
    #     brand_code = self.env.company.brand_id.code
    #     access_tokens = self.env["api.access.token.cs"].sudo().search([('user_id', '=', user_id),
    #                                                                    ('brand_code', '=', brand_code),
    #                                                                    ('token_type', '=', 'voice')],
    #                                                                   order="id DESC", limit=1)
    #     # Kiểm tra nếu có token thì lấy token
    #     token = None
    #     expire = False
    #     # Chưa có thì tạo mới
    #     if access_tokens:
    #         access_token = access_tokens[0]
    #         if access_token.has_expired():
    #             # Có mà hết hạn thì tạo mới
    #             access_token.unlink()
    #             expire = True
    #         else:
    #             token = access_token.token
    #     if not access_tokens or expire:
    #         expires = datetime.utcnow() + timedelta(days=365, seconds=0)
    #         vals = {
    #             "user_id": user_id,
    #             "phone": phone,
    #             "expires": expires.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
    #             "token": nonce_voice(phone, access_key, expires),
    #             "brand_code": brand_code,
    #             "token_type": 'voice',
    #         }
    #         access_token = self.env["api.access.token.cs"].sudo().create(vals)
    #         token = access_token.token
    #     return token
    #
    # def get_token_caresoft_voice(self, user_id=None, access_key=None, brand_code=None):
    #     # access_key = self.env.company.brand_id.cs_access_token
    #     # user_id = self.env.user.id
    #     phone = self.env.user.cs_ip_phone
    #     # brand_code = self.env.company.brand_id.code
    #     access_tokens = self.env["api.access.token.cs"].sudo().search([('user_id', '=', user_id),
    #                                                                    ('brand_code', '=', brand_code),
    #                                                                    ('token_type', '=', 'voice')],
    #                                                                   order="id DESC", limit=1)
    #     # Kiểm tra nếu có token thì lấy token
    #     token = None
    #     expire = False
    #     # Chưa có thì tạo mới
    #     if access_tokens:
    #         access_token = access_tokens[0]
    #         if access_token.has_expired():
    #             # Có mà hết hạn thì tạo mới
    #             access_token.unlink()
    #             expire = True
    #         else:
    #             token = access_token.token
    #     if not access_tokens or expire:
    #         expires = datetime.utcnow() + timedelta(days=365, seconds=0)
    #         vals = {
    #             "user_id": user_id,
    #             "phone": phone,
    #             "expires": expires.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
    #             "token": nonce_voice(phone, access_key, expires),
    #             "brand_code": brand_code,
    #             "token_type": 'voice',
    #         }
    #         access_token = self.env["api.access.token.cs"].sudo().create(vals)
    #         token = access_token.token
    #
    #     return token


class Users(models.Model):
    _inherit = "res.users"

    cs_token_ids = fields.One2many("api.access.token.cs", "user_id", string="Access Tokens Caresoft",
                                         domain=[('token_type', '=', 'click2call')])
    cs_ip_phone = fields.Char("Caresoft ip phone")
