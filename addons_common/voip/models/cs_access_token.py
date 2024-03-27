import logging
from datetime import datetime, timedelta

import jwt
from odoo import api, models
from odoo import fields, models
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

_logger = logging.getLogger(__name__)


def nonce_voice(phone, access_key, expired):
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


class APIAccessTokenCs(models.Model):
    _inherit = "api.access.token.cs"

    @api.model
    def get_token_cs_voice(self):
        if self.env.user.brand_ip_phone_ids:
            if len(self.env.user.brand_ip_phone_ids) == 1:
                phone = self.env.user.brand_ip_phone_ids.ip_phone
                # _logger.info("User")
                # _logger.info(request.env.user)
                if not phone:
                    return {
                        'status': 'error',
                        'message': 'Chưa cấu hình số điện thoại IP Phone Caresoft vào hệ thống ERP. Vui lòng liên hệ quản trị để được hỗ trợ',
                        'token': '',
                        'cs_url': ''
                    }

                token = False
                phone = self.env.user.brand_ip_phone_ids.ip_phone
                if not phone:
                    return token
                access_key = self.env.user.brand_ip_phone_ids.brand_id
                # Check key
                user_id = self.env.user.id
                brand_code = self.env.user.brand_ip_phone_ids.brand_id.code
                if access_key:
                    access_tokens = self.env["api.access.token.cs"].sudo().search([('user_id', '=', user_id),
                                                                                   ('brand_code', '=', brand_code),
                                                                                   ('token_type', '=', 'voice')],
                                                                                  order="id DESC", limit=1)

                    # Kiểm tra nếu có token thì lấy token

                    expire = False
                    # Chưa có thì tạo mới
                    if access_tokens:
                        access_token = access_tokens[0]
                        if access_token.has_expired():
                            # Có mà hết hạn thì tạo mới
                            access_token.unlink()
                            expire = True
                        else:
                            token = access_token.token
                    if not access_tokens or expire:
                        expires = datetime.utcnow() + timedelta(days=365, seconds=0)
                        vals = {
                            "user_id": user_id,
                            "phone": phone,
                            "expires": expires.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                            "token": nonce_voice(phone, access_key, expires),
                            "brand_code": brand_code,
                            "token_type": 'voice',
                        }
                        access_token = self.env["api.access.token.cs"].sudo().create(vals)
                        token = access_token.token
                    return token

    def get_token_caresoft_voice(self, user_id=None, access_key=None, brand_code=None, ip_phone=None):
        # access_key = self.env.company.brand_id.cs_access_token
        # user_id = self.env.user.id
        phone = ip_phone
        # brand_code = self.env.company.brand_id.code
        access_tokens = self.env["api.access.token.cs"].sudo().search([('user_id', '=', user_id),
                                                                       ('brand_code', '=', brand_code),
                                                                       ('token_type', '=', 'voice')],
                                                                      order="id DESC", limit=1)
        # Kiểm tra nếu có token thì lấy token
        token = None
        expire = False
        # Chưa có thì tạo mới
        if access_tokens:
            access_token = access_tokens[0]
            if access_token.has_expired():
                # Có mà hết hạn thì tạo mới
                access_token.unlink()
                expire = True
            else:
                token = access_token.token
        if not access_tokens or expire:
            expires = datetime.utcnow() + timedelta(days=365, seconds=0)
            vals = {
                "user_id": user_id,
                "phone": phone,
                "expires": expires.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                "token": nonce_voice(phone, access_key, expires),
                "brand_code": brand_code,
                "token_type": 'voice',
            }
            access_token = self.env["api.access.token.cs"].sudo().create(vals)
            token = access_token.token
        return token
