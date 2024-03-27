import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class ServiceDepartmentEHC(models.Model):
    _name = "crm.hh.ehc.faculty"
    _description = 'Faculty EHC'

    name = fields.Char('Tên khoa')
    id_ehc = fields.Integer('ID EHC')
    code = fields.Char('Mã khoa')