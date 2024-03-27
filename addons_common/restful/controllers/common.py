"""Part of odoo. See LICENSE file for full copyright and licensing details."""
from odoo.addons.restful.common import (
    extract_arguments,
    invalid_response,
    valid_response
)
from odoo.addons.restful.controllers.main import (
    validate_token
)

import datetime
import logging
from odoo import http
from odoo import tools
from odoo.http import request

_logger = logging.getLogger(__name__)


class CommonController(http.Controller):

    @validate_token
    @http.route("/api/v1/brand", type="http", auth="none", methods=["GET"], csrf=False)
    def get_brand(self, **payload):
        """ API 1.1 Danh sách thương hiệu """

        domain, fields, offset, limit, order = extract_arguments(payload)
        # domain = [('active', '=', True)]
        fields = ['id', 'code', 'name']
        data = request.env['res.brand'].search_read(
            domain=domain, fields=fields, offset=offset, limit=limit, order=order,
        )
        if data:
            return valid_response(data)
        else:
            return valid_response(data)

    @validate_token
    @http.route("/api/v1/country", type="http", auth="none", methods=["GET"], csrf=False)
    def get_country(self, **payload):
        """ API 1.7 Danh sách country """
        domain, fields, offset, limit, order = extract_arguments(payload)
        return valid_response(request.env['res.country'].api_get_data_country(domain=domain,
                                                                      offset=offset,
                                                                      limit=limit,
                                                                      order=order))

    @validate_token
    @http.route("/api/v1/location", type="http", auth="none", methods=["GET"], csrf=False)
    def get_company(self, **payload):
        """ API 1.2 Danh sách cơ sở """
        domain, fields, offset, limit, order = extract_arguments(payload)
        return valid_response(request.env['res.company'].api_get_data_company(request.brand_id,
                                                                      offset=offset,
                                                                      limit=limit,
                                                                      order=order))

    # @validate_token
    # @http.route("/api/v1/price-list", type="http", auth="none", method=['GET'], csrf=False)
    # def get_price_list(self, **payload):
    #     """ API 1.5 Danh sách bảng giá """
    #     domain, fields, offset, limit, order = extract_arguments(payload)
    #     return valid_response(request.env['product.pricelist'].api_get_data(request.brand_id,
    #                                                                         offset=offset,
    #                                                                         limit=limit,
    #                                                                         order=order))

    # @validate_token
    # @http.route("/api/v1/price-list/<id>", type="http", auth="none", method=['GET'], csrf=False)
    # def get_price_list_by_id(self, id=None, **payload):
    #     return valid_response(request.env['product.pricelist'].api_get_data_by_id(request.brand_id, id))

    @validate_token
    @http.route("/api/v1/services1", type="http", auth="none", method=['GET'], csrf=False)
    def get_services(self, company_id=None, pricelist_id=None, code=None, **payload):
        # Chuyển về thành /api/v1/services nếu muốn sử dụng lại code cũ
        data = []
        if not pricelist_id:
            return valid_response(data)

        if not code:
            return valid_response(data)
        # Tách mã dịch vụ bằng dấu phẩy
        codes = code.split(',')
        start = datetime.datetime.now()
        end = datetime.datetime.now()
        thoi_gian = end - start
        # print(thoi_gian.microseconds / 1000)
        for code in codes:
            value = request.env['product.product'].api_get_data(int(pricelist_id), code)
            data += value
        return valid_response(data)
        """ API 1.2 Danh sách dịch vụ"""
        domain, fields, offset, limit, order = extract_arguments(payload)
        brand_type = request.brand_type
        domain = [('active', '=', True)]

        """
            Nếu pricelist_id tổn tại: Lấy ra danh sách thông tin sản phẩm là dịch vụ thuộc bảng giá (product_pricelist) lọc theo company_id và type != 'guarantee'
            Nếu pricelist_id không tồn tại: lấy danh sách thông tin sản phẩm theo brand
    
                - Thương hiệu là học viện thì lấy thông tin danh sách dịch vụ từ danh sách khóa học (op.course)
                - Thương hiệu là bệnh viện thì lấy thông tin danh sách dịch vụ là danh sách dịch vụ bệnh viện (sh_medical_health_center_service)
        {
            "id": 67871,
            "default_code": "CSDA01",
            "name": "Spa - chăm sóc da cơ bản",
            "type": "service",
            "company_id": 10,
            "pricelist_id': 11,
        }
        """
        # return valid_response(request.env['product.product'].search_read([('default_code', 'in', codes)], ['id']))

        if code:
            # Tách mã dịch vụ bằng dấu phẩy
            codes = code.split(',')
            # Lấy dịch vụ theo code
            products = request.env['product.product'].search_read([('default_code', 'in', codes)], ['id'])
            product_ids = list([product['id'] for product in products])
            if product_ids:
                domain.append(('product_id', 'in', product_ids))
            else:
                # Sai code sẽ không trả về sản phẩm nào
                domain.append(('product_id', '=', 0))
        # Không có code sẽ không trả về sản phẩm nào
        else:
            domain.append(('product_id', '=', 0))
        data = []

        company_name = False

        if company_id:
            company_id = eval(company_id)
            company = request.env['res.company'].browse(company_id)
            company_name = company.name
        # Bảng giá là bắt buộc
        if pricelist_id:
            product_pricelist = request.env['product.pricelist'].browse(eval(pricelist_id))

            if product_pricelist:

                if not company_id:
                    company = product_pricelist.company_id
                    company_name = company.name
                    company_id = company.id

            if company_id:
                domain.append(('company_id', 'in', [False, company_id]))

            domain.append(('pricelist_id', '=', eval(pricelist_id)))

            price_list_item = request.env['product.pricelist.item'].search(domain)

            product_info = request.env['product.product']
            ls_product = []

            for rec in price_list_item:
                if rec.applied_on == '0_product_variant':  # Biến thể sản phẩm
                    ls_product.append(rec)
                elif rec.applied_on == '1_product':  # Sản phẩm
                    for prd in rec.product_tmpl_id.product_variant_ids:
                        ls_product.append(prd)
                elif rec.applied_on == '2_product_category':  # Nhóm sản phẩm/dịch vụ
                    for prd in product_info.search([('categ_id', '=', rec.categ_id.id)]):
                        ls_product.append(prd)
                else:  # Tất cả sản phẩm/dịch vụ
                    for rec in product_info.search([]):
                        ls_product.append(rec)

            for record in ls_product:
                product = record.product_id
                price = tools.format_amount(request.env, record.fixed_price, request.env.ref('base.VND'), 'vn'),
                val = {
                    'id': product.id,
                    'default_code': product.default_code,
                    # 'name': product.name,
                    'name': '[%s] %s - %s' % (product.default_code, product.name, price[0]),
                    'type': product.type,
                    # 'brand': [{'id': brand.id, 'name': brand.name}],
                    'company': [{'id': company_id, 'name': company_name}],
                    # 'pricelist': {'id': price_list.pricelist_id.id, 'name': price_list.pricelist_id.name},
                }
                data.append(val)
        # else:
        #     if brand_type == 'academy':
        #         # Dịch vụ là các khóa học.
        #         data_course = request.env['op.course'].search(domain).mapped(
        #             lambda element: (element, element.product_id, element.company_id))
        #         for rec in data_course:
        #             # course = rec[0]
        #             product = rec[1]
        #             company = rec[2]
        #             val = {
        #                 'id': product.id,
        #                 'default_code': product.default_code,
        #                 # 'name': product.name,
        #                 'name': '[%s] %s - %s' % (product.default_code, product.name, product.price),
        #                 'type': product.type,
        #                 # 'brand': [{'id': brand_id, 'name': brand.name}],
        #                 'company': [{'id': company.id, 'name': company.name}],
        #                 # 'course': {'id': course.id, 'name': course.name}
        #             }
        #             data.append(val)
        #     else:
        #         # Dịch vụ là dịch vụ y tế.
        #         service_center = request.env['sh.medical.health.center.service']
        #         data_medical_health = service_center.search(domain).mapped(
        #             lambda element: (element, element.product_id))
        #
        #         for element in data_medical_health:
        #             service = element[0]
        #             product = element[1]
        #
        #             val = {
        #                 'id': product.id,
        #                 'default_code': product.default_code,
        #                 # 'name': product.name,
        #                 'name': '[%s] %s' % (product.default_code, product.name),
        #                 'type': product.type,
        #                 # 'brand': [{'id': ins.brand.id, 'name': ins.brand.name} for ins in service.institution],
        #                 'company': [{'id': ins.his_company.id, 'name': ins.his_company.name} for ins in
        #                             service.institution],
        #             }
        #             data.append(val)
        if data:
            return valid_response(data)
        else:
            return valid_response(data)


    # @validate_token
    # @http.route("/api/v1/country", type="http", auth="none", methods=["GET"], csrf=False)
    # def get_brand(self, **payload):
    #     """ API 1.1 Danh sách Quốc gia"""
    #
    #     domain, fields, offset, limit, order = extract_arguments(payload)
    #     # domain = [('active', '=', True)]
    #     fields = ['id', 'code', 'name', 'phone_code']
    #     data = request.env['res.country'].search_read(
    #         domain=domain, fields=fields, offset=offset, limit=limit, order=order,
    #     )
    #     if data:
    #         return valid_response(data)
    #     else:
    #         return valid_response(data)
    #
    # @validate_token
    # @http.route("/api/v1/location", type="http", auth="none", methods=["GET"], csrf=False)
    # def get_company(self, **payload):
    #     """ API 1.2 Danh sách cơ sở"""
    #
    #     # Thông tin người dùng từ request
    #     brand_id = request.brand_id
    #
    #     domain, fields, offset, limit, order = extract_arguments(payload)
    #     domain = [('brand_id', '=', brand_id), ("code", "!=", "KN.HCM.03")]
    #     fields = ['id', 'code', 'name']
    #     data = request.env['res.company'].search_read(
    #         domain=domain, fields=fields, offset=offset, limit=limit, order=order,
    #     )
    #     if data:
    #         return valid_response(data)
    #     else:
    #         return valid_response(data)

    @validate_token
    @http.route("/api/v1/location/<id>", type="http", auth="none", methods=["GET"], csrf=False)
    def get_company_by_id(self, id=None, **payload):
        """ API 1.2 Chi tiết cơ sở"""
        try:
            _id = int(id)
        except Exception as e:
            return invalid_response("invalid object id", "invalid literal %s for id with base " % id)

        domain, fields, offset, limit, order = extract_arguments(payload)
        return valid_response(request.env['res.company'].api_get_data(request.brand_id, _id, limit=limit, order=order, offset=offset))
        domain = [("id", "=", _id)]
        # fields = ['id', 'code', 'name']
        data = request.env['res.company'].search_read(
            domain=domain, fields=fields, offset=offset, limit=limit, order=order,
        )
        if data:
            return valid_response(data)
        else:
            return valid_response(data)

    @validate_token
    @http.route("/api/v1/complain_code", type="http", auth="none", methods=["GET"], csrf=False)
    def get_complain(self, **payload):
        """ API 1.5 Danh sách nội dung khiếu nại"""
        #Todo: Model complain.code đã bỏ từ ERP
        domain, fields, offset, limit, order = extract_arguments(payload)
        # domain = [('active', '=', True)]
        fields = ['id', 'code', 'name', 'department_id']
        data = request.env['crm.complain.code'].search_read(
            domain=domain, fields=fields, offset=offset, limit=limit, order=order,
        )
        if data:
            return valid_response(data)
        else:
            return valid_response(data)
    #
    # @validate_token
    # @http.route("/api/v1/services", type="http", auth="none", method=['GET'], csrf=False)
    # def get_services(self, company_id=None, pricelist_id=None, code=None, **payload):
    #     # TODO
    #     """ API 1.2 Danh sách dịch vụ"""
    #     domain, fields, offset, limit, order = extract_arguments(payload)
    #     brand_type = request.brand_type
    #     domain = [('active', '=', True)]
    #
    #     """
    #         Nếu pricelist_id tổn tại: Lấy ra danh sách thông tin sản phẩm là dịch vụ thuộc bảng giá (product_pricelist) lọc theo company_id và type != 'guarantee'
    #         Nếu pricelist_id không tồn tại: lấy danh sách thông tin sản phẩm theo brand
    #
    #             - Thương hiệu là học viện thì lấy thông tin danh sách dịch vụ từ danh sách khóa học (op.course)
    #             - Thương hiệu là bệnh viện thì lấy thông tin danh sách dịch vụ là danh sách dịch vụ bệnh viện (sh_medical_health_center_service)
    #     {
    #         "id": 67871,
    #         "default_code": "CSDA01",
    #         "name": "Spa - chăm sóc da cơ bản",
    #         "type": "service",
    #         "company_id": 10,
    #         "pricelist_id': 11,
    #     }
    #     """
    #
    #     if code:
    #         # Tách mã dịch vụ bằng dấu phẩy
    #         codes = code.split(',')
    #         # Lấy dịch vụ theo code
    #         products = request.env['product.product'].search_read([('default_code', 'in', codes)], ['id'])
    #         product_ids = list([product['id'] for product in products])
    #         if product_ids:
    #             domain.append(('product_id', 'in', product_ids))
    #         else:
    #             # Sai code sẽ không trả về sản phẩm nào
    #             domain.append(('product_id', '=', 0))
    #     # Không có code sẽ không trả về sản phẩm nào
    #     else:
    #          domain.append(('product_id', '=', 0))
    #     data = []
    #
    #     company_name = False
    #
    #     if company_id:
    #         company_id = eval(company_id)
    #         company = request.env['res.company'].browse(company_id)
    #         company_name = company.name
    #     # Bảng giá là bắt buộc
    #     if pricelist_id:
    #         product_pricelist = request.env['product.pricelist'].browse(eval(pricelist_id))
    #
    #         if product_pricelist:
    #
    #             if not company_id:
    #                 company = product_pricelist.company_id
    #                 company_name = company.name
    #                 company_id = company.id
    #
    #         if company_id:
    #             domain.append(('company_id', 'in', [False, company_id]))
    #
    #         domain.append(('pricelist_id', '=', eval(pricelist_id)))
    #
    #         price_list_item = request.env['product.pricelist.item'].search(domain)
    #
    #         product_info = request.env['product.product']
    #         ls_product = []
    #
    #         for rec in price_list_item:
    #             if rec.applied_on == '0_product_variant':  # Biến thể sản phẩm
    #                 ls_product.append(rec)
    #             elif rec.applied_on == '1_product':  # Sản phẩm
    #                 for prd in rec.product_tmpl_id.product_variant_ids:
    #                     ls_product.append(prd)
    #             elif rec.applied_on == '2_product_category':  # Nhóm sản phẩm/dịch vụ
    #                 for prd in product_info.search([('categ_id', '=', rec.categ_id.id)]):
    #                     ls_product.append(prd)
    #             else:  # Tất cả sản phẩm/dịch vụ
    #                 for rec in product_info.search([]):
    #                     ls_product.append(rec)
    #
    #         for record in ls_product:
    #             product = record.product_id
    #             price = tools.format_amount(request.env, record.fixed_price, request.env.ref('base.VND'), 'vn'),
    #             val = {
    #                 'id': product.id,
    #                 'default_code': product.default_code,
    #                 # 'name': product.name,
    #                 'name': '[%s] %s - %s' % (product.default_code, product.name, price[0]),
    #                 'type': product.type,
    #                 # 'brand': [{'id': brand.id, 'name': brand.name}],
    #                 'company': [{'id': company_id, 'name': company_name}],
    #                 # 'pricelist': {'id': price_list.pricelist_id.id, 'name': price_list.pricelist_id.name},
    #             }
    #             data.append(val)
    #     # else:
    #     #     if brand_type == 'academy':
    #     #         # Dịch vụ là các khóa học.
    #     #         data_course = request.env['op.course'].search(domain).mapped(
    #     #             lambda element: (element, element.product_id, element.company_id))
    #     #         for rec in data_course:
    #     #             # course = rec[0]
    #     #             product = rec[1]
    #     #             company = rec[2]
    #     #             val = {
    #     #                 'id': product.id,
    #     #                 'default_code': product.default_code,
    #     #                 # 'name': product.name,
    #     #                 'name': '[%s] %s - %s' % (product.default_code, product.name, product.price),
    #     #                 'type': product.type,
    #     #                 # 'brand': [{'id': brand_id, 'name': brand.name}],
    #     #                 'company': [{'id': company.id, 'name': company.name}],
    #     #                 # 'course': {'id': course.id, 'name': course.name}
    #     #             }
    #     #             data.append(val)
    #     #     else:
    #     #         # Dịch vụ là dịch vụ y tế.
    #     #         service_center = request.env['sh.medical.health.center.service']
    #     #         data_medical_health = service_center.search(domain).mapped(
    #     #             lambda element: (element, element.product_id))
    #     #
    #     #         for element in data_medical_health:
    #     #             service = element[0]
    #     #             product = element[1]
    #     #
    #     #             val = {
    #     #                 'id': product.id,
    #     #                 'default_code': product.default_code,
    #     #                 # 'name': product.name,
    #     #                 'name': '[%s] %s' % (product.default_code, product.name),
    #     #                 'type': product.type,
    #     #                 # 'brand': [{'id': ins.brand.id, 'name': ins.brand.name} for ins in service.institution],
    #     #                 'company': [{'id': ins.his_company.id, 'name': ins.his_company.name} for ins in
    #     #                             service.institution],
    #     #             }
    #     #             data.append(val)
    #     if data:
    #         return valid_response(data)
    #     else:
    #         return valid_response(data)

    @validate_token
    @http.route("/api/v1/services/<id>", type="http", auth="none", method=['GET'], csrf=False)
    def get_services_by_id(self, id=None):
        """ API 1.2 Lấy chi tiết dịch vụ theo ID - CHƯA THẤY SỬ DỤNG"""
        try:
            _id = int(id)
        except Exception as e:
            return invalid_response("invalid object id", "invalid literal %s for id with base " % id)
        return valid_response(request.env['product.product'].api_get_data_by_id(request.brand_id, pid=_id))
        domain = [('active', '=', True), ('id', '=', _id)]
        list_data = []
        product_product = request.env['product.product'].search(domain)

        if product_product:
            val = {
                'id': _id,
                'code': product_product.default_code,
                # 'name': product_product.product_tmpl_id.name,
                'name': '[%s] %s' % (product_product.default_code, product_product.product_tmpl_id.name),
                'type': product_product.product_tmpl_id.type,
            }

            list_data.append(val)

        data = list_data

        if data:
            return valid_response(data)
        else:
            return valid_response(data)

    @validate_token
    @http.route("/api/v1/service_categories", type="http", auth="none", method=['GET'], csrf=False)
    def get_service_categories(self, **payload):
        """ API 1.7 Danh sách nhóm dịch vụ"""
        domain, fields, offset, limit, order = extract_arguments(payload)
        return valid_response(request.env['product.category'].api_get_data(offset=offset,
                                                                      limit=limit,
                                                                      order=order))
        # Thông tin người dùng từ request
        brand_id = request.brand_id

        domain = [('active', '=', 'true'), ('brand_id', '=', brand_id)]
        service_cate = request.env['product.category'].search(domain=domain, fields=fields, offset=offset, limit=limit, order=order,)
        data = []
        for sv in service_cate:
            val = {
                'id': sv.id,
                'name': sv.name,
            }
            data.append(val)

        if data:
            return valid_response(data)
        else:
            return valid_response(data)

    @validate_token
    @http.route("/api/v1/complain_code/<id>", type="http", auth="none", methods=["GET"], csrf=False)
    def get_complain_by_id(self, _id=None, **payload):
        """ API 1.6 Nội dung khiếu nại"""
        #Todo: Model crm.complain.code hiện đang ko dùng nữa
        domain, fields, offset, limit, order = extract_arguments(payload)
        domain = [("id", "=", _id)]
        # fields = ['id', 'code', 'name']
        data = request.env['crm.complain.code'].search_read(
            domain=domain, fields=fields, offset=offset, limit=limit, order=order,
        )
        domain.append(('id', '=', _id))

        data = request.env['product.pricelist'].search_read(
            domain=domain, fields=fields, offset=offset, limit=limit, order=order)

        if data:
            return valid_response(data)
        else:
            return valid_response(data)

    # @validate_token
    # @http.route("/api/v1/price-list", type="http", auth="none", method=['GET'], csrf=False)
    # def get_price_list(self, **payload):
    #     """ API 1.3 Danh sách bảng giá """
    #
    #     # Thông tin người dùng từ request
    #     brand_id = request.brand_id
    #
    #     domain, fields, offset, limit, order = extract_arguments(payload)
    #
    #     domain = [('active', '=', 'true'), ('type', '=', 'service'), ('brand_id', '=', brand_id)]
    #     data = []
    #     price_list_info = request.env['product.pricelist'].search(domain)
    #     for element in price_list_info:
    #         brand = element.brand_id
    #         company = element.company_id
    #         val = {
    #             'id': element.id,
    #             'name': element.name,
    #             'type': element.type,
    #             'currency_id': element.currency_id.name,
    #             'brand': [{'id': brand.id, 'name': brand.name}],
    #             'company': [{'id': company.id, 'name': company.name}],
    #         }
    #         data.append(val)
    #     if data:
    #         return valid_response(data)
    #     else:
    #         return valid_response(data)

    # @validate_token
    # @http.route("/api/v1/price-list/<id>", type="http", auth="none", method=['GET'], csrf=False)
    # def get_price_list_by_id(self, id=None, **payload):
    #     """ API 1.5 Danh sách bảng giá """
    #
    #     # Thông tin người dùng từ request
    #     brand_id = request.brand_id
    #
    #     domain, fields, offset, limit, order = extract_arguments(payload)
    #
    #     try:
    #         _id = int(id)
    #     except Exception as e:
    #         return invalid_response("invalid object id", "invalid literal %s for id with base " % id)
    #
    #     domain = [('active', '=', 'true'), ('type', '=', 'service'), ('brand_id', '=', brand_id), ('id', '=', _id)]
    #
    #     data = []
    #     price_list_info = request.env['product.pricelist'].search(domain)
    #
    #     for element in price_list_info:
    #         brand = element.brand_id
    #         company = element.company_id
    #         val = {
    #             'id': element.id,
    #             'name': element.name,
    #             'type': element.type,
    #             'currency_id': element.currency_id.name,
    #             'brand': [{'id': brand.id, 'name': brand.name}],
    #             'company': [{'id': company.id, 'name': company.name}],
    #         }
    #         data.append(val)
    #     if data:
    #         return valid_response(data)
    #     else:
    #         return valid_response(data)

    @validate_token
    @http.route("/api/v1/price-list-items/<id>", type="http", auth="none", method=['GET'], csrf=False)
    def get_price_items_list_by_id(self, id=None, **payload):
        """ API 1.5 Lấy chi tiết bảng giá theo ID"""
        domain, fields, offset, limit, order = extract_arguments(payload)

        try:
            _id = int(id)
        except Exception as e:
            return invalid_response("invalid object id", "invalid literal %s for id with base " % id)

        price_list_items = []
        try:
            price_list_info = request.env['product.pricelist'].browse(_id)
            data = [{'info_price_list': {
                'brand': {'id': price_list_info.brand_id.id, 'name': price_list_info.brand_id.name},
                'company': {'id': price_list_info.company_id.id, 'name': price_list_info.company_id.name}}},
                {'info_price_list_item': price_list_items}]
        except Exception as e:
            return invalid_response("invalid object id", "invalid literal %s for id with base " % id)

        domain = [('pricelist_id', '=', _id)]
        price_list_item_info = request.env['product.pricelist.item'].search(domain)

        if len(price_list_item_info) > 0:
            product_info = request.env['product.product']
            for element in price_list_item_info:
                if element.applied_on == '0_product_variant':  # Biến thể sản phẩm
                    product = element.product_id
                    val = {
                        'id': product.id,
                        'product': {'id': product.id, 'name': product.name},
                        'min_quantity': element.min_quantity,
                        'currency_id': element.currency_id.name,
                        'price': element.price,
                        'date_start': element.date_start,
                        'date_end': element.date_end,
                    }
                    price_list_items.append(val)
                elif element.applied_on == '1_product':  # Sản phẩm
                    for point in element.product_tmpl_id.product_variant_ids:
                        product = point
                        val = {
                            'id': product.id,
                            'product': {'id': product.id, 'name': product.name},
                            'min_quantity': element.min_quantity,
                            'currency_id': element.currency_id.name,
                            'price': element.price,
                            'date_start': element.date_start,
                            'date_end': element.date_end,
                        }
                        price_list_items.append(val)
                elif element.applied_on == '2_product_category':  # Nhóm sản phẩm/dịch vụ
                    for point in product_info.search([('categ_id', '=', element.categ_id.id)]):
                        product = point
                        val = {
                            'id': product.id,
                            'product': {'id': product.id, 'name': product.name},
                            'min_quantity': element.min_quantity,
                            'currency_id': element.currency_id.name,
                            'price': element.price,
                            'date_start': element.date_start,
                            'date_end': element.date_end,
                        }
                        price_list_items.append(val)
                else:  # Tất cả sản phẩm/dịch vụ
                    for point in product_info.search([]):
                        product = point
                        val = {
                            'id': product.id,
                            'product': {'id': product.id, 'name': product.name},
                            'min_quantity': element.min_quantity,
                            'currency_id': element.currency_id.name,
                            'price': element.price,
                            'date_start': element.date_start,
                            'date_end': element.date_end,
                        }
                        price_list_items.append(val)

        if data:
            return valid_response(data)
        else:
            return valid_response(data)

    @validate_token
    @http.route("/api/v1/promotion", type="http", auth="none", method=['GET'], csrf=False)
    def get_promotion(self, company_id=None, **payload):
        """ API 1.4 Chương trình khuyến mại"""
        domain, fields, offset, limit, order = extract_arguments(payload)
        return valid_response(request.env['crm.discount.program'].api_get_data(request.brand_id,
                                                                            offset=offset,
                                                                            limit=limit,
                                                                            order=order))
        # Thông tin người dùng từ request
        brand_id = request.brand_id
        domain = [('active', '=', 'true'), ('brand_id', '=', brand_id)]
        if company_id:
            domain.append(('company_id', '=', eval(company_id)))
        info_discount_program = request.env['crm.discount.program'].search(domain)
        data = []
        for element in info_discount_program:
            campaign = element.campaign_id
            company = element.company_ids

            val = {
                'id': element.id,
                'code': element.code,
                'name': element.name,
                'campaign': {'id': campaign.id, 'name': campaign.name},
                'brand': {'id': brand_id, 'name': element.brand_id.name},
                'company': [{'id': rec.id, 'name': rec.name} for rec in company]
            }

            data.append(val)

        if data:
            return valid_response(data)
        else:
            return valid_response(data)

    @validate_token
    @http.route("/api/v1/promotion/<id>", type="http", auth="none", method=['GET'], csrf=False)
    def get_promotion_by_id(self, id=None, **payload):
        """ API 1.3 Lấy danh sách khuyến mại theo ID"""
        return valid_response(request.env['crm.discount.program'].api_get_data(request.brand_id, int(id)))
        # Thông tin người dùng từ request
        # brand_id = request.brand_id
        #
        # domain, fields, offset, limit, order = extract_arguments(payload)
        #
        # try:
        #     _id = int(id)
        # except Exception as e:
        #     return invalid_response("invalid object id", "invalid literal %s for id with base " % id)
        #
        # domain.append(('id', '=', _id))
        #
        # info_discount_program = request.env['crm.discount.program'].search(domain)
        # data = []
        # for element in info_discount_program:
        #     campaign = element.campaign_id
        #     company = element.company_ids
        #
        #     val = {
        #         'id': element.id,
        #         'code': element.code,
        #         'name': element.name,
        #         'campaign': {'id': campaign.id, 'name': campaign.name},
        #         'brand': {'id': brand_id, 'name': element.brand_id.name},
        #         'company': [{'id': rec.id, 'name': rec.name} for rec in company]
        #     }
        #
        #     data.append(val)
        #
        # if data:
        #     return valid_response(data)
        # else:
        #     return valid_response(data)
