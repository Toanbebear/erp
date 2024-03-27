# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AccountAsset(models.Model):
    _inherit = 'account.asset'

    x_code = fields.Char(string='Mã tài sản')
    x_employee_id = fields.Many2one('hr.employee', string='Nhân viên')
    x_specification = fields.Text(string='Thông số của máy')
    x_info_invoice = fields.Char(string='Thông tin hóa đơn')
    x_date_invoice = fields.Date(string='Ngày hóa đơn')
    company_name = fields.Char(string='Công ty', related='company_id.name')
    x_qty = fields.Float(string='Qty')
    x_uom_id = fields.Many2one('uom.uom', string='Uom')

    asset_model_id = fields.Many2one(
        'account.asset', string="Asset Model", domain="[('state', '=', 'model')]")

    @api.onchange('asset_model_id')
    def _onchange_asset_model_id(self):
        if self.asset_model_id:
            self.account_asset_id = self.asset_model_id.account_asset_id
            self.account_depreciation_id = self.asset_model_id.account_depreciation_id
            self.account_depreciation_expense_id = self.asset_model_id.account_depreciation_expense_id
            self.journal_id = self.asset_model_id.journal_id
            self.method = self.asset_model_id.method
            self.method_number = self.asset_model_id.method_number
            self.method_period = self.asset_model_id.method_period
            self.prorata = self.asset_model_id.prorata

    def action_transfer(self):
        """ Transfer Asset"""
        self.ensure_one()
        new_wizard = self.env['account.asset.transfer'].create({
            'asset_id': self.id,
        })
        return {
            'name': _('Asset Transfer'),
            'view_mode': 'form',
            'res_model': 'account.asset.transfer',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': new_wizard.id,
        }

    def action_validate_asset(self):
        for record in self:
            if record.state == 'draft':
                record.validate()

    @api.model
    def create(self, vals):
        res = super(AccountAsset, self).create(vals)
        if res.x_code:
            x_code_exist = self.env['account.asset'].search([('x_code', '=', res.x_code), ('company_id', '=', res.company_id.id), ('active', '=', True), ('id', '!=', res.id)])
            print(x_code_exist)
            if x_code_exist:
                raise ValidationError('Mã tài sản này đã tồn tại')
        return res

    def write(self, vals):
        res = super(AccountAsset, self).write(vals)
        for record in self:
            if vals.get('x_code'):
                x_code_exist = self.env['account.asset'].search([
                    ('x_code', '=', vals.get('x_code')), ('company_id', '=', record.company_id.id), ('active', '=', True), ('id', '!=', record.id)])
                print(x_code_exist)
                if x_code_exist:
                    raise ValidationError('Mã tài sản này đã tồn tại')
        return res
