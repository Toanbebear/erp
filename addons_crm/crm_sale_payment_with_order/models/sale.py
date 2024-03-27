from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class OrderLineAmountRemain(models.Model):
    _inherit = 'sale.order.line'

    amount_remain = fields.Monetary(string='Tiền chưa sử dụng', compute='_compute_amount_remain', store=True)
    amount_owed = fields.Monetary(string='Tiền nợ', compute='_compute_amount_owed', store=True)

    @api.depends('crm_line_id.remaining_amount', 'line_product.remaining_amount')
    def _compute_amount_remain(self):
        for record in self:
            #Todo: Lần đầu update code thêm điều kiện if record.amount_remain: để không chạy các data cũ, sau khi update xong có thể dùng cron để xử lý các data cũ
            """
            Tiền chưa sử dụng ở SO Line bằng tiền chưa sử dụng ở CRM line 
            Chỉ tính đối với các so line có SO đang ở trạng thái draft hoặc sent
            """
            if record.crm_line_id and record.order_id.state in ['draft', 'sent']:
                self.env.cr.execute(""" UPDATE sale_order_line
                                        SET amount_remain = %s
                                         WHERE id = %s;""" % (record.crm_line_id.remaining_amount, record.id))

            elif record.line_product and record.order_id.state in ['draft', 'sent']:
                self.env.cr.execute(""" UPDATE sale_order_line
                                        SET amount_remain = %s
                                         WHERE id = %s;""" % (record.line_product.remaining_amount, record.id))

    @api.depends('crm_line_id.amount_owed', 'line_product.amount_owed')
    def _compute_amount_owed(self):
        for record in self:
            # Todo: Lần đầu update code thêm điều kiện if record.amount_owed: để không chạy các data cũ, sau khi update xong có thể dùng cron để xử lý các data cũ
            """
            Tiền nợ ở SO Line bằng tiền nợ ở CRM line 
            Chỉ tính đối với các so line có SO đang ở trạng thái draft hoặc sent
            """
            if record.crm_line_id and record.order_id.state in ['draft', 'sent']:
                self.env.cr.execute(""" UPDATE sale_order_line
                                            SET amount_owed = %s
                                             WHERE id = %s;""" % (record.crm_line_id.amount_owed, record.id))

            elif record.line_product and record.order_id.state in ['draft', 'sent']:
                self.env.cr.execute(""" UPDATE sale_order_line
                                            SET amount_owed = %s
                                             WHERE id = %s;""" % (record.line_product.amount_owed, record.id))


class OrderAmountRemain(models.Model):
    _inherit = 'sale.order'

    amount_remain = fields.Float(string='Tổng tiền được sử dụng', compute='_compute_amount_remain_so', store=True)
    amount_owed = fields.Float(string='Tổng tiền nợ', compute='_compute_amount_owed_so', store=True)

    @api.depends('order_line.amount_remain')
    def _compute_amount_remain_so(self):
        for record in self:
            total_amount_remain = sum(record.order_line.mapped('amount_remain'))
            self.env.cr.execute(""" UPDATE sale_order
                                    SET amount_remain = %s
                                    WHERE id = %s and state in ('draft', 'sent');""" % (total_amount_remain, record.id))

    @api.depends('order_line.amount_owed')
    def _compute_amount_owed_so(self):
        for record in self:
            total_amount_owed = sum(record.order_line.mapped('amount_owed'))
            self.env.cr.execute(""" UPDATE sale_order
                                        SET amount_owed = %s
                                        WHERE id = %s and state in ('draft', 'sent');""" % (total_amount_owed, record.id))

    def check_order_missing_money(self):
        for line in self.order_line:
            if line.price_subtotal > (line.amount_remain + line.amount_owed):
                return True
        if (self.state in ['draft', 'sent']) and self.pricelist_type != 'product':
            walkin = self.env['sh.medical.appointment.register.walkin'].sudo().search([
                ('state', 'not in', ['Completed', 'Cancelled']), ('sale_order_id', '=', self.id)])
            if walkin:
                if (self.amount_total > self.amount_remain + self.amount_owed) or (len(walkin) != 1):
                    return True
        elif (self.pricelist_type == 'product') and (self.state in ['draft', 'sent']):
            if self.amount_total > (self.amount_remain + self.amount_owed):
                return True
        return False

    def amount_missing_money(self):
        """
        Trả về tổng tiền còn thiếu của các line trong SO
        """
        missing_money = 0
        for line in self.order_line:
            if line.price_subtotal > line.amount_remain:
                missing_money += (line.price_subtotal - line.amount_remain)
        return missing_money



