from odoo import api, models, fields
import base64
import requests
import datetime


class NextCLoudImageWalkinImage(models.Model):
    _name = 'sh.medical.appointment.register.walkin.image'
    _description = "Hình ảnh mô tả"

    # khai bao field 'image_link' để connect nextcloud
    image = fields.Binary("Hình ảnh", required=True)
    walkin_id = fields.Many2one("sh.medical.appointment.register.walkin")
    image_link = fields.Char("Link nextcloud")
    create_datetime = fields.Datetime("Ngày giờ", default=datetime.datetime.now(), store=True)
    image_name = fields.Char('Tên ảnh')

    @api.model
    def create(self, vals_list):
        vals_list['create_datetime'] = datetime.datetime.now()
        record = super(NextCLoudImageWalkinImage, self).create(vals_list)
        # print(record.walkin_id.patient.)
        walkin_name = record.walkin_id.name
        patient_name = "[{0}] {1}".format(record.walkin_id.patient.code_customer, record.walkin_id.patient.name)
        self.env['sci.nextcloud'].nextcloud_create("sh.medical.appointment.register.walkin.image", "image",
                                                   record.id, patient_name, walkin_name)

        return record

    @api.model
    def unlink(self):
        res = super(NextCLoudImageWalkinImage, self).unlink()
        if res:
            for rec in self:
                self.env['sci.nextcloud'].nextcloud_delete("sh.medical.appointment.register.walkin.image", "image",
                                                           rec.id)
