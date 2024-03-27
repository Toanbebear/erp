# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models
from odoo.http import request


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    def get_current_brand(self):
        dict_ids = dict([(id,
                          id) for id in request.env.user.company_ids.ids])
        cids = request.httprequest.cookies.get('cids')

        if cids == 'undefined' or cids == '' or cids is False or cids is None:
            cookies_cids = [request.env.user.company_id.id]
        else:
            try:
                cookies_cids = [int(r) for r in request.httprequest.cookies.get('cids').split(",")]
            except:
                cookies_cids = [request.env.user.company_id.id]

        for company_id in cookies_cids:
            if company_id not in dict_ids:
                cookies_cids.remove(company_id)
        if not cookies_cids:
            cookies_cids = [request.env.company.id]

        if cookies_cids:
            company = request.env['res.company'].browse(cookies_cids[0])
            if company:
                return company.brand_id
        return False

    def session_info(self):
        res = super(IrHttp, self).session_info()
        brand = self.get_current_brand()
        if brand:
            brand_id = brand.id
            brand_code = brand.code.lower()
        else:
            brand_id = 0
            brand_code = ''
        res['brand_id'] = brand_id
        res['brand_code'] = brand_code
        res['current_brand'] = (brand_id, brand_code)
        return res
