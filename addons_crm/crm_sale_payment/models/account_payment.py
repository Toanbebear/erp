from openpyxl.worksheet import related
import numpy as np

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError

SERVICE_HIS_TYPE = [('Spa', 'Spa'), ('Laser', 'Laser'), ('Odontology', 'Nha'), ('Surgery', 'Phẫu thuật'),
                    ('ChiPhi', 'Chi phí khác')]


class PaymentCrmLine(models.Model):
    _inherit = 'crm.line'
    total_received = fields.Monetary('Tiền đã thu', readonly=True)
    currency_id = fields.Many2one('res.currency', store=True, string='Currency',
                                  default=lambda self: self.env.company.currency_id)
    remaining_amount = fields.Monetary(string="Tiền chưa sử dụng", currency_field="currency_id",
                                       compute="_calculate_remaining_amount_crm_line", readonly=True)

    # số tiền chưa sử dụng ở booking sẽ tính ở tất cả các công ty
    # remaining amount = số tiền đã thu - số tiền đã thực hiện trong sale.order
    @api.depends('total_received')
    def _calculate_remaining_amount_crm_line(self):
        for rec in self:
            rec.remaining_amount = rec.total_received
            if rec.total_received > 0:
                order_line_ids = self.env['sale.order'].sudo().search([('booking_id', '=', rec.crm_id.id),
                                                                       ('state', 'in', ['sale', 'done'])]) \
                    .mapped('order_line').filtered(lambda x: x.crm_line_id.id == rec.id)
                if order_line_ids:
                    rec.remaining_amount = rec.total_received - sum(i.price_subtotal for i in order_line_ids)

    # dịch vụ phụ thu
    service_id_2 = fields.Many2one('sh.medical.health.center.service', string='Dịch vụ phụ thu')

    @api.onchange('service_id_2')
    def onchange_service_id_2(self):
        if self.service_id_2:
            self.service_id = self.service_id_2
            item_price = self.env['product.pricelist.item'].search(
                [('pricelist_id', '=', self.price_list_id.id), ('product_id', '=', self.service_id_2.product_id.id)])
            if item_price:
                self.unit_price = item_price.fixed_price
            else:
                raise ValidationError(_('This service is not included in the price list'))
        else:
            self.unit_price = 0
            self.quantity = 1
            self.discount_cash = 0
            self.discount_percent = 0

    def action_save_new_crm_line(self):
        if not self.product_id:
            self.write({
                'product_id': self.service_id_2.product_id.id,
                'service_id': self.service_id_2.id
            })
        if self.env.context.get("account_payment_id"):
            account_payment = self.env['account.payment'].browse(self.env.context.get("account_payment_id"))
            if account_payment.exists():
                account_payment.write({
                    'service_ids': [(0, 0, {'crm_line_id': self.id,
                                            'company_id': self.company_id.id})]
                })


class PaymentCrmLineProduct(models.Model):
    _inherit = 'crm.line.product'
    total_received = fields.Float('Tiền đã thu', readonly=True)
    currency_id = fields.Many2one('res.currency', store=True, string='Currency',
                                  default=lambda self: self.env.company.currency_id)
    remaining_amount = fields.Monetary(string="Tiền chưa sử dụng", currency_field="currency_id",
                                       compute="_calculate_remaining_amount_crm_line_product", readonly=True)

    # số tiền chưa sử dụng ở booking sẽ tính tổng các công ty
    # remaining amount = số tiền đã thu - số tiền đã thực hiện trong sale.order
    @api.depends('total_received')
    def _calculate_remaining_amount_crm_line_product(self):
        for rec in self:
            rec.remaining_amount = rec.total_received
            if rec.total_received > 0:
                order_line_ids = self.env['sale.order'].search([('booking_id', '=', rec.booking_id.id),
                                                                ('state', 'in', ['sale', 'done'])]) \
                    .mapped('order_line').filtered(lambda x: x.line_product.id == rec.id)
                if order_line_ids:
                    # rec.remaining_amount = rec.total_received - sum(i.price_subtotal for i in order_line_ids)

                    # Tiền chưa sử dụng = Tiền đã thu - đã giao(qty_delivered) * (1 - chiết khâu) * đơn giá - đã giao * (đơn giá - giảm giá tiền mặt / số lượng)
                    # - đã giao * giảm còn / số lượng - đã giao * giảm khác / số lượng(các trường này lấy ở SO khi SO ở trạng sale / done)
                    # rec.remaining_amount = rec.total_received - sum(
                    #     i.qty_delivered * (1 - i.discount)*i.price_unit - i.qty_delivered*(i.price_unit - i.discount_cash/i.product_uom_qty)
                    #     - i.qty_delivered*i.sale_to/i.product_uom_qty - i.qty_delivered*i.other_discount/i.product_uom_qty
                    #     for i in order_line_ids)

                    # Nếu trường giảm còn trong SO có dữ liệu.
                    order_line_sale_to = order_line_ids.filtered(lambda x: x.sale_to > 0)
                    amount_sale_to, amount_not_sale_to = 0, 0
                    if order_line_sale_to:
                        # Tiền chưa sử dụng = Tiền đã thu - đã giao * (giảm còn / số lượng - chiết khấu * đơn giá - giảm giá tiền mặt / số lượng - giảm khác / số lượng)
                        amount_sale_to = sum(
                            i.qty_delivered * (
                                    i.sale_to / i.product_uom_qty - i.discount * i.price_unit / 100 - i.discount_cash / i.product_uom_qty - i.other_discount / i.product_uom_qty)
                            for i in order_line_sale_to)
                    # Nếu trường giảm còn trong SO không có dữ liệu.
                    order_line_not_sale_to = order_line_ids.filtered(lambda x: x.sale_to == 0)
                    if order_line_not_sale_to:
                        # Tiền chưa sử dụng = Tiền đã thu - đã giao * (đơn giá - giảm giá tiền mặt/số lượng - giảm khác/số lượng - đơn giá*chiết khấu)
                        # amount_not_sale_to = sum(
                        #     i.qty_delivered * (
                        #             i.price_unit - i.discount_cash / i.product_uom_qty - i.other_discount / i.product_uom_qty - i.price_unit * i.discount / 100)
                        #     for i in order_line_ids.filtered(lambda x: x.sale_to == 0))
                        amount_not_sale_to = sum(
                            i.product_uom_qty * (
                                    i.price_unit - i.discount_cash / i.product_uom_qty - i.other_discount / i.product_uom_qty - i.price_unit * i.discount / 100)
                            for i in order_line_ids.filtered(lambda x: x.sale_to == 0))
                    # Tính tiền chưa sử dụng.
                    rec.remaining_amount = rec.total_received - amount_sale_to - amount_not_sale_to


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    service_ids = fields.One2many('crm.account.payment.detail', 'account_payment_id', string="Account payment detail")
    product_ids = fields.One2many('crm.account.payment.product.detail', 'account_payment_id',
                                  string="Account payment product detail")
    crm_sale_payment_ids = fields.One2many('crm.sale.payment', 'account_payment_id', string="Sale payment")
    check_auto_input_money = fields.Boolean(string='Tự động điền thông tin số tiền giao dịch', default=False)
    check_auto_input_money_product = fields.Boolean(string='Tự động điền thông tin số tiền giao dịch', default=False)
    transfer_payment_id = fields.Many2one('crm.transfer.payment', string='Phiếu điều chuyển')
    subtotal_service = fields.Monetary(string='Tổng tiền sau giảm của dịch vụ', compute='_get_subtotal_service')
    subtotal_product = fields.Monetary(string='Tổng tiền sau giảm của sản phẩm', compute='_get_subtotal_product')
    currency_service_id = fields.Many2one('res.currency', string='Currency Service',
                                          default=lambda self: self.env.company.currency_id)

    is_deposit = fields.Boolean(string="Đặt cọc")
    is_share_booking = fields.Boolean(string="Có chia sẻ booking không?", compute="_get_share_booking", default=False)
    is_old_payment = fields.Boolean(string="Có là phiếu cũ không?", compute="_is_old_payment", default=False)
    is_update_payment_list = fields.Boolean(string="Có đang cập nhật phiếu hay không", default=False)
    num_of_move_line = fields.Integer('Bút toán phát sinh', compute='compute_num_of_move_line')

    @api.constrains('service_ids')
    def prepayment_service_constrains(self):
        for rec in self.service_ids:
            if rec.total and rec.prepayment_amount:
                if rec.prepayment_amount < 0:
                    raise ValidationError(_('Số tiền giao dịch phải lớn hơn hoặc bằng 0.'))
                if rec.payment_type == 'outbound':
                    if round(rec.remaining_amount) < round(rec.prepayment_amount):
                        raise ValidationError(_('Số tiền giao dịch phải nhỏ hơn hoặc bằng số tiền chưa sử dụng.'))
                else:
                    if round(rec.total) < round(rec.total_received) + round(rec.prepayment_amount):
                        raise ValidationError(_('Số tiền giao dịch phải nhỏ hơn hoặc bằng số tiền cần phải đóng.'))

    @api.constrains('product_ids')
    def prepayment_product_constrains(self):
        for rec in self.product_ids:
            if rec.total and rec.prepayment_amount:
                if rec.prepayment_amount < 0:
                    raise ValidationError(_('Số tiền giao dịch phải lớn hơn hoặc bằng 0.'))
                if rec.payment_type == 'outbound':
                    if round(rec.remaining_amount) < round(rec.prepayment_amount):
                        raise ValidationError(_('Số tiền giao dịch phải nhỏ hơn hoặc bằng số tiền chưa sử dụng.'))
                else:
                    if round(rec.total) < round(rec.total_received) + round(rec.prepayment_amount):
                        raise ValidationError(_('Số tiền giao dịch phải nhỏ hơn hoặc bằng số tiền cần phải đóng.'))

    @api.onchange('payment_type')
    def onchange_payment_type(self):
        if self.service_ids:
            for rec in self.service_ids:
                rec.prepayment_amount = 0
        if self.product_ids:
            for rec in self.product_ids:
                rec.prepayment_amount = 0

    @api.depends('move_line_ids')
    def compute_num_of_move_line(self):
        for rec in self:
            rec.num_of_move_line = 0
            if rec.move_line_ids:
                rec.num_of_move_line = len(rec.move_line_ids)

    @api.depends('crm_id')
    def _get_share_booking(self):
        for rec in self:
            rec.is_share_booking = False
            if rec.crm_id.company2_id:
                rec.is_share_booking = True

    # @api.depends('crm_id')
    # def _is_old_payment(self):
    #     for rec in self:
    #         rec.is_old_payment = False
    #         if rec.id:
    #             # Kiểm tra xem có trong sale payment không?
    #             if not self.env['crm.sale.payment'].search([('account_payment_id.id', '=', rec.id)]):
    #                 rec.is_old_payment = True

    @api.depends('state', 'service_ids', 'product_ids')
    def _is_old_payment(self):
        """
        Phiếu thu cũ là phiếu thu đã xác nhận và ko có các line phân bổ
        """
        for record in self:
            record.is_old_payment = False
            if record.state not in ['draft', 'cancel'] and (not record.service_ids and not record.product_ids):
                record.is_old_payment = True

    @api.depends('service_ids')
    def _get_subtotal_service(self):
        for rec in self:
            if rec.service_ids:
                subtotal_distinct = set(
                    [(line['crm_line_id'][0] if line['crm_line_id'] else False, line['total']) for line in
                     rec.service_ids.filtered(lambda x: x.stage != 'cancel')])
                rec.subtotal_service = sum([pay[1] for pay in subtotal_distinct if pay[0]])
                # Fix vấn đề khi mở xem bản ghi tự động cập nhật lại bản ghi
                # rec.currency_service_id = rec.service_ids[0].currency_id.id
            else:
                rec.subtotal_service = 0.0

    @api.depends('product_ids')
    def _get_subtotal_product(self):
        for rec in self:
            if rec.product_ids:
                subtotal_distinct = set([(line['crm_line_product_id'][0], line['total']) for line in
                                         rec.product_ids.filtered(lambda x: x.stage != 'cancel')])
                rec.subtotal_product = sum([pay[1] for pay in subtotal_distinct])
                # Fix vấn đề khi mở xem bản ghi tự động cập nhật lại bản ghi
                # rec.currency_service_id = rec.product_ids[0].currency_id.id
            else:
                rec.subtotal_product = 0.0

    # số tiền tổng giao dịch phải bằng tổng số tiền phân bổ.
    @api.constrains('state', 'amount_vnd', 'product_ids', 'service_ids')
    def amount_constrains(self):
        for rec in self:
            if rec.state != 'cancelled':
                prepayment_amount_service = sum(i.prepayment_amount for i in rec.service_ids)
                prepayment_amount_product = sum(i.prepayment_amount for i in rec.product_ids)
                if prepayment_amount_service + prepayment_amount_product != 0:
                    if rec.amount_vnd != round(prepayment_amount_service + prepayment_amount_product):
                        raise ValidationError(_('Tổng số tiền giao dịch phải bằng tổng số tiền phân bổ.'))

    # 2. cập nhật booking
    @api.onchange('crm_id')
    def onchange_crm(self):
        res = self._create_account_payment_line(self.crm_id)
        self.write({
            'service_ids': res[0],
            'product_ids': res[1]
        })

    @api.onchange('check_auto_input_money')
    def _onchange_check_auto_input_money(self):
        for rec in self.service_ids:
            rec.prepayment_amount = (rec.total - rec.total_received) \
                if self.check_auto_input_money else 0

    @api.onchange('check_auto_input_money_product')
    def _onchange_check_auto_money_product(self):
        for rec in self.product_ids:
            rec.prepayment_amount = (rec.total - rec.total_received) \
                if self.check_auto_input_money_product else 0

    # 1. Tạo mới account payment
    @api.model
    def create(self, vals):
        if vals.get('crm_id') and not vals.get('service_ids') and not vals.get('product_ids') \
                and not self.service_ids and not self.product_ids:
            # Nếu chưa có line dịch vụ/sp thì tạo line.
            # Trong trường hợp tạo phiếu đặt cọc -> tự động tạo line dịch vụ
            crm_id = self.env['crm.lead'].browse(int(vals.get('crm_id')))
            res = self._create_account_payment_line(self.crm_id if self.crm_id else crm_id)
            vals.update({
                'service_ids': res[0],
                'product_ids': res[1]
            })
        # print('VALUES : ', vals)
        if 'currency_service_id' not in vals:
            vals.update({'currency_service_id': self.env.company.currency_id.id})
        res = super(AccountPayment, self).create(vals)
        # print('CREATED : ', res)
        return res


    def _prepare_payment_moves(self):
        ''' Prepare the creation of journal entries (account.move) by creating a list of python dictionary to be passed
        to the 'create' method.

        Example 1: outbound with write-off:

        Account             | Debit     | Credit
        ---------------------------------------------------------
        BANK                |   900.0   |
        RECEIVABLE          |           |   1000.0
        WRITE-OFF ACCOUNT   |   100.0   |

        Example 2: internal transfer from BANK to CASH:

        Account             | Debit     | Credit
        ---------------------------------------------------------
        BANK                |           |   1000.0
        TRANSFER            |   1000.0  |
        CASH                |   1000.0  |
        TRANSFER            |           |   1000.0

        :return: A list of Python dictionary to be passed to env['account.move'].create.
        '''
        all_move_vals = []
        for payment in self:
            company_currency = payment.company_id.currency_id
            move_names = payment.move_name.split(payment._get_move_name_transfer_separator()) if payment.move_name else None

            # Compute amounts.
            write_off_amount = payment.payment_difference_handling == 'reconcile' and -payment.payment_difference or 0.0
            if payment.payment_type in ('outbound', 'transfer'):
                counterpart_amount = payment.amount
                liquidity_line_account = payment.journal_id.default_debit_account_id
            else:
                counterpart_amount = -payment.amount
                liquidity_line_account = payment.journal_id.default_credit_account_id

            # Manage currency.
            if payment.currency_id == company_currency:
                # Single-currency.
                balance = counterpart_amount
                write_off_balance = write_off_amount
                counterpart_amount = write_off_amount = 0.0
                currency_id = False
            else:
                # Multi-currencies.
                balance = payment.currency_id._convert(counterpart_amount, company_currency, payment.company_id, payment.payment_date)
                write_off_balance = payment.currency_id._convert(write_off_amount, company_currency, payment.company_id, payment.payment_date)
                currency_id = payment.currency_id.id

            # Manage custom currency on journal for liquidity line.
            if payment.journal_id.currency_id and payment.currency_id != payment.journal_id.currency_id:
                # Custom currency on journal.
                liquidity_line_currency_id = payment.journal_id.currency_id.id
                liquidity_amount = company_currency._convert(
                    balance, payment.journal_id.currency_id, payment.company_id, payment.payment_date)
            else:
                # Use the payment currency.
                liquidity_line_currency_id = currency_id
                liquidity_amount = counterpart_amount

            # Compute 'name' to be used in receivable/payable line.
            rec_pay_line_name = ''
            if payment.payment_type == 'transfer':
                rec_pay_line_name = payment.name
            else:
                if payment.partner_type == 'customer':
                    if payment.payment_type == 'inbound':
                        rec_pay_line_name += _("Customer Payment")
                    elif payment.payment_type == 'outbound':
                        rec_pay_line_name += _("Customer Credit Note")
                elif payment.partner_type == 'supplier':
                    if payment.payment_type == 'inbound':
                        rec_pay_line_name += _("Vendor Credit Note")
                    elif payment.payment_type == 'outbound':
                        rec_pay_line_name += _("Vendor Payment")
                if payment.invoice_ids:
                    rec_pay_line_name += ': %s' % ', '.join(payment.invoice_ids.mapped('name'))

            # Compute 'name' to be used in liquidity line.
            if payment.payment_type == 'transfer':
                liquidity_line_name = _('Transfer to %s') % payment.destination_journal_id.name
            else:
                liquidity_line_name = payment.name

            # ==== 'inbound' / 'outbound' ====

            move_vals = {
                'date': payment.payment_date,
                'ref': payment.communication,
                'lydo': payment.communication,
                'journal_id': payment.journal_id.id,
                'payment_id': payment.id,
                'currency_id': payment.journal_id.currency_id.id or payment.company_id.currency_id.id,
                # 'currency_id': currency_id,
                'partner_id': payment.partner_id.id,
                'line_ids': [
                    # Receivable / Payable / Transfer line.
                    (0, 0, {
                        'name': rec_pay_line_name,
                        'amount_currency': counterpart_amount + write_off_amount,
                        'currency_id': currency_id,
                        'debit': balance + write_off_balance > 0.0 and balance + write_off_balance or 0.0,
                        'credit': balance + write_off_balance < 0.0 and -balance - write_off_balance or 0.0,
                        'date_maturity': payment.payment_date,
                        'partner_id': payment.partner_id.id,
                        'account_id': payment.destination_account_id.id,
                        'payment_id': payment.id,
                    }),
                    # Liquidity line.
                    (0, 0, {
                        'name': liquidity_line_name,
                        'amount_currency': -liquidity_amount,
                        'currency_id': liquidity_line_currency_id,
                        'debit': balance < 0.0 and -balance or 0.0,
                        'credit': balance > 0.0 and balance or 0.0,
                        'date_maturity': payment.payment_date,
                        'partner_id': payment.partner_id.id,
                        'account_id': liquidity_line_account.id,
                        'payment_id': payment.id,
                    }),
                ],
            }
            if write_off_balance:
                # Write-off line.
                move_vals['line_ids'].append((0, 0, {
                    'name': payment.writeoff_label,
                    'amount_currency': -write_off_amount,
                    'currency_id': currency_id,
                    'debit': write_off_balance < 0.0 and -write_off_balance or 0.0,
                    'credit': write_off_balance > 0.0 and write_off_balance or 0.0,
                    'date_maturity': payment.payment_date,
                    'partner_id': payment.partner_id.id,
                    'account_id': payment.writeoff_account_id.id,
                    'payment_id': payment.id,
                }))

            if move_names:
                move_vals['name'] = move_names[0]

            all_move_vals.append(move_vals)

            # ==== 'transfer' ====
            if payment.payment_type == 'transfer':

                if payment.destination_journal_id.currency_id:
                    transfer_amount = payment.currency_id._convert(counterpart_amount, payment.destination_journal_id.currency_id, payment.company_id, payment.payment_date)
                else:
                    transfer_amount = 0.0

                transfer_move_vals = {
                    'date': payment.payment_date,
                    'ref': payment.communication,
                    'lydo': payment.communication,
                    'partner_id': payment.partner_id.id,
                    'journal_id': payment.destination_journal_id.id,
                    'line_ids': [
                        # Transfer debit line.
                        (0, 0, {
                            'name': payment.name,
                            'amount_currency': -counterpart_amount,
                            'currency_id': currency_id,
                            'debit': balance < 0.0 and -balance or 0.0,
                            'credit': balance > 0.0 and balance or 0.0,
                            'date_maturity': payment.payment_date,
                            'partner_id': payment.partner_id.id,
                            'account_id': payment.company_id.transfer_account_id.id,
                            'payment_id': payment.id,
                        }),
                        # Liquidity credit line.
                        (0, 0, {
                            'name': _('Transfer from %s') % payment.journal_id.name,
                            'amount_currency': transfer_amount,
                            'currency_id': payment.destination_journal_id.currency_id.id,
                            'debit': balance > 0.0 and balance or 0.0,
                            'credit': balance < 0.0 and -balance or 0.0,
                            'date_maturity': payment.payment_date,
                            'partner_id': payment.partner_id.id,
                            'account_id': payment.destination_journal_id.default_credit_account_id.id,
                            'payment_id': payment.id,
                        }),
                    ],
                }

                if move_names and len(move_names) == 2:
                    transfer_move_vals['name'] = move_names[1]

                all_move_vals.append(transfer_move_vals)
        return all_move_vals


    def write(self, vals):
        # check_state = False
        if vals.get('state') and vals.get('state') == 'posted':
            if self.payment_type == 'outpay':
                # Nếu là phiếu cũ: cập nhập write_date theo phiếu cũ
                write_date = self.write_date if self.is_old_payment else fields.datetime.today()

                if vals.get('state') == 'posted':
                    crm_sale_payment_service = [(5, 0, 0)] + [(0, 0, {
                        "account_payment_detail_id": service.id,
                        "amount_proceeds": (0 - service.prepayment_amount) if self.payment_type == 'outbound'
                        else service.prepayment_amount,
                        "currency_id": service.currency_id.id,
                        "product_type": 'service',
                        "product_category_id": service.crm_line_id.service_id.categ_id.id,
                        # "product_id": ,
                        "service_id": service.crm_line_id.service_id.id,
                        "department": service.crm_line_id.service_id.his_service_type,
                        # "kpi_point": service.crm_line_id.service_id.kpi_point,
                        "booking_id": self.crm_id.id,
                        "crm_line_id": service.crm_line_id.id,
                        "coupon_ids": [(6, 0, service.crm_line_id.prg_ids.ids)],
                        "account_payment_id": self.id,
                        "partner_id": self.partner_id.id,
                        "is_deposit": self.is_deposit,
                        "user_id": self.user.id,
                        "company_id": service.company_id.id,
                        "transaction_company_id": self.company_id.id,
                        "payment_type": self.payment_type,
                        "internal_payment_type": self.internal_payment_type,
                        "communication": self.communication,
                        "write_date": write_date
                        # "category_source_id": category_source_id,
                        # "utm_source_id": utm_source_id,
                    }) for service in self.service_ids.filtered(lambda x: x.prepayment_amount != 0)]

                    # products
                    crm_sale_payment_product = [(0, 0, {
                        "account_payment_product_detail_id": product.id,
                        "amount_proceeds": (0 - product.prepayment_amount) if self.payment_type == 'outbound'
                        else product.prepayment_amount,
                        "currency_id": product.currency_id.id,
                        "product_type": 'product',
                        "product_category_id": product.crm_line_product_id.product_id.categ_id.id,
                        # "product_id": ,
                        "product_id": product.crm_line_product_id.product_id.id,
                        "department": product.department_product,
                        # "kpi_point": product.crm_line_product_id.product_id.kpi_point,
                        "booking_id": self.crm_id.id,
                        "crm_line_product_id": product.crm_line_product_id.id,
                        "coupon_ids": [(6, 0, product.crm_line_product_id.prg_ids.ids)],
                        "account_payment_id": self.id,
                        "partner_id": self.partner_id.id,
                        "is_deposit": self.is_deposit,
                        "user_id": self.user.id,
                        "company_id": product.company_id.id,
                        "transaction_company_id": self.company_id.id,
                        "payment_type": self.payment_type,
                        "internal_payment_type": self.internal_payment_type,
                        "communication": self.communication,
                        "write_date": write_date
                        # "category_source_id": category_source_id,
                        # "utm_source_id": utm_source_id,
                    }) for product in self.product_ids.filtered(lambda x: x.prepayment_amount != 0)]
                    vals['crm_sale_payment_ids'] = crm_sale_payment_service + crm_sale_payment_product

                    # Update total received in booking
                    # if self.is_old_payment is False:
                    self.service_ids.update_total_received_crm_line(self.payment_type)
                    self.product_ids.update_total_received_crm_line_product(self.payment_type)
            else:
                # Check: need to input before confirm.
                prepayment_amount_service = sum(i.prepayment_amount for i in self.service_ids)
                prepayment_amount_product = sum(i.prepayment_amount for i in self.product_ids)
                if (vals.get('partner_type', "supplier") != "supplier" or (not vals.get('partner_type',
                                                                                        False) and self.partner_type not in ["supplier", "employee"])) and (self.crm_id and prepayment_amount_service + prepayment_amount_product == 0):
                    raise ValidationError(_('Bạn phải điền số tiền giao dịch.'))
                    # print('Bạn phải điền số tiền giao dịch.')
                else:
                    # Nếu là phiếu cũ: cập nhập write_date theo phiếu cũ
                    write_date = self.write_date if self.is_old_payment else fields.datetime.today()

                    if vals.get('state') == 'posted':
                        crm_sale_payment_service = [(5, 0, 0)] + [(0, 0, {
                            "account_payment_detail_id": service.id,
                            "amount_proceeds": (0 - service.prepayment_amount) if self.payment_type == 'outbound'
                            else service.prepayment_amount,
                            "currency_id": service.currency_id.id,
                            "product_type": 'service',
                            "product_category_id": service.crm_line_id.service_id.categ_id.id,
                            # "product_id": ,
                            "service_id": service.crm_line_id.service_id.id,
                            "department": service.crm_line_id.service_id.his_service_type,
                            # "kpi_point": service.crm_line_id.service_id.kpi_point,
                            "booking_id": self.crm_id.id,
                            "crm_line_id": service.crm_line_id.id,
                            "coupon_ids": [(6, 0, service.crm_line_id.prg_ids.ids)],
                            "account_payment_id": self.id,
                            "partner_id": self.partner_id.id,
                            "is_deposit": self.is_deposit,
                            "user_id": self.user.id,
                            "company_id": service.company_id.id,
                            "transaction_company_id": self.company_id.id,
                            "payment_type": self.payment_type,
                            "internal_payment_type": self.internal_payment_type,
                            "communication": self.communication,
                            "write_date": write_date
                            # "category_source_id": category_source_id,
                            # "utm_source_id": utm_source_id,
                        }) for service in self.service_ids.filtered(lambda x: x.prepayment_amount != 0)]

                        # products
                        crm_sale_payment_product = [(0, 0, {
                            "account_payment_product_detail_id": product.id,
                            "amount_proceeds": (0 - product.prepayment_amount) if self.payment_type == 'outbound'
                            else product.prepayment_amount,
                            "currency_id": product.currency_id.id,
                            "product_type": 'product',
                            "product_category_id": product.crm_line_product_id.product_id.categ_id.id,
                            # "product_id": ,
                            "product_id": product.crm_line_product_id.product_id.id,
                            "department": product.department_product,
                            # "kpi_point": product.crm_line_product_id.product_id.kpi_point,
                            "booking_id": self.crm_id.id,
                            "crm_line_product_id": product.crm_line_product_id.id,
                            "coupon_ids": [(6, 0, product.crm_line_product_id.prg_ids.ids)],
                            "account_payment_id": self.id,
                            "partner_id": self.partner_id.id,
                            "is_deposit": self.is_deposit,
                            "user_id": self.user.id,
                            "company_id": product.company_id.id,
                            "transaction_company_id": self.company_id.id,
                            "payment_type": self.payment_type,
                            "internal_payment_type": self.internal_payment_type,
                            "communication": self.communication,
                            "write_date": write_date
                            # "category_source_id": category_source_id,
                            # "utm_source_id": utm_source_id,
                        }) for product in self.product_ids.filtered(lambda x: x.prepayment_amount != 0)]
                        vals['crm_sale_payment_ids'] = crm_sale_payment_service + crm_sale_payment_product

                        # Update total received in booking
                        # if self.is_old_payment is False:
                        self.service_ids.update_total_received_crm_line(self.payment_type)
                        self.product_ids.update_total_received_crm_line_product(self.payment_type)

        res = super(AccountPayment, self).write(vals)
        return res

    # lấy danh sách các service/product trong quá khứ
    def get_line_account_payment_history(self, crm_id):
        def is_exist_in_array(input_list, check_item):
            index = 0
            for item in input_list:
                if check_item[0] == item[0] and check_item[1] == item[1]:
                    return index
                index += 1
            return -1

        service_company_list = []
        product_company_list = []

        # mặc định lấy từ booking.
        if crm_id.crm_line_ids:
            service_company_list = list(
                set([(sub['id'], sub['company_id']['id'], sub['remaining_amount']) for sub in crm_id.crm_line_ids]))
        if crm_id.crm_line_product_ids:
            product_company_list = list(set([(sub['id'], sub['company_id']['id'], sub['remaining_amount']) for sub in
                                             crm_id.crm_line_product_ids]))

        # check các service/product đã được thanh toán, (share booking hoặc điều chuyển phải check thêm ở đây)
        sale_payment_list = self.env['crm.sale.payment'].search_read([('booking_id.id', '=', crm_id.id)])

        for pay in sale_payment_list:
            if pay['crm_line_id']:
                index = is_exist_in_array(service_company_list, (pay['crm_line_id'][0], pay['company_id'][0]))
                if index >= 0:
                    if service_company_list[index][2] > pay['remaining_amount']:
                        list(service_company_list[index])[2] = pay['remaining_amount']
                else:
                    service_company_list += [(pay['crm_line_id'][0], pay['company_id'][0], pay['remaining_amount'])]

        for pay in sale_payment_list:
            if pay['crm_line_product_id']:
                index = is_exist_in_array(product_company_list, (pay['crm_line_product_id'][0], pay['company_id'][0]))
                if index >= 0:
                    if product_company_list[index][2] > pay['remaining_amount']:
                        list(product_company_list[index])[2] = pay['remaining_amount']
                else:
                    product_company_list += [
                        (pay['crm_line_product_id'][0], pay['company_id'][0], pay['remaining_amount'])]

        # service_company_list += list(set([(pay['crm_line_id'][0], pay['company_id'][0], pay['remaining_amount']) for pay in sale_payment_list if pay['crm_line_id']]))
        # product_company_list += list(set([(pay['crm_line_product_id'][0], pay['company_id'][0], pay['remaining_amount']) for pay in sale_payment_list if pay['crm_line_product_id']]))

        return list(set(service_company_list)), list(set(product_company_list))

    def _create_account_payment_line(self, crm_id):
        detail_line, product_detail_line = [(5, 0, 0)], [(5, 0, 0)]
        service_list, product_list = self.get_line_account_payment_history(crm_id)
        # tạo line mới
        for line in service_list:
            detail_line.append((0, 0, {'crm_line_id': line[0],
                                       'company_id': line[1],
                                       'allow_unlink': False,
                                       'consultants_1': crm_id.crm_line_ids.filtered(
                                           lambda x: x.id == line[0]).consultants_1.id
                                       }))
        for line_product in product_list:
            product_detail_line.append((0, 0, {'crm_line_product_id': line_product[0],
                                               'company_id': line_product[1],
                                               'allow_unlink': False,
                                               'consultants_1': crm_id.crm_line_product_ids.filtered(
                                                   lambda x: x.id == line_product[0]).consultants_1.id
                                               }))
        return detail_line, product_detail_line

    def action_create_line(self):
        self.ensure_one()
        return {
            'name': _('Tạo Dòng dịch vụ'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('crm_sale_payment.crm_new_line').id,
            'res_model': 'crm.line',
            'context': {
                'account_payment_id': self.id,
                'default_crm_id': self.crm_id.id,
                'default_company_id': self.crm_id.company_id.id,
                'default_price_list_id': self.crm_id.price_list_id.id,
                'default_source_extend_id': self.crm_id.source_id.id,
                'default_status_cus_come': 'come',
                'default_stage': 'new',
                'default_is_new': True,
                'default_quantity': 1,
                'default_number_used': 1,
            },
            'target': 'new',
        }

    def update_payment_list(self):
        self.ensure_one()
        self.is_update_payment_list = True
        self.onchange_crm()

    # Cập nhật các bảng sale.payment/account.payment.detail/product.detail ở phiếu thanh toán cũ
    def update_old_payment(self):
        # self.write({
        #     'state': 'posted',
        # })
        self.is_update_payment_list = False
        if self.service_ids:
            for line in self.service_ids:
                if line.prepayment_amount != 0:
                    spm = self.env['crm.sale.payment'].sudo().search(
                        [('booking_id', '=', self.crm_id.id), ('account_payment_id', '=', self.id),
                         ('crm_line_id', '=', line.crm_line_id.id)])
                    if spm:
                        spm.amount_proceeds = (
                                0 - line.prepayment_amount) if self.payment_type == 'outbound' else line.prepayment_amount
                    else:
                        self.env['crm.sale.payment'].create({
                            "account_payment_detail_id": line.id,
                            "amount_proceeds": (0 - line.prepayment_amount) if line.account_payment_id.payment_type == 'outbound'
                            else line.prepayment_amount,
                            "currency_id": line.currency_id.id,
                            "product_type": 'service',
                            "product_category_id": line.crm_line_id.service_id.categ_id.id,
                            "service_id": line.crm_line_id.service_id.id,
                            "department": line.crm_line_id.service_id.his_service_type,
                            "booking_id": self.crm_id.id,
                            "crm_line_id": line.crm_line_id.id,
                            "coupon_ids": [(6, 0, line.crm_line_id.prg_ids.ids)],
                            "account_payment_id": line.account_payment_id.id,
                            "partner_id": line.account_payment_id.partner_id.id,
                            "is_deposit": line.account_payment_id.is_deposit,
                            "user_id": line.account_payment_id.user.id,
                            "company_id": line.company_id.id,
                            "transaction_company_id": line.account_payment_id.company_id.id,
                            "payment_type": line.account_payment_id.payment_type,
                            "internal_payment_type": line.account_payment_id.internal_payment_type,
                            "communication": line.account_payment_id.communication
                        })
        if self.product_ids:
            for line in self.product_ids:
                if line.prepayment_amount != 0:
                    spm = self.env['crm.sale.payment'].sudo().search(
                        [('booking_id', '=', self.crm_id.id), ('account_payment_id', '=', self.id),
                         ('crm_line_product_id', '=', line.crm_line_product_id.id)])
                    if spm:
                        spm.amount_proceeds = (
                                    0 - line.prepayment_amount) if self.payment_type == 'outbound' else line.prepayment_amount
                    else:
                        self.env['crm.sale.payment'].create({
                            "account_payment_product_detail_id": line.id,
                            "amount_proceeds": (0 - line.prepayment_amount) if line.account_payment_id.payment_type == 'outbound'
                            else line.prepayment_amount,
                            "currency_id": line.currency_id.id,
                            "product_type": 'product',
                            "product_category_id": line.crm_line_product_id.product_id.categ_id.id,
                            # "product_id": ,
                            "product_id": line.crm_line_product_id.product_id.id,
                            "department": line.department_product,
                            # "kpi_point": product.crm_line_product_id.product_id.kpi_point,
                            "booking_id": line.account_payment_id.crm_id.id,
                            "crm_line_product_id": line.crm_line_product_id.id,
                            "coupon_ids": [(6, 0, line.crm_line_product_id.prg_ids.ids)],
                            "account_payment_id": line.account_payment_id.id,
                            "partner_id": line.account_payment_id.partner_id.id,
                            "is_deposit": line.account_payment_id.is_deposit,
                            "user_id": line.account_payment_id.user.id,
                            "company_id": line.company_id.id,
                            "transaction_company_id": line.account_payment_id.company_id.id,
                            "payment_type": line.account_payment_id.payment_type,
                            "internal_payment_type": line.account_payment_id.internal_payment_type,
                            "communication": line.account_payment_id.communication,
                        })
        self.crm_id.recompute_remaining_amount()

    def edit(self):
        self.write({
            'state': 'draft',
        })

    def onchange_crm_sci(self):
        if self.crm_id and self.crm_id.crm_line_ids:
            lines = self.crm_id.crm_line_ids
            for line in lines:
                spm = self.env['crm.account.payment.detail'].search([('account_payment_id', '=', self.id), ('crm_line_id', '=', line.id)])
                if not spm:
                    self.env['crm.account.payment.detail'].create({
                        'account_payment_id': self.id,
                        'crm_line_id': line.id,
                        'company_id': line.company_id.id,
                        'allow_unlink': False,
                        'consultants_1': line.consultants_1.id
                    })
            line_products = self.crm_id.crm_line_product_ids
            for line in line_products:
                spm = self.env['crm.account.payment.product.detail'].search(
                    [('account_payment_id', '=', self.id), ('crm_line_product_id', '=', line.id)])
                if not spm:
                    self.env['crm.account.payment.product.detail'].create({
                        'account_payment_id': self.id,
                        'crm_line_product_id': line.id,
                        'company_id': line.company_id.id,
                        'allow_unlink': False,
                        'consultants_1': line.consultants_1.id
                    })

    def delete_payment_list(self):
        if self.service_ids:
            # self.service_ids.sudo().unlink()
            for service in self.service_ids:
                service.prepayment_amount = 0
        if self.product_ids:
            # self.product_ids.sudo().unlink()
            for product in self.product_ids:
                product.prepayment_amount = 0
        self.is_update_payment_list = True
        self.onchange_crm_sci()
        # transfer_list = self.env['crm.transfer.payment'].sudo().search([('crm_id', '=', self.id)])
        # for rec in transfer_list:
        #     rec.state = 'draft'
        #     rec.sudo().unlink()
        # self.env['crm.sale.payment'].sudo().search(
        #     [('booking_id', '=', self.crm_id.id), ('account_payment_id', '=', self.id)]).sudo().unlink()
        spm = self.env['crm.sale.payment'].sudo().search(
            [('booking_id', '=', self.crm_id.id), ('account_payment_id', '=', self.id)])
        for record in spm:
            record.amount_proceeds = 0
        self.crm_id.compute_remaining_amount()


class CRMAccountPaymentDetail(models.Model):
    _name = 'crm.account.payment.detail'
    _description = 'CRM account payment detail'

    account_payment_id = fields.Many2one('account.payment', string="Phiếu thu tiền", ondelete='cascade')
    state = fields.Selection(related='account_payment_id.state', readonly=True)
    payment_type = fields.Selection(related='account_payment_id.payment_type', readonly=True)

    payment_list_id = fields.Many2one('payment.list', string="Bảng kê thanh toán", ondelete='cascade')
    crm_line_id = fields.Many2one('crm.line', string='Dịch vụ', readonly=True)
    currency_id = fields.Many2one('res.currency', string='Tiền tệ', tracking=True,
                                  related='crm_line_id.currency_id')
    unit_price = fields.Monetary(string="Đơn giá", related='crm_line_id.unit_price',
                                 readonly=True)
    quantity = fields.Integer(string="Số lượng", related='crm_line_id.quantity', readonly=True, default=1)
    uom_price = fields.Float(string="Đơn vị xử lý", related='crm_line_id.uom_price', readonly=True, default=1.0)
    number_used = fields.Integer(string="Đã sử dụng", related='crm_line_id.number_used', readonly=True)
    discount_percent = fields.Float(string="Giảm giá", related='crm_line_id.discount_percent', readonly=True)
    stage = fields.Selection(string="Trạng thái", related='crm_line_id.stage', readonly=True)
    discount_cash = fields.Monetary(string="Giảm giá tiền mặt",
                                    related='crm_line_id.discount_cash', readonly=True)
    consultants_1 = fields.Many2one('res.users', string='Tư vấn viên 1', default=lambda self: self._uid)
    sale_to = fields.Monetary(string="Giảm còn", related='crm_line_id.sale_to', readonly=True)
    other_discount = fields.Monetary(string="Giảm khác",
                                     related='crm_line_id.other_discount', readonly=True)
    total_before_discount = fields.Monetary(string="Tiền trước giảm",
                                            related='crm_line_id.total_before_discount', readonly=True)
    total = fields.Monetary(string="Tiền sau giảm", related='crm_line_id.total', readonly=True)
    total_received = fields.Monetary(string="Tiền đã thu", currency_field="currency_id",
                                     compute="_calculate_total_received", readonly=True, store=True)
    remaining_amount = fields.Monetary(string="Tiền chưa sử dụng", currency_field="currency_id",
                                       compute="_calculate_remaining_amount", readonly=True, store=True)
    prepayment_amount = fields.Monetary(string="Tiền giao dịch", default=0)
    is_another_cost = fields.Boolean(string="Phụ thu", compute='_compute_is_another_cost', default=False)
    allow_unlink = fields.Boolean(string="Cho phép xoá?", default=True)

    # @api.depends('account_payment_id')
    # def _compute_consultants_1(self):
    #     for rec in self:
    #         rec.consultants_1 = rec.crm_line_id.consultants_1

    @api.depends('crm_line_id')
    def _compute_is_another_cost(self):
        for rec in self:
            rec.is_another_cost = False
            if rec.crm_line_id.service_id.service_category.is_another_cost:
                rec.is_another_cost = True

    @api.depends('account_payment_id')
    def _compute_domain_company_id(self):
        company2_ids = []
        if self.env.context.get('default_parent_id'):
            parent_obj = self.env['account.payment'].browse(self.env.context.get('default_parent_id'))
            if parent_obj:
                company2_ids = parent_obj.crm_id.company2_id.ids
        elif self.account_payment_id:
            company2_ids = self.account_payment_id.crm_id.company2_id.ids
        company2_ids.append(self.account_payment_id.crm_id.company_id.id)
        self.domain_company_ids = company2_ids

    company_id = fields.Many2one('res.company', string="Công ty ghi nhận doanh số")
    domain_company_ids = fields.Many2many('res.company', compute="_compute_domain_company_id",
                                          default=lambda self: [self.env.company.id])

    # số tiền đã thu + số tiền đã hoàn cho dịch vụ này.
    @api.depends('account_payment_id', 'crm_line_id', 'payment_list_id')
    def _calculate_total_received(self):
        for rec in self:
            if not rec.prepayment_amount:
                # check payment list or account payment
                booking_id = rec.account_payment_id.crm_id.id if rec.account_payment_id \
                    else rec.payment_list_id.crm_id.id
                # [SCI1359] Phiếu thanh toán: Trường Tiền đã thu và Tiền chưa sử dụng không cập nhật như trong Booking
                service_payment_list = self.env['crm.sale.payment'].search([
                    ('booking_id', '=', booking_id),
                    ('crm_line_id', '=', rec.crm_line_id.id),
                    ('company_id', '=', rec.company_id.id),
                ])
                rec.total_received = sum(i.amount_proceeds for i in service_payment_list)

    # số tiền chưa sử dụng = số tiền đã thu - số tiền đã thực hiện trong sale.order
    @api.depends('total_received')
    def _calculate_remaining_amount(self):
        for rec in self:
            rec.remaining_amount = rec.total_received
            if rec.total_received > 0:
                if rec.crm_line_id.id and rec.company_id:
                    order_line_ids = self.env['sale.order'].search(
                        [('booking_id', '=', rec.account_payment_id.crm_id.id),
                         ('state', 'in', ['sale', 'done'])]) \
                        .mapped('order_line').filtered(lambda x: x.crm_line_id.id == rec.crm_line_id.id
                                                                 and x.company_id.id == rec.company_id.id)
                    if order_line_ids:
                        rec.remaining_amount = rec.total_received - sum(i.price_subtotal for i in order_line_ids)

    def write(self, vals):
        res = super(CRMAccountPaymentDetail, self).write(vals)
        return res

    def create(self, vals):
        res = super(CRMAccountPaymentDetail, self).create(vals)
        return res

    # def unlink(self):
    #     for rec in self:
    #         if rec.account_payment_id.state != "draft" and not rec.account_payment_id.is_old_payment:
    #             raise UserError(_('Bạn chỉ có thể xoá dịch vụ ở trạng thái nháp'))
    #     return super(CRMAccountPaymentDetail, self).unlink()

    def unlink(self):
        """
        Hải SCI : Khi xóa 1 line phân bổ (dịch vụ) sẽ xóa 1 bản ghi bên sale_payment(Danh sách thanh toán) (nếu có)
        """
        for rec in self:
            sale_payment = self.env['crm.sale.payment'].search([('account_payment_detail_id', '=', rec.id)])
            if sale_payment:
                sale_payment.sudo().unlink()
        return super(CRMAccountPaymentDetail, self).unlink()

    def update_total_received_crm_line(self, payment_type):
        for rec in self:
            if rec.prepayment_amount:
                if payment_type == 'outbound':
                    # rec.write({'total_received': rec.crm_line_id.total_received - rec.prepayment_amount})
                    rec.crm_line_id.write({'total_received': rec.crm_line_id.total_received - rec.prepayment_amount})
                else:
                    # rec.write({'total_received': rec.crm_line_id.total_received + rec.prepayment_amount})
                    rec.crm_line_id.write({'total_received': rec.crm_line_id.total_received + rec.prepayment_amount})

    # Share booking: creates new line with same service
    def share(self):
        for rec in self:
            rec.account_payment_id.write({
                'service_ids': [(0, 0, {'crm_line_id': rec.crm_line_id.id,
                                        'company_id': rec.account_payment_id.crm_id.company2_id[0].id})]
            })


class CRMAccountPaymentProductDetail(models.Model):
    _name = 'crm.account.payment.product.detail'
    _description = 'CRM account payment product detail'

    account_payment_id = fields.Many2one('account.payment', string="Phiếu thu tiền", ondelete='cascade')
    state = fields.Selection(related='account_payment_id.state', readonly=True)
    payment_type = fields.Selection(related='account_payment_id.payment_type', readonly=True)

    payment_list_id = fields.Many2one('payment.list', string="Bảng kê thanh toán", ondelete='cascade')
    crm_line_product_id = fields.Many2one('crm.line.product', string='Sản phẩm', readonly=True)
    currency_id = fields.Many2one('res.currency', string='Tiền tệ', tracking=True,
                                  related='account_payment_id.currency_id')

    unit_price = fields.Float(string="Đơn giá", related='crm_line_product_id.price_unit',
                              readonly=True)
    quantity = fields.Float(string="Số lượng", related='crm_line_product_id.product_uom_qty', readonly=True,
                            default=1.0)
    discount_percent = fields.Float(string="Giảm giá", related='crm_line_product_id.discount_percent', readonly=True)
    stage = fields.Selection(string="Trạng thái", related='crm_line_product_id.stage_line_product', readonly=True)
    discount_cash = fields.Float(string="Giảm giá tiền mặt",
                                 related='crm_line_product_id.discount_cash', readonly=True)
    consultants_1 = fields.Many2one('res.users', string='Tư vấn viên 1',
                                    related='crm_line_product_id.consultants_1')
    sale_to = fields.Float(string="Giảm còn", related='crm_line_product_id.sale_to', readonly=True)
    other_discount = fields.Float(string="Giảm khác",
                                  related='crm_line_product_id.discount_other', readonly=True)
    total_before_discount = fields.Float(string="Tiền trước giảm",
                                         related='crm_line_product_id.total_before_discount', readonly=True)
    total = fields.Float(string="Tiền sau giảm", related='crm_line_product_id.total', readonly=True)
    total_received = fields.Monetary(string="Tiền đã thu", currency_field="currency_id",
                                     compute="_calculate_total_received", readonly=True, store=True)
    remaining_amount = fields.Monetary(string="Tiền chưa sử dụng", currency_field="currency_id",
                                       compute="_calculate_remaining_amount", readonly=True, store=True)
    prepayment_amount = fields.Monetary(string="Tiền giao dịch", default=0)
    allow_unlink = fields.Boolean(string="Cho phép xoá?", default=True)
    department_product = fields.Selection(SERVICE_HIS_TYPE, string='Phòng ban')

    @api.depends('account_payment_id')
    def _compute_domain_company_id(self):
        company2_ids = []
        if self.env.context.get('default_parent_id'):
            parent_obj = self.env['account.payment'].browse(self.env.context.get('default_parent_id'))
            if parent_obj:
                company2_ids = parent_obj.crm_id.company2_id.ids
        elif self.account_payment_id:
            company2_ids = self.account_payment_id.crm_id.company2_id.ids
        company2_ids.append(self.account_payment_id.crm_id.company_id.id)
        self.domain_company_ids = company2_ids

    company_id = fields.Many2one('res.company', string="Công ty ghi nhận doanh số",
                                 default=lambda self: self.env.company)
    domain_company_ids = fields.Many2many('res.company', compute="_compute_domain_company_id",
                                          default=lambda self: [self.env.company.id])

    # số tiền đã thu + số tiền đã hoàn cho sản phầm này.
    @api.depends('account_payment_id', 'crm_line_product_id')
    def _calculate_total_received(self):
        for rec in self:
            if not rec.prepayment_amount:
                # check payment list or account payment
                booking_id = rec.account_payment_id.crm_id.id if rec.account_payment_id \
                    else rec.payment_list_id.crm_id.id
                service_payment_list = self.env['crm.sale.payment'].search([
                    ('booking_id', '=', booking_id),
                    ('crm_line_product_id', '=', rec.crm_line_product_id.id),
                    ('company_id', '=', rec.company_id.id)
                ])
                rec.total_received = sum(i.amount_proceeds for i in service_payment_list)

    # số tiền chưa sử dụng = số tiền đã thu - số tiền đã thực hiện trong sale.order
    @api.depends('total_received')
    def _calculate_remaining_amount(self):
        for rec in self:
            rec.remaining_amount = rec.total_received
            if rec.total_received > 0:
                if rec.crm_line_product_id.id and rec.company_id:
                    order_line_ids = self.env['sale.order'].search(
                        [('booking_id', '=', rec.account_payment_id.crm_id.id),
                         ('state', 'in', ['sale', 'done'])]) \
                        .mapped('order_line').filtered(lambda x: x.line_product.id == rec.crm_line_product_id.id
                                                                 and x.company_id.id == rec.company_id.id)
                    if order_line_ids:
                        # rec.remaining_amount = rec.total_received - sum(i.price_subtotal for i in order_line_ids)

                        # Tiền chưa sử dụng = Tiền đã thu - đã giao(qty_delivered) * (1 - chiết khâu) * đơn giá - đã giao * (đơn giá - giảm giá tiền mặt / số lượng)
                        # - đã giao * giảm còn / số lượng - đã giao * giảm khác / số lượng(các trường này lấy ở SO khi SO ở trạng sale / done)
                        # rec.remaining_amount = rec.total_received - sum(
                        #     i.qty_delivered * (1 - i.discount)*i.price_unit - i.qty_delivered*(i.price_unit - i.discount_cash/i.product_uom_qty)
                        #     - i.qty_delivered*i.sale_to/i.product_uom_qty - i.qty_delivered*i.other_discount/i.product_uom_qty
                        #     for i in order_line_ids)

                        # Nếu trường giảm còn trong SO có dữ liệu.
                        order_line_sale_to = order_line_ids.filtered(lambda x: x.sale_to > 0)
                        amount_sale_to, amount_not_sale_to = 0, 0
                        if order_line_sale_to:
                            # Tiền chưa sử dụng = Tiền đã thu - đã giao * (giảm còn / số lượng - chiết khấu * đơn giá - giảm giá tiền mặt / số lượng - giảm khác / số lượng)
                            amount_sale_to = sum(
                                i.qty_delivered * (
                                        i.sale_to / i.product_uom_qty - i.discount * i.price_unit / 100 - i.discount_cash / i.product_uom_qty - i.other_discount / i.product_uom_qty)
                                for i in order_line_sale_to)
                        # Nếu trường giảm còn trong SO không có dữ liệu.
                        order_line_not_sale_to = order_line_ids.filtered(lambda x: x.sale_to == 0)
                        if order_line_not_sale_to:
                            # Tiền chưa sử dụng = Tiền đã thu - đã giao * (đơn giá - giảm giá tiền mặt/số lượng - giảm khác/số lượng - đơn giá*chiết khấu)
                            amount_not_sale_to = sum(
                                i.qty_delivered * (
                                        i.price_unit - i.discount_cash / i.product_uom_qty - i.other_discount / i.product_uom_qty - i.price_unit * i.discount / 100)
                                for i in order_line_ids.filtered(lambda x: x.sale_to == 0))
                        # Tính tiền chưa sử dụng.
                        rec.remaining_amount = rec.total_received - amount_sale_to - amount_not_sale_to

    def update_total_received_crm_line_product(self, payment_type):
        for rec in self:
            if rec.prepayment_amount:
                if payment_type == 'outbound':
                    # rec.write({'total_received': rec.crm_line_product_id.total_received - rec.prepayment_amount})
                    rec.crm_line_product_id.write(
                        {
                            'total_received': rec.crm_line_product_id.total_received - rec.prepayment_amount,
                            'department': rec.department_product
                        })
                else:
                    # rec.write({'total_received': rec.crm_line_product_id.total_received + rec.prepayment_amount})
                    rec.crm_line_product_id.write(
                        {'total_received': rec.crm_line_product_id.total_received + rec.prepayment_amount,
                         'department': rec.department_product
                         })

    # Share booking: creates new line with same product
    def share(self):
        for rec in self:
            rec.account_payment_id.write({
                'product_ids': [(0, 0, {'crm_line_product_id': rec.crm_line_product_id.id})]
            })

    def write(self, vals):
        # cap nhat du lieu phong ban trong crm_line_product va crm_sale_payment
        if vals.get('department_product') and self.state == 'posted':
            crm_sale_pay = self.env['crm.sale.payment'].search([('account_payment_product_detail_id', '=', self.id)])
            self.crm_line_product_id.department = vals.get('department_product')
            if crm_sale_pay:
                crm_sale_pay.department = vals.get('department_product')

        res = super(CRMAccountPaymentProductDetail, self).write(vals)
        return res

    # def unlink(self):
    #     for rec in self:
    #         if rec.account_payment_id.state != "draft":
    #             raise UserError(_('Bạn chỉ có thể xoá sản phẩm ở trạng thái nháp'))
    #     return super(CRMAccountPaymentProductDetail, self).unlink()

    def unlink(self):
        """
        Hải SCI : Khi xóa 1 line phân bổ (sản phẩm) sẽ xóa 1 bản ghi bên sale_payment(Danh sách thanh toán) (nếu có)
        """
        for rec in self:
            sale_payment = self.env['crm.sale.payment'].search([('account_payment_product_detail_id', '=', rec.id)])
            if sale_payment:
                sale_payment.sudo().unlink()
        return super(CRMAccountPaymentProductDetail, self).unlink()
