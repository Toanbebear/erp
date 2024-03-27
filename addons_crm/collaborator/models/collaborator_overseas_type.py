import logging

from odoo import fields, api, models, _
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)
from num2words import num2words


class CollaboratorOverseasType(models.Model):
    _name = 'collaborator.overseas.type'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Chính sách Cộng tác viên Việt kièu'

    sales_begin = fields.Float(string="Doanh số khởi điểm", digits=(3, 0), default='10')
    sales_final = fields.Float(string="Doanh số hạn mức", digits=(3, 0), default='5000')
    rate = fields.Float(string='Tỷ lệ(%)', digits=(3, 0))
    currency_id = fields.Many2one('res.currency', string='Tiền tệ', default=2)

    # chuyển name
    def name_get(self):
        record = []
        for rec in self:
            if rec.sales_begin:
                record.append((rec.id, '[' + str(rec.sales_begin) + '$' + ' ' + '-' + ' ' + str(rec.sales_final) + '$' + ']' + str(rec.rate) + '%'))
        return record

    @api.constrains('rate')
    def check_ti_le(self):
        if not 1 <= self.rate < 100:
            raise ValidationError('Tỉ lệ lớn hơn 1%, nhỏ hơn 100%')


