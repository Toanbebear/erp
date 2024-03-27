from odoo import fields, api, models


class CrmInformationConsultant(models.Model):
    _inherit = 'crm.information.consultant'

    crm_line_product_id = fields.Many2one('crm.line.product', string='Dòng sản phẩm')
