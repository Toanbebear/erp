from odoo import models, fields, api


class CRMLeadShare(models.Model):
    _inherit = "crm.lead"
    _description = 'Xử lý case thuê phòng mổ'

    access_wakin_share = fields.Boolean('Cho phép tạo phiếu khám thuê phòng mổ',
                                        compute='_is_access_walkin_share')

    # @api.depends('customer_come', 'company2_id')
    # def _is_access_walkin_share(self):
    #     for record in self:
    #         record.access_wakin_share = False
    #         if record.customer_come == 'yes' and record.company2_id:
    #             record.access_wakin_share = True

    @api.depends('customer_come', 'company2_id')
    def _is_access_walkin_share(self):
        for record in self:
            record.access_wakin_share = False
            if (record.customer_come == 'yes') and (self.env.company in record.company2_id):
                # if self.env.company in record.company2_id:
                    record.access_wakin_share = True

    @api.depends('order_ids.amount_total', 'order_ids.state', 'order_ids.order_line.qty_delivered', 'order_ids.partner_company')
    def set_used_booking(self):
        """
        Hàm tính tổng tiền đã sử dụng của BK: Bằng tổng của :
            + SO bán dịch vụ đã xác nhận (Không tính các SO với khách hàng thuê phòng mổ)
            + Tất cả các line có số lượng đã giao khác 0 của SO bán sản phẩm => Làm tròn
        """
        for rec in self:
            used = 0
            rec.order_ids = rec.order_ids.filtered(lambda so: not so.partner_company)
            if rec.order_ids:
                for order in rec.order_ids:
                    if order.state in ['sale', 'done'] and order.pricelist_type != 'product':
                        used += order.amount_total
                    elif order.state in ['sale', 'done'] and order.pricelist_type == 'product':
                        line_return_amount_total = sum(
                            [line.qty_delivered * (line.price_subtotal / line.product_uom_qty) for line in
                             order.order_line])
                        used += round(line_return_amount_total / 1000) * 1000
            rec.amount_used = used

    def select_service_share(self):
        return {
            'name': 'Phiếu khám thuê phòng mổ',
            'view_mode': 'form',
            'res_model': 'create.walkin.share',
            'type': 'ir.actions.act_window',
            'view_id': self.env.ref('crm_booking_share.walkin_share_form').id,
            'context': {
                'default_booking': self.id,
                'default_partner_walkin': self.partner_id.id,
                'default_partner_so': self.company_id.partner_id.id,
            },
            'target': 'new',
        }