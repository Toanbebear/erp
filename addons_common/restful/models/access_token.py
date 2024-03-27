import hashlib
import logging
import os
from datetime import datetime, timedelta

from odoo import fields, models
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

_logger = logging.getLogger(__name__)

expires_in = "restful.access_token_expires_in"


def nonce(length=40, prefix="access_token"):
    rbytes = os.urandom(length)
    return "{}_{}".format(prefix, str(hashlib.sha1(rbytes).hexdigest()))


class APIAccessToken(models.Model):
    _name = "api.access_token"
    _description = "API Access Token"

    token = fields.Char("Access Token", required=True)
    user_id = fields.Many2one("res.users", string="User", required=True)
    expires = fields.Datetime(string="Expires", required=True)
    scope = fields.Char(string="Scope")

    # Thêm các trường cho bảng acpi_access_token: brand_id, brand_code, brand_type, company_id
    c_id = fields.Many2one('res.company', string='Công ty', related='user_id.company_id', store=True)
    brand_id = fields.Many2one('res.brand', string='Thương hiệu', related='c_id.brand_id', store=True)
    brand_code = fields.Char(string="Brand code", related='brand_id.code', store=True)
    brand_type = fields.Selection(string='Brand type', related='brand_id.type', store=True)

    # @profile
    def find_one_or_create_token(self, user_id=None, create=False):
        if not user_id:
            user_id = self.env.user.id

        access_token = self.env["api.access_token"].sudo().search([("user_id", "=", user_id)], order="id DESC", limit=1)
        if access_token:
            access_token = access_token[0]
            if access_token.has_expired():
                access_token = None
        if not access_token and create:
            expires = datetime.now() + timedelta(seconds=int(self.env.ref(expires_in).sudo().value))
            vals = {
                "user_id": user_id,
                "scope": "userinfo",
                "expires": expires.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                "token": nonce(),
            }
            access_token = self.env["api.access_token"].sudo().create(vals)
        if not access_token:
            return None
        return access_token.token

    def find_or_create_token(self, expires=expires, token=token, user_id=user_id, create=False):
        if expires and token:
            if datetime.now() > fields.Datetime.from_string(expires):
                if not create:
                    return None
                else:
                    access_token = None
            else:
                return token
        else:
            if not user_id:
                user_id = self.env.user.id

            access_token = self.env["api.access_token"].sudo().search([("user_id", "=", user_id)], order="id DESC",
                                                                      limit=1)

        if access_token:
            access_token = access_token[0]
            if access_token.has_expired():
                access_token = None
            else:
                return access_token.token

        if not access_token and create:
            expires = datetime.now() + timedelta(seconds=int(self.env.ref(expires_in).sudo().value))
            vals = {
                "user_id": user_id,
                "scope": "userinfo",
                "expires": expires.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                "token": nonce(),
            }
            access_token = self.env["api.access_token"].sudo().create(vals)
            return access_token.token
        else:
            return None

    def is_valid(self, scopes=None):
        """
        Checks if the access token is valid.

        :param scopes: An iterable containing the scopes to check or None
        """
        self.ensure_one()
        return not self.has_expired() and self._allow_scopes(scopes)


    def has_expired(self):
        self.ensure_one()
        return datetime.now() > fields.Datetime.from_string(self.expires)


    def _allow_scopes(self, scopes):
        self.ensure_one()
        if not scopes:
            return True

        provided_scopes = set(self.scope.split())
        resource_scopes = set(scopes)

        return resource_scopes.issubset(provided_scopes)


class Users(models.Model):
    _inherit = "res.users"
    token_ids = fields.One2many("api.access_token", "user_id", string="Access Tokens")
