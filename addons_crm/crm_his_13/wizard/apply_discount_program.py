from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, date
import itertools


class InheritApplyDiscountProgram(models.TransientModel):
    _inherit = 'crm.apply.discount.program'
    _description = 'Inherit Apply Discount Program'

    note = fields.Html('Note', related='program_discount_id.note')

    # Hàm hoàn lại CTKM
    def reverse_prg_ids(self):
        if self.type_action == 'reverse_part':
            # Lấy ra danh sách (B1) các dịch vụ của BK chưa sử dụng và đc áp CTKM đã chọn
            crm_line_new_ids = self.crm_id.crm_line_ids.filtered(
                lambda l: (l.stage == 'new') and (self.program_discount_id in l.prg_ids))
            for line in crm_line_new_ids:
                line_discount_history = self.env['crm.line.discount.history'].search(
                    [('crm_line', '=', line.id), ('booking_id', '=', self.crm_id.id),
                     ('discount_program', '=', self.program_discount_id.id)])
                if line_discount_history.type == 'discount':
                    # Nếu xác định line dịch vụ này hưởng khuyến mãi đơn lẻ thì giảm trừ như bình thường
                    if line_discount_history.index == 0:
                        line.prg_ids = [(3, self.program_discount_id.id)]
                        if line_discount_history.type_discount == 'percent':
                            line.discount_percent = line.discount_percent - line_discount_history.discount
                        elif line_discount_history.type_discount == 'cash':
                            line.discount_cash = line.discount_cash - line_discount_history.discount
                        else:
                            line.sale_to = line.sale_to - line_discount_history.discount
                    # Nếu xác định line dịch vụ này hưởng khuyến mãi combo thì:
                    # Bước 1: Tìm bản ghi lịch sử km khác có chung lead/bk, có cùng chỉ số, và cùng CTKM
                    # Bước 2: Kiểm tra line dịch vụ đó đã sử dụng chưa, nếu chưa thì hoàn lại luôn cho cả combo, nếu đã sử dụng sẽ không được hủy CTKM cho cả combo này nữa
                    # Bước 3: Xóa line đã hoàn khỏi danh sách B1
                    elif line_discount_history.index != 0:
                        line_related = self.env['crm.line']
                        line_discount_history_related = self.env['crm.line.discount.history'].search(
                            [('index', '=', line_discount_history.index), ('booking_id', '=', self.crm_id.id),
                             ('discount_program', '=', self.program_discount_id.id),
                             ('id', '!=', line_discount_history.id)])
                        line_related += line_discount_history_related.crm_line
                        if line_related.stage == 'new':
                            if line_discount_history_related.type == 'discount':
                                # Hoàn giảm giá ở line liên quan
                                line_related.prg_ids = [(3, self.program_discount_id.id)]
                                if line_discount_history_related.type_discount == 'percent':
                                    line_related.discount_percent = line_related.discount_percent - line_discount_history_related.discount
                                elif line_discount_history_related.type_discount == 'cash':
                                    line_related.discount_cash = line_related.discount_cash - line_discount_history_related.discount
                                else:
                                    line_related.sale_to = line_related.sale_to - line_discount_history_related.discount
                            elif line_discount_history_related.type == 'gift':
                                line_related.unlink()
                            line_discount_history_related.unlink()
                            # Hoàn giảm giá ở line ban đầu
                            line.prg_ids = [(3, self.program_discount_id.id)]
                            if line_discount_history.type_discount == 'percent':
                                line.discount_percent = line.discount_percent - line_discount_history.discount
                            elif line_discount_history.type_discount == 'cash':
                                line.discount_cash = line.discount_cash - line_discount_history.discount
                            else:
                                line.sale_to = line.sale_to - line_discount_history.discount

                line_discount_history.unlink()
        else:
            crm_line_ids = self.crm_id.crm_line_ids.filtered(
                lambda l: (self.program_discount_id in l.prg_ids))
            for line in crm_line_ids:
                line_discount_history = self.env['crm.line.discount.history'].search(
                    [('crm_line', '=', line.id), ('booking_id', '=', self.crm_id.id),
                     ('discount_program', '=', self.program_discount_id.id)])
                if line_discount_history.type == 'discount':
                    line.prg_ids = [(3, self.program_discount_id.id)]
                    if line_discount_history.type_discount == 'percent':
                        line.discount_percent = line.discount_percent - line_discount_history.discount
                    elif line_discount_history.type_discount == 'cash':
                        line.discount_cash = line.discount_cash - line_discount_history.discount
                    else:
                        line.sale_to = line.sale_to - line_discount_history.discount
                else:
                    line.unlink()
                line_discount_history.unlink()

    def check_prg(self):
        if self.crm_id and self.program_discount_id.company_ids and \
                self.crm_id.company_id not in self.program_discount_id.company_ids:
            raise ValidationError(
                'Chi nhánh %s không có trong danh sách áp dụng coupon giảm giá !!!' % self.crm_id.company_id.name)
        else:
            self.reverse_prg_ids()
            lines = self.crm_id.crm_line_ids.filtered(
                lambda line: line.stage in ['new', 'processing']
                             and line.number_used == 0
                             and not line.voucher_id
                             and self.program_discount_id not in line.prg_ids)
            if lines and self.program_discount_id.coupon_type == '1':  # Rẽ nhánh chạy theo từng loại coupon
                self.check_coupon_type_1(lines, self.program_discount_id)

    # Hàm check điều kiện cho coupon đơn lẻ
    def check_coupon_type_1(self, lines, program_discount_id):
        for discount_line in program_discount_id.discount_program_list:
            if discount_line.gift:
                self.create_crm_line_gift(discount_line.product_ids, discount_line)
            else:
                if discount_line.type_product == 'product_ctg':
                    line_result = lines.filtered(
                        lambda l: (l.service_id.service_category in discount_line.product_ctg_ids) and (
                                self.program_discount_id not in l.prg_ids))
                    quantity = sum(line_result.mapped('quantity'))
                    if (quantity >= discount_line.dc_min_qty) and (quantity <= discount_line.dc_max_qty):
                        self.set_discount_coupon_1(line_result, discount_line)
                else:
                    line_result = lines.filtered(lambda l: (l.product_id in discount_line.product_ids) and (
                            self.program_discount_id not in l.prg_ids))
                    quantity = sum(line_result.mapped('quantity'))
                    if (quantity >= discount_line.dc_min_qty) and (quantity <= discount_line.dc_max_qty):
                        self.set_discount_coupon_1(line_result, discount_line)

    # Hàm set CTKM cho từng line dịch vụ
    def set_discount_coupon_1(self, line_result, discount_line):
        for line in line_result:
            discount_rec = line.prg_ids.mapped('discount_program_list')
            discounted = discount_rec.filtered(lambda d: (line.product_id in d.product_ids) or (
                    line.service_id.service_category in d.product_ctg_ids)).mapped('incremental')
            if (all(discounted) and discount_line.incremental) or (discount_line and not discount_rec):
                if not line.prg_ids or (
                        line.prg_ids and (
                        'sale_to' not in discount_line.mapped('type_discount')) and line.sale_to == 0):
                    if discount_line.type_discount == 'percent':
                        line.discount_percent += discount_line.discount
                    elif discount_line.type_discount == 'cash':
                        line.discount_cash += discount_line.discount * line.quantity
                    else:
                        line.sale_to = discount_line.discount
                    line.prg_ids = [(4, self.program_discount_id.id)]
                    self.crm_id.prg_ids = [(4, self.program_discount_id.id)]
                    self.env['crm.line.discount.history'].create({
                        'booking_id': self.crm_id.id,
                        'crm_line': line.id,
                        'discount_program': self.program_discount_id.id,
                        'index': 0,
                        'type': 'discount',
                        'type_discount': discount_line.type_discount,
                        'discount': discount_line.discount * line.quantity
                    })
                    if line.stage == 'processing':
                        # Nếu line dv này có ở trạng thái đang xử lý cần sửa giá ở SO nữa
                        order_id = self.env['sale.order'].search(
                            [('booking_id', '=', self.crm_id.id), ('state', '=', 'draft')])
                        if order_id:
                            order_line_id = order_id.order_line.filtered(lambda l: l.crm_line_id == line)
                            if order_line_id:
                                order_line_id.discount = line.discount_percent
                                order_line_id.discount_cash = line.discount_cash
                                order_line_id.sale_to = line.sale_to
                        # Nếu có payment dạng nháp cũng sửa luôn nữa
                        walkin = self.env['sh.medical.appointment.register.walkin'].search(
                            [('sale_order_id', '=', order_id.id), ('state', 'in', ['Scheduled', 'WaitPayment'])])
                        if walkin:
                            payment = self.env['account.payment'].search(
                                [('crm_id', '=', self.crm_id.id), ('walkin', '=', walkin.id),
                                 ('state', '=', 'draft')])
                            if payment:
                                payment.amount = order_id.amount_total

    # def check_product_ctg_program(self):
    #     # Trước khi add CTKM cần hoàn lại CTKM nếu CTKM này đã được add trước đó
    #     self.reverse_prg_ids()
    #     lines = self.crm_id.crm_line_ids.filtered(
    #         lambda line: line.stage in ['new', 'processing']
    #                      and line.number_used == 0
    #                      and not line.voucher_id
    #                      and self.program_discount_id not in line.prg_ids)
    #     if lines:
    #         list_index = self.program_discount_id.discount_program_list.mapped('index')
    #         list_index_le = True if 0 in list_index else False
    #         list_index_set = set(list_index)
    #         list_index_set.discard(0)
    #         dict = {}
    #         for index in list_index_set:
    #             dict[index] = list_index.count(index)
    #         values_sorted = sorted(dict.items(), key=lambda x: x[1], reverse=True)
    #         list_index_result = []
    #         for value in values_sorted:
    #             list_index_result.append(value[0])
    #         dict_required = {}
    #         for index in list_index_result:
    #             required_combo = self.env['crm.discount.program.list'].search(
    #                 [('index', '=', index), ('discount_program', '=', self.program_discount_id.id)])
    #             dict_required[index] = len(required_combo.filtered(lambda l: l.required_combo))
    #         values_sorted_required_combo = sorted(dict_required.items(), key=lambda x: x[1], reverse=True)
    #         list_result = []
    #         for value in values_sorted_required_combo:
    #             list_result.append(value[0])
    #         # dict_used = {}
    #         # for index in list_result:
    #         #     used = self.env['crm.discount.program.list'].search([('index', '=', index), ('discount_program', '=', self.program_discount_id.id)])
    #         #     print(used)
    #         #     dict_used[index] = len(used.filtered(lambda l: l.used))
    #         # values_sorted_used = sorted(dict_used.items(), key=lambda x: x[1], reverse=True)
    #         # print(values_sorted_used)
    #         # list_used_result = []
    #         # for value in values_sorted_used:
    #         #     list_used_result.append(value[0])
    #         if list_result:
    #             for index in list_result:
    #                 # list discount quà tặng (A1)
    #                 gift_discount_ids = self.program_discount_id.discount_program_list.filtered(
    #                     lambda l: l.index == index and l.gift)
    #
    #                 # list discount không có quà tặng(A2)
    #                 list_discount_ids_not_gift = self.program_discount_id.discount_program_list.filtered(
    #                     lambda l: l.index == index and not l.gift)
    #
    #                 # Từ A2 lấy ra các discount có used (A3)
    #                 list_discount_used = list_discount_ids_not_gift.filtered(lambda l: l.used)
    #
    #                 # Từ A2 lấy ra các discount không used (A4)
    #                 list_discount_ids = list_discount_ids_not_gift.filtered(lambda l: not l.used)
    #
    #                 # Từ A4 lấy ra các discount có product
    #                 list_discount_product = list_discount_ids.filtered(lambda l: l.product_ids)
    #
    #                 # Từ discount lấy ra các discount có product_cate
    #                 list_discount_categ = list_discount_ids.filtered(lambda l: l.product_ctg_ids)
    #
    #                 # Nếu có nhóm used thì vào đây
    #                 if list_discount_used:
    #                     # Phần này kiểm tra các crm line xem có dịch vụ/ nhóm dịch vụ thuộc A3 không
    #                     list_discount_used_product = list_discount_used.mapped('product_ids')
    #                     list_discount_used_categ = list_discount_used.mapped('product_ctg_ids')
    #                     used_product = self.env['crm.line'].search(
    #                         [('number_used', '>', 0), ('crm_id.partner_id', '=', self.partner_id.id),
    #                          ('product_id', 'in', list_discount_used_product.ids)])
    #                     used_categ = self.env['crm.line'].search(
    #                         [('number_used', '>', 0), ('crm_id.partner_id', '=', self.partner_id.id),
    #                          ('service_id.service_category', 'in', list_discount_used_categ.ids)])
    #
    #                     # Todo: Đoạn này hệ thống đnag chỉ check KH đã sử dụng 1 trong các DV/nhóm DV điều kiện hay chưa
    #                     if used_product or used_categ:
    #                         discountable_lines = self.env['crm.line']
    #                         list_required = []
    #                         for discount in list_discount_ids:
    #                             if discount.required_combo:
    #                                 list_required.append(discount.mapped('product_ids').ids)
    #                             discountable_lines += lines.filtered(lambda l: ((
    #                                                                                     l.product_id in discount.product_ids) or (
    #                                                                                     l.service_id.service_category in discount.product_ctg_ids)) and (
    #                                                                                    l not in discountable_lines) and (
    #                                                                                    self.program_discount_id not in l.prg_ids))
    #                         list_itertool = list(itertools.product(*list_required))
    #                         # check = any(set(x).issubset(set(discountable_lines.mapped('product_id.id'))) for x in list_itertool)
    #                         product_ids = discountable_lines.mapped('product_id.id')
    #                         check = False  # any(all(x in discountable_lines.mapped('product_id.id') for x in y) for y in list_itertool)
    #                         for combo in list_itertool:
    #                             if all(list_discount_ids.mapped('check_switch')):
    #                                 if len(combo) > len(product_ids) and len(combo) > len(discountable_lines):
    #                                     continue
    #                             if all(p_id in product_ids for p_id in combo) and len(combo) <= len(discountable_lines):
    #                                 check = True
    #
    #                         if check:
    #                             self.set_discount_combo(discountable_lines, index)
    #                 # Nếu không có nhóm used thì vào đây, bỏ qua phần kiểm tra điều kiện used
    #                 else:
    #                     list_discount_required_ids = list_discount_ids.filtered(lambda d: d.required_combo)
    #                     discountable_lines = self.env['crm.line']
    #                     list_required = []
    #                     for discount in list_discount_ids:
    #                         if discount.required_combo:
    #                             if discount.product_ids:
    #                                 list_required.append(discount.mapped('product_ids').ids)
    #                             elif discount.product_ctg_ids:
    #                                 cate_product_ids = discount.mapped('product_ctg_ids')
    #                                 service_ids = self.env['sh.medical.health.center.service'].search(
    #                                     [('service_category', 'in', cate_product_ids.ids)])
    #                                 list_required.append(service_ids.mapped('product_id').ids)
    #                         discountable_lines += lines.filtered(lambda l: ((l.product_id in discount.product_ids) or (
    #                                 l.service_id.service_category in discount.product_ctg_ids)) and (
    #                                                                                l not in discountable_lines) and (
    #                                                                                self.program_discount_id not in l.prg_ids))
    #
    #                     list_itertool = list(itertools.product(*list_required))
    #                     # check = any(set(x).issubset(set(discountable_lines.mapped('product_id.id'))) for x in list_itertool)
    #                     product_ids = discountable_lines.mapped('product_id.id')
    #                     product = discountable_lines.mapped('product_id')
    #                     check = False  # any(all(x in discountable_lines.mapped('product_id.id') for x in y) for y in list_itertool)
    #                     for combo in list_itertool:
    #                         if all(list_discount_ids.mapped('check_switch')):
    #                             if len(combo) > len(product_ids) and len(combo) > len(discountable_lines):
    #                                 continue
    #                         if all(p_id in product_ids for p_id in combo) and len(combo) <= len(discountable_lines):
    #                             check = True
    #
    #                     if check:
    #                         self.set_discount_combo(discountable_lines, index)
    #         if list_index_le:
    #             # list discount không có quà
    #             discount_ids = self.program_discount_id.discount_program_list.filtered(
    #                 lambda l: l.index == 0)
    #             discount_gift_ids = discount_ids.filtered(lambda dc: dc.gift)
    #             discount_no_gift_ids = discount_ids.filtered(lambda dc: dc not in discount_gift_ids)
    #             discount_cate_ids = discount_no_gift_ids.filtered(lambda dc: dc.product_ctg_ids)
    #             discount_product_ids = discount_no_gift_ids.filtered(lambda dc: dc not in discount_cate_ids)
    #             if discount_cate_ids:
    #                 discount_cate_ids = discount_cate_ids.sorted('dc_min_qty', reverse=True)
    #                 for discount in discount_cate_ids:
    #                     if (discount.minimum_group - 1 >= len(self.crm_id.group_booking)) or (
    #                             discount.minimum_group == 0):
    #                         list_line = lines.filtered(
    #                             lambda l: (l.service_id.service_category in discount.product_ctg_ids) and (
    #                                     self.program_discount_id not in l.prg_ids))
    #                         quantity = sum(list_line.mapped('quantity'))
    #                         if (quantity >= discount.dc_min_qty) and (quantity <= discount.dc_max_qty):
    #                             self.set_discount(list_line, discount)
    #             if discount_product_ids:
    #                 discount_product_ids = discount_product_ids.sorted('dc_min_qty', reverse=True)
    #                 for discount in discount_product_ids:
    #                     if (discount.minimum_group - 1 >= len(self.crm_id.group_booking)) or (
    #                             discount.minimum_group == 0):
    #                         list_line = lines.filtered(lambda l: (l.product_id in discount.product_ids) and (
    #                                 self.program_discount_id not in l.prg_ids))
    #                         quantity = sum(list_line.mapped('quantity'))
    #                         if (quantity >= discount.dc_min_qty) and (quantity <= discount.dc_max_qty):
    #                             self.set_discount(list_line, discount)
    #     else:
    #         raise ValidationError('Không có bất kỳ line dịch vụ nào đủ điều kiện để áp dụng chương trình giảm giá !!!')
    #
    # def set_discount(self, lines, discount_line):
    #     for rec in lines:
    #         discount_rec = rec.prg_ids.mapped('discount_program_list')
    #         discounted = discount_rec.filtered(
    #             lambda
    #                 d: rec.product_id in d.product_ids or rec.service_id.service_category in d.product_ctg_ids).mapped(
    #             'incremental')
    #         if (all(discounted) and discount_line.incremental) or (discount_line and not discount_rec):
    #             if not rec.prg_ids or (
    #                     rec.prg_ids and 'sale_to' not in discount_line.mapped('type_discount') and rec.sale_to == 0):
    #                 discount = discount_line.discount
    #                 if discount_line.discount_bonus:
    #                     discount_list_le = self.program_discount_id.discount_program_list.filtered(
    #                         lambda dl: dl.index == 0 and ((rec.product_id in dl.product_ids) or (
    #                                 rec.service_id.service_category in dl.product_ctg_ids)) and dl.type_discount == discount_line.type_discount and not dl.discount_bonus)
    #                     discount_le = discount_list_le.discount if discount_list_le else 0
    #                     discount += discount_line.discount_bonus + discount_le
    #                 if discount_line.type_discount == 'percent':
    #                     rec.discount_percent += discount
    #                 elif discount_line.type_discount == 'cash':
    #                     rec.discount_cash += discount
    #                 else:
    #                     rec.sale_to = discount
    #                 rec.prg_ids = [(4, self.program_discount_id.id)]
    #                 self.crm_id.prg_ids = [(4, self.program_discount_id.id)]
    #                 self.env['crm.line.discount.history'].create({
    #                     'booking_id': self.crm_id.id,
    #                     'crm_line': rec.id,
    #                     'discount_program': self.program_discount_id.id,
    #                     'index': 0,
    #                     'type': 'discount',
    #                     'type_discount': discount_line.type_discount,
    #                     'discount': discount
    #                 })
    #                 if rec.stage == 'processing':
    #                     # Nếu line dv này có ở trạng thái đang xử lý cần sửa giá ở SO nữa
    #                     order_id = self.env['sale.order'].search(
    #                         [('booking_id', '=', self.crm_id.id), ('state', '=', 'draft')])
    #                     if order_id:
    #                         order_line_id = order_id.order_line.filtered(lambda l: l.crm_line_id == rec)
    #                         if order_line_id:
    #                             order_line_id.discount = rec.discount_percent
    #                             order_line_id.discount_cash = rec.discount_cash
    #                             order_line_id.sale_to = rec.sale_to
    #                     # Nếu có payment dạng nháp cũng sửa luôn nữa
    #                     walkin = self.env['sh.medical.appointment.register.walkin'].search(
    #                         [('sale_order_id', '=', order_id.id), ('state', 'in', ['Scheduled', 'WaitPayment'])])
    #                     if walkin:
    #                         payment = self.env['account.payment'].search(
    #                             [('crm_id', '=', self.crm_id.id), ('walkin', '=', walkin.id), ('state', '=', 'draft')])
    #                         if payment:
    #                             payment.amount = order_id.amount_total

    def create_crm_line_gift(self, product_id, discount_line):
        crm_line = self.env['crm.line'].create({
            'name': product_id.name,
            'product_id': product_id.id,
            'quantity': discount_line.gift,
            'unit_price': 0,
            'price_list_id': self.crm_id.price_list_id.id,
            'company_id': self.crm_id.company_id.id,
            'prg_ids': [(4, self.program_discount_id.id)],
            'source_extend_id': self.crm_id.source_id.id,
        })
        self.env['crm.line.discount.history'].create({
            'booking_id': self.crm_id.id,
            'crm_line': crm_line.id,
            'discount_program': self.program_discount_id.id,
            'index': discount_line.index,
            'type': 'gift',
        })
        self.crm_id.prg_ids = [(4, self.program_discount_id.id)]

    # def set_discount_combo(self, lines, index):
    #     # Lấy ra các discount trong CTKM có chỉ số là chỉ số truyền vào (Combo)
    #     discount_list_combo = self.program_discount_id.discount_program_list.filtered(lambda l: l.index == index)
    #     gift_ids = discount_list_combo.filtered(lambda l: l.gift)
    #     for gift in gift_ids:
    #         product_id = gift.mapped('product_ids')
    #         self.create_crm_line_gift(product_id, index)
    #
    #     rec_discounted_list = self.env['crm.line']  # danh sách đã add CTKM của combo
    #     discount_list_combo_discounted = self.env['crm.discount.program.list']  # danh sách discount đã add
    #     # Đầu vào là 1 list các line dịch vụ được add CTKM là combo và 1 chỉ số để xác định combo sẽ add trong CTKM
    #     for rec in lines:
    #         # Với thằng rec này tìm trong rec_discounted đã KM chưa nếu có rồi thì cộng số lượng để tính ra buổi
    #         rec_discount = discount_list_combo_discounted.filtered(
    #             lambda r: (rec.product_id in discount_list_combo_discounted.mapped('product_ids')) or (
    #                     rec.service_id.service_category in discount_list_combo_discounted.mapped('product_ctg_ids')))
    #         if rec_discount:
    #             quantity = sum(rec_discounted_list.mapped('quantity'))
    #         else:
    #             quantity = 0
    #         rec_quantity = rec.quantity + quantity
    #         # Từ danh sách lấy ra được lọc tìm tiếp lấy ra các discount có tên , số lượng mà line booking thỏa mãn
    #         product_discount = discount_list_combo.filtered(
    #             lambda l: ((rec.product_id in l.product_ids) or (rec.service_id.service_category in l.product_ctg_ids))
    #                       and (((l.dc_max_qty >= rec_quantity) and (l.dc_min_qty <= rec_quantity)) or (
    #                     len(self.crm_id.group_booking) <= (l.minimum_group - 1)))
    #                       and (not l.used))
    #         # Phần này sẽ kiểm tra tính cộng dồn: Nếu line bk chưa có CTKM, thì add thoải mái nhưng nếu có rồi ktra xem
    #         # line đó trong CTKM cũ có cộng dồn không và trong CTKM sắp add có đc cộng dồn không
    #         discount_rec = rec.prg_ids.mapped('discount_program_list')
    #         incremental = discount_rec.filtered(lambda d: (rec.product_id in d.product_ids) or (
    #                 rec.service_id.service_category in d.product_ctg_id)).mapped('incremental')
    #         if (product_discount and all(incremental) and product_discount.incremental) or (
    #                 product_discount and not discount_rec):
    #             discount_total = product_discount.discount
    #             # Nếu discount này có phần giảm giá bằng 0 thì tìm line lẻ mà line bk này thỏa mãn để add vào
    #             if product_discount.discount == 0 and product_discount.discount_bonus == 0:
    #                 discount_le = self.program_discount_id.discount_program_list.filtered(lambda l: (l.index == 0)
    #                                                                                                 and ((
    #                                                                                                              rec.product_id in l.product_ids) or (
    #                                                                                                              rec.service_id.service_category in l.product_ctg_ids))
    #                                                                                                 and ((
    #                                                                                                              rec.quantity >= l.dc_min_qty) and (
    #                                                                                                              rec.quantity <= l.dc_max_qty)))
    #
    #                 if discount_le:
    #                     discount_total += discount_le.discount
    #             # Phần này kiểm tra tiếp thỏa mãn điều kiện sale_to:
    #             if not rec.prg_ids or (
    #                     rec.prg_ids and 'sale_to' not in product_discount.mapped('type_discount') and rec.sale_to == 0):
    #                 # Nếu thỏa mãn thì  bắt đầu thực hiện giảm giá và sinh ra bản ghi lịch sử giảm giá
    #                 if product_discount.type_discount == 'percent':
    #                     rec.discount_percent += discount_total
    #                 elif product_discount.type_discount == 'cash':
    #                     rec.discount_cash += discount_total
    #                 else:
    #                     rec.sale_to = discount_total
    #                 rec.prg_ids = [(4, self.program_discount_id.id)]
    #                 self.crm_id.prg_ids = [(4, self.program_discount_id.id)]
    #                 rec_discounted_list += rec
    #                 discount_list_combo_discounted += product_discount
    #                 self.env['crm.line.discount.history'].create({
    #                     'booking_id': self.crm_id.id,
    #                     'crm_line': rec.id,
    #                     'discount_program': self.program_discount_id.id,
    #                     'type': 'discount',
    #                     'index': index,
    #                     'type_discount': product_discount.type_discount,
    #                     'discount': discount_total
    #                 })
    #
    #             else:
    #                 for record in rec_discounted_list:
    #                     crm_line_discount_history = self.env['crm.line.discount.history'].search(
    #                         [('crm_line', '=', record.id), ('booking_id', '=', self.crm_id.id),
    #                          ('discount_program', '=', self.program_discount_id.id),
    #                          ('index', '=', index), ('type', '=', 'discount')], limit=1)
    #                     if crm_line_discount_history:
    #                         vals = {
    #                             'prg_ids': [(3, self.program_discount_id.id)],
    #                         }
    #                         cases = {'percent': {'field': 'discount_percent',
    #                                              'value': record.discount_percent - crm_line_discount_history.discount},
    #                                  'cash': {'field': 'discount_cash',
    #                                           'value': record.discount_cash - crm_line_discount_history.discount},
    #                                  'sale_to': {'field': 'sale_to',
    #                                              'value': record.sale_to - crm_line_discount_history.discount}
    #                                  }
    #                         type_discount = crm_line_discount_history.type_discount
    #                         vals[cases.get(type_discount).get('field')] = cases.get(type_discount).get('value')
    #                         record.write(vals)
    #                 crm_line_gift_history = self.env['crm.line.discount.history'].search(
    #                     [('booking_id', '=', self.crm_id.id),
    #                      ('discount_program', '=', self.program_discount_id.id),
    #                      ('index', '=', index), ('type', '=', 'gift')], limit=1)
    #                 if crm_line_gift_history:
    #                     self.crm_id.crm_line_ids = [(3, crm_line_gift_history.crm_line.id)]
    #
    #     if len(lines) != len(rec_discounted_list):
    #         for record in rec_discounted_list:
    #             crm_line_discount_history = self.env['crm.line.discount.history'].search(
    #                 [('crm_line', '=', record.id),
    #                  ('discount_program', '=', self.program_discount_id.id),
    #                  ('index', '=', index), ('type', '=', 'discount')], limit=1)
    #             if crm_line_discount_history:
    #                 vals = {
    #                     'prg_ids': [(3, self.program_discount_id.id)],
    #                 }
    #                 cases = {'percent': {'field': 'discount_percent',
    #                                      'value': record.discount_percent - crm_line_discount_history.discount},
    #                          'cash': {'field': 'discount_cash',
    #                                   'value': record.discount_cash - crm_line_discount_history.discount},
    #                          'sale_to': {'field': 'sale_to',
    #                                      'value': record.sale_to - crm_line_discount_history.discount}
    #                          }
    #                 type_discount = crm_line_discount_history.type_discount
    #                 vals[cases.get(type_discount).get('field')] = cases.get(type_discount).get('value')
    #                 record.write(vals)
    #                 crm_line_discount_history.unlink()
    #         crm_line_gift_history = self.env['crm.line.discount.history'].sudo().search(
    #             [('booking_id', '=', self.crm_id.id),
    #              ('discount_program', '=', self.program_discount_id.id),
    #              ('index', '=', index),
    #              ('type', '=', 'gift')], limit=1)
    #         if crm_line_gift_history:
    #             self.crm_id.crm_line_ids = [(3, crm_line_gift_history.crm_line.id)]
    #             crm_line_gift_history.unlink()
    #
    #     # đối với những line dv đã đc áp dụng CTKM,nếu ở trạng thái đang xử lý cần tìm SO và payment nháp để sửa giá
    #     for record in rec_discounted_list:
    #         if record.stage == 'processing':
    #             # Nếu line dv này có ở trạng thái đang xử lý cần sửa giá ở SO nữa
    #             order_id = self.env['sale.order'].search(
    #                 [('booking_id', '=', self.crm_id.id), ('state', '=', 'draft')])
    #             if order_id:
    #                 order_line_id = order_id.order_line.filtered(lambda l: l.crm_line_id == rec)
    #                 if order_line_id:
    #                     order_line_id.discount = record.discount_percent
    #                     order_line_id.discount_cash = record.discount_cash
    #                     order_line_id.sale_to = record.sale_to
    #             # Nếu có payment dạng nháp cũng sửa luôn nữa
    #             walkin = self.env['sh.medical.appointment.register.walkin'].search(
    #                 [('sale_order_id', '=', order_id.id), ('state', 'in', ['Scheduled', 'WaitPayment'])])
    #             if walkin:
    #                 payment = self.env['account.payment'].search(
    #                     [('crm_id', '=', self.crm_id.id), ('walkin', '=', walkin.id), ('state', '=', 'draft')])
    #                 if payment:
    #                     payment.amount = order_id.amount_total
