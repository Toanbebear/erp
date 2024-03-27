from odoo import models, fields


class CrmHisWalkin(models.Model):
    _inherit = "sh.medical.appointment.register.walkin"

    is_deposit = fields.Boolean('Đặt cọc',
                                help="Trường hợp khách hàng đặt cọc để làm xét nghiệm, hôm khác làm dịch vụ\n User sẽ tick trường này để người khác biết rằng phiếu khám này chưa cần đóng.")


class ShService(models.Model):
    _inherit = "sh.medical.health.center.service"

    allow_adjust_unit_price = fields.Boolean('Cho phép điều chỉnh đơn giá')

    def name_get(self):
        result = super(ShService, self).name_get()
        if self._context.get('name_service_with_price'):
            new_result = []
            for sub_res in result:
                rec = self.env['sh.medical.health.center.service'].browse(sub_res[0])
                price_list_id = self.env['product.pricelist'].browse(self._context.get('pricelist'))
                price_id = price_list_id.item_ids.filtered(lambda x: x.product_id.id == rec.product_id.id)
                # name = sub_res[1] + str("{:,}".format(int(price_id.fixed_price)))
                name = sub_res[1] + ' -  %s đ' % "{:,}".format(int(price_id.fixed_price))
                new_result.append((sub_res[0], name))
            return new_result
        return result
