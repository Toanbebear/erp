from odoo import api, fields, models


class InheritCrmLineProduct(models.Model):
    _inherit = 'crm.line.product'

    def write(self, vals):
        res = super(InheritCrmLineProduct, self).write(vals)
        if res:
            for rec in self:
                if 'stage_line_product' in vals:
                    if rec.reward_id:
                        if rec.stage_line_product == 'sold':
                            rec.reward_id.sudo().write({'stage': 'used'})
                        elif rec.stage_line_product == 'cancel':
                            rec.reward_id.sudo().write({'stage': 'allow'})


class InheritCrmLine(models.Model):
    _inherit = 'crm.line'

    def write(self, vals):
        res = super(InheritCrmLine, self).write(vals)
        if res:
            for rec in self:
                if 'stage' in vals:
                    if rec.reward_id:
                        if rec.stage == 'done':
                            rec.reward_id.sudo().write({'stage': 'used'})
                        elif rec.stage == 'cancel':
                            rec.reward_id.sudo().write({'stage': 'allow'})
