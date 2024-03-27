from odoo import fields, api, models, _
import logging
from odoo.exceptions import ValidationError,UserError
_logger = logging.getLogger(__name__)


class CollaboratorsProductsDiscount(models.Model):
    _name = 'products.discount'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Loại hợp đồng và chiếu khấu'

    name = fields.Char(string="Loại hợp đồng")
    service_id = fields.Many2many('sh.medical.health.center.service', string='Dịch vụ/Sản phẩm', tracking=True)
    company_id = fields.Many2one('res.company', string='Công ty', required=True, default=lambda self: self.env.company,)
    brand_id = fields.Many2one('res.brand', string='Thương hiệu', related='company_id.brand_id', store=True)
    price_list_id = fields.Many2one('product.pricelist', string='Bảng giá', domain="[('brand_id', '=', brand_id)]")
    currency_id = fields.Many2one('res.currency', string='Tiền tệ', related='price_list_id.currency_id', store=True,)
    product_id = fields.Many2one('product.product', string='Product',)
    discount_percent = fields.Float('Hoa hồng(%)', store=True, tracking=True)
    cancel = fields.Char('Hủy',)
    state = fields.Selection(
        [('draft', 'Nháp'), ('new', 'Có hiệu lực'), ('open', 'Mở lại'), ('cancel', 'Đã hủy')],
        string='Trạng thái', store=True, default='draft', tracking=True)
    description = fields.Text('Ghi chú')

    #huy loại hợp đồng
    REASON_LINE_CANCEL = [('change_service', 'Đổi sang dịch vụ khác cùng nhóm'), ('consider_more', 'Cân nhắc thêm'),
                          ('due_to_illness', 'Hủy do bệnh lý'), ('create_wrong_service', 'Thao tác tạo sai dịch vụ'),
                          ('other', 'Lý do khác (Ghi rõ lý do)')]
    reason_line_cancel = fields.Selection(REASON_LINE_CANCEL, string='Lý do hủy dịch vụ')
    cancel_user = fields.Many2one('res.users', 'Người hủy')
    cancel_date = fields.Datetime('Thời gian hủy')
    note = fields.Char('ghi chú',)

    def set_to_cancel(self):
        return {
            'name': 'HỦY LOẠI HỢP ĐỒNG',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('crm_collaborators.view_form_cancel_products_discount').id,
            'res_model': 'cancel.products.discount',
            'context': {
                'default_contract_id': self.id,
            },
            'target': 'new',
        }

    def set_to_new(self):  # trạng thái
        self.state = 'new'

    def set_to_draft(self):  # mở phiếu
        self.state = 'open'

    def reopen_contract(self): #cập nhật
        self.state = 'new'

    # thương hiệu bảng giá
    @api.onchange('brand_id')
    def onchange_price_list_id(self):
        if 'default_price_list_id' in self._context:
            self.price_list_id = self._context.get('default_price_list_id')
        elif self.brand_id != self.price_list_id:
            self.price_list_id = False


    # bảng giá dịch vụ
    @api.onchange('price_list_id')
    def onchange_name(self):
        if self.price_list_id != self.service_id:
            self.service_id = False


    # @api.onchange('service_id')
    # def _compute_stage_id_domain(self):
    #     #lay hop dong cua ctv
    #     domain_contract = [('state', 'in', ('draft', 'new')), ('source_ctv', '=', self.source_ctv_id.id)]
    #     contract = self.env['utm.source.ctv.contract'].sudo().search(domain_contract)
    #     #lay ra dich vu trong hop dong
    #     for se in contract:
    #         service_contract = self.default_code_id.chosen_line_ids.ids
    #         for re in service_contract:
    #             if re in self.service_id.ids:
    #                 raise ValidationError(_('DỊCH VỤ VỪA CHỌN ĐÃ CÓ TRONG HỢP ĐỒNG HIỆN TẠI'))
    #
    #         service = se.chosen_line_ids.ids
    #         for rec in service:
    #             if rec in self.service_id.ids:
    #                 raise ValidationError(_('DỊCH VỤ VỪA CHỌN ĐÃ CÓ TRONG HỢP ĐỒNG') + " " + "[" + str(se.default_code) + "]")



    #check cty
    @api.onchange('company_id')
    def _onchange_company_id(self):
        if self.company_id.brand_id:
            return {
                'domain': {'price_list_id': [('brand_id', '=', self.company_id.brand_id.id)]}
            }

    #lấy vè dịch vụ theo bảng giá
    @api.onchange('price_list_id')
    def get_service_ids(self):
        product_ids = self.env['product.pricelist.item'].sudo().search(
            [('pricelist_id', '=', self.price_list_id.id)]).mapped('product_id')
        service_ids = self.env['sh.medical.health.center.service'].sudo().search(
            [('product_id', 'in', product_ids.ids)])
        return {'domain': {'service_id': [('id', 'in', service_ids.ids)]}}


    @api.constrains('discount_percent')
    def check_discount_percent(self):
        for rec in self:
            if rec.discount_percent >= 31:
                raise ValidationError('Phần trăm hoa hồng không được vượt quá 30%')


    def write(self, vals):
        return super(CollaboratorsProductsDiscount, self).write(vals)

    def unlink(self):
        for rec in self:
            if rec.state != "draft":
                raise UserError(_('Bạn chỉ có thể xoá khi ở trạng thái nháp, nếu có thể bạn hãy lưu trữ!'))
        return super(CollaboratorsProductsDiscount, self).unlink()




