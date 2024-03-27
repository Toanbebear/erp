from odoo import models, fields, api


class ShService(models.Model):
    _inherit = "sh.medical.health.center.service"

    allow_ctv = fields.Selection([('Yes', 'Cho phép tính'), ('No', 'Không tính')], string='Tính hoa hồng CTV')
    has_created_record = fields.Boolean(string='Đã tạo bản ghi dịch vụ không tính hoa hông', default=False)

    def write(self, vals):
        reslt = super(ShService, self).write(vals)
        for record in self:
            if record.allow_ctv == 'No' and not record.has_created_record:
                service = self.env['collaborator.service.not.allow.config'].sudo().create({
                    'service_id': record.product_id.id,
                    'brand_id': 1,
                })
                record.write({'has_created_record': True})
        return reslt