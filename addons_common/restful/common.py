import logging
import datetime
import json
import ast
from odoo.http import request
import redis
from odoo import api, tools
import werkzeug.wrappers

_logger = logging.getLogger(__name__)

expires_in = "restful.access_token_expires"
db = "restful.access_database_name"

def default(o):
    if isinstance(o, (datetime.date, datetime.datetime)):
        return o.isoformat()
    if isinstance(o, bytes):
        return str(o)


def valid_response(data, status=200):
    """Valid Response
    This will be return when the http request was successfully processed."""
    data = {"error": 0, "message": "Success", "count": len(data) if not isinstance(data, str) else 1, "data": data}
    return werkzeug.wrappers.Response(
        status=status, content_type="application/json; charset=utf-8", response=json.dumps(data, default=default),
    )


def valid_response_once(data_object, status=200):
    """Valid Response One
    This will be return when the http request was successfully processed."""
    data = {"error": 0, "message": "Success", "data": data_object}
    return werkzeug.wrappers.Response(
        status=status, content_type="application/json; charset=utf-8", response=json.dumps(data, default=default),
    )


def invalid_response(typ, message=None, status=401):
    """Invalid Response
    This will be the return value whenever the server runs into an error
    either from the client or the server."""
    # return json.dumps({})
    return werkzeug.wrappers.Response(
        status=status,
        content_type="application/json; charset=utf-8",
        response=json.dumps(
            {"type": typ, "message": str(message) if str(message) else "wrong arguments (missing validation)", },
            default=datetime.datetime.isoformat,
        ),
    )


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


def get_redis():
    return None
    if 'redis_url' in tools.config.options:
        # return redis.Redis(host='10.10.10.246', port=6379, password='123123123', db=0)
        # "redis://:your_password@localhost:6379/0"
        # return redis.Redis.from_url(tools.config['redis_url'])
        r = redis.Redis.from_url(tools.config['redis_url'])
        try:
            # Kiểm tra nếu lỗi server thì không test nữa
            r.get('ping')
        except redis.ConnectionError as e:
            return None
        return r
    else:
        return None

def get_redis_server():
    if 'redis_url' in tools.config.options:
        # return redis.Redis(host='10.10.10.246', port=6379, password='123123123', db=0)
        # "redis://:your_password@localhost:6379/0"
        # return redis.Redis.from_url(tools.config['redis_url'])
        r = redis.StrictRedis.from_url(tools.config['redis_url'], decode_responses=True)
        try:
            # Kiểm tra nếu lỗi server thì không test nữa
            r.get('ping')
        except redis.ConnectionError as e:
            return None
        return r
    else:
        return None
# add log api
def add_log_api(record_id, model_key, input_value, response, name, type_log):
    model_id = request.env['ir.model'].sudo().search([('model', '=', model_key)], limit=1)
    log = request.env['api.log'].sudo().create({
        "name": name,
        "type_log": str(type_log),
        "model_id": model_id.id,
        "id_record": record_id,
        "input": input_value,
        "response": response
    })