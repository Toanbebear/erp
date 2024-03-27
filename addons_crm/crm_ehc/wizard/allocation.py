from datetime import date, datetime

from odoo import fields, api, models, _
from odoo.exceptions import ValidationError


# def num2words_vnm(num):
# 	under_20 = ['không', 'một', 'hai', 'ba', 'bốn', 'năm', 'sáu', 'bảy', 'tám', 'chín', 'mười', 'mười một',
# 				'mười hai', 'mười ba', 'mười bốn', 'mười lăm', 'mười sáu', 'mười bảy', 'mười tám', 'mười chín']
# 	tens = ['hai mươi', 'ba mươi', 'bốn mươi', 'năm mươi', 'sáu mươi', 'bảy mươi', 'tám mươi', 'chín mươi']
# 	above_100 = {100: 'trăm', 1000: 'nghìn', 1000000: 'triệu', 1000000000: 'tỉ'}
#
# 	if num < 20:
# 		return under_20[num]
#
# 	elif num < 100:
# 		under_20[1], under_20[5] = 'mốt', 'lăm'  # thay cho một, năm
# 		result = tens[num // 10 - 2]
# 		if num % 10 > 0:  # nếu num chia 10 có số dư > 0 mới thêm ' ' và số đơn vị
# 			result += ' ' + under_20[num % 10]
# 		return result
#
# 	else:
# 		unit = max([key for key in above_100.keys() if key <= num])
# 		result = num2words_vnm(num // unit) + ' ' + above_100[unit]
# 		if num % unit != 0:
# 			if num > 1000 and num % unit < unit / 10:
# 				result += ' không trăm'
# 			if 1 < num % unit < 10:
# 				result += ' linh'
# 			result += ' ' + num2words_vnm(num % unit)
# 	return result.capitalize()


class SaleAllocation(models.TransientModel):
	_name = 'crm.ehc.sale.allocation'
	_description = 'Sale allocation'
	_inherit = 'money.mixin'

	booking_id = fields.Many2one('crm.lead', string='Booking')
	partner_id = fields.Many2one('res.partner', string='Khách hàng')
	company_id = fields.Many2one('res.company', string='Chi nhánh', default=lambda self: self.env.company.id)
	currency_id = fields.Many2one('res.currency', string='Tiền tệ')
	brand_id = fields.Many2one(related="company_id.brand_id")
	# allocation_line_ids = fields.One2many('crm.ehc.sale.allocation.line', 'allocation_id',
	#                                       string='Dịch vụ phân bổ', compute='_compute_allocation_line_ids')
	# allocation_line_ids = fields.One2many('crm.hh.ehc.statement.payment', 'allocation_id', string='dvpb')
	allocation_line_ids = fields.One2many('crm.hh.ehc.statement.payment', 'booking_id', string='Danh sách thanh toán',
										  compute="_compute_allocation_line_ids")
	crm_line_ids = fields.One2many('crm.line', 'crm_id', string='Danh sách dịch vụ',
								   compute="_compute_crm_line_ids")
	start_date = fields.Date('Ngày bắt đầu', default=date.today())
	end_date = fields.Date('Ngày kết thúc')
	invoice_type = fields.Selection([('1', 'Thu tiền'), ('2', 'Hoàn tiền')])
	amount_total = fields.Monetary('Tổng tiền')

	@api.constrains('start_date', 'end_date')
	def check_dates(self):
		for record in self:
			start_date = fields.Date.from_string(record.start_date)
			end_date = fields.Date.from_string(record.end_date)
			if start_date > end_date:
				raise ValidationError(
					_("End Date cannot be set before Start Date."))

	# @api.onchange('start_date')
	# def _onchange_start_date(self):
	#     if self.start_date:
	#         if self.start_date.month == fields.date.today().month:
	#             self.end_date = fields.date.today()
	#         else:
	#             self.end_date = date(self.start_date.year, self.start_date.month,
	#                                  monthrange(self.start_date.year, self.start_date.month)[1])

	@api.onchange('allocation_line_ids')
	def _compute_amount_total(self):
		for rec in self:
			total = 0
			if rec.allocation_line_ids:
				for allocation_line in rec.allocation_line_ids:
					total += allocation_line.amount_paid
				rec.amount_total = total
			else:
				rec.amount_total = False

	@api.onchange('booking_id', 'start_date', 'end_date', 'invoice_type')
	def _compute_allocation_line_ids(self):
		for rec in self:
			if rec.start_date and rec.end_date and rec.invoice_type:
				rec.allocation_line_ids = rec.booking_id.statement_payment_ehc_ids.filtered(lambda x:
																							x.allotted == False
																							and rec.start_date <= x.invoice_date <= rec.end_date and x.invoice_type == rec.invoice_type and x.invoice_status == '0')
			else:
				rec.allocation_line_ids = None

	@api.onchange('booking_id', 'start_date', 'end_date', 'invoice_type')
	def _compute_crm_line_ids(self):
		for rec in self:
			if rec.start_date and rec.end_date and rec.invoice_type:
				rec.crm_line_ids = rec.booking_id.crm_line_ids.filtered(lambda x:
																		x.allotted == False
																		and x.service_status != 3)
			else:
				rec.crm_line_ids = None

	def create_draft_payment_ehc(self):
		for rec in self:
			total = 0
			if rec.allocation_line_ids:
				for allocation_line in rec.allocation_line_ids:
					total += allocation_line.amount_paid
				rec.amount_total = total
			payment_type = {
				'1': 'inbound',
				'2': 'outbound',
			}
			journal_id = self.env['account.journal'].search(
				[('type', '=', 'cash'), ('company_id', '=', self.env.company.id)], limit=1)

			list_service_all = []
			list_service_no_price = []
			list_service_has_price = []
			for crm_line_id in rec.crm_line_ids:
				if crm_line_id.total:
					list_service_has_price.append(crm_line_id)
				else:
					list_service_no_price.append(crm_line_id)

			if list_service_has_price:
				for rec_service in list_service_has_price:
					# money_list_service_has_price += rec_service.total
					list_service_all.append((0, 0, {
						'crm_line_id': rec_service.id,
						# 'total_before_discount': rec_service.total,
						'prepayment_amount': rec_service.total,
					}))

			# money_list_service_has_price = 0
			# money_list_service_no_price = 0
			# if list_service_no_price:
			#     for rec_service in list_service_has_price:
			#         money_list_service_has_price += rec_service.total
			#         list_service_all.append((0, 0, {
			#             'crm_line_id': rec_service.id,
			#             # 'total_before_discount': rec_service.total,
			#             'prepayment_amount': rec_service.total,
			#         }))
			#     average_money_list_service_no_price = (rec.amount_total - money_list_service_has_price) / len(
			#         list_service_no_price)
			#     for rec_service in list_service_no_price:
			#         list_service_all.append((0, 0, {
			#             'crm_line_id': rec_service.id,
			#             'prepayment_amount': average_money_list_service_no_price,
			#         }))
			# else:
			#     pass
			self.env['account.payment'].create({
				'name': False,
				'partner_id': rec.booking_id.partner_id.id,
				'patient': False,
				'company_id': rec.booking_id.company_id.id,
				'currency_id': rec.booking_id.company_id.currency_id.id,
				'amount': round(rec.amount_total),
				'amount_vnd': round(rec.amount_total),
				'brand_id': rec.booking_id.brand_id.id,
				'crm_id': rec.booking_id.id,
				'communication': "Tổng hợp phiếu thu EHC",
				'text_total': self.num2words_vnm(int(rec.amount_total)) + " đồng",
				'partner_type': 'customer',
				'payment_type': payment_type['1'],
				'payment_date': datetime.now(),  # ngày thanh toán
				'date_requested': datetime.now(),  # ngày yêu cầu
				'payment_method_id': self.env['account.payment.method'].sudo().search(
					[('payment_type', '=', 'inbound')], limit=1).id,
				'journal_id': journal_id.id,
				'walkin': False,
				'service_ids': list_service_all,
				'statement_payment_ehc_ids': rec.allocation_line_ids,
			})


class SaleAllocationLine(models.TransientModel):
	_name = 'crm.ehc.sale.allocation.line'
	_description = 'Sale allocation line'

	allocation_id = fields.Many2one('crm.ehc.sale.allocation', string='Select Statement')
	invoice_code_ehc = fields.Char('Mã phiếu thu')
	invoice_date_ehc = fields.Datetime('Ngày thu')
	invoice_type_ehc = fields.Selection([('1', 'Thu tiền'), ('2', 'Hoàn tiền')])
	amount_paid_ehc = fields.Monetary('Số tiền thanh toán')
	invoice_method = fields.Selection([('1', 'Tiền mặt'), ('2', 'Chuyển khoản'), ('3', 'Ghi nợ'), ('4', 'POS')])
	currency_id = fields.Many2one('res.currency', string='Tiền tệ')


class InheritCRM(models.Model):
	_inherit = 'crm.lead'

	def open_form_sale_allocation_ehc(self):
		return {
			'name': 'Phân bổ doanh số EHC',
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'form',
			'view_id': self.env.ref('crm_ehc.view_form_crm_sale_allocation_ehc').id,
			'res_model': 'crm.ehc.sale.allocation',
			'context': {
				'default_partner_id': self.partner_id.id,
				'default_booking_id': self.id,
			},
			'target': 'new'
		}
