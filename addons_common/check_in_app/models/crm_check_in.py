# -*- coding: utf-8 -*-
#############################################################################
#
#    SCI SOFTWARE
#
#    Copyright (C) 2019-TODAY SCI Software(<https://www.scisoftware.xyz>)
#    Author: SCI Software(<https://www.scisoftware.xyz>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import logging

from odoo.exceptions import ValidationError
from odoo.tools.profiler import profile

from odoo import fields, models, api, _
import re
from datetime import datetime, timedelta, time
import qrcode

_logger = logging.getLogger(__name__)

STAGE = [
    ('cho_tu_van', 'Chờ tư vấn'),
    ('dang_tu_van', 'Đang tư vấn'),
    ('hoan_thanh', 'Kết thúc'),
    # ('huy', 'Hủy'),
]
DESIRE = [('tu_van', 'Tư vấn'),
          ('lam_luon', 'Làm luôn'),
          ('event', 'Tham gia sự kiện'), ('service', 'Thực hiện dịch vụ liệu trình'), ('eva', 'Tái khám'),
          ('maintenance', 'Bảo dưỡng dịch vụ')]
KNOW = [('internet', 'Internet (fb/gg/tiktok...)'),
        ('friend', 'Bạn bè người thân giới thiệu'),
        ('voucher', 'Voucher/quà tặng...'),
        ('signs', 'Biển hiệu chi nhánh')]


class CrmCheckInServiceCategory(models.Model):
    _name = "crm.check.in.service.category"
    _description = 'Nhóm dịch vụ check in'

    name = fields.Char('Tên')
    brand_id = fields.Many2one('res.brand', string="Thương hiệu")


class CrmCheckIn(models.Model):
    _name = 'crm.check.in'
    _description = 'Check in'
    _inherit = 'qrcode.mixin'

    name = fields.Char('Tên khách hàng')
    phone = fields.Char('Số điện thoại')
    year_of_birth = fields.Char('Năm sinh')
    date_of_birth = fields.Date('Ngày sinh')
    company_id = fields.Many2one('res.company', string='Chi nhánh checkin', default=lambda self: self.env.company)
    note = fields.Text('Mong muốn')
    desire = fields.Selection(DESIRE, string='Mong muốn')
    service_category_ids = fields.Many2many('crm.check.in.service.category', string='Nhóm dịch vụ quan tâm')
    partner = fields.Many2one('res.partner', string='Khách hàng')
    booking = fields.Many2one('crm.lead', string='Booking',
                              domain="[('partner_id', '=', partner), ('type', '=', 'opportunity')]")
    booking_company = fields.Many2one(related='booking.company_id', store=True, string='Chi nhánh Booking')
    booking_brand_id = fields.Many2one('res.brand', 'Thương hiệu Booking', related='booking_company.brand_id',
                                       store=True, )
    stage = fields.Selection(STAGE, string='Trạng thái', default='cho_tu_van')
    printed = fields.Boolean('Đã in')
    check_type = fields.Selection(
        [('co_so', 'Checkin cơ sở'), ('ctv', 'Checkin Cộng tác viên'), ('event', 'Checkin Event')],
        string='Loại Checkin', default=False)
    gender = fields.Selection([('male', 'Nam'), ('female', 'Nữ'), ('other', 'Khác')], string="Giới tính")
    check_did_service = fields.Boolean('Đã từng làm dịch vụ', default=False)
    qr_checkin = fields.Binary('QR', compute='_generate_qr_checkin')
    selection_type = fields.Selection([('booking', 'Booking'), ('phone', 'Điện thoại'), ('code', 'Mã khách hàng')],
                                      string="Bạn muốn nhập gì ?", default='booking')
    code_partner = fields.Char('Mã khách hàng')
    code_booking = fields.Char('Mã Booking')

    def _generate_qr_checkin(self):
        for item in self:
            item.qr_checkin = False
            base_url = '%s/web#id=%d&action=1547&view_type=form&model=%s' % (
                self.env['ir.config_parameter'].sudo().get_param('web.base.url'), item.id, item._name)
            item.qr_checkin = self.qrcode(base_url)

    know = fields.Selection(KNOW)

    @api.onchange('code_booking')
    def _onchange_code_booking(self):
        if self.code_booking:
            booking = self.env['crm.lead'].sudo().search([('name', '=', self.code_booking.replace(' ', '')), ('type', '=', 'opportunity')], order='booking_date desc', limit=1)
            if booking:
                self.booking = booking.id
                self.partner = booking.partner_id.id
                self.phone = booking.phone
                if 'BH' in booking.name:
                    self.desire = 'maintenance'
                else:
                    if booking.customer_come == 'no':
                        self.desire = 'tu_van'
            else:
                raise ValidationError('Mã %s không tồn tại hoặc đã hết hạn, hãy thử mã booking khác' % self.code_booking)

    @api.onchange('code_partner')
    def _onchange_code_partner(self):
        if self.code_partner:
            partner = self.env['res.partner'].sudo().search([('code_customer', '=', self.code_partner.replace(' ', ''))])
            if partner:
                domain_book = ['|', ('name', 'like', 'BH'), ('effect', '=', 'effect'), ('type', '=', 'opportunity'), ('partner_id', '=', partner.id)]
                booking = self.env['crm.lead'].sudo().search(domain_book, order='booking_date desc', limit=1)
                self.partner = partner.id
                self.phone = partner.phone
                if booking:
                    self.booking = booking.id
            else:
                raise ValidationError('Mã %s không tồn tại, hãy thử mã khách hàng khác' % self.code_booking)

    @api.onchange('phone')
    def _onchange_phone(self):
        if self.phone:
            partner = self.env['res.partner'].search([('phone', '=', self.phone)], limit=1)
            domain_book = ['|', ('name', 'like', 'BH'), ('effect', '=', 'effect'), ('type', '=', 'opportunity'), '|', '|',
                           ('phone', '=', self.phone),
                           ('mobile', '=', self.phone), ('phone_no_3', '=', self.phone)]
            booking = self.env['crm.lead'].sudo().search(domain_book, order='booking_date desc', limit=1)
            if partner:
                self.name = partner.name
                self.partner = partner.id
            else:
                self.name = False
                self.partner = False

            if booking:
                self.booking = booking.id
            else:
                self.booking = False

    @api.model
    def create(self, vals):
        res = super(CrmCheckIn, self).create(vals)
        if res:
            query = ''' select id from crm_lead cl where cl.stage_id = 4 and cl.phone = '%s' and cl.brand_id = %s limit 1''' % (
                res.phone, res.company_id.brand_id.id)
            self.env.cr.execute(query)
            result = self._cr.fetchall()
            if result:
                res.check_did_service = True
        return res

    @api.onchange('name')
    def upper_name(self):
        if self.name:
            self.name = self.name.upper()

    @api.onchange('date_of_birth')
    def onchange_date_of_birth(self):
        if self.date_of_birth:
            self.year_of_birth = self.date_of_birth.year

    def set_dang_tu_van(self):
        self.stage = 'dang_tu_van'

    def set_cho_tu_van(self):
        self.stage = 'cho_tu_van'

    def set_hoan_thanh(self):
        self.stage = 'hoan_thanh'

    def set_huy(self):
        self.stage = 'huy'

    def print_checkin(self):
        self.printed = True
        kangnam_brand = self.env.ref('sci_brand.res_brand_kn').id
        paris_brand = self.env.ref('sci_brand.res_brand_paris').id
        brand_id = self.company_id.brand_id.id

        if not self.booking:
            if brand_id == paris_brand:
                return self.env.ref('check_in_app.action_customer_info_checkin_pr').report_action(self)
            else:
                return self.env.ref('check_in_app.action_customer_info_checkin').report_action(self)
        else:
            if brand_id == paris_brand:
                return self.env.ref('crm_his_13.action_dentistry_sheet_new').report_action(self.booking.id)
            else:
                return self.env.ref('crm_his_13.action_service_info_sheet').report_action(self.booking.id)

    @api.model
    def toggle_tree_view_state(self):
        # Sử dụng Odoo API để chuyển đổi trạng thái hiển thị view
        view = self.env.ref('check_in_app.crm_check_in_list_tree_view')
        view.active = not view.active
        return True

    def view_booking(self):
        return {
            'name': 'Xem Booking',  # label
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': self.env.ref('crm_base.crm_lead_form_booking').id,
            'res_model': 'crm.lead',
            'target': '_blank',
            'res_id': self.booking.id
        }

    def create_booking(self):
        return {
            'name': 'Tạo Booking',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('check_in_app.create_booking_form_view').id,
            'res_model': 'create.booking',
            'context': {
                'default_partner_id': self.partner.id,
                'default_checkin_id': self.id,
                'default_booking_date': self.create_date,
                'default_company_id': self.company_id.id,
                'default_phone': self.partner.phone if self.partner else self.phone,
                'default_year_of_birth': self.partner.year_of_birth if self.partner else self.year_of_birth,
                'default_country_id': self.partner.country_id.id if self.partner else 241,
                'default_state_id': self.partner.state_id.id if self.partner else False,
                'default_district_id': self.partner.district_id.id if self.partner else False,
                'default_street': self.partner.street if self.partner else False,
                'default_gender': self.partner.gender if self.partner else False,
                'default_birth_date': self.partner.birth_date if self.partner else self.date_of_birth,
                'default_mobile': self.partner.mobile if self.partner else False,
                'default_phone_no_3': self.partner.phone_no_3 if self.partner else False,
                'default_name': self.partner.name if self.partner else self.name,
                'default_note': 'NHÓM DỊCH VỤ QUAN TÂM: %s' % ', '.join(self.service_category_ids.mapped('name')),

            },
            'target': 'new',
        }

    # def data_print(self):
    #     data = {
    #         'name': self.name,
    #         'phone': self.phone,
    #     }
    #     if self.desire == 'tu_van':
    #         data.update({'desire': 'Tư vấn'})
    #     else:
    #         data.update({'desire': 'Làm luôn'})
    #     if self.service_category_ids:
    #         data.update({'service_category_ids': self.service_category_ids.mapped('name')})
    #     return data

    # @profile
    @api.model
    def attendance_scan(self, url, check_type):
        """ Receive a barcode scanned from the Kiosk Mode and change the attendances of corresponding employee.
            Returns either an action or a warning.
        """
        now = datetime.now()
        today = now.date()
        if check_type:
            if 'model=crm.lead' in url:
                id_match = re.search(r"id=([^&]+)", url)
                lead_id = id_match.group(1)
                booking = self.env['crm.lead'].sudo().browse(int(lead_id))
                if booking:
                    if booking.effect == 'effect' or 'BH' in booking.name:
                        check_in = self.sudo().search([('booking', '=', booking.id), (
                            'create_date', '>=', datetime.combine(today, time(0, 0, 0)) - timedelta(hours=7)),
                                                       ('create_date', '<=',
                                                        datetime.combine(today, time(23, 59, 59)) - timedelta(
                                                            hours=7))], limit=1)
                        if check_in:
                            return {'warning': "Khách hàng này đã đến cửa"}
                        else:
                            check_in = self.sudo().create({
                                'name': booking.partner_id.name,
                                'phone': booking.partner_id.phone,
                                'booking_company': booking.company_id.id,
                                'company_id': self.env.company.id if self.env.company else '',
                                'booking': booking.id,
                                'partner': booking.partner_id.id,
                                'check_type': check_type,
                                'stage': 'cho_tu_van'})
                            if booking.customer_come == 'yes':
                                pass
                            else:
                                check_in.write({'desire': 'maintenance' if 'BH' in booking.name else 'tu_van'})
                                stage_not_confirm = self.env.ref('crm_base.crm_stage_not_confirm').id
                                stage_confirm = self.env.ref('crm_base.crm_stage_confirm').id
                                stage_no_come = self.env.ref('crm_base.crm_stage_no_come').id
                                query = """update crm_lead set customer_come = 'yes',arrival_date = '%s'""" % datetime.now().strftime(
                                    '%Y-%m-%d %H:%M:%S')
                                if booking.stage_id.id == int(stage_not_confirm) or booking.stage_id.id == int(
                                        stage_no_come):
                                    query += """, stage_id = %s where id = %s""" % (stage_confirm, lead_id)
                                else:
                                    query += """where id = %s""" % lead_id
                                self._cr.execute(query)
                            return {'success': "Check in thành công"}
                    else:
                        return {'warning': "Booking này đã hết hiệu lực"}
                return {'warning': _('Không tìm thấy mã Booking của QR CODE')}
            else:
                return {'warning': _('QR CODE không hợp lệ')}
        else:
            return {'warning': _('Bạn chưa chọn kiểu checkin mong muốn')}

    def view_information_partner(self):
        if self.partner:
            return {
                'name': 'Xem thông tin khách hàng',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'view_id': self.env.ref('base.view_partner_form').id,
                'res_model': 'res.partner',
                'res_id': self.partner.id
            }
