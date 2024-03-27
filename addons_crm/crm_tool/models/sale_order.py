from odoo import models
from odoo.exceptions import ValidationError


class InheritSaleOrders(models.Model):
    _inherit = 'sale.order'

    def update_amount_remain(self):
        if not self.env.user.has_group('crm_tool.group_tool_so'):
            raise ValidationError(
                'Bạn không có quyền thao tác chức năng này.\nLiên hệ IT để cấp quyền Cập nhật tiền đã thu SO^^')
        if self.order_line:
            amount = 0
            for record in self.order_line:
                if record.crm_line_id and record.order_id.state in ['draft', 'sent']:
                    self.env.cr.execute(""" UPDATE sale_order_line
                                            SET amount_remain = %s
                                             WHERE id = %s;""" % (record.crm_line_id.remaining_amount, record.id))

                elif record.line_product and record.order_id.state in ['draft', 'sent']:
                    self.env.cr.execute(""" UPDATE sale_order_line
                                            SET amount_remain = %s
                                             WHERE id = %s;""" % (record.line_product.remaining_amount, record.id))
                amount += record.amount_remain
            self.amount_remain = amount

    def action_confirm(self):
        res = super(InheritSaleOrders, self).action_confirm()
        # Case SO âm của bán sản phẩm => Hủy phiếu xuất kho
        if self.picking_ids and (self.amount_total < 0):
            for stock_picking in self.picking_ids.filtered(lambda pick: pick.state not in ['done', 'cancel']):
                stock_picking.do_unreserve()
                stock_picking.action_cancel()
        return res
