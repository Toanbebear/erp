from odoo import fields, api, models, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    code = fields.Char('Code company')

    # Chuyển từ module customer_company
    script_sms_id = fields.One2many('script.sms', 'company_id')
    location_shop = fields.Char('Địa chỉ gửi SMS')
    map_shop = fields.Char('Bản đồ đi đường')

    # Chuyển từ module customer_company_sms
    health_declaration = fields.Char('Khai báo y tế')