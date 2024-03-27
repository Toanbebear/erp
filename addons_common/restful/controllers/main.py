"""Part of odoo. See LICENSE file for full copyright and licensing details."""
import functools
import json
import logging
from odoo.tools.profiler import profile
from odoo import http
from odoo.exceptions import AccessError
from odoo.http import request

from odoo.addons.restful.common import (
    extract_arguments,
    invalid_response,
    valid_response,
    get_redis
)

_logger = logging.getLogger(__name__)


def validate_token(func):
    """."""

    @functools.wraps(func)
    def wrap(self, *args, **kwargs):
        """."""
        access_token = request.httprequest.headers.get("access_token")
        model_access_token = request.env["api.access_token"]
        if not access_token:
            return invalid_response("access_token_not_found", "missing access token in request header", 401)

        access_token_data =None
        # check token in redis
        redis_client = get_redis()
        if redis_client:
            token = redis_client.get(access_token)
            if token:
                access_token_data = json.loads(token)

        if not access_token_data:
            access_token_datas = model_access_token.sudo().search_read([("token", "=", access_token)],
                                                                       fields=['id', 'user_id', 'token', 'expires',
                                                                               'brand_id',
                                                                               'brand_code', 'brand_type', 'c_id'],
                                                                       order="id DESC", limit=1)
            if access_token_datas:
                access_token_data = access_token_datas[0]
                if redis_client:
                    # 86400 1 ngày hết hạn
                    redis_client.set(access_token,
                                     json.dumps(access_token_data, indent=4, sort_keys=True, default=str),
                                     86400)
            else:
                access_token_data = None

        if access_token_data:
            user_id = access_token_data['user_id'][0]
            token = access_token_data['token']
            expires = access_token_data['expires']

            if model_access_token.find_or_create_token(expires=expires, token=token, user_id=user_id) != access_token:
                return invalid_response("access_token", "token seems to have expired or invalid", 401)
            else:
                request.session.uid = user_id
                request.uid = user_id
                request.brand_id = access_token_data['brand_id'][0]
                request.brand_code = access_token_data['brand_code']
                request.brand_type = access_token_data['brand_type']
                request.company_id = access_token_data['c_id'][0]

        return func(self, *args, **kwargs)

    return wrap


_routes = ["/api/v1/<model>", "/api/v1/<model>/<id>", "/api/v1/<model>/<id>/<action>"]


def get_url_base():
    return request.env['ir.config_parameter'].sudo().get_param('web.base.url')


class APIController(http.Controller):
    """."""

    def __init__(self):
        self._model = "ir.model"

    @validate_token
    @http.route(_routes, type="http", auth="none", methods=["GET"], csrf=False)
    def get(self, model=None, id=None,count=None, **payload):
        try:
            ioc_name = model
            model = request.env[self._model].search([("model", "=", model)], limit=1)
            if model:
                domain, fields, offset, limit, order = extract_arguments(payload)

                if id:
                    domain.append(("id", "=", int(id)))
                data = request.env[model.model].search_read(
                    domain=domain, fields=fields, offset=offset, limit=limit, order=order,
                )

                if data:
                    return valid_response(data)
                else:
                    return valid_response(data)
            return invalid_response(
                "invalid object model", "The model %s is not available in the registry." % ioc_name,
            )
        except AccessError as e:

            return invalid_response("Access error", "Error: %s" % e.name)

    @validate_token
    @http.route(_routes, type="http", auth="none", methods=["POST"], csrf=False)
    def post(self, model=None, id=None, **payload):
        """Create a new record.
        Basic sage:
        import requests

        headers = {
            'content-type': 'application/x-www-form-urlencoded',
            'charset': 'utf-8',
            'access-token': 'access_token'` `
        }
        data = {
            'name': 'Babatope Ajepe',
            'country_id': 105,
            'child_ids': [
                {
                    'name': 'Contact',
                    'type': 'contact'
                },
                {
                    'name': 'Invoice',
                   'type': 'invoice'
                }
            ],
            'category_id': [{'id': 9}, {'id': 10}]
        }
        req = requests.post('%s/api/res.partner/' %
                            base_url, headers=headers, data=data)

        """
        import ast

        payload = payload.get("payload", {})
        ioc_name = model
        model = request.env[self._model].search([("model", "=", model)], limit=1)
        values = {}
        if model:
            try:
                # changing IDs from string to int.
                for k, v in payload.items():

                    if "__api__" in k:
                        values[k[7:]] = ast.literal_eval(v)
                    else:
                        values[k] = v

                resource = request.env[model.model].create(values)
            except Exception as e:
                request.env.cr.rollback()
                return invalid_response("params", e)
            else:
                data = resource.read()
                if resource:
                    return valid_response(data)
                else:
                    return valid_response(data)
        return invalid_response("invalid object model", "The model %s is not available in the registry." % ioc_name, )

    @validate_token
    @http.route(_routes, type="http", auth="none", methods=["PUT"], csrf=False)
    def put(self, model=None, id=None, **payload):
        """."""
        payload = payload.get('payload', {})
        try:
            _id = int(id)
        except Exception as e:
            return invalid_response("invalid object id", "invalid literal %s for id with base " % id)
        _model = request.env[self._model].sudo().search([("model", "=", model)], limit=1)
        if not _model:
            return invalid_response(
                "invalid object model", "The model %s is not available in the registry." % model, 404,
            )
        try:
            record = request.env[_model.model].sudo().browse(_id)
            record.write(payload)
        except Exception as e:
            request.env.cr.rollback()
            return invalid_response("exception", e.name)
        else:
            return valid_response(record.read())

    @validate_token
    @http.route(_routes, type="http", auth="none", methods=["DELETE"], csrf=False)
    def delete(self, model=None, id=None, **payload):
        """."""
        try:
            _id = int(id)
        except Exception as e:
            return invalid_response("invalid object id", "invalid literal %s for id with base " % id)
        try:
            record = request.env[model].sudo().search([("id", "=", _id)])
            if record:
                record.unlink()
            else:
                return invalid_response("missing_record", "record object with id %s could not be found" % _id, 404, )
        except Exception as e:
            request.env.cr.rollback()
            return invalid_response("exception", e.name, 503)
        else:
            return valid_response("record %s has been successfully deleted" % record.id)

    @validate_token
    @http.route(_routes, type="http", auth="none", methods=["PATCH"], csrf=False)
    def patch(self, model=None, id=None, action=None, **payload):
        """."""
        payload = payload.get('payload')
        action = action if action else payload.get('_method')
        args = []
        # args = re.search('\((.+)\)', action)
        # if args:
        #     args = ast.literal_eval(args.group())

        # if re.search('\w.+\(', action):
        #     action = re.search('\w.+\(', action)
        #     action = action.group()[0:-1]

        try:
            _id = int(id)
        except Exception as e:
            return invalid_response("invalid object id", "invalid literal %s for id with base" % id)
        try:
            record = request.env[model].sudo().search([("id", "=", _id)])
            _callable = action in [method for method in dir(record) if callable(getattr(record, method))]
            if record and _callable:
                # action is a dynamic variable.
                getattr(record, action)(*args) if args else getattr(record, action)()
            else:
                return invalid_response(
                    "missing_record",
                    "record object with id %s could not be found or %s object has no method %s" % (_id, model, action),
                    404,
                )
        except Exception as e:
            return invalid_response("exception", e, 503)
        else:
            return valid_response("record %s has been successfully update" % record.id)

    @validate_token
    @http.route("/api/v1/<model>/count", type="http", auth="none", methods=["GET"], csrf=False)
    def count(self, model=None, id=None, **payload):
        try:
            ioc_name = model
            model = request.env[self._model].search([("model", "=", model)], limit=1)
            if model:
                domain, fields, offset, limit, order = extract_arguments(payload)

                if id:
                    domain.append(("id", "=", int(id)))

                data = request.env[model.model].search_count(
                   domain
                )

                if data:
                    return json.dumps({
                        'error' : 0,
                        'len' : data
                    })
                else:
                    return json.dumps({
                        'error' : 0,
                        'len' : 0
                    })
            return invalid_response(
                "invalid object model", "The model %s is not available in the registry." % ioc_name,
            )
        except AccessError as e:

            return invalid_response("Access error", "Error: %s" % e.name)

