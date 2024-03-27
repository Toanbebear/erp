# -*- coding: utf-8 -*-

import logging
from datetime import timedelta

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class SHealthReExamService(models.Model):
    _name = 'sh.medical.walkin.service.reexam'
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

    name = fields.Char("Tên")
    name_phone = fields.Char("Tên")
    name_sms = fields.Char("Tên")
    reexam_id = fields.Many2one('sh.medical.reexam', 'Lịch', ondelete='cascade')
    service_date = fields.Datetime('Ngày làm dịch vụ', related='reexam_id.date')
    service_date_out = fields.Datetime('Ngày ra viện', related='reexam_id.date_out')
    date_recheck_print = fields.Date('Ngày chăm sóc', compute="_compute_date_recheck_print")
    date_recheck_phone = fields.Date('Ngày phone call', compute="_compute_date_recheck_phone")
    date_recheck_sms = fields.Datetime('Ngày sms', compute="_compute_date_recheck_sms")
    after_service_date = fields.Integer('Sau ngày(ngày)', default=1, required=True)
    after_service_phone_date = fields.Integer('Sau ngày(ngày)', default=1)
    after_service_sms_date = fields.Integer('Sau ngày(ngày)', default=1)
    care_type = fields.Selection(
        [('Spa', 'Spa'), ('Laser', 'Laser'), ('Odontology', 'Nha'), ('Surgery', 'Phẫu thuật'),
         ('DVKH', 'Dịch vụ khách hàng')], 'Đơn vị chăm sóc')
    type = fields.Selection(NOTE, 'Loại', required=True, default='Check')
    type_date = fields.Selection([('m', 'Ngày KH ra viện (M)'), ('n', 'Ngày KH làm dịch vụ (N)')],
                                 string='Loại ngày sinh')
    for_service = fields.Text('Cho dịch vụ')
    # for_service_phone = fields.Text('Cho dịch vụ')
    for_service_phone = fields.Many2many('sh.medical.health.center.service',
                                         'sh_service_sh_medical_walkin_service_reexam_rel', 'servie_phone_id',
                                         'center_service_id', string='Dịch vụ',
                                         domain="[('id', 'in', parent.services)]")
    for_service_sms = fields.Text('Nội dung')
    is_phonecall = fields.Boolean('Sinh phonecall?', default=False)
    is_print = fields.Boolean('Sinh hướng dẫn?', default=False)
    is_sms = fields.Boolean('Sinh SMS?', default=False)

    system = fields.Boolean('Hệ thống', default=False)
    # brand = fields.Many2one('res.brand', compute='get_brand_walkin')
    brand_id = fields.Many2one('res.brand', compute='get_brand_walkin', store=True)

    def get_brand_walkin(self):
        for re in self:
            reexam_id = re.reexam_id
            if reexam_id and reexam_id.walkin:
                re.brand_id = reexam_id.walkin.institution.brand

    @api.depends('service_date', 'service_date_out', 'after_service_date', 'after_service_phone_date',
                 'after_service_sms_date', 'type_date')
    def _compute_date_recheck_print(self):
        for record in self:
            record.date_recheck_print = False
            if record.type_date == 'n':
                if record.after_service_date and record.service_date:
                    record.date_recheck_print = record.service_date + timedelta(days=record.after_service_date)
            else:
                if record.after_service_date and record.service_date_out:
                    record.date_recheck_print = record.service_date_out + timedelta(days=record.after_service_date)

    @api.depends('service_date', 'service_date_out', 'after_service_date', 'after_service_phone_date',
                 'after_service_sms_date', 'type_date')
    def _compute_date_recheck_phone(self):
        for record in self:
            record.date_recheck_phone = False
            if record.type_date == 'n':
                if record.after_service_date and record.service_date:
                    record.date_recheck_phone = record.service_date + timedelta(days=record.after_service_phone_date)
                    if record.is_phonecall and record.is_print:
                        record.after_service_phone_date = record.after_service_date - 1
                        record.date_recheck_phone = record.service_date + timedelta(
                            days=record.after_service_phone_date)
            else:
                if record.after_service_date and record.service_date_out:
                    record.date_recheck_phone = record.service_date_out + timedelta(
                        days=record.after_service_phone_date)
                    if record.is_phonecall and record.is_print:
                        record.after_service_phone_date = record.after_service_date - 1
                        record.date_recheck_phone = record.service_date_out + timedelta(
                            days=record.after_service_phone_date)

    @api.depends('service_date', 'service_date_out', 'after_service_date', 'after_service_phone_date',
                 'after_service_sms_date', 'type_date')
    def _compute_date_recheck_sms(self):
        for record in self:
            record.date_recheck_sms = False
            if record.type_date == 'n':
                if record.after_service_date and record.service_date:
                    record.date_recheck_sms = (
                            record.service_date + timedelta(days=record.after_service_sms_date)).replace(hour=2)
            else:
                if record.after_service_date and record.service_date_out:
                    record.date_recheck_sms = (
                            record.service_date_out + timedelta(days=record.after_service_sms_date)).replace(hour=2)

    # @api.depends('reexam_id.date', 'reexam_id.date_out', 'after_service_date', 'after_service_phone_date',
    #              'after_service_sms_date', 'type_date')
    # def _compute_date(self):
    #     for record in self:
    #         record.date_recheck_print = record.date_recheck_phone = record.date_recheck_sms = False
    #         if record.type_date == 'n':
    #             if record.after_service_date and record.service_date:
    #                 # record.after_service_phone_date = record.after_service_sms_date = record.after_service_date
    #                 record.date_recheck_print = record.service_date + timedelta(days=record.after_service_date)
    #                 record.date_recheck_phone = record.service_date + timedelta(days=record.after_service_phone_date)
    #                 record.date_recheck_sms = (
    #                         record.service_date + timedelta(days=record.after_service_sms_date)).replace(hour=2)
    #                 if record.is_phonecall and record.is_print:
    #                     record.after_service_phone_date = record.after_service_date - 1
    #                     record.date_recheck_phone = record.service_date + timedelta(
    #                         days=record.after_service_phone_date)
    #         else:
    #             if record.after_service_date and record.service_date_out:
    #                 # record.after_service_phone_date = record.after_service_date
    #                 record.date_recheck_print = record.service_date_out + timedelta(days=record.after_service_date)
    #                 record.date_recheck_phone = record.service_date_out + timedelta(
    #                     days=record.after_service_phone_date)
    #                 record.date_recheck_sms = (
    #                         record.service_date_out + timedelta(days=record.after_service_sms_date)).replace(hour=2)
    #                 if record.is_phonecall and record.is_print:
    #                     record.after_service_phone_date = record.after_service_date - 1
    #                     record.date_recheck_phone = record.service_date_out + timedelta(
    #                         days=record.after_service_phone_date)

