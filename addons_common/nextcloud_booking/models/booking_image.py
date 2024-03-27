from odoo import api, models, fields
import base64
import requests
import datetime


class NextCLoudImageBooking(models.Model):
    _name = 'crm.lead.image'
    _description = "Hình ảnh mô tả"

    # khai bao field 'image_link' để connect nextcloud
    image = fields.Binary("Hình ảnh", required=True)
    booking_id = fields.Many2one("crm.lead")
    image_link = fields.Char("Link nextcloud")
    create_datetime = fields.Datetime("Ngày giờ", default=datetime.datetime.now(),store=True)
    image_name = fields.Char('Tên ảnh')

    @api.model
    def create(self, vals_list):
        vals_list['create_datetime'] = datetime.datetime.now()
        record = super(NextCLoudImageBooking, self).create(vals_list)
        booking_name = record.booking_id.name
        customer_name = "[{0}] {1}".format(record.booking_id.partner_id.code_customer, record.booking_id.partner_id.name)
        self.env['sci.nextcloud'].nextcloud_create("crm.lead.image", "image",
                                                   record.id, customer_name, booking_name)

        return record

    @api.model
    def unlink(self):
        res = super(NextCLoudImageBooking, self).unlink()
        if res:
            for rec in self:
                self.env['sci.nextcloud'].nextcloud_delete("crm.lead.image", "image",
                                                           rec.id)
