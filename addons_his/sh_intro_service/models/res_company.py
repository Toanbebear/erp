from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ResCompany(models.Model):
    _inherit = 'res.company'

    x_is_corporation = fields.Boolean(default=False, string='Tổng công ty')

    @api.constrains('x_is_corporation')
    def constrains_x_is_corporation(self):
        for company in self:
            if company.sudo().search_count([('x_is_corporation', '=', True)]) > 1:
                raise UserError('Đã tồn tại 1 Tổng công ty. Vui lòng kiểm tra lại!')