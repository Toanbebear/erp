# -*- coding: utf-8 -*- 

import datetime
import logging

import pytz
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)
DATETYPE = [('days', 'Ngày'), ('months', 'tháng'), ('years', 'năm')]

import base64
from odoo.modules.module import get_module_resource


class Department(models.Model):
    _inherit = ['hr.department']

    device_ids = fields.One2many('sci.device.main', 'department_id', string='Thiết bị')


class MainDevice(models.Model):
    _name = 'sci.device.main'
    _description = 'Main Device'
    _inherit = ['sci.device', 'image.mixin', 'qrcode.mixin']

    @api.model
    def _default_image(self):
        image_path = get_module_resource('sci_device', 'static/img', 'default_image.png')
        return base64.b64encode(open(image_path, 'rb').read())

    default_code = fields.Char('Mã thiết bị', size=50, required=True)
    name = fields.Char('Tên vật tư', size=255, required=True)
    name_print = fields.Char('Tên in QR', size=38)
    type_device = fields.Selection(
        [('TSCD', 'Tài sản cố định'), ('CCDC', 'Công cụ dụng cụ'), ('CPTT', 'Chi phí trả trước')],
        'Loại tài sản', required=True, default='TSCD')
    quantity = fields.Integer('Số lượng', default=1)
    company_id = fields.Many2one('res.company', 'Company', index=True, default=lambda self: self.env.company)
    department_id = fields.Many2one('hr.department', 'Phòng ban sử dụng', domain="[('company_id', '=', company_id)]")
    parent_id = fields.Many2one('hr.employee', 'Quản lý', related='department_id.manager_id')
    employee_id = fields.Many2one('hr.employee', string="Người sử dụng",
                                  domain="[('department_id', 'child_of', department_id)]")
    partner_id = fields.Many2one('res.partner', string='Nhà cung cấp', domain="[('supplier_rank', '=', 1)]")
    description_images_ids = fields.One2many('sci.device.image', 'main_device_id', string='Hình ảnh mô tả')
    extra_device_ids = fields.One2many('sci.device.extra', 'main_device_id', 'Thiết bị phụ tùng')
    count_extra_device = fields.Integer('Quantity Of Extra Devices', compute="_compute_quantity_of_extra_device")
    serial_no = fields.Char('Serial Number')
    root_department = fields.Many2one('res.brand', string='Khối (Thương hiệu)', related='company_id.brand_id',
                                      store=True)
    image_1920 = fields.Image(default=_default_image)

    # Bảo dưỡng
    last_maintenance = fields.Date('Bảo dưỡng lần cuối', readonly="1")
    maintenance_deadline = fields.Integer('Thời hạn bảo dưỡng', size=3, track_visibility="onchange")
    maintenance_deadline_type = fields.Selection(DATETYPE, 'Date Type', default="months", required=True,
                                                 track_visibility="onchange")
    maintenance_deadline_display = fields.Char('Thời hạn bảo dưỡng', compute="_compute_deadline_display")
    maintenance_status = fields.Text('Tình trạng', compute="_compute_status", compute_sudo=False)
    maintenance_expire_date = fields.Date('Ngày đến hạn', compute="_compute_status", compute_sudo=False,
                                          store=True)  # Ngày đến hạn bảo dưỡng

    qr_image = fields.Binary("QR Code", compute='_generate_qr_code')
    _sql_constraints = [('unique_code', 'unique(default_code)', 'Mã đã tồn tại!!.')]

    def name_get(self):
        # Prefetch the fields used by the `name_get`, so `browse` doesn't fetch other fields
        return [(template.id, '%s%s' % (template.default_code and '[%s] ' % template.default_code or '', template.name))
                for template in self]

    def _generate_qr_code(self):
        for item in self:
            base_url = '%s/web#id=%d&view_type=form&model=%s' % (
                self.env['ir.config_parameter'].sudo().get_param('web.base.url'),
                item.id,
                item._name)
            item.qr_image = self.qrcode(base_url)

    @api.onchange('name')
    def _onchange_name(self):
        if not self.name_print:
            self.name_print = self.name

    @api.onchange('department_id')
    def _onchange_department(self):
        self.parent_id = self.department_id.manager_id

    @api.depends('extra_device_ids')
    def _compute_quantity_of_extra_device(self):
        for record in self:
            record.count_extra_device = len(record.extra_device_ids)

    def get_extra_device_in_main_device(self):
        action = self.env.ref('sci_device.act_sci_device_extra_view').read()[0]
        if self:
            action['display_name'] = self.display_name
            action['context'] = {'search_default_main_device_id': self.id}
        return action

    @api.onchange('department_id')
    def _onchange_category(self):
        self.employee_id = None

    @api.depends('maintenance_deadline', 'maintenance_deadline_type', 'first_date_use')
    def _compute_deadline_display(self):
        for record in self:
            if record.maintenance_deadline > 0 and record.maintenance_deadline_type:
                time_type = ''
                if record.maintenance_deadline_type == 'days':
                    time_type = _('days')
                elif record.maintenance_deadline_type == 'months':
                    time_type = _('months')
                elif record.maintenance_deadline_type == 'years':
                    time_type = _('years')
                record.maintenance_deadline_display = str(record.maintenance_deadline) + ' ' + time_type
            else:
                record.maintenance_deadline_display = _('Undefined')

    def count_deadline(self, date, date_type, index):
        time = datetime.datetime.now()
        tz_current = pytz.timezone(self._context.get('tz') or 'UTC')  # get timezone user
        tz_database = pytz.timezone('UTC')
        time = tz_database.localize(time)
        time = time.astimezone(tz_current)
        time = time.date()
        if date_type == 'days':
            date += relativedelta(days=+index)
        elif date_type == 'months':
            date += relativedelta(months=+index)
        elif date_type == 'years':
            date += relativedelta(years=+index)
        days = (date - time).days
        return {'date': date, 'days': days}

    @api.depends('last_maintenance', 'first_date_use', 'maintenance_deadline', 'maintenance_deadline_type')
    def _compute_status(self):
        for record in self:
            repair_msg = ''
            maintenance_msg = ''
            if record.first_date_use:
                # first_date_use = datetime.datetime.strptime(record.first_date_use, '%Y-%m-%d').date()
                first_date_use = record.first_date_use
                # maintenance
                if record.maintenance_deadline > 0 and record.maintenance_deadline_type:
                    if record.last_maintenance and record.last_maintenance > record.first_date_use:
                        date = record.last_maintenance
                    else:
                        date = first_date_use
                    deadine_maintenance = self.count_deadline(date, record.maintenance_deadline_type,
                                                              record.maintenance_deadline)
                    days = deadine_maintenance['days']
                    record.maintenance_expire_date = deadine_maintenance['date']
                    if days < 0:
                        maintenance_msg += ('Quá hạn bảo dưỡng {0} ngày').format(str(abs(days)))
                    elif days == 0:
                        maintenance_msg += ('Hôm nay là ngày bảo dưỡng')
                    elif days < 15:
                        maintenance_msg += ('{0} ngày nữa là ngày bảo dưỡng').format(str(abs(days)))

            record.maintenance_status = maintenance_msg
            record.repair_status = repair_msg

    @api.model
    def create(self, vals):
        device = super(MainDevice, self).create(vals)
        if vals.get('employee_id'):
            payload = {
                'type': 'export',
                'category_id': device.category_id.id,
                'department_id': device.department_id.id,
                'parent_id': device.department_id.manager_id.id if device.department_id.manager_id else None,
                'employee_use': device.employee_id.id,
                'description': 'Phiếu bàn giao thiết bị!!!',
                'state': 'approved',
                'device_ids': [(4, device.id)]
            }
            self.env['ems.equipment.export'].create(payload)
            device.activate = 'usage'
        return device

    def write(self, vals):
        return super(MainDevice, self).write(vals)

    def open_liquidate(self):
        self.activate = 'liquidate'

    def open_less_use(self):
        self.activate = 'less_use'

    def open_loss(self):
        self.activate = 'loss'
