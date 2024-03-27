from odoo import fields, models


class ResBrand(models.Model):
    _inherit = 'res.brand'

    master_merchant_code = fields.Char(default='A000000775', help='Mã doanh nghiệp phat triển merchant')
    merchant_code = fields.Char(help='Mã merchant')
    merchant_name = fields.Char(help='Tên viêt tắt của Merchant')
    merchant_type = fields.Char(default='', help='Loại hình doanh nghiệp. Giá trị mặc định để empty')

    app_id = fields.Char(string='App Id', help='Được VNPAY cung cấp')
    secret_key = fields.Char(string='Mã bảo mật', help='Được VNPAY cung cấp cùng App Id')
