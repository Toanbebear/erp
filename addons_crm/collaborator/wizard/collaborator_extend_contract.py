from odoo import fields, models, _
from odoo.exceptions import ValidationError

class CollaboratorExtendContract(models.TransientModel):
    _name = 'collaborator.extend.contract'
    _description = 'Gia hạn hợp đồng'

    collaborator = fields.Many2one('collaborator.collaborator', string='Cộng tác viên')
    contract_ids = fields.Many2one('collaborator.contract', 'Hợp đồng')
    company_id = fields.Many2one('res.company', string='Công ty', required=True, default=lambda self: self.env.company, tracking=True)
    brand_id = fields.Many2one('res.brand', string='Thương hiệu', related='company_id.brand_id', store=True, tracking=True)
    contract_type_id = fields.Many2one('collaborator.contract.type', string='Loại hợp đồng', tracking=True)
    start_date = fields.Date('Ngày bắt đầu')
    end_date = fields.Date('Ngày kết thúc')
    referrer_id = fields.Many2one('res.partner', string='Người giới thiệu CTV',
                                  help='Nhân viên, khách hàng hoặc tổ chức giới thiệu cộng tác viên cho thương hiệu',)
    manager_id = fields.Many2one('hr.employee', string='Quản lý CTV',)

    def extend_create_contract(self):
        self.collaborator.state = 'effect'
        self.collaborator.company_id = self.company_id.id
        self.contract_ids.write({
            'start_date': self.start_date,
            'end_date': self.end_date,
            'contract_type_id': self.contract_type_id.id,
            'state': 'effect',
            'manager_id': self.manager_id.id,
            'referrer_id': self.referrer_id.id,
        })

