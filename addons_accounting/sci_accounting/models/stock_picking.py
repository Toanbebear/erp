# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _


class StockPickingInherit(models.Model):
    _inherit = 'stock.picking'


    # Ly do: làm sai tk input và output khi mua hàng từ partner là công ty chi nhánh khác.

    # def action_done(self):
    #     """Adjusting stock output and input account in case of transferring between companies."""
    #     partner_company = self.env['res.company'].sudo().search([('partner_id', '=', self.partner_id.id)], limit=1)
    #     partner = self.partner_id.with_context(force_company=self.company_id.id)
    #     if partner_company and partner_company.enable_inter_company_transfer:  # and self.company_id.enable_inter_company_transfer:
    #         if self.picking_type_id.code == 'outgoing':
    #             self = self.with_context(stock_output=partner.property_account_receivable_id.id)
    #         if self.picking_type_id.code == 'incoming':
    #             self = self.with_context(stock_input=partner.property_account_payable_id.id)
    #     return super(StockPickingInherit, self).action_done()
