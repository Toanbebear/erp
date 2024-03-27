from odoo import fields, api, models, _

class ResCompany(models.Model):
    _inherit = 'res.company'

    journal_internal_collect_id = fields.Many2one('account.journal', string=_('Sổ nhật ký thu hộ'))
    journal_internal_pay_id = fields.Many2one('account.journal', string=_('Sổ nhật ký chi hộ'))
    journal_internal_intro_service_id = fields.Many2one('account.journal', string=_('Sổ nhật ký giới thiệu dịch vụ'))
    journal_internal_transfer_asset_id = fields.Many2one('account.journal', string=_('Sổ nhật ký điều chuyển tài sản'))
    journal_internal_transfer_product_id = fields.Many2one('account.journal', string=_('Sổ nhật ký điều chuyển hàng hóa'))
