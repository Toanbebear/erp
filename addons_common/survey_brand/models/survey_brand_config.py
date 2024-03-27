from datetime import timedelta
import requests

from odoo import models, fields
import logging


_logger = logging.getLogger(__name__)


class SurveyBrandConfig(models.Model):
    _name = 'survey.brand.config'
    _description = 'Cấu hình khảo sát'
    _rec_name = 'brand_id'
    _inherits = {
        'res.brand': 'brand_id',
    }

    brand_id = fields.Many2one('res.brand', ondelete="cascade", required=True)
    survey_sms = fields.Text(string='Nội dung gửi',
                             help="Nội dung sẽ gửi cho khách hàng, [LINK] sẽ được thay thế bằng link của khảo sát cho khách hàng, [NAME] sẽ được thay thế bằng tên khách hàng")

    survey_brand_url = fields.Char(string='Url của thương hiệu',
                                   help="Url của thương hiệu, vd: https://khaosat.benhvienthammykangnam.vn")

    survey_brand_user = fields.Char(string='Tên đăng nhập',
                                    help="Tài khoản đăng nhập vào trang khảo sát của thương hiệu")

    survey_brand_password = fields.Char(string='Mật khẩu',
                                        help="Mật khẩu đăng nhập")

    survey_brand_token = fields.Char(string='Token API', help="Token để kết nối với khảo sát thương hiệu")
    survey_brand_expires = fields.Datetime(string="Thời điểm hết hạn token")
    is_remove_vietnamese = fields.Boolean(string='Loại bỏ dấu trong tên khách hàng', default=True,
                                          help='Loại bỏ dấu tiếng Việt khỏi tên khách hàng [NAME], giúp tăng ký tự trong nội dung tin nhắn')

    _sql_constraints = [('brand_unique', 'unique(brand_id)', "Thương hiệu đã được cấu hình! Vui lòng kiểm tra lại")]

    def action_get_token_survey(self):
        url = self.survey_brand_url + "api/auth/token"
        login = self.survey_brand_user
        password = self.survey_brand_password
        data = {
            'login': login,
            'password': password
        }
        response = requests.get(url, data=data)
        response = response.json()
        token = response['access_token']
        self.survey_brand_token = token
        self.survey_brand_expires = fields.datetime.now() + timedelta(seconds=int(response['expires_in']))

    def get_link_survey(self, survey_id, phone, name, partner_id, group_service, time, booking, walkin, evaluation, phone_call, user):
        token = self.survey_brand_token
        url = self.survey_brand_url + 'api/v1/get-link-survey'
        headers = {
            'Authorization': token
        }
        data = {
            'survey_id': survey_id,
            'partner_phone': phone,
            'partner_name': name,
            'group_service_id': group_service,
            'time': time,
            'booking_id': booking,
            'walkin_id': walkin,
            'evaluation_id': evaluation,
            'phone_call_id': phone_call,
            'user_id': user
        }
        self.env['api.log'].sudo().create({
            "name": "Tạo link survey",
            "type_log": False,
            "model_id": False,
            "id_record": False,
            "input": data,
            "response": False,
            "url": False,
            "status_code": False,
            "header": False,
        })
        link = ''
        response = requests.get(url, headers=headers, data=data)
        response = response.json()
        if response['status'] == 0:
            data = response['data']
            if 'url' in data:
                link = data['url']
        return link
