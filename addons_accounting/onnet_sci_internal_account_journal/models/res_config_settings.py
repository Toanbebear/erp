from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    journal_internal_collect_id = fields.Many2one('account.journal', string=_('Sổ nhật ký thu hộ'),
                                            related='company_id.journal_internal_collect_id', readonly=False)
    journal_internal_pay_id = fields.Many2one('account.journal', string=_('Sổ nhật ký chi hộ'),
                                            related='company_id.journal_internal_pay_id', readonly=False)
    journal_internal_intro_service_id = fields.Many2one('account.journal', string=_('Sổ nhật ký giới thiệu dịch vụ'),
                                            related='company_id.journal_internal_intro_service_id', readonly=False)
    journal_internal_transfer_asset_id = fields.Many2one('account.journal', string=_('Sổ nhật ký điều chuyển tài sản'),
                                            related='company_id.journal_internal_transfer_asset_id', readonly=False)
    journal_internal_transfer_product_id = fields.Many2one('account.journal', string=_('Sổ nhật ký điều chuyển hàng hóa'),
                                            related='company_id.journal_internal_transfer_product_id', readonly=False)