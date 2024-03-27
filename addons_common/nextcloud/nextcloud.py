from webdav3.client import Client, Resource
from odoo.http import request
import werkzeug
import odoo.http as http
import requests
import xmltodict
import pprint
import json
import re
import PIL.Image as Image
import io
import base64
import requests

headers = {
    'OCS-APIRequest': 'true',
}


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


class NextCloud:
    def __init__(self, username, password, folder_user):
        self.username = username
        self.password = password
        # self.folder_name = folder_name
        self.folder_user = folder_user

    def connect(self):
        options = {
            'webdav_hostname': "https://drive.scigroup.com.vn/remote.php/dav",
            'webdav_login': self.username,
            'webdav_password': self.password,
            'disable_check': True
        }

        client = Client(options)

        return client

    # def add_folder(self):
    #     client = self.connect()
    #     file_dir = "files/%s/%s" % (self.username, no_accent_vietnamese(str(self.folder_user)))
    #     client.mkdir(file_dir)

    def add_image(self, patient_name, walkin_name, extension, path, db, store_fname):
        client = self.connect()
        store_fname = store_fname
        x = store_fname.split("/")

        client.mkdir("files/%s/%s" % (
            self.username, no_accent_vietnamese(str(patient_name))
        ))

        file_dir = "files/%s/%s/%s" % (
            self.username, no_accent_vietnamese(str(patient_name)),
            no_accent_vietnamese(str(walkin_name)))

        client.mkdir(file_dir)

        image_dir = str(path) + "/filestore/" + str(db) + "/" + str(store_fname)

        client.upload_sync(file_dir + "/" + no_accent_vietnamese(str(self.folder_user)) + "-" + x[1] + "." + extension,
                           image_dir)

        file_path = "/%s/%s/%s.%s" % (
            no_accent_vietnamese(str(patient_name)),
            no_accent_vietnamese(str(walkin_name)), no_accent_vietnamese(str(self.folder_user)) + "-" + x[1], extension)
        return self.sharing(file_path)

    def sharing(self, file):
        url = "https://drive.scigroup.com.vn/ocs/v2.php/apps/files_sharing/api/v1/shares?path={}&shareType=3".format(
            file)
        headers = {
            'OCS-APIRequest': 'true',
        }

        response = requests.request("POST", url, headers=headers, auth=(self.username, self.password))

        o = xmltodict.parse(response.text)
        return o["ocs"]["data"]["url"]

    def delete_image(self, username, file):
        url = "https://drive.scigroup.com.vn/remote.php/dav/files/{0}/{1}".format(username,
                                                                                  file)

        headers = {
            'OCS-APIRequest': 'true',
        }
        response = requests.request("DELETE", url, headers=headers, auth=(self.username, self.password))

        return response
