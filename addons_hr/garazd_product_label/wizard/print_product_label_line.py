# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class PrintProductLabelLine(models.TransientModel):
    _name = "print.product.label.line"
    _description = 'Line with Product Label Data'

    selected = fields.Boolean(
        string='Print',
        compute='_compute_selected',
        readonly=True,
    )
    wizard_id = fields.Many2one('print.product.label', 'Print Wizard')
    product_id = fields.Many2one('sci.device.main', 'Product', required=True)
    barcode = fields.Char('QR Code')
    qty_initial = fields.Integer('Initial Qty', default=1)
    qty = fields.Integer('Label Qty', default=1)

    @api.depends('qty')
    def _compute_selected(self):
        for record in self:
            if record.qty > 0:
                record.update({'selected': True})
            else:
                record.update({'selected': False})

    def action_plus_qty(self):
        for record in self:
            record.update({'qty': record.qty + 1})

    def action_minus_qty(self):
        for record in self:
            if record.qty > 0:
                record.update({'qty': record.qty - 1})
