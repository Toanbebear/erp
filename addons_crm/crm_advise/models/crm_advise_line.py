from odoo import models, fields, api
import datetime
from odoo.exceptions import ValidationError


class AdviseLine(models.Model):
    _name = 'crm.advise.line'
    _description = 'Dòng tư vấn'
    _rec_name = 'service'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    group_service = fields.Many2one('sh.medical.health.center.service.category', string='Nhóm dịch vụ',
                                    related='service.service_category', store=True)
    information = fields.Char(string='Thông tin tư vấn')
    conclude = fields.Char(string='Kết luận')
    crm_id = fields.Many2one('crm.lead', 'Booking')
    walkin_id = fields.Many2one('sh.medical.appointment.register.walkin', 'Phiếu khám')
    brand_id = fields.Many2one('res.brand', compute='get_company', string='Thương hiệu',compute_sudo=True)
    service = fields.Many2one('sh.medical.health.center.service', string='Dịch vụ tư vấn',
                              domain="[('service_category.brand_id','=',brand_id)]")
    company_id = fields.Many2one('res.company', compute='get_company', string='Chi nhánh', store=True,compute_sudo=True)
    # desire_ids = fields.Many2many('crm.advise.desire', string='Mong muốn', domain="[('brand_id', '=', brand_id)]")
    desire_ids = fields.Many2many('crm.advise.desire', string='Mong muốn',
                                  domain="[('service_group','=',group_service)]")
    pain_point_ids = fields.Many2many('crm.advise.painpoint', string='Điểm đau',
                                      domain="[('service_group','=',group_service)]")
    state_ids = fields.Many2many('crm.advise.state', string='Tình trạng',
                                 domain="[('service_group','=',group_service)]")

    crm_line_id = fields.Many2one('crm.line', 'Dòng dịch vụ')
    stage = fields.Selection(
        [('chotuvan', 'Chờ tư vấn'), ('new', 'Allow to use'), ('processing', 'Processing'), ('done', 'Done'),
         ('waiting', 'Awaiting approval'),
         ('cancel', 'Cancel')],
        string='Trạng thái', related='crm_line_id.stage', store=True)
    consultant = fields.Many2one('res.users', 'Tư vấn viên', compute='get_consultant', store=True)
    is_potential = fields.Boolean('Tiềm năng')
    stage_potential = fields.Selection(
        [('potential', 'Tiềm năng'), ('exploited', 'Đã khai thác'), ('cancel', 'Hết tiềm năng')],
        'Trạng thái tiềm năng')
    currency_id = fields.Many2one('res.currency', string='Tiền tệ', related='crm_line_id.currency_id')
    unit_price = fields.Monetary(string='Giá', related='crm_line_id.unit_price')
    total = fields.Monetary(string='Tổng tiền sau giảm', related='crm_line_id.total')
    partner_id = fields.Many2one(related='crm_id.partner_id', string='Khách hàng')
    advise_required = fields.Boolean(related='group_service.advise_required', string='Khách hàng')
    REASON_LINE_CANCEL = [('change_service', 'Đổi sang dịch vụ khác cùng nhóm'),
                          ('due_to_illness', 'Hủy do bệnh lý'), ('create_wrong_service', 'Thao tác tạo sai dịch vụ'),
                          ('not_money', 'Không đủ chi phí'), ('consultant', 'Tham khảo trước'),
                          ('other', 'Lý do khác (Ghi rõ lý do)')]
    reason_line_cancel = fields.Selection(REASON_LINE_CANCEL, string='Lý do hủy dịch vụ')
    note = fields.Char('Ghi chú', related='crm_line_id.note')
    booking_source = fields.Many2one(related='crm_id.source_id', string='Nguồn Booking', store=True)
    booking_by = fields.Many2one(related='crm_id.create_by', string='Người tạo Booking')
    reason_cancel_potential = fields.Selection(
        [('no_service', 'Hết nhu cầu làm dịch vụ'), ('other_branch', 'Đã làm tại cơ sở khác')],
        string='Lí do hủy tiềm năng')
    note_cancel_potential = fields.Char('Ghi chú hủy tiềm năng')
    company_done = fields.Many2one('res.company', string='Chi nhánh khai thác thành công')

    @api.onchange('desire_ids')
    def set_value_desire_ids(self):
        if self.desire_ids:
            advise_line_ids = self.env['crm.advise.line'].sudo().search([('group_service', '=', self.group_service.id),
                                                                         ('crm_id', '=',
                                                                          self._context['default_crm_id']),
                                                                         ('desire_ids', '=', False)])
            if advise_line_ids:
                for advise in advise_line_ids:
                    advise.desire_ids = self.desire_ids

    @api.onchange('pain_point_ids')
    def set_value_pain_point_ids(self):
        if self.pain_point_ids:
            advise_line_ids = self.env['crm.advise.line'].sudo().search([('group_service', '=', self.group_service.id),
                                                                         ('crm_id', '=',
                                                                          self._context['default_crm_id']),
                                                                         ('pain_point_ids', '=', False)])
            if advise_line_ids:
                for advise in advise_line_ids:
                    advise.pain_point_ids = self.pain_point_ids

    @api.onchange('state_ids')
    def set_value_state_ids(self):
        if self.state_ids:
            advise_line_ids = self.env['crm.advise.line'].sudo().search([('group_service', '=', self.group_service.id),
                                                                         ('crm_id', '=',
                                                                          self._context['default_crm_id']),
                                                                         ('state_ids', '=', False)])
            if advise_line_ids:
                for advise in advise_line_ids:
                    advise.state_ids = self.state_ids

    @api.onchange('service')
    def get_value_advise(self):
        if self.group_service:
            advise_line_ids = self.env['crm.advise.line'].sudo().search([('group_service', '=', self.group_service.id),
                                                                         ('crm_id', '=',
                                                                          self._context['default_crm_id']),
                                                                         ('desire_ids', '!=', False),
                                                                         ('pain_point_ids', '!=', False),
                                                                         ('state_ids', '!=', False)])
            if advise_line_ids:
                self.desire_ids = advise_line_ids[0].desire_ids
                self.pain_point_ids = advise_line_ids[0].pain_point_ids
                self.state_ids = advise_line_ids[0].state_ids
            else:
                self.desire_ids = False
                self.pain_point_ids = False
                self.state_ids = False

    @api.depends('crm_id', 'crm_line_id')
    def get_company(self):
        for rec in self:
            if rec.crm_line_id:
                rec.company_id = rec.crm_line_id.company_id.id
                rec.brand_id = rec.crm_line_id.company_id.brand_id.id
            else:
                rec.company_id = rec.crm_id.company_id.id
                rec.brand_id = rec.crm_id.company_id.brand_id.id

    def action_chot(self):
        # Xử lý khi nút chốt được nhấn
        if len(self.desire_ids) < 1 and len(self.pain_point_ids) < 1 and len(
                self.pain_point_ids) < 1 and self.advise_required:
            raise ValidationError('Vui lòng nhập Mong muốn/ Điểm đau/ Tình trạng/Thông tin tư vấn')
        if not self.information:
            raise ValidationError('Vui lòng nhập Mong muốn/ Điểm đau/ Tình trạng/Thông tin tư vấn')
        self.conclude = "Đã chốt"
        self.crm_line_id.is_new = True
        self.crm_line_id.state = 'new'

    REASON_LINE_CANCEL = [('change_service', 'Đổi sang dịch vụ khác cùng nhóm'), ('consider_more', 'Cân nhắc thêm'),
                          ('due_to_illness', 'Hủy do bệnh lý'), ('create_wrong_service', 'Thao tác tạo sai dịch vụ'),
                          ('not_money', 'Không đủ chi phí'), ('consultant', 'Tham khảo trước'),
                          ('other', 'Lý do khác (Ghi rõ lý do)')]
    reason_line_cancel = fields.Selection(REASON_LINE_CANCEL, string='Lý do hủy dịch vụ')

    @api.depends('crm_line_id')
    def get_consultant(self):
        for rec in self:
            if rec.crm_line_id:
                if rec.brand_id.id == 1:
                    rec.consultant = rec.crm_line_id.consultants_1.id
                elif rec.brand_id.id == 3:
                    crm_information_consultant = self.env['crm.information.consultant'].sudo().search(
                        [('crm_line_id', '=', rec.crm_line_id.id), ('role', '=', 'recept')])
                    if crm_information_consultant:
                        rec.consultant = crm_information_consultant[0].user_id.id
                    else:
                        rec.consultant = rec.create_uid
            else:
                rec.consultant = rec.create_uid

    def action_huy(self):
        if len(self.desire_ids) < 1 and len(self.pain_point_ids) < 1 and len(
                self.pain_point_ids) < 1 and self.advise_required:
            raise ValidationError('Vui lòng nhập Mong muốn/ Điểm đau/ Tình trạng/Thông tin tư vấn')
        if not self.information:
            raise ValidationError('Vui lòng nhập Mong muốn/ Điểm đau/ Tình trạng/Thông tin tư vấn')
        return {
            'name': 'HỦY DỊCH VỤ',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('crm_advise.view_form_cancel_crm_advise').id,
            'res_model': 'crm.advise.cancel',
            'context': {
                'default_crm_line_id': self.crm_line_id.id,
                'default_advise_id': self.id
            },
            'target': 'new',
        }

    def create_phone_call_info_line(self):
        pc = self.env['crm.phone.call'].create({
            'name': 'Khai thác dịch vụ tiềm năng',
            'subject': 'Khai thác dịch vụ tiềm năng',
            'partner_id': self.partner_id.id,
            'phone': self.partner_id.phone,
            'direction': 'out',
            'company_id': self.company_id.id,
            'crm_id': self.crm_id.id,
            'country_id': self.crm_id.country_id.id,
            'street': self.crm_id.street,
            'type_pc': 'Potential',
            'type_crm_id': self.env.ref('crm_base.type_phone_call_customer_ask_info').id,
            # 'booking_date': self.booking_date,
            'call_date': datetime.datetime.now(),
            'advise_line_id': self.id
        })

        return {
            'name': 'Phone call',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': pc.id,
            'view_id': self.env.ref('crm_base.view_form_phone_call').id,
            'res_model': 'crm.phone.call',
            'context': {},
        }

    @api.model
    def create(self, vals):
        res = super(AdviseLine, self).create(vals)
        if res:
            if not res.crm_line_id:
                res.conclude = "Hủy, tiềm năng"
                res.is_potential = True
                res.stage_potential = 'potential'
        return res

    def cancel_potential(self):
        return {
            'name': 'Hết tiềm năng',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('crm_advise.view_form_cancel_crm_advise_potential').id,
            'res_model': 'crm.advise.cancel.potential',
            'context': {
                'default_crm_advise_id': self.id,
            },
            'target': 'new',
        }
