from odoo import models, api


class UtmSource(models.Model):
    _inherit = 'crm.lead'

    @api.onchange('brand_id')
    def _onchange_brand_id(self):
        if self.brand_id:
            source_ids = self.env['utm.source'].search([('brand_id', '=', self.brand_id.id)])
            if source_ids:
                return {'domain': {'source_id': [('id', 'in', source_ids.ids)]}}
            else:
                return {'domain': {'source_id': [('id', 'in', [])]}}
        else:
            return {'domain': {'source_id': [('id', 'in', [])]}}
