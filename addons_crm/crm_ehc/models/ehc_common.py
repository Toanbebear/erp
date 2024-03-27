import json
import logging

import requests

from odoo.http import request

_logger = logging.getLogger(__name__)


def get_company_bvhh():
	company = request.env['res.company'].sudo().search([('code', '=', 'BVHH.HN.01')])
	return company


def get_url_ehc():
	config = request.env['ir.config_parameter'].sudo()
	url_ehc = config.get_param('url_ehc')
	return url_ehc


def get_api_code_ehc():
	config = request.env['ir.config_parameter'].sudo()
	api_code_ehc = config.get_param('api_code_ehc')
	return api_code_ehc


def get_token_ehc():
	config = request.env['ir.config_parameter'].sudo()
	username = config.get_param('username_acc_api_ehc')
	pwd = config.get_param('password_acc_api_ehc')
	url_ehc = get_url_ehc()
	api_code_ehc = get_api_code_ehc()

	url = url_ehc + '/api/login?api=%s' % api_code_ehc

	headers = {
		'Content-Type': 'application/json'
	}

	data = {
		"username": username,
		"password": pwd
	}
	r = requests.post(url, headers=headers, data=json.dumps(data))
	response = r.json()
	if 'status' in response and response['status']:
		token = response['token']
		return token
	else:
		return {
			'status': False,
			'message': 'Get token fail',
			'response': response
		}
