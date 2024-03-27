from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    order_id = fields.Many2one('sale.order', string='Đơn hàng')


class CostCode(models.Model):
    _name = 'cost.code'
    _description = 'Chi phí'

    name = fields.Char('Mã chi phí')
    active = fields.Boolean(default=True)


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    partner_code = fields.Char(related="partner_id.code_customer", string='Mã đối tác', store=True)
    cost_code = fields.Many2one('cost.code', string='Mã chi phí')

    def view_move_line(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Bút toán phát sinh chi tiết',
            'res_model': 'account.move.line',
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': self.env.ref('account.view_move_line_form').id,
            'target': 'new',
        }

    def view_move(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Bút toán sổ nhật ký',
            'res_model': 'account.move',
            'res_id': self.move_id.id,
            'view_mode': 'form',
            'view_id': self.env.ref('account.view_move_form').id,
            'target': 'current',
        }
