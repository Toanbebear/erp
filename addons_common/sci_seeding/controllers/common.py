"""Part of odoo. See LICENSE file for full copyright and licensing details."""
import re
import ast
import functools
import logging
from odoo.exceptions import AccessError

from odoo import http
from odoo.addons.restful.common import (
    extract_arguments,
    invalid_response,
    valid_response,
)
from odoo.http import request

_logger = logging.getLogger(__name__)


def seeding_validate_token(func):
    """."""

    @functools.wraps(func)
    def wrap(self, *args, **kwargs):
        """."""
        authorization = request.httprequest.headers.get("Authorization")
        if not authorization:
            return invalid_response("access_token_not_found", "missing access token in request header", 401)
        config = request.env['ir.config_parameter'].sudo()
        result = config.get_param('token_api_connect_seeding')

        if result != authorization:
            return invalid_response(
                "authorization", "authorization seems to have expired or invalid", 401
            )
        return func(self, *args, **kwargs)

    return wrap