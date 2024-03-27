import json
import logging
from datetime import datetime

import pytz
from dateutil.relativedelta import relativedelta

from odoo import models, fields

_logger = logging.getLogger(__name__)

TEMPLATE_QUALITY = [('hight', 'HIGH'), ('medium', 'MEDIUM'), ('low', 'LOW'), ('undefined', 'UNDEFINED')]
TEMPLATE_TAG = [('OTP', 'OTP'), ('IN_TRANSACTION', 'Xác nhận/Cập nhật giao dịch'),
                ('POST_TRANSACTION', 'Hỗ trợ dịch vụ liên quan sau giao dịch'),
                ('ACCOUNT_UPDATE', 'Cập nhật thông tin tài khoản'), ('GENERAL_UPDATE', 'Thay đổi thông tin dịch vụ'),
                ('FOLLOW_UP', 'Thông báo ưu đãi đến khách hàng cũ')]


class CRMZaloZNSTemplate(models.Model):
    _name = 'crm.zalo.zns.template'
    _description = 'Zalo ZNS Template'

    template_id = fields.Interger(string='Template ID')
    template_name = fields.Char(string='Tên template')
    status = fields.Char(string='Trạng thái')
    timeout = fields.Char(string='Thời gian timeout')
    preview_url = fields.Char(string='Url xem trước template')
    template_quality = fields.Selection(TEMPLATE_QUALITY, string='Chất lượng gửi tin',
                                        help='Trường hợp chất lượng gửi tin hiện tại của template là Low thì template có khả năng bị khóa')
    template_tag = fields.Selection(TEMPLATE_TAG, string='Loại nội dung')
    price = fields.Char(string='Đơn giá')
    apply_template_quota = fields.Boolean(string='Quá hạn mức Daily Quota', default=False,
                                          help='Hạn mức Daily Quota chỉ áp dụng cho một số template đặc biệt mang tính thử nghiệm và đã trực tiếp được đăng ký với Zalo. Các template bình thường sẽ không bị ảnh hưởng bởi giới hạn này')
    template_daily_quota = fields.Char(string='Số tin ZNS được phép gửi trong ngày',
                                       help='Trường thông tin này chỉ được trả về khi trường Quá hạn mức Daily Quota được tích')
    template_remaining_quota = fields.Char(string='Số tin ZNS được gửi trong ngày còn lại',
                                           help='Trường thông tin này chỉ được trả về khi trường Quá hạn mức Daily Quota được tích')

    zns_param_ids = fields.One2many('crm.zalo.zns.template.param', 'template_id', string='Danh sách param')


class CRMZaloZNSTemplateParam(models.Model):
    _name = 'crm.zalo.zns.template.param'
    _description = 'Template parameter'

    template_id = fields.Many2one('crm.zalo.zns.template', string='Template ZNS')
    name = fields.Char(string='Tên thuộc tính')
    require = fields.Boolean(string='Tính bắt buộc', default=False)
    type = fields.Char(string='Định dạng validate')
    max_length = fields.Integer(string='Số kí tự tối đa được truyền vào')
    min_length = fields.Integer(string='Số kí tự tối thiểu được truyền vào')
    accept_null = fields.Boolean(string='Có thể gửi giá trị rỗng')
