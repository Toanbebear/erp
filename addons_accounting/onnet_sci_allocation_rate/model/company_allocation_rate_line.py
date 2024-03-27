from odoo import api, models, fields, _
from odoo.exceptions import ValidationError

class ServiceAllocationRateLine(models.Model):
    _name = 'service.allocation.rate.line'
    _description = "Service Allocation Rate Line"

    # referral_company = fields.Many2one('res.company', string="Công ty giới thiệu dịch vụ", store=False, compute='get_referral_company')
    introduced_company = fields.Many2one('res.company', string="Công ty được giới thiệu dịch vụ", required=True)

    service_allocation_rate_id = fields.Many2one('service.allocation.rate', "Tỷ lệ phân bổ giới thiệu dịch vụ", readonly=False, ondelete="cascade")
    # config_setting_id = fields.Many2one('res.config.settings', string="Config Settings", required=True)

    rate = fields.Float(string='Tỷ lệ phân bổ giới thiệu dịch vụ')

    # @api.depends()
    # def get_referral_company(self):
    #     company_id = self.env.company.id
    #     self.referral_company = company_id

    # @api.onchange('referral_company')
    # def _onchange_referral_company(self):
    #     company_id = self.env.company.id
    #     for rec in self:
    #         rec.referral_company = company_id


    # @api.constrains('referral_company', 'introduced_company')
    # def check_referral_company(self):
    #     for rec in self:
    #         if rec.referral_company.id == rec.introduced_company.id:
    #             raise ValidationError(
    #                 _('Công ty giới thiệu dịch vụ và công ty được giới thiệu dịch vụ phải khác nhau. Vui lòng thử lại!'))
    #         exist_record = super(CompanyAllocationRateLine, self).search_count([('referral_company', '=', rec.referral_company.id), ('introduced_company', '=', rec.introduced_company.id)])
    #         if exist_record > 1:
    #             raise ValidationError(
    #                 _("Đã có dữ liệu tỷ lệ phân bổ cho công ty %s và công ty %s. Vui lòng thử lại!") % (
    #                 rec.referral_company.name, rec.introduced_company.name))




