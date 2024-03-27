import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)

TYPE_API_LOG = [('0', 'Thành công'), ('1', 'Lỗi')]


class APILog(models.Model):
    _name = 'api.log'
    _description = 'API Log'

    name = fields.Char('Tên')
    type_log = fields.Selection(TYPE_API_LOG, string='Kiểu log')
    model_id = fields.Many2one('ir.model', string='Model')
    id_record = fields.Integer('ID bản ghi')
    key = fields.Char('Key', related="model_id.model", stored=True)
    input = fields.Text('Input')
    response = fields.Text('Response')
    status_code = fields.Integer('Status Code')
    url = fields.Char('Url')
    header = fields.Char('Header')
