# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class SHealthReExamService(models.Model):
    _inherit = 'sh.medical.walkin.service.reexam'
    _description = "Lịch tái khám theo phiếu khám"

    NOTE = [
        ('Check', 'Chăm sóc lần 1'),
        ('Check1', 'Chăm sóc lần 2'),
        ('Check2', 'Chăm sóc lần 3'),
        ('Check3', 'Chăm sóc lần 4'),
        ('Check8', 'Chăm sóc lần 5'),
        ('Check4', 'Chăm sóc kết thúc liệu trình lần 1'),
        ('Check5', 'Chăm sóc kết thúc liệu trình lần 2'),
        ('Check6', 'Chăm sóc kết thúc liệu trình lần 3'),
        ('Check7', 'Chăm sóc kết thúc liệu trình lần 4'),
        ('Check8', 'Chăm sóc kết thúc liệu trình lần 5'),
        ('Change', 'Thay băng lần 1'),
        ('Change1', 'Thay băng lần 2'),
        ('Change2', 'Thay băng lần 3'),
        ('Change3', 'Thay băng lần 4'),
        ('Change4', 'Thay băng lần 5'),
        ('Change5', 'Thay băng lần 6'),
        ('ReCheck', 'Cắt chỉ'),
        ('ReCheck1', 'Hút dịch'),
        ('ReCheck2', 'Rút ống mũi'),
        ('ReCheck3', 'Thay nẹp mũi'),
        ('ReCheck4', 'Tái khám lần 1'),
        ('ReCheck5', 'Tái khám lần 2'),
        ('ReCheck6', 'Tái khám lần 3'),
        ('ReCheck7', 'Tái khám lần 4'),
        ('ReCheck8', 'Tái khám lần 5'),
        ('ReCheck11', 'Tái khám lần 6'),
        ('ReCheck9', 'Tái khám định kì'),
        ('ReCheck10', 'Nhắc liệu trình'),
        ('Return', 'Tái khai thác KH cũ'),
        ('Sale1', 'Chăm sóc bán lần 1'),
        ('Sale2', 'Chăm sóc bán lần 2')
    ]

    type = fields.Selection(NOTE, 'Loại', required=True, default='Check')
