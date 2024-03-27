from odoo import fields, api, models, _
from odoo.exceptions import UserError, AccessError, ValidationError, Warning

class CrmUomPriceSource(models.TransientModel):
    _name = 'crm.uom.price.source'
    _description = 'Cập nhật đơn vị xử lý và nguồn'

    walkin_id = fields.Many2one('sh.medical.appointment.register.walkin', string='Phiếu khám')
    order_lines = fields.Many2many('sale.order.line', string='Dòng đơn hàng')
    crm_line = fields.Many2one('crm.line', string='Dòng dịch vụ',
                                 domain="[('sale_order_line_id','in',order_lines),('create_uid','=',uid)]")
    uom_price = fields.Float('Đơn vị xử lý ', default=1)
    source_extend_id = fields.Many2one('utm.source', string='Nguồn mở rộng',
                                       domain="[('extend_source', '=', True)]")

    @api.onchange('walkin_id')
    def onchange_walkin_id(self):
        if self.walkin_id:
            self.order_lines = self.walkin_id.sudo().sale_order_id.order_line
        else:
            self.order_lines = False

    @api.onchange('crm_line')
    def onchange_crm_line(self):
        if self.crm_line:
            if self.crm_line.total_before_discount != self.crm_line.total:
                raise ValidationError(_('Dòng dịch vụ đã áp dụng CTKM nên không được sửa!!!'))

            self.uom_price = self.crm_line.uom_price
            self.source_extend_id = self.crm_line.source_extend_id

    def confirm_so(self):
        # cập nhật so line
        sol = self.env['sale.order.line'].sudo().search([('order_id', '=', self.walkin_id.sale_order_id.id), ('crm_line_id', '=', self.crm_line.id)], limit=1)
        if sol:
            sol.uom_price = self.uom_price

        if self.walkin_id.sudo().sale_order_id.check_order_missing_money():
            self.walkin_id.create_draft_payment()

        view = self.env.ref('sh_message.sh_message_wizard')
        context = dict(self._context or {})
        context['message'] = 'Bạn đã cập nhật thành công cho lần khám này: %s - Đơn vị xử lý: %s - Nguồn: %s' % (self.crm_line.service_id.name,self.uom_price,self.crm_line.source_extend_id.name or '')

        return {
            'name': _('Cập nhật thành công'),  # label
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': view.id,
            'res_model': 'sh.message.wizard',  # model want to display
            'target': 'new',  # if you want popup
            'context': context,
        }

    def confirm_booking(self):
        # cập nhật so line
        # source_update = self.source_extend_id if self.source_extend_id else self.walkin_id.booking_id.source_id
        source_update = self.env['utm.source']
        if self.source_extend_id:
            source_update += self.source_extend_id
        else:
            source_update += self.crm_line.source_extend_id if self.crm_line.source_extend_id else self.walkin_id.booking_id.source_id

        self.crm_line.write({'uom_price': self.uom_price, 'source_extend_id': source_update})
        # cập nhật so line
        walkin_so_line = self.env['sale.order.line'].sudo().search([('crm_line_id', '=', self.crm_line.id), ('order_id', '=', self.walkin_id.sale_order_id.id)], limit=1)
        walkin_so_line.write({'uom_price': self.uom_price})

        # # xử lý tính toán tiền
        # total_so = self.walkin_id.sudo().sale_order_id.amount_total
        # total_payment_walkin = self.walkin_id.sudo().sale_order_id.amount_remain
        # amount_owed = self.walkin_id.sudo().sale_order_id.amount_owed  # Số tiền khách được duyệt nợ

        if self.walkin_id.sudo().sale_order_id.check_order_missing_money():
            self.walkin_id.create_draft_payment()

        view = self.env.ref('sh_message.sh_message_wizard')
        context = dict(self._context or {})
        context['message'] = 'Bạn đã cập nhật thành công Dòng dịch vụ: %s - Đơn vị xử lý: %s - Nguồn: %s' % (self.crm_line.service_id.name,self.uom_price,self.crm_line.source_extend_id.name or '')

        return {
            'name': _('Cập nhật thành công'),  # label
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': view.id,
            'res_model': 'sh.message.wizard',  # model want to display
            'target': 'new',  # if you want popup
            'context': context,
        }

class InheritWalkin(models.Model):
    _inherit = 'sh.medical.appointment.register.walkin'

    department_create_user = fields.Many2one('hr.department', string='Phòng Ban Người tạo', compute='set_department', store=True)

    @api.depends('create_uid')
    def set_department(self):
        for rec in self:
            rec.department_create_user = False
            employee = self.env['hr.employee'].search([('user_id', '=', rec.create_uid.id)])
            if employee and len(employee) == 1:
                rec.department_create_user = employee.department_id.id

    def crm_update_uom_price_source_action(self):
        self.ensure_one()
        return {
            'name': 'Cập nhật đơn vị xử lý và nguồn',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'view_id': self.env.ref('crm_his_13.crm_update_uom_price_source_view_form').id,
            'context': {'default_walkin_id': self.id},
            'res_model': 'crm.uom.price.source'
        }
