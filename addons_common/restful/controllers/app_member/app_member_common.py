"""Part of odoo. See LICENSE file for full copyright and licensing details."""
import datetime
import functools
import json
import logging

import werkzeug.wrappers

from odoo.addons.restful.common import (
    invalid_response,
)
from odoo.http import request

_logger = logging.getLogger(__name__)


def app_member_validate_token(func):
    """."""

    @functools.wraps(func)
    def wrap(self, *args, **kwargs):
        """."""
        authorization = request.httprequest.headers.get("Authorization")
        if not authorization:
            return invalid_response(
                "authorization", "missing authorization in request header", 401
            )
        config = request.env['ir.config_parameter'].sudo()
        result = config.get_param('token_api_connect_app_member')
        if result != authorization:
            return invalid_response(
                "authorization", "authorization seems to have expired or invalid", 401
            )
        return func(self, *args, **kwargs)

    return wrap


def default(o):
    if isinstance(o, (datetime.date, datetime.datetime)):
        return o.isoformat()
    if isinstance(o, bytes):
        return str(o)


def response(data, message_type, message_content, status, res_status=200):
    """Default Response
    This will be return when the http request was successfully processed."""
    return werkzeug.wrappers.Response(
        status=res_status,
        content_type="application/json; charset=utf-8",
        response=json.dumps({
            "status": status,
            "message": {
                "type": message_type,
                "content": message_content
            },
            "data": data
        },
            default=default),
    )
