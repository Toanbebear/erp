from odoo import fields, models


class CollaboratorBank(models.Model):
    _name = 'collaborator.bank'
    _description = 'Tài khoản ngân hàng'

    collaborator_id = fields.Many2one('collaborator.collaborator', string='Cộng tác viên', required=True)
    bank_id = fields.Many2one('collaborator.bank.config', string='Ngân hàng')
    name = fields.Char(string='Tên chủ tài khoản')
    card_number = fields.Char(string='Số tài khoản')
    active = fields.Boolean(string='Lưu trữ', default=True)
    
    chi_nhanh = fields.Char('Chi nhánh')
    logo = fields.Binary(related='bank_id.logo', string='Logo', readonly=True)
    code = fields.Char(related='bank_id.code', string='Mã', readonly=True)
    default_banking = fields.Boolean('Thẻ mặc định', default=False)

    def name_get(self):
        result = super(CollaboratorBank, self).name_get()
        # if self._context.get('name_collaborator_bank'):
        new_result = []
        for sub_res in result:
            record = self.env['collaborator.bank'].browse(sub_res[0])
            name = '%s - %s - %s' % (record.name, record.bank_id.code, record.card_number)
            if record.default_banking == True:
                name += ' (TK mặc định)'
            else:
                name += ''
            new_result.append((sub_res[0], name))
        return new_result
        # return result


