from odoo import fields, api, models, _
from odoo.exceptions import ValidationError


class CrmLine(models.Model):
    _inherit = 'crm.line'

    prg_voucher_ids = fields.Many2many('crm.voucher.program', 'line_voucher_ref', 'voucher', 'line',
                                       string='Voucher program')
    voucher_id = fields.Many2many('crm.voucher', string='Voucher')


class CrmLineProduct(models.Model):
    _inherit = 'crm.line.product'

    prg_voucher_ids = fields.Many2many('crm.voucher.program', string='Chương trình Voucher')


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    def apply_voucher(self):
        return {
            'name': 'Áp dụng voucher',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('crm_voucher.view_apply_discount').id,
            'res_model': 'crm.apply.voucher',
            'context': {
                'default_partner_id': self.partner_id.id,
                'default_crm_id': self.id,
            },
            'target': 'new',
        }