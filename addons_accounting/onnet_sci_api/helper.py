import requests
import json
import logging

from odoo import _
from odoo.http import request
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)
api_url = "onnet_sci_api.accounting_api_url"
access_token = "onnet_sci_api.token_enterprise"


def call_api(method, url, data, headers):
    resp = requests.request(method, url=url, data=data, headers=headers)
    res = resp.json()
    # request.env.cr.execute('INSERT INTO enterprise_api_log (name, url, type, header, request, response, status) VALUES (%s, %s, %s, %s, %s, %s, %s)',('sync to enterprise', url, method, json.dumps(headers, ensure_ascii=False), data, json.dumps(res, ensure_ascii=False), code))
    return res


def create_records(self, model, data):
    try:
        if not api_url:
            return False
        path = "/sync/" + model
        payload = json.dumps({
            "data": data
        })
        headers = {
            'Content-Type': 'application/json',
            'access-token': self.env.ref(access_token).sudo().value
        }
        url = self.env.ref(api_url).sudo().value + path
        response = call_api('POST', url, payload, headers)
    except Exception as e:
        _logger.error(e)
        return False


def update_record(self, model, data, com_id):
    try:
        if not api_url:
            return False
        ent = self.env['records.com.ent.rel'].sudo().search([('model', '=', model), ('com_id', '=', com_id)],
                                                            limit=1)
        if ent and ent.ent_id:
            path = "/sync/" + model + "/" + str(ent.ent_id)
            method = 'PUT'
        else:
            path = "/sync/" + model
            method = 'POST'
            data = [data]
        company_id = self.env['records.com.ent.rel'].sudo().search(
            [('model', '=', 'res.company'), ('com_id', '=', self.env.company.id)],
            limit=1).ent_id
        payload = json.dumps({
            "data": data,
            "company_id": company_id
        })
        headers = {
            'Content-Type': 'application/json',
            'access-token': self.env.ref(access_token).sudo().value
        }
        url = self.env.ref(api_url).sudo().value + path
        response = call_api(method, url, payload, headers)
        if method == 'POST' and response.get('result', False) and response['result']['errorCode'] == 200:
            ent_id = json.loads(response['result']['data'])['data']['ids'][0]
            if model != "account.move.line":
                if ent:
                    ent.sudo().write({'ent_id': ent_id, 'status': 'success'})
                else:
                    ent = self.env['records.com.ent.rel'].sudo().create({
                        'model': model,
                        'com_id': com_id,
                        'ent_id': ent_id
                    })
                create_log(url, method, headers, data, response, ent.id)
            return ent_id
        elif not response.get('result', False) or response['result']['errorCode'] != 200:
            if model != "account.move.line":
                if ent:
                    ent.sudo().write({'status': 'failed'})
                else:
                    ent = self.env['records.com.ent.rel'].sudo().create({
                        'model': model,
                        'com_id': com_id,
                        'status': 'failed'
                    })
                create_log(url, method, headers, data, response, ent.id)
            return False
        ent.sudo().write({'status': 'success'})
        create_log(url, method, headers, data, response, ent.id)
        return ent.ent_id
    except Exception as e:
        _logger.error(e)
        return False


def create_log(url, method, headers, data, response, map_id):
    code = response.get('result', False) and response.get('result')['errorCode'] or 401
    request.env['enterprise.api.log'].sudo().create({
        'name': 'sync to enterprise',
        'url': url,
        'type': method,
        'header': json.dumps(headers, ensure_ascii=False),
        'request': data,
        'response': json.dumps(response, ensure_ascii=False),
        'status': code,
        'map_id': map_id
    })


def get_ent_id(self, model, com_id):
    if com_id:
        rel = self.env['records.com.ent.rel'].sudo().search(
            [('model', '=', model), ('com_id', '=', com_id), ('status', '=', 'success')],
            limit=1)
        if rel:
            return rel.ent_id
        if model == 'res.company':
            return self.env[model].create_enterprise(com_id)
        return self.env[model].sync_record(com_id)
    else:
        return False


def delete_record(self, model, com_id):
    try:
        if not api_url:
            return False
        ent = self.env['records.com.ent.rel'].sudo().search([('model', '=', model), ('com_id', '=', com_id)],
                                                            limit=1)
        if ent:
            if ent.ent_id:
                path = "/sync/" + model + '/' + str(com_id)
                headers = {
                    'Content-Type': 'application/json',
                    'access-token': self.env.ref(access_token).sudo().value
                }
                url = self.env.ref(api_url).sudo().value + path
                response = call_api('DELETE', url, json.dumps({}), headers)
                if response.get('result', False) and response['result']['errorCode'] == 200:
                    ent.unlink()
                else:
                    ent.sudo().write({'status': 'failed', 'action': 'delete'})
            else:
                ent.sudo().unlink()
    except Exception as e:
        _logger.error(e)
        return False


def remove_duplicate(record, channel):
    func_string_edit = f"{record._name}({record.id},).sync_record({record.id})"
    func_string_create = f"{record._name}().sync_record({record.id})"
    existing_job = record.env['queue.job'].sudo().search([
        '|',
        ('func_string', '=', func_string_edit),
        ('func_string', '=', func_string_create),
        ('channel', '=', channel),
        ('state', 'in', ['pending'])
    ])
    if existing_job:
        existing_job.sudo().unlink()
