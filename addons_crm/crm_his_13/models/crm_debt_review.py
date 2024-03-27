import datetime
from odoo import fields, api, models
from odoo.exceptions import ValidationError


class DebtReview(models.Model):
    _inherit = 'crm.debt.review'
    walkin_id = fields.Many2one('sh.medical.appointment.register.walkin', string='Phiếu khám')

    @api.onchange('booking_id')
    def onchange_booking_id(self):
        self.walkin_id = False
        self.order_id = False
        if self.booking_id:
            return {
                'domain': {'walkin_id': [('id', 'in', self.env['sh.medical.appointment.register.walkin'].sudo().search(
                    [('booking_id', '=', self.booking_id.id), ('state', 'not in', ['Complete', 'Cancelled'])]).ids)]}}

    @api.onchange('walkin_id', 'partner_id', 'booking_id')
    def onchange_walkin_id(self):
        self.order_id = False
        if self.walkin_id:
            self.order_id = self.walkin_id.sale_order_id
        else:
            domain = [('state', '=', 'draft')]
            if self.partner_id:
                domain += [('partner_id', '=', self.partner_id.id)]
            if self.booking_id:
                domain += [('booking_id', '=', self.booking_id.id)]
            return {'domain': {'order_id': [
                ('id', 'in', self.env['sale.order'].search(domain).ids)]}}

    def set_approve(self):
        res = super(DebtReview, self).set_approve()
        if self.booking_id and self.order_id:
            walkin = self.env['sh.medical.appointment.register.walkin']
            if self.walkin_id:
                walkin += self.walkin_id
            else:
                walkin += self.env['sh.medical.appointment.register.walkin'].sudo().search(
                    [('sale_order_id', '=', self.order_id.id), ('booking_id', '=', self.booking_id.id)],
                    order='id desc', limit=1)
            if self.amount_total == self.amount_owed:  # Nếu nợ 100% số tiền cần duyệt thì chuyển trạng thái PK sang Đang thực hiện
                # walkin = self.env['sh.medical.appointment.register.walkin'].sudo().search(
                #         [('sale_order_id', '=', self.order_id.id), ('booking_id', '=', self.booking_id.id)],
                #         order='id desc', limit=1)
                walkin.set_to_progress()
            # elif self.order_id.amount_total > self.order_id.amount_remain:
            elif self.amount_total > self.amount_owed:  # Nếu số tiền nợ nhỏ hơn số tiền ban đầu thì sinh Payment chênh lệch
                # walkin = self.env['sh.medical.appointment.register.walkin']
                # if self.walkin_id:
                #     walkin += self.walkin_id
                # else:
                #     walkin += self.env['sh.medical.appointment.register.walkin'].sudo().search(
                #         [('sale_order_id', '=', self.order_id.id), ('booking_id', '=', self.booking_id.id)],
                #         order='id desc', limit=1)
                if walkin.service:
                    draft_payment = False

                    if walkin.payment_ids:  # Lấy ra payment nháp gắn với phiếu khám này
                        draft_payment = walkin.sudo().payment_ids.search(
                            [('id', 'in', walkin.sudo().payment_ids.ids), ('state', '=', 'draft'),
                             ('payment_type', '=', 'inbound')], order='id desc', limit=1)
                    if draft_payment:  # nếu có phiếu nháp thì chỉnh tiền và ghi chú ở phiếu nháp
                        draft_payment = draft_payment.sudo()
                        draft_payment.amount = self.amount_total - self.amount_owed
                        draft_payment.text_total = self.num2words_vnm(
                            int(self.amount_total - self.amount_owed)) + " đồng"
                        draft_payment.communication = "Thu phí dịch vụ cho phiếu khám %s (duyệt nợ)" % walkin.name
                        draft_payment.payment_date = fields.Date.today()
                        draft_payment.date_requested = fields.Date.today()

                    else:  # tạo mới nếu ko có payment nháp
                        journal_id = self.env['account.journal'].sudo().search(
                            [('type', '=', 'cash'), ('company_id', '=', walkin.institution.his_company.id)], limit=1)
                        self.env['account.payment'].sudo().create({
                            'partner_id': walkin.patient.partner_id.id,
                            'patient': walkin.patient.id,
                            'company_id': walkin.institution.his_company.id,
                            'currency_id': self.currency_id.id,
                            'amount': self.amount_total - self.amount_owed,
                            'brand_id': walkin.booking_id.brand_id.id,
                            'crm_id': walkin.booking_id.id,
                            'communication': "Thu phí dịch vụ cho phiếu khám %s (duyệt nợ)" % walkin.name,
                            'text_total': self.num2words_vnm(int(self.amount_total - self.amount_owed)) + " đồng",
                            'partner_type': 'customer',
                            'payment_type': 'inbound',
                            'payment_date': datetime.date.today(),  # ngày thanh toán
                            'date_requested': datetime.date.today(),  # ngày yêu cầu
                            'payment_method_id': self.env['account.payment.method'].with_user(1).search(
                                [('payment_type', '=', 'inbound')], limit=1).id,
                            'journal_id': journal_id.id,
                            'walkin': walkin.id,
                        })
            else:
                raise ValidationError('Số tiền khách thanh toán hiện lớn hơn số tiền của SO này!!!')
        self.color = 4
        return res

    def set_refuse(self):
        res = super(DebtReview, self).set_refuse()
        if self.booking_id and self.order_id:
            if self.order_id.amount_total > self.order_id.amount_remain:
                walkin = self.env['sh.medical.appointment.register.walkin'].search(
                    [('sale_order_id', '=', self.order_id.id), ('state', '=', 'WaitPayment'),
                     ('booking_id', '=', self.booking_id.id)], order='id desc', limit=1)
                if walkin.service:
                    draft_payment = False

                    if walkin.payment_ids:
                        draft_payment = walkin.payment_ids.search(
                            [('id', 'in', walkin.payment_ids.ids), ('state', '=', 'draft'),
                             ('payment_type', '=', 'inbound')], limit=1)
                    # if draft_payment:  # nếu có phiếu nháp thì chỉnh tiền và ghi chú ở phiếu nháp
                    #     draft_payment.amount = self.amount_total
                    #     draft_payment.text_total = num2words_vnm(int(self.amount_total)) + " đồng"
                    #     draft_payment.communication = "Thu phí dịch vụ cho phiếu khám %s (duyệt nợ)" % walkin.name
                    #     draft_payment.payment_date = fields.Date.today()
                    #     draft_payment.date_requested = fields.Date.today()

                    if not draft_payment:  # tạo mới nếu ko coa payment nháp
                        journal_id = self.env['account.journal'].search(
                            [('type', '=', 'cash'), ('company_id', '=', walkin.institution.his_company.id)], limit=1)
                        self.env['account.payment'].create({
                            'partner_id': walkin.patient.partner_id.id,
                            'patient': walkin.patient.id,
                            'company_id': self.company_id.id,
                            'currency_id': self.currency_id.id,
                            'amount': self.amount_total,
                            'brand_id': walkin.booking_id.brand_id.id,
                            'crm_id': walkin.booking_id.id,
                            'communication': "Thu phí dịch vụ cho phiếu khám %s (duyệt nợ)" % walkin.name,
                            'text_total': self.num2words_vnm(int(self.amount_total)) + " đồng",
                            'partner_type': 'customer',
                            'payment_type': 'inbound',
                            'payment_date': datetime.date.today(),  # ngày thanh toán
                            'date_requested': datetime.date.today(),  # ngày yêu cầu
                            'payment_method_id': self.env['account.payment.method'].with_user(1).search(
                                [('payment_type', '=', 'inbound')], limit=1).id,
                            'journal_id': journal_id.id,
                            'walkin': walkin.id,
                        })
        self.color = 0
        return res
