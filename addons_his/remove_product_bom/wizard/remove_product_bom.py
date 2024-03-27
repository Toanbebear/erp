from odoo import api, fields, models
from odoo.exceptions import ValidationError


class RemoveProductBom(models.TransientModel):
    _name = 'remove.product.bom'
    _description = 'Tool xóa các sản phẩm trong BOM'

    import_data = fields.Char('Mã BOM', help='Danh sách BOM cần xóa sản phẩm')
    bom_ids = fields.Many2many('sh.medical.product.bundle', string='Danh sách BOM')
    type = fields.Selection([('1', 'Dấu phẩy'), ('2', 'Dấu cách'), ('3', 'Dấu chấm phẩy')], string='Khoảng cách giữa các mã', default='2')

    @api.onchange('import_data', 'type')
    def get_bom_ids(self):
        if self.import_data:
            if self.type == '1':
                list_bom = list(self.import_data.replace(" ", "").split(","))
                bom_ids = self.env['sh.medical.product.bundle'].sudo().search([('code','in',list_bom)])
                if bom_ids:
                    self.bom_ids = bom_ids.ids
                else:
                    raise ValidationError("Không tìm thấy BOM")
            elif self.type == '2':
                list_bom = list(self.import_data.split(" "))
                bom_ids = self.env['sh.medical.product.bundle'].sudo().search([('code', 'in', list_bom)])
                if bom_ids:
                    self.bom_ids = bom_ids.ids
                else:
                    raise ValidationError("Không tìm thấy BOM")
            else:
                list_bom = list(self.import_data.replace(" ", "").split(";"))
                bom_ids = self.env['sh.medical.product.bundle'].sudo().search([('code', 'in', list_bom)])
                if bom_ids:
                    self.bom_ids = bom_ids.ids
                else:
                    raise ValidationError("Không tìm thấy BOM")
        else:
            self.bom_ids = None

    def disable(self):
        bom_disable = """
        delete from sh_medical_products_line smpl
        where smpl.bundle in %s
        """
        self.env.cr.execute(bom_disable, [tuple(self.bom_ids.ids)])
        view = self.env.ref('sh_message.sh_message_wizard')
        view_id = view and view.id or False
        context = dict(self._context or {})
        context['message'] = "Các sản phẩm của BOM đã được xóa thành công."
        return {
            'name': 'THÔNG BÁO THÀNH CÔNG',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sh.message.wizard',
            'views': [(view_id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': context,
        }

