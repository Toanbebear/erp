from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from itertools import zip_longest


class InheritApplyCouponType3(models.TransientModel):
    _inherit = 'crm.apply.coupon'
    _description = 'Inherit Apply Coupon Type 3'

    # giảm giá theo combo
    def combo_service_coupon(self):
        self.get_index()
        index = self.index
        list_not_availble = []
        for line, line_pro in zip_longest(self.line_ids, self.line_product_ids, fillvalue=None):
            for discount in self.coupon_id.discount_program_list:
                if discount.index == index:
                    if self.check_crm_line(discount, line) is True or self.check_crm_line(discount, line_pro) is True:
                        if self.check_incremental(discount, line) is False:
                            list_not_availble.append(line)
                        if self.check_incremental(discount, line_pro) is False:
                            list_not_availble.append(line_pro)
        if len(list_not_availble) > 0:
            string = ''
            for rec in self.check_suitable_combo(list_not_availble):
                string += rec.service_id.name
                string += ', '
            raise ValidationError('Dịch vụ %s không thể áp dụng %s cùng với coupon trước đó' % (string, self.coupon_id.name))
            # self.mes_success()

        for line, line_pro in zip_longest(self.line_ids, self.line_product_ids, fillvalue=None):
            for discount in self.coupon_id.discount_program_list:
                # bổ sung crm_line_ids_select + combo_select
                if discount.index == index and self.check_quantity(discount) is True:
                    if self.check_crm_line(discount, line) is True:
                        self.apply_discount(discount, line)
                    elif self.check_crm_line(discount, line_pro) is True:
                        self.apply_discount(discount, line_pro)

    def select_combo_index(self, indexs):
        for index in indexs:
            check = False
            note = ''
            if len(indexs) == 1:
                check = True
            for rec in self.coupon_id.discount_program_list:
                if index == rec.index:
                    note = rec.combo_note
            self.env['crm.apply.coupon.detail'].create({
                'check': check,
                'apply_coupon_id': self.id,
                'index': index,
                'combo_note': note,
            })

    # Kiểm tra số lượng
    # input: line trong coupon và line trong booking/lead
    # ouput: True/Fasle
    def check_quantity(self, discount):
        quantity = 0
        for line, line_pro in zip_longest(self.line_ids, self.line_product_ids, fillvalue=None):
            if self.check_crm_line(discount, line) is True:
                quantity += line.quantity_charged
            if self.check_crm_line(discount, line_pro) is True:
                quantity += line_pro.product_uom_qty
        if discount.dc_min_qty <= quantity <= discount.dc_max_qty:
            result = True
        elif discount.discount_program.coupon_type == '4' and discount.dc_min_qty <= quantity:
            result = True
        else:
            result = False
        return result

    # loại bỏ các index trùng
    # input: list_available_combo
    # ouput: danh sách index phù hợp
    def check_suitable_combo(self, list_index):
        if len(list_index) != 0:
            list_index = set(list_index)
            list_index = list(list_index)
        return list_index

    # kiểm tra trường hợp combo bắt buộc phải có 1 dịch vụ/nhóm dịch vụ trong line booking/lead
    def check_required_combo(self, discount):
        check = False
        if discount.required_combo is True:
            for line, line_pro in zip_longest(self.line_ids, self.line_product_ids, fillvalue=None):
                if self.check_crm_line(discount, line) is True:
                    check = True
                if self.check_crm_line(discount, line_pro) is True:
                    check = True
        else:
            check = True
        coupon = discount.discount_program
        if coupon.coupon_type == '7' and coupon.type_data_partner != self.partner_id.type_data_partner:
            check = False
        return check

    # lấy danh sách index, loại bỏ các trường hợp không đủ số lượng, không có dịch vụ/nhóm dịch vụ bắt buộc
    # ouput: danh sách các index có thể áp dụng
    def list_available_combo(self, coupon_id):
        discount_index = []
        remove_index = []
        result_index = []
        # kiểm tra từng discount list trong coupon nếu khả dụng thì thêm vào danh sách discount_index ngược lại thì thêm vào danh sách remove_index
        for line in self.line_ids:
            if len(line.prg_ids.ids) > 0:
                self.line_ids -= line
        line_service = self.line_ids
        line_product = self.line_product_ids
        for line, line_pro in zip_longest(line_service, line_product, fillvalue=None):
            for discount in coupon_id.discount_program_list:
                if self.check_quantity(discount) is True and self.check_required_combo(discount) is True:
                    # if self.check_crm_line(discount, line) is True or self.check_crm_line(discount, line_pro) is True:
                    discount_index.append(discount.index)
                elif self.check_quantity(discount) is False and discount.required_combo is True:
                    remove_index.append(discount.index)
                if coupon_id.coupon_type == '8' and self.check_list_product_used(discount) is False:
                    remove_index.append(discount.index)
                # khong cho cong don coupon tat ca cac loai
                if line and line.prg_ids:
                    remove_index.append(discount.index)


        # sau khi kiểm tra thì loại bỏ các các index trong discount_index có trong remove index
        if discount_index:
            for index in discount_index:
                if index not in remove_index:
                    result_index.append(index)
        return result_index

    def check_crm_line(self, discount, line):
        if discount.type_product == 'product':
            if line and line.product_id in discount.product_ids:
                return True
        else:
            if line and line.product_id.type == 'service':
                if line.service_id.service_category in discount.product_ctg_ids:
                    return True

    # Kiểm tra kiểu giảm giá và gán giá trị giảm vào crm_line_ids cộng dồn
    def apply_discount(self, discount, line):
        deposit = self.env['crm.request.deposit'].search([('booking_id', '=', self.crm_id.id), ('coupon_id', '=', self.coupon_id.id)])
        if deposit:
            pass
        for rec in deposit:
            rec.used = True

        if discount.limit_discount < 1:
            raise ValidationError('Coupon đã hết lượt sử dụng, kiểm tra lại trong Coupon chi tiết')
        else:
            discount.limit_discount -= 1

        line.prg_ids += self.coupon_id
        self.crm_id.prg_ids += self.coupon_id
        if discount.type_discount == 'percent':
            line.discount_percent += discount.discount
            line.discount_percent += discount.discount_bonus
        elif discount.type_discount == 'cash':
            if line.product_id.type == 'service':
                quantity = line.quantity_charged
            else:
                quantity = line.product_uom_qty
            line.discount_cash += discount.discount * quantity
            line.discount_cash += discount.discount_bonus * quantity
        else:
            line.sale_to = discount.discount
            line.sale_to -= discount.discount_bonus

        self.create_history(discount, line)
        self.update_sale_order(line)

    def check_program_discount_new(self, discount, line):
        check = False
        for program in line.prg_ids:
            if self.coupon_id.id == program.id:
                raise ValidationError('Coupon %s đã được áp dụng trên dịch vụ %s trước đó' % (self.coupon_id.name, line.product_id.name))
            for coupon in discount.not_incremental_coupon:
                if coupon.id == program.id:
                    check = True
        return check

    def check_program_discount_exist(self, line):
        check = False
        for coupon in line.prg_ids.discount_program_list:
            if coupon.incremental is False:
                check = True
            for discount in coupon.not_incremental_coupon:
                if discount.id == self.coupon_id.id:
                    check = True
        return check

    # kiểm tra cộng dồn trong discount.program.list đối với coupon thêm mới
    def check_incremental(self, discount, line):
        check = True
        if line and len(line.prg_ids) > 0:
            if discount.incremental is True:
                if self.check_program_discount_new(discount, line) is True or self.check_program_discount_exist(
                        line) is True:
                    check = False
            else:
                check = False
        return check






