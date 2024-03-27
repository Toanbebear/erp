from odoo import fields, models, api


class UtmSource(models.Model):
    _inherit = 'utm.source'

    brand_id = fields.Many2one('res.brand', string="Thương hiệu")
    # thương hiệu Paris dùng bộ nguồn cũ nên ko cần thêm trường new_id_pr
    new_id_kn = fields.Many2one('utm.source', string='Nguồn mới Kangnam')
    new_id_hh = fields.Many2one('utm.source', string='Nguồn mới Hồng Hà')

    not_sale = fields.Boolean(string='Không tính doanh số', default=False)
    _sql_constraints = [
        ('code_source_uniq', 'unique(code, brand_id)', 'Mã là duy nhất trên thương hiệu!')
    ]

    @api.model
    def get_import_templates(self):
        return [{
            'label': ('Import Template for Source'),
            'template': 'addons_crm/ct_utm/static/xls/utm_source.xls'
        }]
