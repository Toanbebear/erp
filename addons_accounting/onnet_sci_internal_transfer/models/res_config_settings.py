from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    internal_transfer_account = fields.Many2one('account.account', string=_('Phải thu điều chuyển nội bộ'),
                                                related='company_id.internal_transfer_account', readonly=False)
    x_internal_payable_account_id = fields.Many2one('account.account', 'Tài khoản phải trả nội bộ',
                                                    related='company_id.x_internal_payable_account_id', readonly=False)
    x_journal_internal_id = fields.Many2one('account.journal', string='Sổ nhật ký tài khoản nội bộ',
                                            related='company_id.x_journal_internal_id', readonly=False)
    x_service_referral_allocation_rate = fields.Float(string='Tỉ lệ phân bổ giới thiệu dịch vụ (%)', digits='Discount',
                                                      related='company_id.x_service_referral_allocation_rate',
                                                      readonly=False)

    # compute = 'get_company_allocation_rate_id',
    # @api.depends('company_id')
    # def get_company_allocation_rate_id(self):
    #     allocation_rate = self.env['company.allocation.rate'].sudo().search([('res_company_ids', '=', self.company_id)])
    #     if allocation_rate:
    #         self.company_allocation_rate_id = allocation_rate[0]
    #     else:
    #         self.company_allocation_rate_id = False
