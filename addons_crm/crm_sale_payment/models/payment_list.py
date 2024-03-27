from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PaymentList(models.Model):
    _inherit = 'payment.list'

    service_ids = fields.One2many('crm.account.payment.detail', 'payment_list_id', string="Account payment detail")
    product_ids = fields.One2many('crm.account.payment.product.detail', 'payment_list_id',
                                  string="Account payment product detail")
    check_auto_input_money = fields.Boolean(string='Tự động điền thông tin số tiền phải nộp', default=False)
    check_auto_input_money_product = fields.Boolean(string='Tự động điền thông tin số tiền phải nộp', default=False)
    check_manual_allocation = fields.Boolean(string='Phân bổ thủ công', default=True)

    # @api.onchange('check_manual_allocation')
    # def _onchange_check_auto_input_money(self):
    #     for rec in self.service_ids:
    #         rec.prepayment_amount = (rec.total_before_discount - rec.total_received) \
    #             if self.check_auto_input_money else 0

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

    @api.onchange('crm_id')
    def onchange_crm(self):
        res = self._create_account_payment_line(self.crm_id, self.id)
        self.write({
            'service_ids': res[0],
            'product_ids': res[1]
        })
        # print('CREATED : ', self)

    # tổng số tiền phân bổ bằng tổng số tiền ở bảng kê thanh toán.
    @api.constrains('state', 'product_ids', 'service_ids')
    def amount_constrains(self):
        for rec in self:
            if rec.state != 'draft' and not rec.check_manual_allocation:
                prepayment_amount_service = sum(i.prepayment_amount for i in rec.service_ids)
                prepayment_amount_product = sum(i.prepayment_amount for i in rec.product_ids)
                if prepayment_amount_service + prepayment_amount_product != 0:
                    if rec.amount_subtotal != prepayment_amount_service + prepayment_amount_product:
                        raise ValidationError(_('Tổng số tiền phải nộp phải bằng tổng số tiền bảng kê.'))

    @api.model
    def create(self, vals):
        res = super(PaymentList, self).create(vals)
        # print('CREATED : ', res)
        return res

    def write(self, vals):
        if self and vals.get('state') == 'waiting':
            if not self.check_manual_allocation:
                prepayment_amount_service = sum(i.prepayment_amount for i in self.service_ids)
                prepayment_amount_product = sum(i.prepayment_amount for i in self.product_ids)
                if prepayment_amount_service + prepayment_amount_product == 0:
                    raise ValidationError(_('Bạn phải điền số tiền phải nộp.'))

            # Update: the services and the products each item in payment_ids
            for pay in self.payment_ids:
                _service_ids = [(5, 0, 0)] + [(0, 0, {
                    'crm_line_id': line.crm_line_id.id,
                    'company_id': line.crm_line_id.company_id.id,
                    'prepayment_amount': round(line.prepayment_amount * pay.amount_vnd / self.amount_subtotal),
                    'total_received': line.total_received
                }) for line in self.service_ids]

                _product_ids = [(5, 0, 0)] + [(0, 0, {
                    'crm_line_product_id': line_product.crm_line_product_id.id,
                    'company_id': line_product.crm_line_product_id.company_id.id,
                    'prepayment_amount': round(line_product.prepayment_amount * pay.amount_vnd / self.amount_subtotal),
                    'total_received': line_product.total_received
                }) for line_product in self.product_ids]

                pay.write({
                    'service_ids': _service_ids,
                    'product_ids': _product_ids
                })

        res = super(PaymentList, self).write(vals)
        # print('UPDATE : ', vals)
        return res

    # def action_edit_form(self):
    #     self.ensure_one()
    #     return {
    #         'name': 'Mở: Phiếu thanh toán',
    #         'type': 'ir.actions.act_window',
    #         'view_type': 'form',
    #         'view_mode': 'form',
    #         'view_id': self.env.ref('account.view_account_payment_form').id,
    #         'res_model': 'account.payment',
    #         'context': {},
    #         'target': 'new',
    #     }

    def _create_account_payment_line(self, crm_id, payment_list_id):
        detail_line, product_detail_line = [(5, 0, 0)], [(5, 0, 0)]
        service_list, product_list = self.env['account.payment'].get_line_account_payment_history(crm_id)
        # tạo line mới
        for line in service_list:
            detail_line.append((0, 0, {'crm_line_id': line[0],
                                       'company_id': line[1],
                                       'payment_list_id': payment_list_id}))
        for line_product in product_list:
            product_detail_line.append((0, 0, {'crm_line_product_id': line_product[0],
                                               'company_id': line_product[1],
                                               'payment_list_id': payment_list_id}))
        return detail_line, product_detail_line

