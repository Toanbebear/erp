# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from lxml import etree

from odoo import api, fields, models, _
# from odoo.osv.orm import setup_modifiers


class AssetModify(models.TransientModel):
    _name = 'asset.modify'
    _description = 'Modify Asset'

    name = fields.Text(string='Lý do', required=True)
    method_number = fields.Integer(string='Số lần khấu hao', required=True)
    method_period = fields.Integer(string='Số tháng trong lũy kế')
    method_end = fields.Date(string='Ngày kết thúc')
    value_residual = fields.Float(string="Giá trị còn lại", help="New residual amount for the asset")
    salvage_value = fields.Float(string='Điều chỉnh giảm')
    salvage_value_2 = fields.Float(string='Điều chỉnh tăng')
    asset_method_time = fields.Char(compute='_get_asset_method_time', string='Asset Method Time', readonly=True)
    gain_value = fields.Boolean(compute="_compute_gain_value",
                                help="Technical field to know if we should display the fields for the creation of gross increase asset")
    account_asset_counterpart_id = fields.Many2one('account.account', string='Đối ứng TK nguyên giá')
    account_asset_id = fields.Many2one('account.account', string='Tài khoản nguyên giá', required=True,
                                       domain=[('internal_type', '=', 'other'), ('deprecated', '=', False)],
                                       help="Account used to record the purchase of the asset at its original price.")
    account_depreciation_id = fields.Many2one('account.account', string='Bút toán khấu hao: Tài khoản tài sản',
                                              required=True,
                                              domain=[('internal_type', '=', 'other'), ('deprecated', '=', False)],
                                              help="Account used in the depreciation entries, to decrease the asset value.")
    account_depreciation_expense_id = fields.Many2one('account.account', string='Bút toán khấu hao: Tài khoản chi phí',
                                                      required=True, domain=[('internal_type', '=', 'other'),
                                                                             ('deprecated', '=', False)],
                                                      help="Account used in the periodical entries, to record a part of the asset as expense.")

    def _get_asset_method_time(self):
        if self.env.context.get('active_id'):
            asset = self.env['account.asset.asset'].browse(self.env.context.get('active_id'))
            self.asset_method_time = asset.method_time

    # @api.model
    # def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
    #     result = super(AssetModify, self).fields_view_get(view_id, view_type, toolbar=toolbar, submenu=submenu)
    #     asset_id = self.env.context.get('active_id')
    #     active_model = self.env.context.get('active_model')
    #     if active_model == 'account.asset.asset' and asset_id:
    #         asset = self.env['account.asset.asset'].browse(asset_id)
    #         doc = etree.XML(result['arch'])
    #         if asset.method_time == 'number' and doc.xpath("//field[@name='method_end']"):
    #             node = doc.xpath("//field[@name='method_end']")[0]
    #             node.set('invisible', '1')
    #             setup_modifiers(node, result['fields']['method_end'])
    #         elif asset.method_time == 'end' and doc.xpath("//field[@name='method_number']"):
    #             node = doc.xpath("//field[@name='method_number']")[0]
    #             node.set('invisible', '1')
    #             setup_modifiers(node, result['fields']['method_number'])
    #         result['arch'] = etree.tostring(doc, encoding='unicode')
    #     return result

    @api.depends('value_residual', 'salvage_value', 'salvage_value_2')
    def _compute_gain_value(self):
        if self.env.context.get('active_id'):
            asset = self.env['account.asset.asset'].browse(self.env.context.get('active_id'))
            self.gain_value = self.value_residual + self.salvage_value + self.salvage_value_2 > asset.value_residual + asset.salvage_value

    @api.model
    def default_get(self, fields):
        res = super(AssetModify, self).default_get(fields)
        asset_id = self.env.context.get('active_id')
        asset = self.env['account.asset.asset'].browse(asset_id)
        if 'name' in fields:
            res.update({'name': asset.name})
        if 'value_residual' in fields:
            res.update({'value_residual': asset.value_residual})
        if 'method_number' in fields and asset.method_time == 'number':
            res.update({'method_number': asset.method_number})
        if 'method_period' in fields:
            res.update({'method_period': asset.method_period})
        if 'method_end' in fields and asset.method_time == 'end':
            res.update({'method_end': asset.method_end})
        if 'account_asset_id' in fields:
            res.update({'account_asset_id': asset.category_id.account_asset_id.id})
        if 'account_depreciation_id' in fields:
            res.update({'account_depreciation_id': asset.category_id.account_depreciation_id.id})
        if 'account_depreciation_expense_id' in fields:
            res.update({'account_depreciation_expense_id': asset.category_id.account_depreciation_expense_id.id})
        if self.env.context.get('active_id'):
            active_asset = self.env['account.asset.asset'].browse(self.env.context.get('active_id'))
            res['asset_method_time'] = active_asset.method_time
        return res

    def modify(self):
        """ Modifies the duration of asset for calculating depreciation
        and maintains the history of old values, in the chatter.
        """
        asset_id = self.env.context.get('active_id', False)
        asset = self.env['account.asset.asset'].browse(asset_id)
        old_values = {
            'method_number': asset.method_number,
            'method_period': asset.method_period,
            'method_end': asset.method_end,
            'salvage_value': asset.salvage_value,
            'salvage_value_2': asset.salvage_value_2,
        }
        asset_vals = {
            'method_number': self.method_number,
            'method_period': self.method_period,
            'method_end': self.method_end,
        }
        if self.salvage_value:
            asset_vals["salvage_value"] = self.salvage_value
        if self.salvage_value_2:
            asset_vals["salvage_value_2"] = asset.salvage_value_2 + self.salvage_value_2

        asset.write(asset_vals)
        asset.compute_depreciation_board()
        tracked_fields = self.env['account.asset.asset'].fields_get(['method_number', 'method_period', 'method_end'])
        changes, tracking_value_ids = asset._message_track(tracked_fields, old_values)
        if changes:
            asset.message_post(subject=_('Depreciation board modified'), body=self.name, tracking_value_ids=tracking_value_ids)
        return {'type': 'ir.actions.act_window_close'}
