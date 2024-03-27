from odoo import api, models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    service_allocation_rate_id = fields.Many2one('service.allocation.rate', string="Tỉ lệ phân bổ giới thiệu dịch vụ")
    has_service_allocation_rate = fields.Boolean(string="Đã có tỉ lệ phân bổ giới thiệu dịch vụ", default=False)

    @api.model_create_multi
    def create(self, vals_list):
        if isinstance(vals_list, list):
            for item in vals_list:
                if item.get('service_allocation_rate_id', False):
                    item['has_service_allocation_rate'] = True
        else:
            if vals_list.get('service_allocation_rate_id', False):
                vals_list['has_service_allocation_rate'] = True
        res = super(ResCompany, self).create(vals_list)
        return res

    def write(self, vals):
        if isinstance(vals, list):
            for item in vals:
                if item.get('service_allocation_rate_id', False):
                    item['has_service_allocation_rate'] = True
        else:
            if vals.get('service_allocation_rate_id', False):
                vals['has_service_allocation_rate'] = True
        res = super(ResCompany, self).write(vals)
        return res
class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    service_allocation_rate_id = fields.Many2one('service.allocation.rate', string="Tỉ lệ phân bổ giới thiệu dịch vụ",
                                                 related='company_id.service_allocation_rate_id', readonly=False)

    has_service_allocation_rate = fields.Boolean(string="Đã có tỉ lệ phân bổ giới thiệu dịch vụ", related='company_id.has_service_allocation_rate', readonly=True)



class ServiceAllocationRate(models.Model):
    _name = 'service.allocation.rate'
    _description = "Company Allocation Rate"

    name = fields.Char(string='Tên', readonly=True, copy=False, related='company_id.name')
    line_ids = fields.One2many('service.allocation.rate.line', 'service_allocation_rate_id', "Service Allocation Rate Lines")
    company_id = fields.Many2one('res.company', string='Công ty', default=lambda self: self.env.company)



    # res_company_ids = fields.One2many('res.company', 'company_allocation_rate_id', "Company")
