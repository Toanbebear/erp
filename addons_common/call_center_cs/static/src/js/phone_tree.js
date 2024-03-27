odoo.define('call_center_cs.PhoneTree', function (require) {
    "use strict";

    var basicFields = require('web.basic_fields');
    var core = require('web.core');
    var config = require('web.config');
    var Dialog = require('web.Dialog');
    var session = require('web.session');
    var fieldRegistry = require('web.field_registry');
    var _t = core._t;

    var PhoneTree = basicFields.FieldChar.extend({
        supportedFieldTypes: ['char'],

        _renderReadonly: function () {
            this._super.apply(this, arguments);
            this.encrypt_phone = session.encrypt_phone;

            var maskPhone;
            if (this.encrypt_phone === 'True') {
                maskPhone = this.maskPhoneNumber(this.value);
            } else {
                maskPhone = this.value;
            }
            this.$el.html(maskPhone);
        },

//        Thay 4 số giữa, hiển thị 3 số cuối
        maskPhoneNumber: function (phoneNumber) {
          // Kiểm tra xem số điện thoại có đủ 10 chữ số không
          if (phoneNumber.length >= 10) {
            // Giữ 3 số cuối
            var slice_4 = phoneNumber.length - 3;
            var slice_mid_4 = phoneNumber.length - 7;

            var lastFourDigits = phoneNumber.slice(slice_4);
            var middleFourDigits = phoneNumber.slice(slice_mid_4, slice_4);
            var firstDigits = phoneNumber.slice(0, slice_mid_4);

            // Tạo chuỗi "xxxx" có độ dài bằng với 4 số cuối
            var mask = "x".repeat(middleFourDigits.length);

            // Thay thế 4 số cuối bằng chuỗi "xxxx"
            var maskedNumber = firstDigits + mask + lastFourDigits;

            return maskedNumber;
          } else {
            // Trả về số điện thoại không thay đổi nếu không đủ 10 chữ số
            return phoneNumber;
          }
        }
    });

    fieldRegistry.add('phone_tree', PhoneTree);

    return PhoneTree;
});