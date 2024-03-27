import logging

from odoo import fields, api, models, _
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)
from num2words import num2words


class CollaboratorContractType(models.Model):
    _name = 'collaborator.contract.type'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Loại hợp đồng'

    name = fields.Char(string="Tên loại hợp đồng")
    service_ids = fields.Many2many('product.product',
                                   'collaborator_contract_type_service_rel',
                                   'contract_type_id',
                                   'service_ids',
                                   string='Dịch vụ')
    service_not_allow_ids = fields.Many2many('product.product',
                                             'collaborator_contract_type_service_not_allow_rel',
                                             'contract_type_id',
                                             'service_not_allow_ids',
                                             string='Dịch vụ loại trừ')
    # Todo default chọn Kangnam
    brand_id = fields.Many2one('res.brand', string='Thương hiệu')
    company_id = fields.Many2one('res.company', string='Công ty')

    # rate = fields.Many2one('collaborator.rate.config', 'Tỷ lệ(%)', tracking=True,
    #                        help="Tỷ lệ hoa hồng của loại hợp đồng. Ví dụ 10%")
    rate = fields.Float(string='Tỷ lệ(%)')
    rate_text_total = fields.Text('% bằng chữ', compute='compute_rate')
    state = fields.Selection([('draft', 'Nháp'), ('effect', 'Hiệu lực')],
                             string='Trạng thái', default='draft', tracking=True)

    description = fields.Text('Ghi chú')
    active = fields.Boolean('Active', default=True)

    price_list_ids = fields.Many2many('product.pricelist', 'collaborator_contract_type_price_list_rel',
                                      'contract_type_id',
                                      'price_list_id', string='Bảng giá',
                                      domain="[('brand_id', '=', brand_id), ('type', '!=', 'product')]")
    collaborator_agency = fields.Boolean('Là đại lý', default=False)
    overseas = fields.Selection([('no', 'Không là hợp đồng Việt kiều'), ('yes', 'Là hợp đồng Việt kiều')], string='Việt kiều', default='no')
    currency_id = fields.Many2one('res.currency', string='Tiền tệ')
    overseas_type_ids = fields.Many2many('collaborator.overseas.type', string='Tỷ lệ ngoại kiều')
    require_collaborator = fields.Boolean('Bắt buộc nhập giá trị', default=True)

    def compute_rate(self):
        if self.rate:
            self.rate_text_total = num2words(round(self.rate), lang='vi_VN') + ' ' + "phần trăm"
        else:
            self.rate_text_total = "Không phầm trăm"

    @api.constrains('rate')
    def check_ti_le(self):
        if not self.env.user.has_group('collaborator.collaborator_group_manager_admin'):
            if self.overseas == 'no':
                if not 1 <= self.rate < 100:
                    raise ValidationError('Tỉ lệ hợp đồng lớn hơn 0, nhỏ hơn 100%')

    @api.onchange('overseas')
    def check_oversaeas(self):
        if self.overseas == 'yes':
            self.rate = 0
            self.currency_id = 2
        else:
            self.currency_id = False

    @api.model
    def create(self, vals):
        res = super(CollaboratorContractType, self).create(vals)
        list_service_not_allow = []
        # lấy ra dịch vụ không được phép tính hoa hồng
        service_not_allow = self.env['collaborator.service.not.allow.config'].sudo().search(
            [('brand_id', '=', res.brand_id.id)])
        if service_not_allow:
            list_service_not_allow = service_not_allow.service_id.ids
            res.service_not_allow_ids = [(6, 0, list_service_not_allow)]
        return res

    def write(self, vals):
        if vals.get('price_list_ids'):
            for rec in self:
                list_service_not_allow = []
                # lấy ra dịch vụ không được phép tính hoa hồng
                service_not_allow = self.env['collaborator.service.not.allow.config'].sudo().search(
                    [('brand_id', '=', rec.brand_id.id)])
                if service_not_allow:
                    list_service_not_allow = service_not_allow.service_id.ids
                    vals['service_not_allow_ids'] = [(6, 0, list_service_not_allow)]
                # lấy dịch vụ từ bảng giá
                data = []
                price_list_ids = self.env['product.pricelist'].sudo().browse(vals['price_list_ids'][0][2])
                if price_list_ids:
                    for pl_id in price_list_ids:
                        for item in pl_id.item_ids:
                            data.append(item.product_id.id)
                    if data:
                        data = list(set(data))
                    # lấy dịch vụ được phép tính hoa hồng
                    service = [ser for ser in data if ser not in list_service_not_allow]
                    if service:
                        vals['service_ids'] = [(6, 0, service)]
        return super(CollaboratorContractType, self).write(vals)

    def set_to_effect(self):  # trạng thái
        self.state = 'effect'

    def action_draft(self):
        self.state = 'draft'

    def unlink(self):
        for rec in self:
            if rec.state != "draft":
                raise UserError(_('Bạn chỉ có thể xoá khi ở trạng thái nháp, nếu có thể bạn hãy lưu trữ!'))
        return super(CollaboratorContractType, self).unlink()

    def update_set_service(self):
        contact_type = self.search([('state', '=', 'effect')])
        service = self.env['sh.medical.health.center.service'].search([('allow_ctv', '=', 'Yes')])
        for rec in contact_type:
            service_ids = rec.service_ids
            for record in service.product_id:
                if record and record not in service_ids:
                    service_ids = record.ids
                    rec.write({'service_ids': [(4, service_id) for service_id in service_ids]})
