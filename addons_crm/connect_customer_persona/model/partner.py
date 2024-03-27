from odoo import models


class Partner(models.Model):
    _inherit = "res.partner"

    def view_customer_persona(self):
        domain = self.env['ir.config_parameter'].sudo().get_param('domain_customer_persona_extend')
        url = domain + '/app/customer-portrait/profile?company_id=%s&partner_id=%s' % (
        self.env.company.id, self.id)
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }