import json
import logging
from odoo import models, api, tools

from odoo.addons.restful.common import (
    get_redis, get_redis_server
)

_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def write(self, values):
        res = super(ProductProduct, self).write(values)
        if any(key in values.keys() for key in ['default_code', 'name', 'type', 'active', 'currency_id', 'list_price']):
            self.recache()
        return res
    @api.model
    def create(self, values):
        res = super(ProductProduct, self).create(values)
        if res.type == 'service':
            res.recache()
        return res

    def unlink(self):
        res = super(ProductProduct, self).unlink()
        if self.type == 'service':
            self.recache()
        return res

    def recache(self, pricelist=None, code=None):
        redis_client = get_redis_server()
        if pricelist and code:
            key = self.get_key_product_code(code)
            data = self._get_data(pricelist, code)
            if redis_client:
                redis_client.set(key,
                                 json.dumps(data, indent=4, sort_keys=False, default=str))

    def get_services(self):
        domain = [('active', '=', 'true'), ('type', '=', 'service'), ('default_code', '!=', False)]
        records = self.env['product.product'].search(domain)
        data = {}
        for record in records:
            data[record.default_code] = record.id
        return data

    def get_data(self, pricelist=None, codes=None):
        if not codes:
            return []

        domain = [('active', '=', True), ('type', '=', 'service'), ('default_code', 'in', codes)]
        records = self.env['product.product'].search(domain)
        pricelist_items = self.env['product.pricelist.item'].search([('pricelist_id', '=', pricelist),
                                                                     ('product_id', 'in', records.ids)])

        product_ids = pricelist_items.mapped('product_id')
        data = []
        for record in records:
            if record in product_ids:
                pricelist_item = pricelist_items.filtered(lambda pli: pli.product_id == record)
                if pricelist_item:
                    fixed_price = pricelist_item[0].fixed_price
                else:
                    fixed_price = 'Chưa có giá'
                val = {
                    'id': record.id,
                    'name': '[%s] %s - %s' % (record.default_code, record.name, fixed_price),
                    'type': record.type,
                    'default_code': record.default_code,
                    'currency_id': record.currency_id.name,
                    'pricelist_ids': [pricelist],
                }
                data.append(val)
        return data
    def _get_data(self, pricelist=None, code=None):
        if not code:
            return {}

        domain = [('active', '=', True), ('type', '=', 'service'), ('default_code', '=', code)]
        records = self.env['product.product'].search(domain)
        pricelist_items = self.env['product.pricelist.item'].search([('pricelist_id', '=', pricelist),
                                                                     ('product_id', 'in', records.ids)])

        product_ids = pricelist_items.mapped('product_id')
        if records:
            record = records[0]
            if record in product_ids:
                pricelist_item = pricelist_items.filtered(lambda pli: pli.product_id == record)
                if pricelist_item:
                    fixed_price = pricelist_item[0].fixed_price
                else:
                    fixed_price = 'Chưa có giá'
                val = {
                    'id': record.id,
                    'name': '[%s] %s - %s' % (record.default_code, record.name, fixed_price),
                    'type': record.type,
                    'default_code': record.default_code,
                    'currency_id': record.currency_id.name,
                    'pricelist_ids': [pricelist],
                }

                return val

        return {}
    # def get_key(self, pricelist_id=None, codes=None, pid=None):
    #     # Mỗi bảng giá sẽ có 1 key trong redis, chứa tất cả codes của dịch vụ trong bảng giá
    #     # Cần cập nhật mỗi khi thay đổi bảng giá hoặc dịch vụ
    #     key_pricelist_codes = "pricelist_%s" % pricelist_id
    #
    #     # Mỗi mã dịch vụ có 1 key trong redis
    #     key_codes = []
    #     for code in codes:
    #         key_codes.append(self.get_key_product_code(code))
    #     return key_pricelist_codes, key_codes

    def get_key_product_code(self, code):
        return "product_code_%s" % code

    def api_get_data_product(self, pricelist_id=None, codes=None, offset=0, limit=None, order=None):
        """
            Sale chọn 1 hoặc nhiều dịch vụ, sau đó tạo booking, chọn bảng giá sẽ gọi api và trả về mã dịch vụ
            có nằm trong bảng giá đó không, nếu không thì chọn lại

            Tách từng mã code, lấy dữ liệu và merge lại
        """
        result = []
        for code in codes:
            # Xử lý từng mã dịch vụ, nếu không tìm thấy trong cache thì lấy trong database
            line = self._api_get_data_product(pricelist_id, code)
            if line:
                result.append(line)
        return result

    def _api_get_data_product(self, pricelist_id=None, code=None):
        redis_client = get_redis_server()
        if redis_client:
            _logger.info('REDIS: %s_%s get from cache' % (pricelist_id, code))
            key_code = self.get_key_product_code(code)
            service = redis_client.get(key_code)
            if service:
                # Kiểm tra pricelist_id có trong pricelist_ids của service không
                line = json.loads(service)
                if 'pricelist_ids' in line:
                    if pricelist_id in line['pricelist_ids']:
                        line.pop('pricelist_ids')

        result = self._get_data(pricelist_id, code)
        if result:
            if redis_client:
                redis_client.set(self.get_key_product_code(result['default_code']),
                                  json.dumps(result, indent=4, sort_keys=False, default=str))
            result.pop('pricelist_ids')
        return result

    def api_get_data(self, pricelist_id=None, code=None, offset=0, limit=None, order=None):
        domain = [('active', '=', True), ('type', '=', 'service')]
        pricelist_items = self.env['product.pricelist.item'].search([('pricelist_id', '=', pricelist_id)])
        product_ids = pricelist_items.mapped('product_id')
        domain += [('id', 'in', product_ids.ids)]
        if code:
            domain += [('default_code', '=', code)]
        records = self.env['product.product'].search(domain)
        data = []
        for record in records:
            # brand = record.brand_id
            # company = record.company_id
            pricelist_item = pricelist_items.filtered(lambda pli: pli.product_id == record)
            if pricelist_item:
                fixed_price = pricelist_item[0].fixed_price
            else:
                fixed_price = 'Chưa có giá'
            val = {
                'id': record.id,
                'name': '[%s] %s - %s' % (record.default_code, record.name, fixed_price),
                'type': record.type,
                'default_code': record.default_code,
                'currency_id': record.currency_id.name,
                # 'company': [{'id': company_id.id, 'name': company_id.name}],
            }
            data.append(val)
        return data

    #
    # def api_get_data_product1(self, pricelist_id=None, codes=None, offset=0, limit=None, order=None):
    #     """
    #         Sale chọn 1 hoặc nhiều dịch vụ, sau đó tạo booking, chọn bảng giá sẽ gọi api và trả về mã dịch vụ
    #         có nằm trong bảng giá đó không, nếu không thì chọn lại
    #     """
    #     key_pricelist_codes, key_codes = self.get_key(pricelist_id, codes)
    #
    #     redis_client = get_redis()
    #     if redis_client:
    #         _logger.info('REDIS: %s, %s get from cache' % (key_pricelist_codes, key_codes))
    #         services = redis_client.mget(key_codes)
    #         data = []
    #         for service in services:
    #             # Kiểm tra pricelist_id có trong pricelist_ids của service không
    #             line = json.loads(service)
    #             if 'pricelist_ids' in line:
    #                 if pricelist_id in line['pricelist_ids']:
    #                     line.pop('pricelist_ids')
    #                     data.append(line)
    #         return data
    #
    #     result = self.get_data(pricelist_id, codes)
    #     if result:
    #         if redis_client:
    #             for line in result:
    #                 redis_client.set(self.get_key_product_code(line['default_code']),
    #                                   json.dumps(line, indent=4, sort_keys=False, default=str))
    #         for line in result:
    #             pass
    #             #line.pop('pricelist_ids')
    #     return result

    def api_get_data_by_id(self, brand_id=None, pid=None):
        # Check log không thấy sử dụng
        key = self.get_key_product_code(brand_id, pid)
        redis_client = get_redis()
        if redis_client:
            data = redis_client.get(key)
            if data:
                return json.loads(data)

        result = self.get_data(brand_id, pid)
        if result:
            if redis_client:
                redis_client.set(key, json.dumps(result, indent=4, sort_keys=True, default=str))
        return result

    def api_get_data_by_codes(self,  company_id=None, pricelist_id=None, codes=None):
        result = []
        redis_client = get_redis()
        if redis_client:
            for code in codes:
                key = "%s_%s_%s" % (company_id, pricelist_id, code)

                if redis_client.exists(key):
                    value = redis_client.get(key)
                    result.append(json.loads(value))
                else:
                    # Nếu không có key thì lấy giá trị trong db và lưu vào cache
                    value = self.get_data_by_code(company_id, pricelist_id, code)
                    if value:
                        # lưu cache
                        redis_client.set(key, json.dumps(value, indent=4, sort_keys=True, default=str))
                        result.append(value)

            return result

        else:
            domain = [('active', '=', True)]
            # Lấy dịch vụ theo code
            products = self.env['product.product'].search_read([('default_code', 'in', codes)], ['id'])
            product_ids = list([product['id'] for product in products])
            if product_ids:
                domain.append(('product_id', 'in', product_ids))
            else:
                return result

            company_name = False
            if company_id:
                company_id = eval(company_id)
                company = self.env['res.company'].browse(company_id)
                company_name = company.name

            # Bảng giá là bắt buộc
            if pricelist_id:
                product_pricelist = self.env['product.pricelist'].browse(eval(pricelist_id))

                if product_pricelist:

                    if not company_id:
                        company = product_pricelist.company_id
                        company_name = company.name
                        company_id = company.id

                if company_id:
                    domain.append(('company_id', 'in', [False, company_id]))

                domain.append(('pricelist_id', '=', eval(pricelist_id)))

                price_list_item = self.env['product.pricelist.item'].search(domain)

                product_info = self.env['product.product']
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
                    price = tools.format_amount(self.env, record.fixed_price, self.env.ref('base.VND'), 'vn'),
                    val = {
                        'id': product.id,
                        'default_code': product.default_code,
                        'name': '[%s] %s - %s' % (product.default_code, product.name, price[0]),
                        'type': product.type,
                        'company': [{'id': company_id, 'name': company_name}],
                    }
                    result.append(val )
            return result

    def get_data_by_code(self,  company_id=None, pricelist_id=None, code=None):
        val = None
        domain = [('active', '=', True)]
        # Lấy dịch vụ theo code
        products = self.env['product.product'].search_read([('default_code', '=', code)], ['id'])
        product_ids = list([product['id'] for product in products])
        if product_ids:
            domain.append(('product_id', 'in', product_ids))

            company_name = False
            if company_id:
                company_id = eval(company_id)
                company = self.env['res.company'].browse(company_id)
                company_name = company.name

            # Bảng giá là bắt buộc
            if pricelist_id:
                product_pricelist = self.env['product.pricelist'].browse(eval(pricelist_id))

                if product_pricelist:

                    if not company_id:
                        company = product_pricelist.company_id
                        company_name = company.name
                        company_id = company.id

            if company_id:
                domain.append(('company_id', 'in', [False, company_id]))

            domain.append(('pricelist_id', '=', eval(pricelist_id)))

            price_list_item = self.env['product.pricelist.item'].search(domain)

            product_info = self.env['product.product']
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
                price = tools.format_amount(self.env, record.fixed_price, self.env.ref('base.VND'), 'vn'),
                val = {
                    'id': product.id,
                    'default_code': product.default_code,
                    'name': '[%s] %s - %s' % (product.default_code, product.name, price[0]),
                    'type': product.type,
                    'company': [{'id': company_id, 'name': company_name}],
                }
                break
        return val
