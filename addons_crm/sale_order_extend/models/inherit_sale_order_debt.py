from odoo import models, fields, api, _


class InheritSaleOrderDebt(models.Model):
    _inherit = 'sale.order.debt'

    sale_order_line_id = fields.Many2one('sale.order.line')

    def confirm_debt_ctv(self):
        if self.sale_order_id.state == 'sale':
            for so in self.sale_order_id:
                if so.booking_id.collaborator_id:
                    contract = so.booking_id.collaborator_id.contract_ids.filtered(
                        lambda hd: (hd.company_id == so.booking_id.company_id or so.booking_id.company_id in hd.company_ids) and hd.state == 'effect')
                    if contract:
                        walkin = [wk.id for wk in so.booking_id.walkin_ids.filtered(lambda wl: wl.sale_order_id.id == so.id)]
                        if walkin:
                            so.check_transaction_collaborator = True
                            walkin_name = self.env['sh.medical.appointment.register.walkin'].browse(int(walkin[0]))
                            services_not_allow = contract.contract_type_id.service_not_allow_ids.ids
                            total_amount_total = 0
                            for sol in so.order_line:
                                # lấy ra tỏng tiền $ trên SO trc khi trả nợ
                                if sol.product_id.type == 'service' and sol.product_id.id not in services_not_allow:
                                    tong = sol.price_subtotal - sol.amount_owed
                                    total_amount_total += tong
                            if self.sale_order_line_id.product_id.type == 'service':
                                if self.sale_order_line_id.product_id.id in services_not_allow:
                                    hoa_hong = 0
                                else:
                                    if contract.contract_type_id.overseas == 'yes':
                                        # Tổng tiền đã đóng
                                        amount_total = self.amount_paid * contract.contract_type_id.currency_id.rate
                                        amount_total_all = total_amount_total * contract.contract_type_id.currency_id.rate
                                        total_before = (total_amount_total * contract.contract_type_id.currency_id.rate) - amount_total
                                        # Tỉ lệ sau trước khi trả nợ
                                        overseas_before = [var.id for var in contract.contract_type_id.overseas_type_ids.filtered(lambda var: var.sales_begin <= total_before < var.sales_final)]
                                        ty_le_before = self.env['collaborator.overseas.type'].browse(int(overseas_before[0]))
                                        rate_before = ty_le_before.rate

                                        # Tỉ lệ sau khi trả nợ
                                        overseas = [over.id for over in contract.contract_type_id.overseas_type_ids.filtered(lambda over: over.sales_begin <= amount_total_all < over.sales_final)]
                                        ty_le = self.env['collaborator.overseas.type'].browse(int(overseas[0]))
                                        rate = ty_le.rate

                                        hoa_hong_1 = (total_amount_total - self.amount_paid) * ((rate - rate_before) / 100)
                                        hoa_hong = (self.amount_paid * rate / 100) + hoa_hong_1
                                    else:
                                        rate = contract.contract_type_id.rate
                                        hoa_hong = self.amount_paid * rate / 100
                                        amount_total = 0
                                    transaction = self.env['collaborator.transaction'].sudo().create({
                                        'collaborator_id': so.booking_id.collaborator_id.id,
                                        'contract_id': contract.id,
                                        'company_id': contract.company_id.id,
                                        'company_id_so': so.company_id.id,
                                        'brand_id': so.company_id.brand_id.id,
                                        'booking_id': so.booking_id.id,
                                        'walkin_id': walkin[0] if walkin else False,
                                        'sale_order': so.id,
                                        'amount_total': self.amount_paid,
                                        'discount_percent': rate,
                                        'amount_used': hoa_hong,
                                        'service_id': self.product_id.id,
                                        'service_date': so.date_order,
                                        'note': 'Cộng tiền duyệt nợ phiếu khám' + ' ' + walkin_name.name,
                                        'rate': 1 / contract.contract_type_id.currency_id.rate if contract.contract_type_id.currency_id else None,
                                        'amount_total_usd': amount_total if amount_total else None,
                                        'check_overseas': True if contract.contract_type_id.overseas == 'yes' else False,
                                    })

                                    collaborator_account = self.env['collaborator.account'].sudo().search(
                                        [('collaborator_id', '=', so.booking_id.collaborator_id.id),
                                         ('contract_id', '=', contract.id), ('company_id', '=', contract.company_id.id)])
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


    def roll_back_debt(self):
        if self.sale_order_id.state == 'sale':
            amount_total = 0
            for so in self.sale_order_id:
                if so.booking_id.collaborator_id:
                    contract = so.booking_id.collaborator_id.contract_ids.filtered(
                        lambda hd: (hd.company_id == so.booking_id.company_id or so.booking_id.company_id in hd.company_ids) and hd.state == 'effect')
                    if contract:
                        walkin = [wk.id for wk in
                                  so.booking_id.walkin_ids.filtered(lambda wl: wl.sale_order_id.id == so.id)]
                        if walkin:
                            walkin_name = self.env['sh.medical.appointment.register.walkin'].browse(int(walkin[0]))
                            services_not_allow = contract.contract_type_id.service_not_allow_ids.ids
                            total_amount_total = 0
                            for sol in so.order_line:
                                # lấy ra tỏng tiền $ trên SO trc khi trả nợ
                                if sol.product_id.type == 'service' and sol.product_id.id not in services_not_allow:
                                    tong = sol.price_subtotal - sol.amount_owed
                                    total_amount_total += tong
                            if self.sale_order_line_id.product_id.type == 'service':
                                if self.sale_order_line_id.product_id.id in services_not_allow:
                                    hoa_hong = 0
                                else:
                                    amount_paid = self.amount_paid * -1
                                    if contract.contract_type_id.overseas == 'yes':
                                        # Tổng tiền đã đóng
                                        amount_total = amount_paid * contract.contract_type_id.currency_id.rate
                                        amount_total_all = (total_amount_total * contract.contract_type_id.currency_id.rate) + amount_total
                                        # Tỉ lệ sau trước khi trả nợ
                                        overseas_before = [var.id for var in contract.contract_type_id.overseas_type_ids.filtered(lambda var: var.sales_begin <= total_amount_total * contract.contract_type_id.currency_id.rate < var.sales_final)]
                                        ty_le_before = self.env['collaborator.overseas.type'].browse(int(overseas_before[0]))
                                        rate_before = ty_le_before.rate

                                        # Tỉ lệ sau khi trả nợ
                                        overseas = [over.id for over in
                                                    contract.contract_type_id.overseas_type_ids.filtered(lambda over: over.sales_begin <= amount_total_all < over.sales_final)]
                                        ty_le = self.env['collaborator.overseas.type'].browse(int(overseas[0]))
                                        rate = ty_le.rate

                                        hoa_hong_1 = total_amount_total * ((rate - rate_before) / 100)
                                        hoa_hong = (amount_paid * rate / 100) + hoa_hong_1
                                    else:
                                        rate = contract.contract_type_id.rate
                                        hoa_hong = amount_paid * rate / 100
                                        amount_total = 0
                                    transaction = self.env['collaborator.transaction'].sudo().create({
                                        'collaborator_id': so.booking_id.collaborator_id.id,
                                        'contract_id': contract.id,
                                        'company_id': contract.company_id.id,
                                        'company_id_so': so.company_id.id,
                                        'brand_id': so.company_id.brand_id.id,
                                        'booking_id': so.booking_id.id,
                                        'walkin_id': walkin[0] if walkin else False,
                                        'sale_order': so.id,
                                        'amount_total': amount_paid  * -1,
                                        'discount_percent': rate,
                                        'amount_used': hoa_hong * - 1,
                                        'service_id': self.product_id.id,
                                        'service_date': so.date_order,
                                        'note': 'Trừ tiền do hủy duyệt nợ phiếu khám' + ' ' + walkin_name.name,
                                        'rate': 1 / contract.contract_type_id.currency_id.rate if contract.contract_type_id.currency_id else None,
                                        'amount_total_usd': amount_total * -1 if amount_total else None,
                                        'check_overseas': True if contract.contract_type_id.overseas == 'yes' else False,
                                    })

                                    collaborator_account = self.env['collaborator.account'].sudo().search(
                                        [('collaborator_id', '=', so.booking_id.collaborator_id.id),
                                         ('contract_id', '=', contract.id),
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