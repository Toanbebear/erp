from odoo import models, fields


class CrmContentComplainService(models.Model):
    _name = 'crm.content.complain.service'
    _description = 'CRM content complain service'
    _rec_name = 'product_id'

    content_complain = fields.Many2one('crm.content.complain')
    product_id = fields.Many2one('product.product', string='Sản phẩm/Dịch vụ')
    employee_ids = fields.Many2many('hr.employee', string='Nhân viên')


class CrmContentComplainInherit(models.Model):
    _inherit = 'crm.content.complain'

    complain_service_ids = fields.One2many('crm.content.complain.service', 'content_complain',
                                           string='Dịch vụ/Sản phẩm bị khiếu nại')
