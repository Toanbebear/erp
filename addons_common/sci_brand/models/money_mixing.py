import base64
from io import BytesIO

from odoo import models

class MoneyMixin(models.AbstractModel):
    _name = 'money.mixin'
    _description = 'Money Mixin'

    def num2words_vnm(self, num):
        under_20 = ['không', 'một', 'hai', 'ba', 'bốn', 'năm', 'sáu', 'bảy', 'tám', 'chín', 'mười', 'mười một',
                    'mười hai', 'mười ba', 'mười bốn', 'mười lăm', 'mười sáu', 'mười bảy', 'mười tám', 'mười chín']
        tens = ['hai mươi', 'ba mươi', 'bốn mươi', 'năm mươi', 'sáu mươi', 'bảy mươi', 'tám mươi', 'chín mươi']
        above_100 = {100: 'trăm', 1000: 'nghìn', 1000000: 'triệu', 1000000000: 'tỉ'}

        if num < 20:
            return under_20[num]

        elif num < 100:
            under_20[1], under_20[5] = 'mốt', 'lăm'  # thay cho một, năm
            result = tens[num // 10 - 2]
            if num % 10 > 0:  # nếu num chia 10 có số dư > 0 mới thêm ' ' và số đơn vị
                result += ' ' + under_20[num % 10]
            return result

        else:
            unit = max([key for key in above_100.keys() if key <= num])
            result = self.num2words_vnm(num // unit) + ' ' + above_100[unit]
            if num % unit != 0:
                if num > 1000 and num % unit < unit / 10:
                    result += ' không trăm'
                if 1 < num % unit < 10:
                    result += ' linh'
                result += ' ' + self.num2words_vnm(num % unit)
        return result.capitalize()