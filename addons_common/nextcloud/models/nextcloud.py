from odoo import api, models, fields, tools
from odoo.exceptions import UserError
from .. import nextcloud
import base64
import requests
import re
import os


def no_accent_vietnamese(s):
    s = re.sub(r'[àáạảãâầấậẩẫăằắặẳẵ]', 'a', s)
    s = re.sub(r'[ÀÁẠẢÃĂẰẮẶẲẴÂẦẤẬẨẪ]', 'A', s)
    s = re.sub(r'[èéẹẻẽêềếệểễ]', 'e', s)
    s = re.sub(r'[ÈÉẸẺẼÊỀẾỆỂỄ]', 'E', s)
    s = re.sub(r'[òóọỏõôồốộổỗơờớợởỡ]', 'o', s)
    s = re.sub(r'[ÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠ]', 'O', s)
    s = re.sub(r'[ìíịỉĩ]', 'i', s)
    s = re.sub(r'[ÌÍỊỈĨ]', 'I', s)
    s = re.sub(r'[ùúụủũưừứựửữ]', 'u', s)
    s = re.sub(r'[ƯỪỨỰỬỮÙÚỤỦŨ]', 'U', s)
    s = re.sub(r'[ỳýỵỷỹ]', 'y', s)
    s = re.sub(r'[ỲÝỴỶỸ]', 'Y', s)
    s = re.sub(r'[Đ]', 'D', s)
    s = re.sub(r'[đ]', 'd', s)
    return s


class NextCloud(models.Model):
    _name = "sci.nextcloud"
    _description = 'SCI Next Cloud'

    name = fields.Char("Name")
    res_model = fields.Char('Model')
    res_field = fields.Char('field')
    res_id = fields.Char('id')
    store_fname = fields.Char('store')
    checksum = fields.Char('checksum')
    mimetype = fields.Char('mimetype')

    @api.model
    def nextcloud_create(self, res_model, res_field, res_id, patient_name, walkin_name):
        username = self.env['ir.config_parameter'].sudo().get_param('nextcloud.nextcloud_username') or False
        password = self.env['ir.config_parameter'].sudo().get_param('nextcloud.nextcloud_password') or False
        if username and password:
            db_name = self._cr.dbname
            res_users_login = self.env['res.users'].sudo().browse(self._context.get('uid')).login
            if res_users_login.split("@"):
                login_name = res_users_login.split("@")[0]
            else:
                login_name = res_users_login


            data_dir = tools.config['data_dir']
            ir_attach = self.env['ir.attachment'].sudo().search(
                [('res_id', '=', int(res_id)), ('res_field', '=', str(res_field)), ('res_model', '=', str(res_model))])

            extension = ir_attach.mimetype.split("/")
            if ir_attach:
                nc = nextcloud.NextCloud(username, password, str(login_name))
                image_link = nc.add_image(patient_name, walkin_name, extension[1], data_dir, db_name, ir_attach.store_fname)
                store_fname = "/%s/%s/%s.%s" % (
                    no_accent_vietnamese(str(patient_name)),
                    no_accent_vietnamese(str(walkin_name)),
                    no_accent_vietnamese(str(login_name)) + "-" + str(ir_attach.checksum), str(extension[1]))
                self.env['sci.nextcloud'].sudo().create({
                    "res_model": res_model,
                    "res_field": res_field,
                    "res_id": res_id,
                    # "store_fname": str(
                    #     login_name) + "/" +  str(
                    #     no_accent_vietnamese(str(patient_name))) + "/" + str(ir_attach.checksum) + "." + str(extension[1]),
                    "store_fname": store_fname,
                    "checksum": ir_attach.checksum,
                    "mimetype": ir_attach.mimetype

                })

                image_record = self.env[res_model].sudo().browse(res_id)
                image_record.write({
                    "image_link": str(image_link) + "/download"
                })
                count_link = self.env['ir.attachment'].sudo().search_count(
                    [('store_fname', '=', ir_attach.store_fname)])
                if count_link <= 1:
                    if os.path.exists(str(data_dir) + "/filestore/" + str(db_name) + "/" + str(ir_attach.store_fname)):
                        os.remove(str(data_dir) + "/filestore/" + str(db_name) + "/" + str(ir_attach.store_fname))

                ir_attach.unlink()

                return image_record
        else:
            raise UserError("Chưa có cấu hình tài khoản NextCloud. \nVui lòng vào thiết lập cấu hình tài khoản NextCloud để lưu trữ hình ảnh!")

    @api.model
    def nextcloud_delete(self, res_model, res_field, res_id):
        res_users_login = self.env['res.users'].sudo().browse(self._context.get('uid')).login
        login_name = res_users_login.split("@")[0]
        username = self.env['ir.config_parameter'].sudo().get_param('nextcloud.nextcloud_username') or False
        password = self.env['ir.config_parameter'].sudo().get_param('nextcloud.nextcloud_password') or False
        db_name = self._cr.dbname
        data_dir = tools.config['data_dir']

        nextcloud_record = self.env['sci.nextcloud'].sudo().search(
            [('res_model', '=', res_model), ('res_field', '=', res_field), ('res_id', '=', res_id)])
        extension = nextcloud_record.mimetype.split("/")
        count_link = self.env['sci.nextcloud'].sudo().search_count([('store_fname', '=', nextcloud_record.store_fname)])
        if count_link <= 1:
            # print("Số đếm : ", count_link)
            nc = nextcloud.NextCloud(username, password, str(login_name))
            nc.delete_image(username, nextcloud_record.store_fname)
        nextcloud_record.unlink()
