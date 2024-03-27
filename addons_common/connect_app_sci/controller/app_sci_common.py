import re
import ast
import functools
import logging
import json
import datetime
from odoo.exceptions import AccessError
import werkzeug.wrappers

from odoo import http
from odoo.addons.restful.common import (
    extract_arguments,
    invalid_response,
    valid_response,
)
from odoo.http import request

_logger = logging.getLogger(__name__)


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


def validate_token(func):
    """."""

    @functools.wraps(func)
    def wrap(self, *args, **kwargs):
        """."""
        access_token = request.httprequest.headers.get("Authorization")
        if not access_token:
            return response({}, message_type=1,
                            message_content="Vui lòng đăng nhập để sử dụng tính năng này! ",
                            status=1)
        access_token_data = (
            request.env["api.access_token"].sudo().search([("token", "=", access_token)], order="id DESC", limit=1)
        )

        if access_token_data.find_one_or_create_token(user_id=access_token_data.user_id.id) != access_token:
            return response({}, message_type=1,
                            message_content="Giá trị Authorization trong header không chính xác hoặc đã hết hạn",
                            status=1)

        request.session.uid = access_token_data.user_id.id
        request.uid = access_token_data.user_id.id
        return func(self, *args, **kwargs)

    return wrap


def get_user_by_token(token=None):
    access_token_data = (
        request.env["api.access_token"].sudo().search([("token", "=", token)], order="id DESC", limit=1)
    )
    return access_token_data.user_id


def extract_arguments(payloads, offset=0, limit=0, order=None):
    """Parse additional data  sent along request."""
    # payloads = payloads.get("payload", {})
    fields, domain, payload = [], [], {}

    if payloads.get("domain", None):
        domain = ast.literal_eval(payloads.get("domain"))
    if payloads.get("fields"):
        fields = ast.literal_eval(payloads.get("fields"))
    if payloads.get("offset"):
        offset = int(payloads.get("offset"))
    if payloads.get("limit"):
        limit = int(payloads.get("limit"))
    if payloads.get("order"):
        order = payloads.get("order")
    filters = [domain, fields, offset, limit, order]

    return filters
