"""Part of odoo. See LICENSE file for full copyright and licensing details."""
import logging

from odoo import http
from odoo.http import request
import requests
import json
import time
_logger = logging.getLogger(__name__)


class VoiceCaresoftController(http.Controller):
    """."""
    def get_current_brand(self):
        cids = request.httprequest.cookies.get('cids')
        if cids and cids != 'undefined':
            cookies_cids = [int(r) for r in request.httprequest.cookies.get('cids').split(",")]
        else:
            cookies_cids = [request.env.user.company_id.id]

        for company_id in cookies_cids:
            if company_id not in request.env.user.company_ids.ids:
                cookies_cids.remove(company_id)
        if not cookies_cids:
            cookies_cids = [request.env.company.id]

        if cookies_cids:
            company = request.env['res.company'].browse(cookies_cids[0])
            if company:
                return company.brand_id
        return False

    @http.route('/caresoft/voice_token', auth='user', type='json', cors="*")
    def get_voice_token(self, **kwargs):
        # phone = request.env.user.cs_ip_phone
        # # _logger.info("User")
        # # _logger.info(request.env.user)
        # if not phone:
        #     return {
        #         'status': 'error',
        #         'message': 'Chưa cấu hình số điện thoại IP Phone Caresoft vào hệ thống ERP. Vui lòng liên hệ quản trị để được hỗ trợ',
        #         'token': '',
        #         'cs_url': ''
        #     }
        #
        # brand = self.get_current_brand()
        # if brand:
        #     cs_url = brand.cs_url
        #     access_key = brand.cs_access_token
        #     if cs_url and access_key:
        #         token = request.env["api.access.token.cs"].sudo().get_token_caresoft_voice(request.env.user.id,
        #                                                                              access_key,
        #                                                                              brand.code)
        #
        #         if brand.code == 'KN':
        #             domain = 'kangnam'
        #         elif brand.code == 'DA':
        #             domain = 'dongabeauty'
        #         elif brand.code == 'PR':
        #             domain = 'nhakhoaparis'
        #         else:
        #             domain = 'benhvienhongha'
        #         cs_voice_url = 'https://capi.caresoft.vn/%s/thirdParty/login' % domain
        #
        #         # Login
        #         data = {
        #             'token': token,
        #         }
        #         headers = {}
        #         try:
        #             req = requests.post(cs_voice_url, data=data, headers=headers, timeout=20)
        #             req.raise_for_status()
        #
        #         except requests.HTTPError:
        #             print('lỗi')
        #         # req.json().get('access_token')
        #         return {
        #             'token': token,
        #             'cs_url': cs_voice_url,
        #             'domain': domain,
        #             'status': 'ok',
        #             'message': '',
        #         }
        #     else:
        #         return {
        #             'status': 'error',
        #             'message': 'Thương hiệu %s chưa cấu hình link gọi Voice API' % brand.name,
        #             'token': '',
        #             'cs_url': ''
        #         }
        #
        # return {
        #     'status': 'error',
        #     'message': 'Công ty không thuộc thương hiệu',
        #     'token': '',
        #     'cs_url': ''
        # }

        if request.env.user.brand_ip_phone_ids:
            if len(request.env.user.brand_ip_phone_ids) == 1:
                phone = request.env.user.brand_ip_phone_ids.ip_phone
                # _logger.info("User")
                # _logger.info(request.env.user)
                if not phone:
                    return {
                        'status': 'error',
                        'message': 'Chưa cấu hình số điện thoại IP Phone Caresoft vào hệ thống ERP. Vui lòng liên hệ quản trị để được hỗ trợ',
                        'token': '',
                        'cs_url': ''
                    }

                brand = request.env.user.brand_ip_phone_ids.brand_id
                if brand:
                    cs_url = brand.cs_url
                    access_key = brand.cs_access_token
                    if cs_url and access_key:
                        token = request.env["api.access.token.cs"].sudo().get_token_caresoft_voice(request.env.user.id,
                                                                                                   access_key,
                                                                                                   brand.code,
                                                                                                   phone)
                        token_cs = request.env["api.access.token.cs"].sudo().search([('user_id', '=', request.env.user.id),
                                                                           ('brand_code', '=', brand.code),
                                                                           ('token_type', '=', 'voice')])
                        if brand.code == 'KN':
                            domain = 'kangnam'
                        elif brand.code == 'DA':
                            domain = 'dongabeauty'
                        elif brand.code == 'PR':
                            domain = 'nhakhoaparis'
                        else:
                            domain = 'benhvienhongha'
                        cs_voice_url = 'https://capi.caresoft.vn/%s/thirdParty/login' % domain

                        # Login
                        data = {
                            'token': token,
                        }
                        headers = {}
                        try:
                            req = requests.post(cs_voice_url, data=data, headers=headers, timeout=20)
                            res = req.json()
                            if res['code'] == 'ok':
                                req.raise_for_status()
                            else:
                                token_cs.sudo().unlink()
                                token = request.env["api.access.token.cs"].sudo().get_token_caresoft_voice(
                                    request.env.user.id,
                                    access_key,
                                    brand.code,
                                    phone)
                                req = requests.post(cs_voice_url, data=data, headers=headers, timeout=20)
                                req.raise_for_status()
                        except requests.HTTPError:
                            print('lỗi 1')
                        # req.json().get('access_token')
                        return {
                            'token': token,
                            'cs_url': cs_voice_url,
                            'domain': domain,
                            'status': 'ok',
                            'message': '',
                        }
                    else:
                        return {
                            'status': 'error',
                            'message': 'Thương hiệu %s chưa cấu hình link gọi Voice API' % brand.name,
                            'token': '',
                            'cs_url': ''
                        }
            else:
                ip_phone = None
                bk = request.env[kwargs['res_model']].sudo().browse(int(kwargs['res_id']))
                if bk.brand_id:
                    ip_phone = request.env['brand.ip.phone'].sudo().search(
                        [('user_id', '=', request.env.user.id), ('brand_id', '=', bk.brand_id.id)], limit=1)
                if ip_phone:
                    cs_url = bk.brand_id.cs_url
                    access_key = bk.brand_id.cs_access_token
                    if cs_url and access_key:
                        token = request.env["api.access.token.cs"].sudo().get_token_caresoft_voice(request.env.user.id,
                                                                                                   access_key,
                                                                                                   bk.brand_id.code,
                                                                                                   ip_phone.ip_phone)
                        token_cs = request.env["api.access.token.cs"].sudo().search(
                            [('user_id', '=', request.env.user.id),
                             ('brand_code', '=', bk.brand_id.code),
                             ('token_type', '=', 'voice')])
                        if bk.brand_id.code == 'KN':
                            domain = 'kangnam'
                        elif bk.brand_id.code == 'DA':
                            domain = 'dongabeauty'
                        elif bk.brand_id.code == 'PR':
                            domain = 'nhakhoaparis'
                        else:
                            domain = 'benhvienhongha'
                        cs_voice_url = 'https://capi.caresoft.vn/%s/thirdParty/login' % domain

                        # Login
                        data = {
                            'token': token,
                        }
                        headers = {}
                        try:
                            req = requests.post(cs_voice_url, data=data, headers=headers, timeout=20)
                            res = req.json()
                            if res['code'] == 'ok':
                                req.raise_for_status()
                            else:
                                token_cs.sudo().unlink()
                                token = request.env["api.access.token.cs"].sudo().get_token_caresoft_voice(
                                    request.env.user.id,
                                    access_key,
                                    bk.brand_id.code,
                                    ip_phone.ip_phone)
                                req = requests.post(cs_voice_url, data=data, headers=headers, timeout=20)
                                req.raise_for_status()
                        except requests.HTTPError:
                            print('lỗi 2')
                        # req.json().get('access_token')
                        return {
                            'token': token,
                            'cs_url': cs_voice_url,
                            'domain': domain,
                            'status': 'ok',
                            'message': '',
                        }
                    else:
                        return {
                            'status': 'error',
                            'message': 'Thương hiệu %s chưa cấu hình link gọi Voice API' % bk.brand_id.name,
                            'token': '',
                            'cs_url': ''
                        }
                else:
                    ip_phone = request.env['brand.ip.phone'].search([('user_id', '=', request.env.user.id)],
                                                                    order="id DESC", limit=1)
                    if ip_phone:
                        cs_url = ip_phone.brand_id.cs_url
                        access_key = ip_phone.brand_id.cs_access_token
                        if cs_url and access_key:
                            token = request.env["api.access.token.cs"].sudo().get_token_caresoft_voice(
                                request.env.user.id,
                                access_key,
                                ip_phone.brand_id.code,
                                ip_phone.ip_phone)
                            token_cs = request.env["api.access.token.cs"].sudo().search(
                                [('user_id', '=', request.env.user.id),
                                 ('brand_code', '=', ip_phone.brand_id.code),
                                 ('token_type', '=', 'voice')])
                            if ip_phone.brand_id.code == 'KN':
                                domain = 'kangnam'
                            elif ip_phone.brand_id.code == 'DA':
                                domain = 'dongabeauty'
                            elif ip_phone.brand_id.code == 'PR':
                                domain = 'nhakhoaparis'
                            else:
                                domain = 'benhvienhongha'
                            cs_voice_url = 'https://capi.caresoft.vn/%s/thirdParty/login' % domain

                            # Login
                            data = {
                                'token': token,
                            }
                            headers = {}
                            try:
                                req = requests.post(cs_voice_url, data=data, headers=headers, timeout=20)
                                res = req.json()
                                if res['code'] == 'ok':
                                    req.raise_for_status()
                                else:
                                    token_cs.sudo().unlink()
                                    token = request.env["api.access.token.cs"].sudo().get_token_caresoft_voice(
                                        request.env.user.id,
                                        access_key,
                                        ip_phone.brand_id.code,
                                        ip_phone.ip_phone)
                                    req = requests.post(cs_voice_url, data=data, headers=headers, timeout=20)
                                    req.raise_for_status()
                            except requests.HTTPError:
                                print('lỗi 3')
                            # req.json().get('access_token')
                            return {
                                'token': token,
                                'cs_url': cs_voice_url,
                                'domain': domain,
                                'status': 'ok',
                                'message': '',
                            }
                        else:
                            return {
                                'status': 'error',
                                'message': 'Thương hiệu %s chưa cấu hình link gọi Voice API' % ip_phone.brand_id.name,
                                'token': '',
                                'cs_url': ''
                            }
        # return {
        #     'status': 'error',
        #     'message': 'Công ty không thuộc thương hiệu',
        #     'token': '',
        #     'cs_url': ''
        # }

    @http.route('/create/phone-call-history', auth='user', type='http', cors="*", methods=["POST"], csrf=False)
    def create_phone_call_history(self, *args, **kwargs):
        message = json.loads(kwargs['message'])
        res_id = int(kwargs['res_id'])
        res_model = kwargs['model']
        if 'ticketId' in message:
            phone_call = request.env['crm.phone.call.history'].sudo().search(
                [('call_id', '=', str(message['callID'])), ('ticket_id', '=', str(message['ticketId']))])
            if not phone_call:
                request.env['crm.phone.call.history'].sudo().create({
                    'call_id': str(message['callID']),
                    'ticket_id': str(message['ticketId']),
                    'res_id': res_id,
                    'res_model': res_model
                })
        return json.dumps({
            'status': 'success',
            'message': 'Thành công'
        })