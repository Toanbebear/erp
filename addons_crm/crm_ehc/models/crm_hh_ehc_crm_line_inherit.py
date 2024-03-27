import logging

from odoo import fields, api, models

_logger = logging.getLogger(__name__)

SERVICE_OBJECT = [('0', 'Thu tiền'), ('1', 'Không thu tiền')]
SERVICE_STATUS = [('0', 'Đã chỉ định'), ('1', 'Đang thực hiện'), ('2', 'Đã trả kết quả'), ('3', 'Hủy')]


class ServiceDepartmentEHC(models.Model):
	_inherit = "crm.line"

	key_data_master = fields.Integer('Key data master EHC')
	key_data = fields.Integer('Key data EHC')
	service_order_form_id = fields.Char('ID phiếu chỉ định dịch vụ EHC')
	service_order_form_code = fields.Char('Code phiếu chỉ định dịch vụ EHC')
	service_object = fields.Selection(SERVICE_OBJECT, 'Đối tượng')

	service_designated_date = fields.Date('Ngày chỉ định')
	service_date = fields.Date('Ngày thực hiện')
	service_result_day = fields.Date('Ngày trả kết quả')

	service_designator = fields.Many2one('crm.hh.ehc.user', 'Người chỉ định')
	service_executor = fields.Many2one('crm.hh.ehc.user', 'Người thực hiện')
	service_result_payer = fields.Many2one('crm.hh.ehc.user', 'Người trả kết quả')

	service_designated_room = fields.Many2one('crm.hh.ehc.department', 'Phòng chỉ định')
	service_implementation_room = fields.Many2one('crm.hh.ehc.department', 'Phòng thực hiện')
	service_result_room = fields.Many2one('crm.hh.ehc.department', 'Phòng trả kết quả')

	service_status = fields.Selection(SERVICE_STATUS, 'Trạng thái dịch vụ')

	allotted = fields.Boolean('Đã phân bổ', default=False)

	is_hh = fields.Boolean('Brand Hồng Hà', compute='check_hh', default=False, store=True)

	create_phone_call = fields.Boolean('Tạo PC', default=False)

	source_payment = fields.Selection([('0', 'Khách hàng'), ('1', 'Hợp đồng')], string='Nguồn thanh toán')

	@api.depends('company_id')
	def check_hh(self):
		for rec in self:
			rec.is_hh = True if rec.company_id.brand_id.code == "HH" else False
