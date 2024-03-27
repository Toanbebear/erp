import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class ProductEHC(models.Model):
	_inherit = 'product.product'

	# thông tin cho dịch vụ EHC
	service_id_ehc = fields.Integer('ID dịch vụ EHC')
	service_code_ehc = fields.Char('Mã dịch vụ EHC')
	service_price_bhyt = fields.Monetary('Giá BHYT')
	service_code_bhyt = fields.Char('Mã BHYT')
	service_type = fields.Char('Loại phẫu thuật')
	service_unit = fields.Char('Đơn vị tính')
	# service_room_id = fields.Many2one('crm.hh.ehc.department', string='Phòng')
	service_room_ids = fields.Many2many('crm.hh.ehc.department', 'crm_hh_ehc_department_prd_prd_rel', 'service_id', 'room_id',
										string='Phòng thực hiện')
	stage = fields.Selection([('0', 'Đang hoạt động'), ('1', 'Không hoạt động')])

	# thông tin cho thuốc - vật tư EHC
	material_id = fields.Integer('ID th/vt EHC')
	master_id = fields.Integer('Master ID')
	group_id = fields.Integer('Group ID')
	material_code = fields.Char('ID th/vt EHC')
	material_unit = fields.Char('Đơn vị tính')
	material_content = fields.Char('Hàm lượng')
	material_category = fields.Selection([('1', 'Bán lẻ'), ('0', 'Sử dụng trong bệnh viện')])
	material_specifications = fields.Char('Quy cách')
	material_route_of_use = fields.Char('Đường dùng')
	material_brand_name = fields.Char('Biệt dược')
	material_active_ingredient = fields.Char('Tên hoạt chất')
	type_material_ehc = fields.Selection([('th', 'Thuốc'), ('vt', 'Vật tư')])

	# phân loại dịch vụ
	vs_hm = fields.Boolean('VSHM', default=False)
	pttm = fields.Boolean('PTTM', default=False)
	da_khoa = fields.Boolean('DAKHOA', default=False)