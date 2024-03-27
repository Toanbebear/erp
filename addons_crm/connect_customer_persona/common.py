# Part of odoo. See LICENSE file for full copyright and licensing details.
import json
import logging

import werkzeug.wrappers
import datetime
from odoo import http
from odoo.http import request
from odoo.exceptions import AccessError, AccessDenied
import functools
import ast

_logger = logging.getLogger(__name__)

expires_in = "connect_customer_persona.access_token_expires"
db = "connect_customer_persona.access_database_name"


def default(o):
    if isinstance(o, (datetime.date, datetime.datetime)):
        return o.isoformat()
    if isinstance(o, bytes):
        return str(o)


# response type http
def http_valid_response(data, status=200):
    """Valid Response
    This will be return when the http request was successfully processed."""
    data = {"error": 0, "message": "Success", "count": len(data) if not isinstance(data, str) else 1, "data": data}
    return werkzeug.wrappers.Response(
        status=status, content_type="application/json; charset=utf-8", response=json.dumps(data, default=default),
    )


def http_valid_response_once(data_object, status=200):
    """Valid Response One
    This will be return when the http request was successfully processed."""
    data = {"error": 0, "message": "Success", "data": data_object}
    return werkzeug.wrappers.Response(
        status=status, content_type="application/json; charset=utf-8", response=json.dumps(data, default=default),
    )


def http_invalid_response(typ, message=None, status=401):
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


# response type json
def json_valid_response(data):
    data = {"count": len(data) if not isinstance(data, str) else 1, "data": data}
    return {
        'status': 0,
        "message": "Success",
        'data': data
    }


# response type json
def json_valid_response_once(data):
    return {
        "status": 0,
        "message": "Success",
        "data": data
    }


def json_invalid_response(message):
    return {
        'status': 1,
        'message': message,
        'data': []
    }


def get_url_base():
    config = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
    if config:
        return config
    return 'http://dev.scigroup.com.vn'


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


def validate_token(func):
    """."""

    @functools.wraps(func)
    def wrap(self, *args, **kwargs):
        """."""
        access_token = request.httprequest.headers.get("access_token")
        if not access_token:
            return json_invalid_response(message="missing access token in request header")
        access_token_data = (
            request.env["api.access_token"].sudo().search([("token", "=", access_token)], order="id DESC", limit=1)
        )

        if access_token_data.find_one_or_create_token(user_id=access_token_data.user_id.id) != access_token:
            return json_invalid_response(message="token seems to have expired or invalid")

        request.session.uid = access_token_data.user_id.id
        request.uid = access_token_data.user_id.id
        # request.brand_id = access_token_data.user_id.company_id.brand_id.id
        # request.brand_code = access_token_data.user_id.company_id.brand_id.code
        # request.brand_type = access_token_data.user_id.company_id.brand_id.type
        request.company_id = access_token_data.user_id.company_id.id
        return func(self, *args, **kwargs)

    return wrap


class AccessToken(http.Controller):
    """."""

    def __init__(self):

        self._token = request.env["api.access_token"]
        self._expires_in = request.env.ref(expires_in).sudo().value

    @http.route("/api/auth/token", methods=["POST"], type="json", auth="none", csrf=False)
    def token(self, **post):
        """Get Token
            payload = json.dumps({
              "login": "",
              "password": ""
            })
            headers = {
              'Content-Type': 'application/json'
            }
        """
        body = json.loads(request.httprequest.data.decode('utf-8'))
        _token = request.env["api.access_token"]
        db, username, password = (
            # params.get("db"),
            request.env.ref("connect_customer_persona.access_database_name").sudo().value,
            body['login'],
            body['password'],
        )
        _credentials_includes_in_body = all([username, password])
        if not _credentials_includes_in_body:
            # The request post body is empty the credetials maybe passed via the headers.
            db = request.env.ref("api_base.access_database_name").sudo().value
            username = body['login']
            password = body['login']
            _credentials_includes_in_headers = all([db, username, password])
            if not _credentials_includes_in_headers:
                # Empty 'db' or 'username' or 'password:
                return http_invalid_response(
                    "missing error", "either of the following are missing [login, password]", 403,
                )
        # Login in odoo database:
        try:
            request.session.authenticate(db, username, password)
        except AccessError as aee:
            # return invalid_response("Access error", "Error: %s" % aee.name)
            return {
                'message': "Access error",
                'content': "Error: %s" % aee.name
            }
        except AccessDenied as ade:
            # return invalid_response("Access denied", "Login, password or db invalid")
            return {
                'message': "Access denied",
                'content': "Login, password or db invalid"
            }
        except Exception as e:
            # Invalid database:
            info = "The database name is not valid {}".format((e))
            error = "invalid_database"
            _logger.error(info)
            # return invalid_response("wrong database name", error, 403)
            return json_invalid_response(message=error)
        uid = request.session.uid
        # odoo login failed:
        if not uid:
            info = "authentication failed"
            error = "authentication failed"
            _logger.error(info)
            # return invalid_response(401, error, info)
            return json_invalid_response(message=error)
        # Generate tokens
        access_token = _token.find_one_or_create_token(user_id=uid, create=True)
        # Successful response:
        # return werkzeug.wrappers.Response(
        #     status=200,
        #     content_type="application/json; charset=utf-8",
        #     headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
        #     response=json.dumps(
        #         {
        #             "uid": uid,
        #             "user_context": request.session.get_context() if uid else {},
        #             "company_id": request.env.user.company_id.id if uid else None,
        #             "company_ids": request.env.user.company_ids.ids if uid else None,
        #             "partner_id": request.env.user.partner_id.id,
        #             "access_token": access_token,
        #             "expires_in": self._expires_in,
        #         }
        #     ),
        # )
        data = {
            "uid": uid,
            "user_context": request.session.get_context() if uid else {},
            "company_id": request.env.user.company_id.id if uid else None,
            "company_ids": request.env.user.company_ids.ids if uid else None,
            "partner_id": request.env.user.partner_id.id,
            "access_token": access_token,
            "expires_in": self._expires_in,
        }
        return json_valid_response_once(data=data)

    @http.route("/api/auth/token", methods=["DELETE"], type="http", auth="none", csrf=False)
    def delete(self, **post):
        """."""
        _token = request.env["api.access_token"]
        access_token = request.httprequest.headers.get("access_token")
        access_token = _token.search([("token", "=", access_token)])
        if not access_token:
            info = "No access token was provided in request!"
            error = "Access token is missing in the request header"
            _logger.error(info)
            return http_invalid_response(400, error, info)
        for token in access_token:
            token.unlink()
        # Successful response:
        return http_valid_response([{"desc": "access token successfully deleted", "delete": True}])
