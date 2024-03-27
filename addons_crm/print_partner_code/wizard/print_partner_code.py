# -*- coding: utf-8 -*-

from odoo import fields, models, api


class PrintPartnerCode(models.TransientModel):
    _name = "print.partner.code"
    _description = 'Print partner code'

    name = fields.Char(
        'Name',
        default='In tem mã khách hàng',
    )
    message = fields.Char(
        'Message',
        readonly=True,
    )
    output = fields.Selection(
        selection=[('pdf', 'PDF')],
        string='Print to',
        default='pdf',
    )

    @api.model
    def _default_print_partner_code(self):
        data = self.env['print.partner.code.data'].sudo().search([('printed', '=', False)], limit=14)
        return data.mapped('partner_id')

    partner_ids = fields.Many2many('res.partner', 'res_partner_print_partner_code_ref',
                                   'print_id', 'partner_id', string='Mã khách hàng',
                                   default=_default_print_partner_code)

    template = fields.Selection(
        selection=[('print_partner_code.report_partner_code_165x155', '14 tem 78x25mm')],
        string='Mẫu giấy in',
        default='print_partner_code.report_partner_code_165x155',
    )
    qty_per_product = fields.Integer(
        string='Label quantity per product',
        default=1,
    )

    def action_print(self):
        data = self.env['print.partner.code.data'].sudo().search([('printed', '=', False)], limit=14)
        self.partner_ids = data.mapped('partner_id')
        return self.env.ref(self.template).with_context(discard_logo_check=True).report_action(self)

    def action_set_qty(self):
        self.label_ids.write({'qty': self.qty_per_product})

    def action_restore_initial_qty(self):
        for label in self.label_ids:
            if label.qty_initial:
                label.update({'qty': label.qty_initial})
