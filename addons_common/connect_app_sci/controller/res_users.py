import datetime
import logging

from odoo.addons.restful.controllers.app_member.app_member_common import response
from odoo.addons.restful.common import get_redis
from odoo.addons.connect_app_sci.controller.app_sci_common import validate_token, response, get_user_by_token, \
    extract_arguments
from odoo.http import request
import json

from odoo import http

_logger = logging.getLogger(__name__)
api_access_database = "restful.api_access_database"
expires_in = "restful.access_token_expires_in"
r = get_redis()


class GetResUser(http.Controller):

    @http.route("/api/v1/get-user-erp", methods=["POST"], type="json", auth="none", csrf=False)
    def v1_get_user_erp(self, **payload):
        data = []
        body = json.loads(request.httprequest.data.decode('utf-8'))
        list_user = request.env['res.users'].sudo().search(
            [('id', '>', body['last_id'])], order='id', limit=100)
        for user in list_user:
            value = {
                'id_erp': user.id,
                'login': user.login if user.login else None,
                'name': user.partner_id.name if user.partner_id.name else '',
            }
            data.append(value)
        if data:
            return {
                'stage': 0,
                'message': 'Thành công',
                'data': data
            }
        else:
            return {
                'stage': 1,
                'message': 'Thất bại',
                'data': {}
            }

    @http.route("/api/v1/auth/login", methods=["POST"], type="json", auth="none", csrf=False)
    def v1_login(self, **post):
        db = request.env['ir.config_parameter'].sudo().get_param('api_access_database')
        body = json.loads(request.httprequest.data.decode('utf-8'))
        login = body['login']
        password = body['password']
        _logger.info("===========")
        _logger.info(password)
        if not login:
            return response({}, message_type=1, message_content="Chưa nhập email đăng nhập !", status=2)

        if not password:
            return response({}, message_type=1, message_content="Chưa nhập mật khẩu", status=2)
        try:
            uid = request.session.authenticate(db, login, password)
        except:
            uid = 0
        _logger.info(uid)
        # Check OTP
        if uid > 0:
            # Generate tokens
            access_token = request.env["api.access_token"].find_one_or_create_token(user_id=uid, create=True)
            return {
                'stage': 0,
                'data': access_token,
                'message': "Đăng nhập thành công"}
        else:
            return {
                'stage': 1,
                'data': None,
                'message': 'Đăng nhập thất bại'
            }

    @http.route("/api/v1/get-menu", methods=["GET"], type="json", auth="none", csrf=False)
    def v1_get_menu(self, **payload):
        token = request.httprequest.headers.get('Authorization')
        list_menu = []
        key = 'menu_' + token
        if r:
            list_menu_erp = r.get(key)
            if list_menu:
                return {
                    'stage': 0,
                    'data': json.loads(list_menu_erp)
                }
        # token = request.httprequest.headers.get('Authorization')
        user = get_user_by_token(token)
        user_group = user.groups_id
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        request.env.cr.execute(""" 
                            select id, name , web_icon  from ir_ui_menu where parent_id is null""")
        root_menus = request._cr.fetchall()
        for rec in root_menus:
            menu = {
                'id': rec[0],
                'name': rec[1],
                'image': base_url + '/' + rec[2].replace(',', '/') if rec[2] else None
            }
            menus = request.env['ir.ui.menu'].sudo().browse(rec[0])
            list_groups = menus.groups_id
            if not list_groups:
                list_menu.append(menu)
            else:
                for group in list_groups:
                    if group in user_group:
                        list_menu.append(menu)
                        break
        if r:
            r.set(key, json.dumps(list_menu))
        if list_menu:
            return {
                'stage': 0,
                'data': list_menu
            }
        else:
            return {
                'stage': 1,
                'data': None
            }

    @http.route("/api/v1/get-user-information", methods=["GET"], type="json", auth="none", csrf=False)
    def user_information(self, **payload):
        area_data = {
            'mb': 'Miền Bắc',
            'mn': 'Miền Nam'
        }
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        token = request.httprequest.headers.get('access-token')
        user = get_user_by_token(token)
        if user:
            value = {}
            employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id), ('active', '=', True)],
                                                                limit=1)
            if employee:
                value.update({
                    'name': employee.name,
                    'code': employee.employee_code,
                    'birthday': employee.birthday.strftime("%d-%m-%Y") if employee.birthday else '',
                    'work_email': employee.work_email if employee.work_email else '',
                    'job_id': employee.job_id.name if employee.job_id else '',
                    'company': employee.company_id.name if employee.company_id else '',
                    'avatar': base_url + '/web/image?' + 'model=hr.employee&id=' + str(
                        employee.id) + '&field=image_1920' if employee.image_1920 else None,
                    'department': employee.department_id.name if employee.department_id.name else None,
                    'sector': employee.sector_id.name if employee.sector_id.name else None,
                    'brand': employee.root_department.name if employee.root_department.name else None,
                    'area': area_data[employee.area] if employee.area else None
                })
            if value:
                return {
                    'stage': 0,
                    'message': 'Thành công',
                    'data': value
                }
            else:
                return {
                    'stage': 1,
                    'message': 'Không có thông tin',
                    'data': None
                }
        else:
            return {
                'stage': 1,
                'message': 'Không tìm thấy user',
                'data': None
            }
