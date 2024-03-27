import logging

from odoo import models, api

_logger = logging.getLogger(__name__)


class InheritResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def create(self, vals):
        res = super(InheritResPartner, self).create(vals)
        if res:
            account = self.env['account.app.member'].sudo().search([('phone', '=', res.phone)])
            if account:
                account.sudo().write({'partner_id': res.id})
        return res
