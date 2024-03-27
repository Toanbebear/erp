import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class ContactGroupExam(models.Model):
    _name = "crm.hh.ehc.contract.group.exam"
    _description = "Hợp đồng khám đoàn EHC"

    contract_code = fields.Char('Mã hợp đồng EHC')
    name = fields.Char('Tên hợp đồng')
    company_name = fields.Char('Tên công ty')
    address = fields.Char('Địa chỉ')
    source_code = fields.Char('Mã người giới thiệu')
    end_date = fields.Date('Ngày kết thúc')
    start_date = fields.Date('Ngày bắt đâu')
    invoice_method = fields.Selection(
        [('1', 'Tiền mặt'), ('2', 'Chuyển khoản'), ('3', 'Ghi nợ'), ('4', 'Quẹt thẻ(POS)')], 'Hình thức thu tiền')
    stage = fields.Selection([('0', 'Đang hoạt động'), ('1', 'Không hoạt động')])
    crm_ids = fields.One2many('crm.lead', 'contract_ehc_id', string='Danh sách booking')


class CrmEHC(models.Model):
    _inherit = "crm.lead"

    contract_ehc_id = fields.Many2one('crm.hh.ehc.contract.group.exam', string='Hợp đồng khám đoán')
