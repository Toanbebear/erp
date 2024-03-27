from openpyxl.worksheet import related

from odoo import fields, models, api, _
from odoo.http import request
from odoo.exceptions import AccessError, UserError, ValidationError
import datetime
import time
from datetime import timedelta
from odoo.api import onchange

SERVICE_HIS_TYPE = [('Spa', 'Spa'), ('Laser', 'Laser'), ('Odontology', 'Nha'), ('Surgery', 'Phẫu thuật'), ('ChiPhi', 'Chi phí khác')]


# def num2words_vnm(num):
#     under_20 = ['không', 'một', 'hai', 'ba', 'bốn', 'năm', 'sáu', 'bảy', 'tám', 'chín', 'mười', 'mười một',
#                 'mười hai', 'mười ba', 'mười bốn', 'mười lăm', 'mười sáu', 'mười bảy', 'mười tám', 'mười chín']
#     tens = ['hai mươi', 'ba mươi', 'bốn mươi', 'năm mươi', 'sáu mươi', 'bảy mươi', 'tám mươi', 'chín mươi']
#     above_100 = {100: 'trăm', 1000: 'nghìn', 1000000: 'triệu', 1000000000: 'tỉ'}
#
#     if num < 20:
#         return under_20[num]
#
#     elif num < 100:
#         under_20[1], under_20[5] = 'mốt', 'lăm'  # thay cho một, năm
#         result = tens[num // 10 - 2]
#         if num % 10 > 0:  # nếu num chia 10 có số dư > 0 mới thêm ' ' và số đơn vị
#             result += ' ' + under_20[num % 10]
#         return result
#
#     else:
#         unit = max([key for key in above_100.keys() if key <= num])
#         result = num2words_vnm(num // unit) + ' ' + above_100[unit]
#         if num % unit != 0:
#             if num > 1000 and num % unit < unit / 10:
#                 result += ' không trăm'
#             if 1 < num % unit < 10:
#                 result += ' linh'
#             result += ' ' + num2words_vnm(num % unit)
#     return result.capitalize()


def _update_transfer_dict(_transfer_dict, transfer_line_id, department, service_id, company_id, transaction_company_id, _type, transfer_amount):
    transfer_dict = _transfer_dict or {}
    if transfer_dict.get((service_id.id, company_id, transaction_company_id, transfer_line_id, department), 0) == 0:
        transfer_dict[(service_id.id, company_id, transaction_company_id, transfer_line_id, department)] = {
            'service_id': service_id,
            'sub_amount': 0,
            'add_amount': 0,
        }
    transfer_dict[(service_id.id, company_id, transaction_company_id, transfer_line_id, department)][_type] += transfer_amount
    return transfer_dict


class TransferPayment(models.Model):
    _name = 'crm.transfer.payment'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'money.mixin']
    _description = 'Phiếu điều chuyển'

    name = fields.Char(string='Số chứng từ', readonly=True, copy=False)
    state = fields.Selection([('draft', 'Draft'), ('done', 'Xác nhận thành công')],
                             readonly=True, default='draft', copy=False, string="Status")
    partner_id = fields.Many2one('res.partner', string='Khách hàng', tracking=True, readonly=True, required=True, states={'draft': [('readonly', False)]},
                                 domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    company_id = fields.Many2one('res.company', string='Công ty', required=True, default=lambda self: self.env.company, readonly=True)
    brand_id = fields.Many2one('res.brand', string='Thương hiệu', related='company_id.brand_id', store=True)
    payment_date = fields.Date(string='Date', default=fields.Date.context_today, required=True, readonly=True,
                               states={'draft': [('readonly', False)]}, copy=False, tracking=True)

    @api.depends('payment_date')
    def _get_current_date_second(self):
        current_date = fields.Datetime.now()
        self.current_date = str(current_date.strftime('%Y-%m-%d %H:%M:%S'))

    current_date = fields.Char(string='Current Date', compute='_get_current_date_second')

    communication = fields.Char(string='Nội dung', readonly=True, required=True, states={'draft': [('readonly', False)]})
    crm_id = fields.Many2one('crm.lead', string='Booking/lead', domain="[('partner_id','=', partner_id), ('type', '=', 'opportunity')]", tracking=True)
    transfer_payment_line_ids = fields.One2many('crm.transfer.payment.line', 'crm_transfer_payment_id', string='Chi tiết điều chuyển', tracking=True, states={'draft': [('readonly', False)]})
    amount_subtotal = fields.Monetary(string='Tổng tiền điều chuyển', compute='_get_amount_subtotal')
    currency_id = fields.Many2one('res.currency', string='Đơn vị tiền tệ', required=True, readonly=True, states={'draft': [('readonly', False)]},
                                  default=lambda self: self.env.company.currency_id.id)
    is_share_booking = fields.Boolean(string="Có chia sẻ booking không?", compute="_get_share_booking", default=False)
    crm_company_id = fields.Many2one('res.company', string='Công ty', store=True, related='crm_id.company_id')
    crm_company2_id = fields.Many2many('res.company', 'transfer_payment_company2_ref', 'transfer_payment', 'company', related='crm_id.company2_id')

    @api.depends('crm_id')
    def _get_share_booking(self):
        for rec in self:
            rec.is_share_booking = False
            if rec.crm_id.company2_id:
                rec.is_share_booking = True

    @api.depends('transfer_payment_line_ids')
    def _get_amount_subtotal(self):
        for rec in self:
            if rec.transfer_payment_line_ids:
                rec.amount_subtotal = sum([pay.transfer_amount for pay in rec.transfer_payment_line_ids])
            else:
                rec.amount_subtotal = 0.0

    def get_domain_user(self):
        thungan_job = self.env['hr.job'].sudo().search([('name', 'ilike', 'thu ngân'), ('company_id', 'in', self.env.companies.ids)])

        emp_user = self.env['hr.employee'].sudo().search([('job_id', 'in', thungan_job.ids),
                                                          ('company_id', 'in', self.env.companies.ids), ('user_id', '!=', False)])

        if thungan_job and emp_user:
            return [("groups_id", "in", [self.env.ref("account.group_account_invoice").id]),
                    ('company_id', 'in', self.env.companies.ids), ('id', 'in', emp_user.sudo().mapped('user_id').ids)]
        else:
            return [("groups_id", "in", [self.env.ref("account.group_account_invoice").id]),
                    ('company_id', 'in', self.env.companies.ids)]

    user = fields.Many2one('res.users', string='Người thực hiện', domain=lambda self: self.get_domain_user(),
                           default=lambda self: self.env.user if self.env.user.has_group(
                               "shealth_all_in_one.group_sh_medical_accountant") else False, tracking=True)

    # load info
    @api.onchange('crm_id')
    def onchange_crm(self):
        for rec in self:
            rec.write({
                'transfer_payment_line_ids': self.create_transfer_payment_line(self.crm_id),
            })

    def create_transfer_payment_line(self, crm_id):
        transfer_payment_line = [(5, 0, 0)]
        service_list, product_list = self.env['account.payment'].get_line_account_payment_history(crm_id)
        for line in service_list:
            crm_line_id = self.env['crm.line'].search([('id', '=', line[0])])
            transfer_payment_line.append((0, 0, {'from_crm_line_id': line[0],
                                                 'crm_transfer_payment_id': self.id,
                                                 'from_department': crm_line_id.service_id.his_service_type,
                                                 'from_company_id': line[1] if not self.crm_id.company2_id else '',
                                                 'to_company_id': line[1] if not self.crm_id.company2_id else '',
                                                 'remaining_amount': line[2]
                                                 }))
        for line_product in product_list:
            crm_line_product_id = self.env['crm.line.product'].search([('id', '=', line_product[0])])
            transfer_payment_line.append((0, 0, {'from_crm_line_product_id': line_product[0],
                                                 'crm_transfer_payment_id': self.id,
                                                 'from_department': crm_line_product_id.department,
                                                 'from_company_id': line_product[1] if not self.crm_id.company2_id else '',
                                                 'to_company_id': line_product[1] if not self.crm_id.company2_id else '',
                                                 'remaining_amount': line_product[2]
                                                 }))
        return transfer_payment_line

    @api.model
    def create(self, vals):
        res = super(TransferPayment, self).create(vals)
        # print('CREATED : ', res)
        return res

    def action_confirm(self):
        self.ensure_one()
        if not self.validate_sang_dich_vu_or_sang_san_pham():
            raise ValidationError(_('Bạn phải điền đầy đủ sang dịch vụ hoặc sang sản phẩm.'))
        if not self.validate_sang_dich_vu_and_sang_san_pham():
            raise ValidationError(_('Bạn không thể điền tất cả sang dịch vụ và sang sản phẩm.'))
        if not self.validate_from_company():
            raise ValidationError(_('Trường Từ công ty không được để trống'))

        if self._context.get('name', _('New')) == _('New'):
            seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(self.payment_date))
            self.name = self.env['ir.sequence'].next_by_code('crm.transfer.payment', sequence_date=seq_date) or _('New')
            self.write({'state': 'done'})

        for line in self.transfer_payment_line_ids:
            line.amount_constrains()

    def validate_sang_dich_vu_or_sang_san_pham(self):
        self.ensure_one()
        is_valid = True
        if len(self.transfer_payment_line_ids) > 0:
            for line in self.transfer_payment_line_ids:
                if line.transfer_amount > 0 and not line.to_crm_line_id and not line.to_crm_line_product_id:
                    is_valid = False
                    break
        return is_valid

    def validate_from_company(self):
        self.ensure_one()
        is_valid = True
        if self.transfer_payment_line_ids.filtered(lambda x:
                                                   x.from_company_id.id is False
                                                   and (x.to_crm_line_product_id or x.to_crm_line_id)):
            is_valid = False
        return is_valid

    def validate_sang_dich_vu_and_sang_san_pham(self):
        self.ensure_one()
        is_valid = True
        if len(self.transfer_payment_line_ids) > 0:
            for line in self.transfer_payment_line_ids:
                if line.to_crm_line_id and line.to_crm_line_product_id:
                    is_valid = False
                    break
        return is_valid

    def action_draft(self):
        self.ensure_one()
        self.name = 'New'
        self.write({'state': 'draft'})

    # Tải lại thông tin ở booking
    def reload(self):
        for rec in self:
            rec.write({
                'transfer_payment_line_ids': self.create_transfer_payment_line(self.crm_id),
            })

    def write(self, vals):
        if self and vals.get('state') == 'done':
            transfer_service_dirt = {}
            transfer_product_dirt = {}
            if not sum(self.transfer_payment_line_ids.mapped('transfer_amount')) \
                    or (not self.transfer_payment_line_ids.mapped('to_crm_line_id.id') and not self.transfer_payment_line_ids.mapped('to_crm_line_product_id.id')):
                raise ValidationError(_('Bạn phải điền thông tin điều chuyển.'))
            for transfer in self.transfer_payment_line_ids:
                # service
                if transfer.from_crm_line_id:
                    from_id = transfer.from_crm_line_id
                    company_id = transfer.from_company_id.id
                    transaction_company_id = transfer.to_company_id.id or transfer.from_company_id.id
                    transfer_service_dirt = _update_transfer_dict(
                        transfer_service_dirt, transfer, transfer.from_department,
                        from_id, company_id, transaction_company_id, 'sub_amount', transfer.transfer_amount)
                if transfer.to_crm_line_id:
                    to_id = transfer.to_crm_line_id
                    company_id = transfer.to_company_id.id or transfer.from_company_id.id
                    transaction_company_id = transfer.from_company_id.id
                    transfer_service_dirt = _update_transfer_dict(
                        transfer_service_dirt, transfer, transfer.to_department,
                        to_id, company_id, transaction_company_id, 'add_amount', transfer.transfer_amount)
                # product
                if transfer.from_crm_line_product_id:
                    from_id = transfer.from_crm_line_product_id
                    company_id = transfer.from_company_id.id
                    transaction_company_id = transfer.to_company_id.id or transfer.from_company_id.id
                    transfer_product_dirt = _update_transfer_dict(
                        transfer_product_dirt, transfer, transfer.from_department,
                        from_id, company_id, transaction_company_id, 'sub_amount', transfer.transfer_amount)
                if transfer.to_crm_line_product_id:
                    to_id = transfer.to_crm_line_product_id
                    company_id = transfer.to_company_id.id or transfer.from_company_id.id
                    transaction_company_id = transfer.from_company_id.id
                    transfer_product_dirt = _update_transfer_dict(
                        transfer_product_dirt, transfer, transfer.to_department,
                        to_id, company_id, transaction_company_id, 'add_amount', transfer.transfer_amount)

            # create account payment
            # print(transfer_service_dirt, transfer_product_dirt)
            # create service
            for transfer in transfer_service_dirt:
                crm_line_id = transfer_service_dirt[transfer].get('service_id', 0)
                if transfer_service_dirt[transfer].get('add_amount', 0) > 0:
                    amount_value = transfer_service_dirt[transfer].get('add_amount', 0)
                    self._create_crm_sale_payment(
                        transfer[3], transfer[4], amount_value, "inbound",
                        crm_line_id=crm_line_id,
                        company_id=transfer[1],
                        transaction_company_id=transfer[2])
                if transfer_service_dirt[transfer].get('sub_amount', 0) > 0:
                    amount_value = transfer_service_dirt[transfer].get('sub_amount', 0)
                    self._create_crm_sale_payment(
                        transfer[3], transfer[4], amount_value, "outbound",
                        crm_line_id=crm_line_id,
                        company_id=transfer[1],
                        transaction_company_id=transfer[2])
            # create product
            for transfer_product in transfer_product_dirt:
                crm_line_product_id = transfer_product_dirt[transfer_product].get('service_id', 0)
                if transfer_product_dirt[transfer_product].get('add_amount', 0) > 0:
                    amount_value = transfer_product_dirt[transfer_product].get('add_amount', 0)
                    self._create_crm_sale_payment(
                        transfer_product[3], transfer_product[4], amount_value, "inbound",
                        crm_line_product_id=crm_line_product_id,
                        company_id=transfer_product[1],
                        transaction_company_id=transfer_product[2])
                if transfer_product_dirt[transfer_product].get('sub_amount', 0) > 0:
                    amount_value = transfer_product_dirt[transfer_product].get('sub_amount', 0)
                    self._create_crm_sale_payment(
                        transfer_product[3], transfer_product[4], amount_value, "outbound",
                        crm_line_product_id=crm_line_product_id,
                        company_id=transfer_product[1],
                        transaction_company_id=transfer_product[2])

        res = super(TransferPayment, self).write(vals)
        # print('UPDATE : ', vals)
        return res

    def _create_crm_sale_payment(self, transfer_line_id, department, amount_value, payment_type, crm_line_id=False, crm_line_product_id=False, company_id=False, transaction_company_id=False):
        # create sale payment
        crm_sale_payment_id = self.env['crm.sale.payment'].sudo().create({
            "booking_id": self.crm_id.id,
            "transfer_payment_id": self.id,
            "transfer_payment_line_id": transfer_line_id.id,
            "department": department,
            "currency_id": self.currency_id.id,
            "product_type": 'service' if crm_line_id else 'product',
            "product_category_id": crm_line_id.service_id.categ_id.id
            if crm_line_id else crm_line_product_id.product_id.categ_id.id,
            "service_id": crm_line_id.service_id.id if crm_line_id else False,
            "crm_line_id": crm_line_id.id if crm_line_id else False,
            "product_id": crm_line_product_id.product_id.id if crm_line_product_id else False,
            "crm_line_product_id": crm_line_product_id.id if crm_line_product_id else False,
            "coupon_ids": [(6, 0, crm_line_id.prg_ids.ids)] if crm_line_id else [(6, 0, crm_line_product_id.prg_ids.ids)],
            "payment_type": payment_type,
            "internal_payment_type": 'tai_don_vi',
            "company_id": company_id,
            "transaction_company_id": transaction_company_id,
            "amount_proceeds": (0 - amount_value) if payment_type == 'outbound' else amount_value,
            "partner_id": self.crm_id.partner_id.id,
            "communication": self.communication
            # "user_id": self.user.id,
        })

        # update total received crm_line
        if crm_sale_payment_id and crm_line_id:
            crm_line_id.write({
                'total_received': (crm_line_id.total_received - amount_value) if payment_type == 'outbound'
                else (crm_line_id.total_received + amount_value)})

        # update total received crm_line_product
        if crm_sale_payment_id and crm_line_product_id:
            crm_line_product_id.write({
                'total_received': (crm_line_product_id.total_received - amount_value) if payment_type == 'outbound'
                else (crm_line_product_id.total_received + amount_value)})

    def unlink(self):
        for transfer in self.filtered(lambda transfer: transfer.state not in ['draft']):
            raise UserError(_('Bạn không được xóa phiếu điều chuyển đã thành công.'))
        return super(TransferPayment, self).unlink()

    def calculate_remaining_amount(self):
        for rec in self:
            for line in rec.transfer_payment_line_ids:
                line.calculate_remaining_amount()

    @api.onchange('transfer_payment_line_ids')
    def _onchange_transfer_payment_line_ids(self):
        transfer_dict = {}

        for transfer_line in self.transfer_payment_line_ids.filtered(lambda x: x.to_crm_line_id or x.to_crm_line_product_id):
            key = str(transfer_line.from_crm_line_id.id) + '_' + str(transfer_line.from_crm_line_product_id.id)
            transfer_dict.setdefault(
                key,
                {
                    "remaining_amount": transfer_line.remaining_amount,
                    "total_transfer_amount": 0,
                }
            )["total_transfer_amount"] += transfer_line.transfer_amount

            if transfer_dict[key]['total_transfer_amount'] > transfer_dict[key]['remaining_amount']:
                raise ValidationError("Số tiền điều chuyển lớn hơn số tiền chưa sử dụng")


    # không dùng nữa
    # def _create_account_payment(self, amount_value, payment_type, service_id=False, product_id=False, company_id=False):
    #
    #     service_list, product_list = self.env['account.payment'].get_line_account_payment_history(self.crm_id)
    #     _service_ids = [(5, 0, 0)] + [(0, 0, {
    #         'crm_line_id': line[0],
    #         'company_id': line[1],
    #         'prepayment_amount': amount_value if (service_id and line[0] == service_id and
    #                                               ((line[1] == company_id) if company_id else True)
    #                                               ) else 0,
    #     }) for line in service_list]
    #
    #     _product_ids = [(5, 0, 0)] + [(0, 0, {
    #         'crm_line_product_id': line_product[0],
    #         'company_id': line_product[1],
    #         'prepayment_amount': amount_value if (product_id and line_product[0] == product_id and
    #                                               ((line_product[1] == company_id) if company_id else True)
    #                                               )else 0,
    #     }) for line_product in product_list]
    #
    #     journal_id = self.env['account.journal'].search(
    #         [('type', '=', 'cash'), ('company_id', '=', self.env.company.id)], limit=1)
    #
    #     account_payment_id = self.env['account.payment'].create({
    #         'partner_id': self.partner_id.id,
    #         'company_id': self.env.company.id,
    #         'currency_id': self.env.company.currency_id.id,
    #         'amount': amount_value,
    #         'brand_id': self.crm_id.brand_id.id,
    #         'crm_id': self.crm_id.id,
    #         'communication': "Điều chuyển dịch vụ/sản phẩm",
    #         'text_total': num2words_vnm(int(amount_value)) + " đồng",
    #         'partner_type': 'customer',
    #         'payment_type': payment_type,
    #         'payment_date': datetime.date.today(),  # ngày thanh toán
    #         'date_requested': datetime.date.today(),  # ngày yêu cầu
    #         'payment_method_id': self.env['account.payment.method'].sudo().search(
    #             [('payment_type', '=', payment_type)], limit=1).id,
    #         'journal_id': journal_id.id,
    #         'transfer_payment_id': self.id,
    #         'service_ids': _service_ids,
    #         'product_ids': _product_ids,
    #         'name': self.name,
    #     })
    #     if account_payment_id:
    #         account_payment_id.write({'state': 'posted'})


class TransferPaymentLine(models.Model):
    _name = 'crm.transfer.payment.line'
    _description = 'Chi tiết điều chuyển'

    crm_transfer_payment_id = fields.Many2one('crm.transfer.payment', 'Phiếu điều chuyển', ondelete='cascade')
    state = fields.Selection([('draft', 'Draft'), ('done', 'Xác nhận thành công')],
                             related='crm_transfer_payment_id.state')
    from_crm_line_id = fields.Many2one('crm.line', string='Từ dịch vụ')
    from_crm_line_product_id = fields.Many2one('crm.line.product', string='Từ sản phẩm')
    to_crm_line_id = fields.Many2one('crm.line', string='Sang dịch vụ')
    to_crm_line_product_id = fields.Many2one('crm.line.product', string='Sang sản phẩm')
    from_department = fields.Selection(SERVICE_HIS_TYPE, string='Từ phòng ban')
    from_company_id = fields.Many2one('res.company', string='Từ công ty', required=True)
    to_department = fields.Selection(SERVICE_HIS_TYPE, string='Đến phòng ban')
    to_company_id = fields.Many2one('res.company', string='Đến công ty', domain=[], required=True)
    domain_to_crm_line_ids = fields.Many2many('crm.line', compute="_set_domain_crm_line", default=None)
    domain_to_crm_line_product_ids = fields.Many2many('crm.line.product',
                                                      compute="_set_domain_crm_line_product", default=None)
    domain_company = fields.Many2many('res.company', compute='_set_domain_company', default=None)
    total_received = fields.Monetary(string="Tiền đã nộp", currency_field="currency_id",
                                     compute="_calculate_total_received", readonly=True, store=True)
    remaining_amount = fields.Monetary(string="Tiền chưa sử dụng", currency_field="currency_id",
                                       compute="_calculate_remaining_amount", readonly=True, store=True)
    currency_id = fields.Many2one('res.currency', string='Tiền tệ', tracking=True,
                                  related='crm_transfer_payment_id.currency_id')
    transfer_amount = fields.Monetary(string="Số tiền điều chuyển", default=0)
    is_block_company = fields.Boolean(string="Đóng chỉnh sửa công ty không?", default=True)
    STAGE_LINE_SERVICE = [
        ('new', 'Được sử dụng'),
        ('processing', 'Đang xử trí'),
        ('done', 'Kết thúc'),
        ('waiting', 'Chờ phê duyệt'),
        ('cancel', 'Hủy')
    ]
    stage_line_service = fields.Selection(STAGE_LINE_SERVICE, string='Trạng thái dịch vụ', related='from_crm_line_id.stage')

    STAGE_LINE_PRODUCT = [
        ('new', 'Mới'),
        ('processing', 'Hóa đơn nháp'),
        ('sold', 'Hoàn thành'),
        ('waiting', 'Chờ phê duyệt'),
        ('cancel', 'Hủy')
    ]
    stage_line_product = fields.Selection(STAGE_LINE_PRODUCT, string='Trạng thái sản phẩm', related='from_crm_line_product_id.stage_line_product')

    # def write(self, vals):
    #     value_update = {
    #         'department': vals.get('to_department')
    #     }
    #     crm_sale_payment_ids = self.env['crm.sale.payment'].sudo().search([
    #         ('transfer_payment_id', '=', self.crm_transfer_payment_id.id),
    #         ('product_id', '=', self.to_crm_line_product_id.product_id.id)])
    #     print(crm_sale_payment_ids, self.id)
    #     crm_sale_payment_ids.sudo().write(value_update)


    # @api.onchange('to_department')
    # def _update_crm_sale_payment_department(self):
    #     for rec in self:
    #         if rec.state == 'done':
    #             value_update = {
    #                 'department': rec.to_department
    #             }
    #             crm_sale_payment_ids = rec.env['crm.sale.payment'].sudo().search([
    #                 ('transfer_payment_line_id', '=', rec.id),
    #                 ('product_id', '=', rec.to_crm_line_product_id.product_id.id)])
    #             print(crm_sale_payment_ids, rec.id)
    #             crm_sale_payment_ids.sudo().write(value_update)

    @api.constrains('to_crm_line_product_id', 'to_department')
    def constraint_department(self):
        for rec in self:
            if rec.to_crm_line_product_id and not rec.to_department:
                raise ValidationError('Bắt buộc chọn phòng ban khi điều chuyển sang sản phẩm')

    @api.depends('crm_transfer_payment_id')
    def _set_domain_crm_line(self):
        crm_line_ids = []
        if self.env.context.get('default_parent_id'):
            parent_obj = self.env['crm.transfer.payment'].browse(self.env.context.get('default_parent_id'))
            if parent_obj:
                crm_line_ids = parent_obj.crm_id.crm_line_ids.ids
        elif self.crm_transfer_payment_id.crm_id:
            crm_line_ids = self.crm_transfer_payment_id.crm_id.crm_line_ids.ids
        self.domain_to_crm_line_ids = crm_line_ids

    @api.depends('crm_transfer_payment_id')
    def _set_domain_company(self):
        company_ids = []
        if self.crm_transfer_payment_id and self.crm_transfer_payment_id.crm_id:
            company_ids = self.crm_transfer_payment_id.crm_id.company2_id.ids
            company_ids += self.crm_transfer_payment_id.crm_id.company_id.ids
        self.domain_company = company_ids

    @api.depends('crm_transfer_payment_id')
    def _set_domain_crm_line_product(self):
        crm_line_product_ids = []
        if self.env.context.get('default_parent_id'):
            parent_obj = self.env['crm.transfer.payment'].browse(self.env.context.get('default_parent_id'))
            if parent_obj:
                crm_line_product_ids = parent_obj.crm_id.crm_line_product_ids.ids
        elif self.crm_transfer_payment_id.crm_id:
            crm_line_product_ids = self.crm_transfer_payment_id.crm_id.crm_line_product_ids.ids
        self.domain_to_crm_line_product_ids = crm_line_product_ids

    # số tiền đã thu + số tiền đã hoàn cho dich vụ/sản phầm này.
    @api.depends('crm_transfer_payment_id', 'from_crm_line_id', 'from_crm_line_product_id', 'from_company_id')
    def _calculate_total_received(self):
        for rec in self:
            # Cập nhật tiền đã thu theo bảng crm_sale_payment
            domain = [('booking_id', '=', rec.crm_transfer_payment_id.crm_id.id),
                      ('company_id', '=', rec.from_company_id.id),
                      ]
            if rec.from_crm_line_id:
                domain.append(('crm_line_id', '=', rec.from_crm_line_id.id))
            elif rec.from_crm_line_product_id:
                domain.append(('crm_line_product_id', '=', rec.from_crm_line_product_id.id))
            service_payment_list = self.env['crm.sale.payment'].search(domain)
            total = sum(i.amount_proceeds for i in service_payment_list) or 0
            rec.total_received = total

    def calculate_remaining_amount(self):
        for rec in self:
            rec._calculate_total_received()
            rec._calculate_remaining_amount()

    # số tiền chưa sử dụng = số tiền đã thu - số tiền đã thực hiện trong sale.order
    @api.depends('total_received')
    def _calculate_remaining_amount(self):
        for rec in self:
            # [SCI1208] tiền chưa sử dụng sẽ được lấy ở booking
            # rec.remaining_amount = rec.total_received
            # if rec.total_received > 0:
            #     order_line_ids = []
            #     order_line_list = self.env['sale.order'].search([
            #         ('booking_id', '=', rec.crm_transfer_payment_id.crm_id.id),
            #         ('state', 'in', ['sale', 'done'])])
            #     if rec.from_crm_line_id:
            #         order_line_ids = order_line_list.mapped('order_line').filtered(lambda x: x.crm_line_id.id == rec.from_crm_line_id.id and x.company_id.id == rec.from_company_id.id)
            #     elif rec.from_crm_line_product_id:
            #         order_line_ids = order_line_list.mapped('order_line').filtered(lambda x: x.line_product.id == rec.from_crm_line_product_id.id and x.company_id.id == rec.from_company_id.id)
            #     if order_line_ids:
            #         rec.remaining_amount = rec.total_received - sum(i.price_subtotal for i in order_line_ids)

                # Trương hợp tạo mới transfer line
                # if isinstance(rec.id, models.NewId):
                #     if rec.from_crm_line_id:
                #         rec.remaining_amount = rec.from_crm_line_id.remaining_amount
                #     if rec.from_crm_line_product_id:
                #         rec.remaining_amount = rec.from_crm_line_product_id.remaining_amount

            if rec.from_crm_line_id:
                rec.remaining_amount = rec.from_crm_line_id.remaining_amount
            if rec.from_crm_line_product_id:
                rec.remaining_amount = rec.from_crm_line_product_id.remaining_amount

    @api.onchange('to_crm_line_id')
    def onchange_to_crm(self):
        if self.to_crm_line_id:
            self.to_crm_line_product_id = None
            self.to_department = self.to_crm_line_id.service_id.his_service_type
        elif not self.to_crm_line_product_id:
            self.to_department = ''

    @api.onchange('to_crm_line_product_id')
    def onchange_to_crm_product(self):
        if self.to_crm_line_product_id:
            self.to_crm_line_id = None
        elif not self.to_crm_line_id:
            self.to_department = ''

    @api.onchange('to_crm_line_id', 'to_crm_line_product_id')
    def onchange_to_crm_line(self):
        check_company = True
        if self.crm_transfer_payment_id.crm_id.company2_id:
            check_company = self.from_company_id.id == self.to_company_id.id
        if self.to_crm_line_id.id:
            if self.to_crm_line_id.id == self.from_crm_line_id.id and check_company:
                raise UserError(_('Bạn không thể điều chuyển chính dịch vụ này.'))
            # return self._set_domain_company('service', service_id=self.to_crm_line_id.id)
        if self.to_crm_line_product_id:
            if self.to_crm_line_product_id.id == self.from_crm_line_product_id.id and check_company:
                raise UserError(_('Bạn không thể điều chuyển chính sản phẩm này.'))
            # return self._set_domain_company('product', self.to_crm_line_product_id.id)
        if self.to_crm_line_id and self.to_crm_line_product_id:
            raise UserError(_('Bạn chỉ được chọn đến một loại điều chuyển.'))

    @api.onchange('to_company_id', 'from_company_id')
    def onchange_company_id(self):
        check_company = True
        if self.crm_transfer_payment_id.crm_id.company2_id:
            check_company = self.from_company_id.id == self.to_company_id.id
        if self.to_crm_line_id.id:
            if self.to_crm_line_id.id == self.from_crm_line_id.id and check_company:
                raise UserError(_('Bạn không thể điều chuyển chính dịch vụ này.'))
        if self.to_crm_line_product_id:
            if self.to_crm_line_product_id.id == self.from_crm_line_product_id.id and check_company:
                raise UserError(_('Bạn không thể điều chuyển chính sản phẩm này.'))

    @api.onchange('from_crm_line_id', 'from_crm_line_product_id')
    def onchange_from_crm_line(self):
        if self.from_crm_line_id and self.from_crm_line_product_id:
            raise UserError(_('Bạn chỉ được chọn từ mội loại điều chuyển.'))
        self.is_block_company = False
        if self.from_crm_line_id.id:
            self.from_department = self.from_crm_line_id.service_id.his_service_type
            # return self._set_domain_company('service', self.from_crm_line_id.id)
        if self.from_crm_line_product_id:
            self.from_department = self.from_crm_line_product_id.department
            # return self._set_domain_company('product', self.from_crm_line_product_id)

    # số tiền điều chuyển <= tiền đã nộp.
    @api.constrains('total_received', 'transfer_amount', 'remaining_amount')
    def amount_constrains(self):
        for rec in self:
            # [SCI1358]
            # Sửa điều kiện để xác nhận trường hợp share booking
            if rec.transfer_amount > rec.remaining_amount and rec.transfer_amount != 0:
                raise ValidationError(_('Số tiền điều chuyển phải nhỏ hơn hoặc bằng số tiền chưa sử dụng.'))
            # check dịch vụ/sp chuyển đến đã đóng đủ chưa.
            if rec.to_crm_line_id:
                # get tiền nhận được đã tính trước đó.
                total_received = rec.crm_transfer_payment_id.transfer_payment_line_ids.filtered(lambda x: x.from_crm_line_id == rec.to_crm_line_id
                                                                                                          and (x.from_company_id == rec.to_company_id or not rec.to_company_id)).total_received
                if rec.to_crm_line_id.total - total_received < rec.transfer_amount:
                    raise ValidationError(_('Số tiền điều chuyển phải nhỏ hơn hoặc bằng số tiền cần phải đóng ở dịch vụ này.'))
            if rec.to_crm_line_product_id:
                total_received = rec.crm_transfer_payment_id.transfer_payment_line_ids.filtered(lambda x: x.from_crm_line_product_id == rec.to_crm_line_product_id
                                                                                                          and (x.from_company_id == rec.to_company_id or not rec.to_company_id)).total_received
                if rec.to_crm_line_product_id.total - total_received < rec.transfer_amount:
                    raise ValidationError(_('Số tiền điều chuyển phải nhỏ hơn hoặc bằng số tiền cần phải đóng ở sản phẩm này.'))

    @api.constrains('to_crm_line_id', 'to_crm_line_product_id', 'to_company_id')
    def company_constrains(self):
        for rec in self:
            if rec.crm_transfer_payment_id.crm_id.company2_id:
                if (rec.to_crm_line_id or rec.to_crm_line_product_id) and not rec.to_company_id:
                    raise ValidationError(_('Bạn phải chọn công ty ghi nhận doanh số'))

    def write(self, vals):
        # cap nhat phong ban den san pham crm.sale.payment
        if vals.get('to_department') and self.state == 'done':
            crm_sale_payment_id = self.env['crm.sale.payment'].search([
                ('transfer_payment_line_id', '=', self.id),
                ('product_id', '=', self.to_crm_line_product_id.product_id.id)
            ])
            if crm_sale_payment_id:
                crm_sale_payment_id.department = vals.get('to_department')
        # cap nhat phong ban tu san pham crm.sale.payment
        if vals.get('from_department') and self.state == 'done':
            crm_sale_payment_id = self.env['crm.sale.payment'].search([
                ('transfer_payment_line_id', '=', self.id),
                ('product_id', '=', self.from_crm_line_product_id.product_id.id)
            ])
            if crm_sale_payment_id:
                crm_sale_payment_id.department = vals.get('from_department')
        res = super(TransferPaymentLine, self).write(vals)
        return res

    # def _set_domain_company(self, _type, service_id):
        # domains = [
        #     ('account_payment_id.crm_id.id', '=', self.crm_transfer_payment_id.crm_id.id),
        #     ('account_payment_id.state', '!=', 'draft')
        # ]
        # if _type == 'service':
        #     domains.append(('crm_line_id.id', '=', service_id))
        #     company_ids = self.env['crm.account.payment.detail'].search(domains).mapped('company_id').ids
        # else:
        #     domains.append(('crm_line_product_id.id', '=', service_id))
        #     company_ids = self.env['crm.account.payment.product.detail'].search(domains).mapped('company_id').ids
        # if company_ids:
        #     self.is_share_booking = True
        # return {'domain': {'to_company_id': [('id', 'in', company_ids)], 'from_company_id': [('id', 'in', company_ids)]}}

        # update: chọn tất cả công ty đươc share
        # company_domain = self.crm_transfer_payment_id.crm_id.company2_id.ids
        # company_domain.append(self.crm_transfer_payment_id.crm_id.company_id.id)# thêm cả công ty hiện tại
        # return {'domain': {'to_company_id': [('id', 'in', company_domain)], 'from_company_id': [('id', 'in', company_domain)]}}

