import logging

from odoo import fields, models, _
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    check_transaction_collaborator = fields.Boolean('Cập nhật tiền CTV', default=False)
    check_source_collaborator = fields.Boolean('Check nguồn CTV', related='source_id.is_collaborator')

    def action_draft(self):
        res = super(SaleOrder, self).action_draft()
        rate = 0
        amount_total = 0
        for so in self:
            if so.booking_id.collaborator_id:
                contract = so.booking_id.collaborator_id.contract_ids.filtered(
                    lambda hd: (hd.company_id == so.booking_id.company_id or so.booking_id.company_id in hd.company_ids) and hd.state == 'effect')
                if contract:
                    walkin = [wk.id for wk in so.booking_id.walkin_ids.filtered(lambda wl: wl.sale_order_id.id == so.id)]
                    walkin_name = self.env['sh.medical.appointment.register.walkin'].search([('id', '=', walkin[0])])
                    services_not_allow = contract.contract_type_id.service_not_allow_ids.ids
                    total_amount_total = 0
                    for sol in so.order_line:
                        # lấy ra tỏng tiền $ trên SO
                        if sol.product_id.type == 'service' and sol.product_id.id not in services_not_allow:
                            tong = (sol.price_subtotal - sol.amount_owed) * contract.contract_type_id.currency_id.rate
                            total_amount_total += tong
                    for sol in so.order_line:
                        if sol.product_id.type == 'service':
                            if sol.product_id.id in services_not_allow:
                                hoa_hong = 0
                            else:
                                if contract.contract_type_id.overseas == 'yes':
                                    amount_total = (sol.price_subtotal - sol.amount_owed) * contract.contract_type_id.currency_id.rate
                                    overseas = [over.id for over in contract.contract_type_id.overseas_type_ids.filtered(lambda over: over.sales_begin <= total_amount_total < over.sales_final)]
                                    if overseas:
                                        ty_le = self.env['collaborator.overseas.type'].browse(int(overseas[0]))
                                        rate = ty_le.rate
                                else:
                                    rate = contract.contract_type_id.rate
                                hoa_hong = (sol.price_subtotal - sol.amount_owed) * rate / 100
                                transaction = self.env['collaborator.transaction'].sudo().create({
                                    'collaborator_id': so.booking_id.collaborator_id.id,
                                    'contract_id': contract.id,
                                    'company_id': contract.company_id.id,
                                    'company_id_so': so.company_id.id,
                                    'brand_id': so.company_id.brand_id.id,
                                    'booking_id': so.booking_id.id,
                                    'walkin_id': walkin[0] if walkin else False,
                                    'sale_order': so.id,
                                    'amount_total': (sol.price_subtotal - sol.amount_owed) * -1,
                                    'discount_percent': rate,
                                    'amount_used': hoa_hong * - 1,
                                    'service_id': sol.product_id.id,
                                    'service_date': so.date_order,
                                    'note': 'Trừ tiền do hủy/mở lại phiếu khám' + ' ' + walkin_name.name,
                                    'check_transaction': True,
                                    'rate': 1 / contract.contract_type_id.currency_id.rate if contract.contract_type_id.currency_id else None,
                                    'amount_total_usd': amount_total * -1 if amount_total else None,
                                    'check_overseas': True if contract.contract_type_id.overseas == 'yes' else False,
                                })

                                collaborator_account = self.env['collaborator.account'].sudo().search(
                                    [('collaborator_id', '=', so.booking_id.collaborator_id.id),('contract_id', '=',contract.id),
                                     ('company_id', '=', contract.company_id.id)])
                                if collaborator_account:
                                    collaborator_account.write({
                                        'collaborator_id': so.booking_id.collaborator_id.id,
                                        'contract_id': contract.id,
                                        'company_id': contract.company_id.id,
                                        'amount_total': collaborator_account.amount_total + (hoa_hong * -1),
                                    })
                                else:
                                    so.env['collaborator.account'].sudo().create({
                                        'collaborator_id': so.booking_id.collaborator_id.id,
                                        'contract_id': contract.id,
                                        'company_id': contract.company_id.id,
                                        'amount_total': hoa_hong * -1,
                                    })

        return res

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        rate = 0
        amount_total = 0
        for so in self:
            if so.booking_id.collaborator_id:
                contract = so.booking_id.collaborator_id.contract_ids.filtered(
                    lambda hd: (hd.company_id == so.booking_id.company_id or so.booking_id.company_id in hd.company_ids) and hd.state == 'effect')
                if contract:
                    walkin = [wk.id for wk in so.booking_id.walkin_ids.filtered(lambda wl: wl.sale_order_id.id == so.id)]
                    if walkin:
                        so.check_transaction_collaborator = True
                        walkin_name = self.env['sh.medical.appointment.register.walkin'].browse(int(walkin[0]))
                        services_not_allow = contract.contract_type_id.service_not_allow_ids.ids
                        # Danh sách để lưu trữ các dòng đơn hàng thỏa mãn điều kiện
                        selected_order_lines = []
                        total_amount_total = 0
                        for sol in so.order_line:
                            # lấy ra tỏng tiền $ trên SO
                            if sol.product_id.type == 'service' and sol.product_id.id not in services_not_allow:
                                tong = (sol.price_subtotal - sol.amount_owed) * contract.contract_type_id.currency_id.rate
                                total_amount_total += tong
                        for sol in so.order_line:
                            if sol.product_id.type == 'service':
                                if sol.product_id.id in services_not_allow:
                                    hoa_hong = 0
                                else:
                                    if contract.contract_type_id.overseas == 'yes':
                                        amount_total = (sol.price_subtotal - sol.amount_owed) * contract.contract_type_id.currency_id.rate
                                        overseas = [over.id for over in contract.contract_type_id.overseas_type_ids.filtered(lambda over: over.sales_begin <= total_amount_total < over.sales_final)]
                                        if overseas:
                                            ty_le = self.env['collaborator.overseas.type'].browse(int(overseas[0]))
                                            rate = ty_le.rate
                                    else:
                                        rate = contract.contract_type_id.rate

                                    hoa_hong = (sol.price_subtotal - sol.amount_owed) * rate / 100
                                    transaction = self.env['collaborator.transaction'].sudo().create({
                                            'collaborator_id': so.booking_id.collaborator_id.id,
                                            'contract_id': contract.id,
                                            'company_id': contract.company_id.id,
                                            'company_id_so': so.company_id.id,
                                            'brand_id': so.company_id.brand_id.id,
                                            'booking_id': so.booking_id.id,
                                            'walkin_id': walkin[0] if walkin else False,
                                            'sale_order': so.id,
                                            'amount_total': sol.price_subtotal - sol.amount_owed,
                                            'discount_percent': rate,
                                            'amount_used': hoa_hong,
                                            'service_id': sol.product_id.id,
                                            'service_date': so.date_order,
                                            'note': 'Cộng tiền phiếu khám' + ' ' + walkin_name.name,
                                            'rate': 1/contract.contract_type_id.currency_id.rate if contract.contract_type_id.currency_id else None,
                                            'amount_total_usd': amount_total if amount_total else None,
                                            'check_overseas': True if contract.contract_type_id.overseas == 'yes' else False,
                                        })
                                    collaborator_account = self.env['collaborator.account'].sudo().search([('collaborator_id', '=', self.booking_id.collaborator_id.id),('contract_id', '=',contract.id),('company_id', '=', contract.company_id.id)])
                                    if collaborator_account:
                                        collaborator_account.write({
                                            'collaborator_id':  so.booking_id.collaborator_id.id,
                                            'contract_id': contract.id,
                                            'company_id': contract.company_id.id,
                                            'amount_total': collaborator_account.amount_total + hoa_hong,
                                        })
                                    else:
                                        soo = so.env['collaborator.account'].sudo().create({
                                            'collaborator_id':  so.booking_id.collaborator_id.id,
                                            'contract_id': contract.id,
                                            'company_id': contract.company_id.id,
                                            'amount_total': hoa_hong,
                                        })
        return res


    def action_transaction_wizard(self):
        for so in self:
            if so.booking_id.collaborator_id:
                contract = so.booking_id.collaborator_id.contract_ids.filtered(
                    lambda hd: (hd.company_id == so.booking_id.company_id or so.booking_id.company_id in hd.company_ids) and hd.state == 'effect')
                if contract:
                    walkin = [wk.id for wk in
                              so.booking_id.walkin_ids.filtered(lambda wl: wl.sale_order_id.id == so.id)]
                    return {
                        'name': 'Cập nhật tiền Cộng tác viên',
                        'view_mode': 'form',
                        'res_model': 'collaborator.sale.order.wizard',
                        'type': 'ir.actions.act_window',
                        'view_id': self.env.ref('collaborator.collaborator_collaborator_sale_order_wizard').id,
                        'context': {
                            'default_sale_order': self.id,
                            'default_collaborator_id': self.booking_id.collaborator_id.id,
                            'default_source_id': self.source_id.id if self.source_id else False,
                            'default_booking_id': self.booking_id.id if self.booking_id else False,
                            'default_company_id': contract.company_id.id,
                            'default_contract_id': contract[0].id if contract else False,
                            'default_walkin_id':  walkin[0] if walkin else False,
                        },
                        'target': 'new'
                    }
                else:
                    raise UserError(_('Cộng tác viên không còn hợp đồng có hiệu lực, vui lòng liên hệ IT!'))
            else:
                raise UserError(_('Booking này không gắn cộng tác viên'))

    def action_update_transaction(self):
        rate = 0
        amount_total = 0
        for so in self:
            if so.booking_id.collaborator_id:
                contract = so.booking_id.collaborator_id.contract_ids.filtered(
                    lambda hd: (hd.company_id == so.booking_id.company_id or so.booking_id.company_id in hd.company_ids) and hd.state == 'effect')
                if contract:
                    walkin = [wk.id for wk in so.booking_id.walkin_ids.filtered(lambda wl: wl.sale_order_id.id == so.id)]
                    if walkin:
                        so.check_transaction_collaborator = True
                        walkin_name = self.env['sh.medical.appointment.register.walkin'].browse(int(walkin[0]))
                        services_not_allow = contract.contract_type_id.service_not_allow_ids.ids
                        for sol in so.order_line:
                            if sol.product_id.type == 'service':
                                if sol.product_id.id in services_not_allow:
                                    hoa_hong = 0
                                else:
                                    if contract.contract_type_id.overseas == 'yes':
                                        amount_total = (sol.price_subtotal - sol.amount_owed) * contract.contract_type_id.currency_id.rate
                                        overseas = [over.id for over in
                                                    contract.contract_type_id.overseas_type_ids.filtered(lambda over: over.sales_begin <= amount_total < over.sales_final)]
                                        if overseas:
                                            ty_le = self.env['collaborator.overseas.type'].browse(int(overseas[0]))
                                            rate = ty_le.rate
                                    else:
                                        rate = contract.contract_type_id.rate
                                    hoa_hong = (sol.price_subtotal - sol.amount_owed) * rate / 100
                                    transaction = self.env['collaborator.transaction'].sudo().create({
                                        'collaborator_id': so.booking_id.collaborator_id.id,
                                        'contract_id': contract.id,
                                        'company_id': contract.company_id.id,
                                        'company_id_so': so.company_id.id,
                                        'brand_id': so.company_id.brand_id.id,
                                        'booking_id': so.booking_id.id,
                                        'walkin_id': walkin[0] if walkin else False,
                                        'sale_order': so.id,
                                        'amount_total': (sol.price_subtotal - sol.amount_owed),
                                        'discount_percent': rate,
                                        'amount_used': hoa_hong,
                                        'service_id': sol.product_id.id,
                                        'service_date': so.date_order,
                                        'note': 'Cộng tiền phiếu khám' + ' ' + walkin_name.name,
                                        'rate': 1 / contract.contract_type_id.currency_id.rate if contract.contract_type_id.currency_id else None,
                                        'amount_total_usd': amount_total if amount_total else None,
                                        'check_overseas': True if contract.contract_type_id.overseas == 'yes' else False,
                                    })

                                    collaborator_account = self.env['collaborator.account'].sudo().search(
                                        [('collaborator_id', '=', self.booking_id.collaborator_id.id),
                                         ('contract_id', '=', contract.id),
                                         ('company_id', '=', contract.company_id.id)])
                                    if collaborator_account:
                                        collaborator_account.write({
                                            'collaborator_id': so.booking_id.collaborator_id.id,
                                            'contract_id': contract.id,
                                            'company_id': contract.company_id.id,
                                            'amount_total': collaborator_account.amount_total + hoa_hong,
                                        })
                                    else:
                                        so.env['collaborator.account'].sudo().create({
                                            'collaborator_id': so.booking_id.collaborator_id.id,
                                            'contract_id': contract.id,
                                            'company_id': contract.company_id.id,
                                            'amount_total': hoa_hong,
                                        })
                                    # # Thêm thông báo thành công ở đây
                                    # success_message = "Cập nhật thành công"
                                    # raise UserError(success_message)
            else:
                raise UserError(_('Booking này không có cộng tác viên'))