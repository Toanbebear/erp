"""Part of odoo. See LICENSE file for full copyright and licensing details."""
import logging

from odoo import http
from odoo.http import request
import requests

_logger = logging.getLogger(__name__)


class CaresoftController(http.Controller):
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

    @http.route('/caresoft/token', auth='user', type='json')
    # def get_token(self):
    #     phone = request.env.user.cs_ip_phone
    #     if not phone:
    #         return {
    #             'status': 'error',
    #             'message': 'Chưa cấu hình số điện thoại IP Phone Caresoft vào hệ thống ERP. Vui lòng liên hệ quản trị để được hỗ trợ',
    #             'token': '',
    #             'cs_url': ''
    #         }
    #
    #     brand = self.get_current_brand()
    #
    #     if brand:
    #         cs_url = brand.cs_url
    #         access_key = brand.cs_access_token
    #
    #         if brand.code == request.env.company.brand_id.code:
    #             if cs_url and access_key:
    #                 token = request.env["api.access.token.cs"].sudo().find_one_or_create_token(request.env.user.id,
    #                                                                                            access_key, brand.code,
    #                                                                                            True)
    #                 return {
    #                     'token': token,
    #                     'cs_url': cs_url,
    #                     'status': 'ok',
    #                     'message': '',
    #                 }
    #             else:
    #                 return {
    #                     'status': 'error',
    #                     'message': 'Thương hiệu chưa cấu hình link gọi Click2Call',
    #                     'token': '',
    #                     'cs_url': ''
    #                 }
    #         else:
    #             if request.env.company.brand_id.name:
    #                 message = 'Số IP Phone Caresoft ' + phone + ' thuộc thương hiệu ' + request.env.company.brand_id.name + ' nên không gọi được cho khách hàng bằng đầu số của thương hiệu ' + brand.name
    #             else:
    #                 message = 'Số IP Phone Caresoft ' + phone + ' không thuộc thương hiệu ' + brand.name
    #
    #             return {
    #                 'status': 'error',
    #                 'message': message,
    #                 'token': '',
    #                 'cs_url': ''
    #             }
    #
    #     return {
    #         'status': 'error',
    #         'message': 'Công ty không thuộc thương hiệu',
    #         'token': '',
    #         'cs_url': ''
    #     }
    def get_token(self, **kwargs):
        if request.env.user.brand_ip_phone_ids:
            if len(request.env.user.brand_ip_phone_ids) == 1:
                phone = request.env.user.brand_ip_phone_ids.ip_phone
                if not phone:
                    return {
                        'status': 'error',
                        'message': 'Chưa cấu hình số điện thoại IP Phone Caresoft vào hệ thống ERP. Vui lòng liên hệ quản trị để được hỗ trợ',
                        'token': '',
                        'cs_url': ''
                    }
                # brand = self.get_current_brand()
                brand = request.env.user.brand_ip_phone_ids.brand_id
                if brand:
                    cs_url = brand.cs_url
                    access_key = brand.cs_access_token
                    if cs_url and access_key:
                        token = request.env["api.access.token.cs"].sudo().find_one_or_create_token(request.env.user.id,
                                                                                                   access_key, brand.code,
                                                                                                   phone,True)
                        return {
                            'token': token,
                            'cs_url': cs_url,
                            'status': 'ok',
                            'message': '',
                        }
                    else:
                        return {
                            'status': 'error',
                            'message': 'Thương hiệu chưa cấu hình link gọi Click2Call',
                            'token': '',
                            'cs_url': ''
                        }
            else:
                ip_phone = None
                bk = request.env[kwargs['res_model']].sudo().browse(int(kwargs['res_id']))
                if bk.brand_id:
                    ip_phone = request.env['brand.ip.phone'].sudo().search([('user_id', '=', request.env.user.id), ('brand_id', '=', bk.brand_id.id)],limit=1)
                if ip_phone:
                    cs_url = bk.brand_id.cs_url
                    access_key = bk.brand_id.cs_access_token
                    if cs_url and access_key:
                        token = request.env["api.access.token.cs"].sudo().find_one_or_create_token(request.env.user.id,
                                                                                                   access_key,
                                                                                                   bk.brand_id.code,
                                                                                                   ip_phone.ip_phone, True)
                        return {
                            'token': token,
                            'cs_url': cs_url,
                            'status': 'ok',
                            'message': '',
                        }
                    else:
                        return {
                            'status': 'error',
                            'message': 'Thương hiệu chưa cấu hình link gọi Click2Call',
                            'token': '',
                            'cs_url': ''
                        }
                else:
                    ip_phone = request.env['brand.ip.phone'].sudo().search([('user_id', '=', request.env.user.id)], order="id DESC", limit=1)
                    if ip_phone:
                        cs_url = ip_phone.brand_id.cs_url
                        access_key = ip_phone.brand_id.cs_access_token
                        if cs_url and access_key:
                            token = request.env["api.access.token.cs"].sudo().find_one_or_create_token(
                                request.env.user.id,
                                access_key,
                                ip_phone.brand_id.code,
                                ip_phone.ip_phone, True)
                            return {
                                'token': token,
                                'cs_url': cs_url,
                                'status': 'ok',
                                'message': '',
                            }
                        else:
                            return {
                                'status': 'error',
                                'message': 'Thương hiệu chưa cấu hình link gọi Click2Call',
                                'token': '',
                                'cs_url': ''
                            }
                    else:
                        return {
                            'status': 'error',
                            'message': 'Chưa cấu hình số điện thoại IP Phone Caresoft vào hệ thống ERP. Vui lòng liên hệ quản trị để được hỗ trợ',
                            'token': '',
                            'cs_url': ''
                        }

        else:
            return {
                'status': 'error',
                'message': 'Chưa cấu hình số điện thoại IP Phone Caresoft vào hệ thống ERP. Vui lòng liên hệ quản trị để được hỗ trợ',
                'token': '',
                'cs_url': ''
            }
    # @http.route('/caresoft/voice_token', auth='user', type='json', cors="*")
    # def get_voice_token(self):
    #     phone = request.env.user.cs_ip_phone
    #     # _logger.info("User")
    #     # _logger.info(request.env.user)
    #     if not phone:
    #         return {
    #             'status': 'error',
    #             'message': 'Chưa cấu hình số điện thoại IP Phone Caresoft vào hệ thống ERP. Vui lòng liên hệ quản trị để được hỗ trợ',
    #             'token': '',
    #             'cs_url': ''
    #         }
    #
    #     brand = self.get_current_brand()
    #     print("brandbrand")
    #     print(brand)
    #     if brand:
    #         cs_url = brand.cs_url
    #         access_key = brand.cs_access_token
    #         print(cs_url)
    #         print(access_key)
    #         if cs_url and access_key:
    #             token = request.env["api.access.token.cs"].sudo().get_token_caresoft_voice(request.env.user.id,
    #                                                                                  access_key,
    #                                                                                  brand.code)
    #
    #             if brand.code == 'KN':
    #                 domain = 'kangnam'
    #             elif brand.code == 'DA':
    #                 domain = 'dongabeauty'
    #             elif brand.code == 'PR':
    #                 domain = 'nhakhoaparis'
    #             else:
    #                 domain = 'hongha'
    #             cs_voice_url = 'https://capi.caresoft.vn/%s/thirdParty/login' % domain
    #
    #             # Login
    #             data = {
    #                 'token': token,
    #             }
    #             headers = {}
    #             try:
    #                 req = requests.post(cs_voice_url, data=data, headers=headers, timeout=20)
    #                 req.raise_for_status()
    #
    #             except requests.HTTPError:
    #                 print('lỗi')
    #             # req.json().get('access_token')
    #
    #
    #
    #             return {
    #                 'token': token,
    #                 'cs_url': cs_voice_url,
    #                 'domain': domain,
    #                 'status': 'ok',
    #                 'message': '',
    #             }
    #         else:
    #             return {
    #                 'status': 'error',
    #                 'message': 'Thương hiệu %s chưa cấu hình link gọi Voice API' % brand.name,
    #                 'token': '',
    #                 'cs_url': ''
    #             }
    #
    #     return {
    #         'status': 'error',
    #         'message': 'Công ty không thuộc thương hiệu',
    #         'token': '',
    #         'cs_url': ''
    #     }
    @http.route('/caresoft/search-account', auth='user', type='json')
    def search_account(self, **kwargs):
        if kwargs.get('res_model') == 'crm.lead' or kwargs.get('res_model') == 'crm.phone.call' or kwargs.get('res_model') == 'crm.case':
            if kwargs.get('value'):
                config = request.env['ir.config_parameter'].sudo()
                model = request.env[kwargs.get('res_model')].sudo().browse(int(kwargs.get('res_id')))
                key = 'domain_caresoft_%s' % model.brand_id.code.lower()
                domain = config.get_param(key)
                token_config = 'domain_caresoft_token_%s' % (model.brand_id.code.lower())
                # get account
                url_api = domain + '/api/v1/contactsByPhone?phoneNo=%s' % kwargs.get('value')
                headers = {
                    'Authorization': 'Bearer ' + config.get_param(token_config),
                    'Content-Type': 'application/json'
                }
                r = requests.get(url_api, headers=headers)
                response = r.json()
                if 'code' in response and response['code'] == 'ok':
                    domain = domain.replace('api', 'web55')
                    domain = domain + '#/index?type=contact&id=%s' % response['contact']['id']
                    return {
                        'status': 0,
                        'url': domain
                    }
                else:
                    return {
                        'status': 1,
                        'message': "Không tìm được Account tương ứng!!!"
                    }
            else:
                return {
                    'status': 1,
                    'message': "Không tìm được số điện thoại!!!"
                }
        return {
            'status': 1,
            'message' : 'Không tìm thấy thương hiệu'
        }
