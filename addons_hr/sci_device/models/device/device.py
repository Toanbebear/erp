# -*- coding: utf-8 -*- 
from odoo import models, fields, api, _, tools


class Device(models.Model):
    _name = 'sci.device'
    _description = "Device"

    date_import = fields.Date('Ngày nhập', required=True, default=fields.Date.today(),
                              track_visibility="onchange")
    first_date_use = fields.Date('Ngày tính khấu hao', default=fields.Date.today())
    period = fields.Integer(string='Bảo hành(Tháng)')
    description = fields.Html('Mô tả', size=1500)
    activate = fields.Selection(
        [('not_used', 'Chưa sử dụng'), ('usage', 'Đang sử dụng'), ('out_of_warranty', 'Hết bảo hành'),
         ('liquidate', 'Chờ thanh lý'), ('less_use', 'Đang Hỏng'), ('loss', 'Đã bị Mất')],
        'Trạng thái', required=True, default='not_used', track_visibility="onchange")


class DeviceImages(models.Model):
    _name = 'sci.device.image'
    _description = 'Device Image'

    name = fields.Char('Name', size=100, required=True)
    image = fields.Binary('Image')
    extra_device_id = fields.Many2one('sci.device.main')
    main_device_id = fields.Many2one('sci.device.main')
    parts_device_id = fields.Many2one('sci.device.parts.in')
    description = fields.Text('Description', size=600)


class BaseAttachment(models.Model):
    _name = 'sci.base.attachment'
    _description = 'SCI base attachment'
    _rec_name = "file_name"

    file = fields.Binary('Choose File', attachment=True, required=True)
    file_name = fields.Char('File name', readonly=True)
    description = fields.Text('Description', size=900, track_visibility="onchange")
    user_id = fields.Many2one('res.users', 'Upload Users', default=lambda self: self.env.user, store=True,
                              readonly=True)
    date = fields.Date('Attached date', default=lambda self: fields.Date.today(), readonly=True)

    def download_file(self):
        self.env.cr.execute('select id from ir_attachment where res_model = \'%s\' and res_id = %s'
                            % (self._name, self.id))
        return {
            "url": "/web/content/%s?download=true" % self.env.cr.fetchone()[0],
            "type": "ir.actions.act_url"
        }

    @api.model
    def create(self, vals):
        record = super(BaseAttachment, self).create(vals)
        # if "file_name" in vals:
        #     self.env.cr.execute('update ir_attachment set filename_field = \'%s\' where res_model = \'%s\' and res_id = %s'
        #                         % (vals["file_name"], record._name, record.id))
        return record

    @api.onchange('file')
    def _onchange_file(self):
        for record in self:
            record.user_id = self.env.user
