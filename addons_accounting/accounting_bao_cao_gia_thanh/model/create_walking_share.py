# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import timedelta

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class WalkinShare(models.TransientModel):
    _inherit = 'create.walkin.share'

    def create_walkin_share(self):
        so = super(WalkinShare, self).create_walkin_share()

        if so.exists():
            self.get_institution()
            vt_thue_phong_mo = self.env.ref('crm_booking_share.vt_thue_phong_mo')
            company = self.env['res.company'].search([('partner_id', '=', self.partner_so.id)])
            if not company:
                raise ValidationError('Không tìm thấy công ty có liên hệ ' + self.partner_so.name)

            picking_type = self.env['stock.picking.type'].sudo().search([
                ('company_id', '=', company.id),
                ('code', '=', 'incoming')])

            if not picking_type:
                raise ValidationError('Không tìm kiểu giao nhận của công ty ' + company.name)

            value = {
                'partner_id': self.institution.his_company.partner_id.id,
                'company_id': company.id,
                'picking_type_id': picking_type.id,
                'order_line': [
                    (0, 0, {
                        'name': vt_thue_phong_mo.name,
                        'product_id': vt_thue_phong_mo.id,
                        'product_qty': 1.0,
                        'product_uom': vt_thue_phong_mo.uom_po_id.id,
                        'price_unit': self.amount,
                        'date_planned': fields.Datetime.now(),
                        'company_id': company.id,
                    }),
                ],
            }

            po = self.env['purchase.order'].with_context(force_company=company.id).sudo().create(value)

            if not po:
                raise ValidationError('Có lỗi xảy ra khi tạo đơn mua hàng.')

            po.with_context(force_company=company.id).sudo().button_confirm()
            if po.state == 'purchase':
                dest_location = self.env['stock.location'].sudo().search([
                                    ('company_id', '=', company.id),
                                    ('is_location_supply_share', '=', True)], limit=1
                )

                if not dest_location:
                    raise ValidationError('Chưa cấu hình Địa điểm nhận VT thuê phòng')

                pickings = po.picking_ids
                for picking in pickings:
                    picking.location_dest_id = dest_location.id
                    picking.with_context(force_company=company.id).sudo().action_assign()
                    wiz = picking.with_context(force_company=company.id).sudo().button_validate()
                    wiz = self.env[wiz['res_model']].browse(wiz['res_id'])
                    wiz.with_context(force_company=company.id).sudo().process()

        return so



