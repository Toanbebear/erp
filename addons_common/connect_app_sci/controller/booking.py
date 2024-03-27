import datetime
import logging

from odoo.addons.restful.controllers.app_member.app_member_common import response
from odoo.addons.restful.common import get_redis
from odoo.addons.connect_app_sci.controller.app_sci_common import validate_token, response, get_user_by_token, \
    extract_arguments
from odoo.http import request
import json

r = get_redis()
from odoo import http

phan_loai = {
    '1': {
        'name': 'Bình thường',
        'color': '#5EC269'
    },
    '2': {
        'name': 'Quan tâm',
        'color': '#17a2b8'
    },
    '3': {
        'name': 'Quan tâm hơn',
        'color': '#ffc107'
    },
    '4': {
        'name': 'Đặc biệt',
        'color': '#dc3545'
    },
    '5': {
        'name': 'Khác hàng V.I.P',
        'color': '#7C7BAD'
    }
}

effect = {
    'not_valid': 'Chưa hiệu lực',
    'effect': 'Hiệu lực',
    'expire': 'Hết hiệu lực'
}
customer_come = {
    'yes': 'Có',
    'no': 'Không'
}
overseas_vietnamese = {
    'no': 'Không',
    'marketing': 'Marketing - Việt kiều',
    'branch': 'Chi nhánh - Việt kiều'

}
type_partner = {
    'old': 'Khách hàng cũ',
    'new': 'Khách hàng mới'
}
_logger = logging.getLogger(__name__)
api_access_database = "restful.api_access_database"
expires_in = "restful.access_token_expires_in"
r = get_redis()


class BookingUser(http.Controller):
    @http.route("/api/list-booking-today", methods=["GET"], type="json", auth="none", csrf=False)
    @validate_token
    def v1_get_list_booking(self, **payload):
        body = json.loads(request.httprequest.data.decode('utf-8'))
        limit = body['limit']
        offset = body['offset']
        booking_today = []
        is_detail = True
        now = datetime.datetime.now().strftime('%Y/%m/%d 00:00:00')
        now_1 = datetime.datetime.now().strftime('%Y/%m/%d 23:59:59')
        today = datetime.datetime.strptime(now, '%Y/%m/%d 00:00:00')
        today_1 = datetime.datetime.strptime(now_1, '%Y/%m/%d %H:%M:%S')
        token = request.httprequest.headers.get('Authorization')
        # user = get_user_by_token(token)
        # user_group = user.groups_id
        # model_access = user_group.model_access
        key = 'list_booking_' + today.strftime("%d-%m-%Y") + '_' + str(limit) + '_' + str(offset)
        if r:
            list_bookings = r.get(key)
            if list_bookings:
                return {
                    'stage': 0,
                    'message': 'Thanh cong ',
                    'data': json.loads(list_bookings)
                }
        list_booking_today = request.env['crm.lead'].sudo().search(
            [('booking_date', '>=', today - datetime.timedelta(hours=7)),
             ('booking_date', '<=', today_1 - datetime.timedelta(hours=7))], limit=limit,
            offset=offset)
        for rec in list_booking_today:
            value = {
                'id': rec.id,
                'is_detail': is_detail,
                'name': rec.partner_id.name,
                'phone': rec.phone,
                'time': (rec.booking_date + datetime.timedelta(hours=7)).strftime(
                    "%d/%m/%Y %H:%M:%S") if rec.booking_date else None,
                'type': {
                    'id': rec.customer_classification,
                    'name': phan_loai[rec.customer_classification]['name'] if rec.customer_classification else None,
                    'color': phan_loai[rec.customer_classification]['color'] if rec.customer_classification else None,
                },
                'status': {
                    'id': rec.stage_id.id,
                    'name': rec.stage_id.name,
                    'color': '#aeafb0'
                }
            }
            booking_today.append(value)
        if booking_today != []:
            if r:
                r.setex(key, 86400000, json.dumps(booking_today))
            return {
                'stage': 0,
                'message': 'Thanh cong',
                'data': booking_today
            }
        else:
            return {
                'stage': 1,
                'message': 'That bai',
                'data': None
            }

    # Chi tiết booking
    @http.route("/api/detail-booking", methods=["GET"], type="json", auth="none", csrf=False)
    def v1_get_detail_booking(self, **payload):
        is_edit = True
        body = json.loads(request.httprequest.data.decode('utf-8'))
        booking_id = body['booking_id']
        key = 'detail_booking_id_' + str(booking_id)
        if r:
            detail = r.get(key)
            if detail:
                _logger.info('Co du lieu trong redis')
                return {
                    'stage': 0,
                    'message': 'Thanh cong !',
                    'data': json.loads(detail)
                }
        booking = request.env['crm.lead'].sudo().browse(booking_id)
        data = {
            'status': {
                'name': booking.stage_id.name,
                'color': '#003471'
            },
            'code_booking': booking.name,
            'type': {
                'id': booking.customer_classification,
                'name': phan_loai[booking.customer_classification]['name'] if booking.customer_classification else None,
                'color': phan_loai[booking.customer_classification][
                    'color'] if booking.customer_classification else None,
            },
            'is_edit': is_edit,
            'is_collection_refund': True,
            'is_deep_discounts': True,
            'is_apply_coupon': True,
            'is_apply_voucher': True,
            'list_info': [
                {
                    'title': 'Thông tin khách hàng',
                    'fields': [
                        {
                            'label_text': 'Tên liên hệ',
                            'value': booking.contact_name if booking.contact_name else None
                        },
                        {
                            'label_text': 'Điện thoại 1',
                            'value': booking.phone if booking.phone else None
                        },
                        {
                            'label_text': 'Điện thoại 2',
                            'value': booking.mobile if booking.mobile else None
                        },
                        {
                            'label_text': 'Điện thoại 3',
                            'value': booking.phone_no_3 if booking.phone_no_3 else None
                        },
                        {
                            'label_text': 'Thẻ thành viên',
                            'value': booking.loyalty_id.name if booking.loyalty_id.name else None
                        },
                        {
                            'label_text': 'Lead/Booking',
                            'value': booking.lead_id.name if booking.lead_id.name else None
                        },
                        {
                            'label_text': 'Việt kiều',
                            'value': overseas_vietnamese[
                                booking.overseas_vietnamese] if booking.overseas_vietnamese else None
                        },
                        {
                            'label_text': 'Giới tính',
                            'value': booking.partner_id.name if booking.partner_id.name else None
                        },
                        {
                            'label_text': 'Ngày/tháng/năm sinh',
                            'value': booking.partner_id.birth_date.strftime(
                                "%d/%m/%Y") if booking.partner_id.birth_date else None
                        }
                    ]

                },
                {
                    'title': 'Thông tin cá nhân',
                    'fields': [
                        {
                            'label_text': 'CMTND/CCCD',
                            'value': booking.pass_port if booking.pass_port else None
                        },
                        {
                            'label_text': 'Ngày cấp',
                            'value': booking.pass_port_date.strftime("%d/%m/%Y") if booking.pass_port_date else None
                        },
                        {
                            'label_text': 'Nơi cấp',
                            'value': booking.pass_port_issue_by if booking.pass_port_issue_by else None
                        },
                        {
                            'label_text': 'Quốc gia',
                            'value': booking.country_id.name if booking.country_id.name else None
                        },
                        {
                            'label_text': 'Tỉnh/TP',
                            'value': booking.state_id.name if booking.state_id.name else None
                        },
                        {
                            'label_text': 'Quận/Huyện',
                            'value': booking.district_id.name if booking.district_id.name else None
                        },
                        {
                            'label_text': 'Phường/Xã',
                            'value': booking.ward_id.name if booking.ward_id.name else None
                        },
                        {
                            'label_text': 'Địa chỉ chi tiết',
                            'value': booking.street if booking.street else None
                        },
                    ]
                },
                {
                    'title': 'Thông tin booking',
                    'fields': [
                        {
                            'label_text': 'Loại khách hàng',
                            'value': type_partner[booking.type_data_partner] if booking.type_data_partner else None,
                        },
                        {
                            'label_text': 'Ngày hẹn lịch',
                            'value': booking.booking_date.strftime(
                                "%d/%m/%Y %H:%M:%S") if booking.booking_date else None,
                        },
                        {
                            'label_text': 'Trạng thái hiệu lực',
                            'value': effect[booking.effect] if booking.effect else None,
                        },
                        {
                            'label_text': 'Hiệu lực đến ngày',
                            'value': booking.day_expire.strftime("%d/%m/%Y %H:%M:%S") if booking.day_expire else None,
                        },
                        {
                            'label_text': 'Khách hàng đến cửa',
                            'value': customer_come[booking.customer_come] if booking.customer_come else None,
                        },
                        {
                            'label_text': 'Chi nhánh',
                            'value': booking.company_id.name if booking.company_id.name else None,
                        },
                        {
                            'label_text': 'Thương hiệu',
                            'value': booking.brand_id.name if booking.brand_id.name else None,
                        },
                        {
                            'label_text': 'Bảng giá',
                            'value': booking.price_list_id.name if booking.price_list_id.name else None,
                        },
                        {
                            'label_text': 'Share booking',
                            'value': booking.company2_id.name if booking.company2_id.name else None,
                        },
                        {
                            'label_text': 'Tiền tệ',
                            'value': booking.currency_id.name if booking.currency_id.name else None,
                        }
                    ]
                },
                {
                    'title': 'Marketing',
                    'fields': [
                        {
                            'label_text': 'Nguồn ban đầu',
                            'value': booking.original_source_id.name if booking.original_source_id.name else None,
                        },
                        {
                            'label_text': 'Nhóm nguồn',
                            'value': booking.category_source_id.name if booking.category_source_id.name else None
                        },
                        {
                            'label_text': 'Nguồn booking',
                            'value': booking.source_id.name if booking.source_id.name else None
                        },
                        {
                            'label_text': 'Tên CTV',
                            'value': booking.collaborators_id.name if booking.collaborators_id.name else None
                        },
                        {
                            'label_text': 'Chiến dịch',
                            'value': booking.campaign_id.name if booking.campaign_id.name else None
                        },
                        {
                            'label_text': 'Giữ CTKM',
                            'value': booking.kept_coupon.id if booking.kept_coupon.id else None
                        },
                        {
                            'label_text': 'Giữ chiến dịch',
                            'value': booking.kept_campaign.name if booking.kept_campaign.name else None
                        }
                    ]
                }
            ]
        }
        if data:
            if r:
                r.setex(key, 86400000, json.dumps(data))
            return {
                'stage': 0,
                'message': 'Thanh cong !',
                'data': data
            }
        else:
            return {
                'stage': 0,
                'message': 'Thất bại !',
                'data': None
            }

    # danh sách + tìm kiếm booking
    @http.route("/api/list-booking", methods=["GET"], type="json", auth="none", csrf=False)
    def v1_get_search_booking(self, **payload):
        list_search_booking = []
        domain = []
        is_detail = True
        body = json.loads(request.httprequest.data.decode('utf-8'))
        now = datetime.datetime.now().strftime('%Y/%m/%d 00:00:00')
        now_1 = datetime.datetime.now().strftime('%Y/%m/%d 23:59:59')
        today = datetime.datetime.strptime(now, '%Y/%m/%d 00:00:00')
        today_1 = datetime.datetime.strptime(now_1, '%Y/%m/%d %H:%M:%S')
        domain.append(('type', '=', 'opportunity'))
        for key, value in body.items():
            if key == 'limit':
                limit = int(value)
            if key == 'offset':
                offset = int(value)
            if key == 'booking_date':
                date_start = value + " 00:00:00"
                date_end = value + " 23:59:59"
                booking_date_start = datetime.datetime.strptime(date_start, '%d/%m/%Y 00:00:00')
                booking_date_end = datetime.datetime.strptime(date_end, '%d/%m/%Y %H:%M:%S')
                domain.append(('booking_date', '>=', booking_date_start))
                domain.append(('booking_date', '<=', booking_date_end))
            if key == 'contact_name':
                domain.append((key, 'ilike', value))
            if key not in ('limit', 'offset', 'booking_date', 'contact_name'):
                domain.append((key, '=', value))
        list_booking = request.env['crm.lead'].sudo().search(domain, limit=limit, offset=offset)
        for rec in list_booking:
            value = {
                'id': rec.id,
                'is_detail': is_detail,
                'name': rec.partner_id.name,
                'phone': rec.phone,
                'time': (rec.booking_date + datetime.timedelta(hours=7)).strftime(
                    "%d/%m/%Y %H:%M:%S") if rec.booking_date else None,
                'type': {
                    'id': rec.customer_classification,
                    'name': phan_loai[rec.customer_classification]['name'] if rec.customer_classification else None,
                    'color': phan_loai[rec.customer_classification]['color'] if rec.customer_classification else None,
                },
                'status': {
                    'id': rec.stage_id.id if rec.stage_id.id else None,
                    'name': rec.stage_id.name if rec.stage_id.name else None,
                    'color': '#aeafb0'
                }
            }
            list_search_booking.append(value)
        if list_search_booking:
            return {
                'stage': 0,
                'message': 'Thanh cong',
                'data': list_search_booking
            }
        else:
            return {
                'stage': 1,
                'message': 'That bai',
                'data': None
            }

    # api thông tin màn giảm giá sâu
    @http.route("/api/deep-discount", methods=["GET"], type="json", auth="none", csrf=False)
    def v1_get_deep_discount(self, **payload):
        body = json.loads(request.httprequest.data.decode('utf-8'))
        booking_id = body['booking_id']
        discount_review = request.env['discount.review'].sudo().search([('booking_id', '=', booking_id)], limit=1)
        reason = [
            {
                'id': 1,
                'name': 'Chi nhánh - KH Bảo hành'
            },
            {
                'id': 2,
                'name': 'Chi nhánh - KH Đối ngoại BGĐ Bệnh viện/Chi nhánh'
            },
            {
                'id': 3,
                'name': 'Chi nhánh - KH Đối ngoại Ban Tổng GĐ Tập đoàn'
            },
            {
                'id': 4,
                'name': 'Chi nhánh - Thuê phòng mổ'
            },
            {
                'id': 5,
                'name': 'Chi nhánh - Theo phân quyền Quản lý'
            },
            {
                'id': 6,
                'name': 'MKT - KH từ nguồn Seeding'
            },
            {
                'id': 7,
                'name': 'MKT - KH trải nghiệm dịch vụ'
            },
            {
                'id': 8,
                'name': 'MKT - KH đồng ý cho dùng hình ảnh truyền thông'
            },
            {
                'id': 9,
                'name': 'MKT – Theo phân quyền Quản lý'
            },
            {
                'id': 10,
                'name': 'SCI - Áp dụng chế độ Người nhà/CBNV (chưa có Coupon)'
            },
            {
                'id': 11,
                'name': 'SCI - Hệ thống chưa có Coupon theo CTKM đang áp dụng'
            },
            {
                'id': 12,
                'name': 'Khác (Yêu cầu ghi rõ lý do)'
            },
            {
                'id': 13,
                'name': 'SCI_Chương trình thiện nguyện/Hoạt động của Tập đoàn'
            }
        ]
        limited_discount = []
        key = 'deep_discount_booking_' + str(booking_id)
        if r:
            deep_discount = r.get(key)
            if deep_discount:
                return {
                    'stage': 0,
                    'message': 'Thành công !',
                    'data': json.loads(deep_discount)
                }
        rule_discount = request.env['crm.rule.discount'].sudo().search([])
        for rec in rule_discount:
            discount = {
                'id': rec.id,
                'name': rec.name
            }
            limited_discount.append(discount)
        discount_for = [
            {
                'id': 'booking',
                'name': 'Dịch vụ'
            },
            {
                'id': 'so',
                'name': 'Đơn hàng'
            }
        ]
        booking = request.env['crm.lead'].sudo().browse(booking_id)
        list_service = []
        if booking.crm_line_ids:
            for service in booking.crm_line_ids:
                list_service.append({
                    'id': service.service_id.id,
                    'name': service.service_id.name
                })
        list_product = []
        if booking.crm_line_product_ids:
            for product in booking.crm_line_product_ids:
                list_product.append({
                    'id': product.product_id.id,
                    'name': product.product_id.name
                })
        type_discount = [
            {
                'id': 'discount_pr',
                'name': 'Giảm giá phần trăm'
            },
            {
                'id': 'discount_cash',
                'name': 'Giảm giá tiền mặt'
            }
        ]
        value = {
            'reason': reason,
            'code': booking.name,
            'name': booking.partner_id.name,
            'limited_discount': limited_discount,
            'discount_for': discount_for,
            'service': list_service if list_service else None,
            'line_product': list_product if list_product else None,
            'type_discount': type_discount
        }
        if value:
            if r:
                r.setex(key, 86400000, json.dumps(value))
            return {
                'stage': 0,
                'message': 'Thành công !',
                'data': value
            }
        else:
            return {
                'stage': 1,
                'message': 'Không có dữ liệu',
                'data': None
            }
