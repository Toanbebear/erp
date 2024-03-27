odoo.define('call_center_cs.PhoneField', function (require) {
"use strict";

const basicFields = require('web.basic_fields');
const core = require('web.core');
const config = require('web.config');
var Dialog = require('web.Dialog');
var session = require('web.session');
const Phone = basicFields.FieldPhone;
const _t = core._t;
const DialingPanel = require('voip.DialingPanel');

var ajax = require('web.ajax');
if (config.device.isMobile) {
    Phone.include({



    /**
     * Reset the star display status.
     *
     * @private
     */
     init: function (){
        this._super.apply(this, arguments);
        this.encrypt_phone = session.encrypt_phone;
    },



    _renderReadonly: function () {
        var def = this._super.apply(this, arguments);
        var maskPhone;
        if (this.encrypt_phone == 'True'){
            maskPhone = this.maskPhoneNumber(this.value);
            //        phân quyền xem số điện thoại
            var self = this;
            session.user_has_group('call_center_cs.group_phone_display').then(function(has_group) {
                if (has_group) {
                    var $ShowButton = $('<a>', {
                        title: _t('Hiển thị số điện thoại'),
                        href: '',
                        class: 'ml-3 d-inline-flex align-items-center',
                        html: $('<strong>', {class: 'font-weight-bold ml-1'}),
//                        click: self._onClickShow.bind(self),
                    });
                    $ShowButton.on('click', function(ev) {
                        ev.preventDefault();
                        self._copyPhoneNumberToClipboard(); // copy số điện thoại
                        self._onClickShow(ev); // hiển thị số điện thoại
                    });
                    $ShowButton.prepend($('<i>', {class: 'fa fa-eye'}));
                    var $buttonContainer = $('<span/>', {class: 'my-button-container'});
                    $buttonContainer.append($ShowButton);
                    self.$el.append($buttonContainer);
                }
            });

        } else{
            maskPhone = this.value;
        }

        this.$el.attr('href', "#");
        this.$el.html(maskPhone);


        return def;
    },
    _copyPhoneNumberToClipboard: function() {
        var phoneNumber = this.value;
        var tempInput = document.createElement("input");
        document.body.appendChild(tempInput);
        tempInput.value = phoneNumber;
        tempInput.select();
        document.execCommand("copy");
        document.body.removeChild(tempInput);
    },


       _onClickShow: function (ev) {
                ev.preventDefault();
                if (this.mode !== 'readonly') {
                    return;
                }
                // Hiển thị số điện thoại thực tế
                var phoneNumber = this.value;
        //        Dialog.alert(this, phoneNumber, {
        //            title: 'Số điện thoại',
        //        });
        //        this.do_notify("Đã sao chép số điện thoại khách hàng",_.str.sprintf(phoneNumber));
        //        this.do_notify("Đã sao chép số điện thoại khách hàng", phoneNumber, true, 'o_partner_autocomplete_test_notify');
                var self = this; // Lưu trữ ngữ cảnh this
                var notification = self.do_notify("Đã sao chép số điện thoại khách hàng ", phoneNumber, true, 'o_partner_autocomplete_test_notify');

                setTimeout(function() {
                    var closeButton = document.querySelector('[aria-label="Close"]');
                    if (closeButton) {
                        closeButton.click();
                    }
                }, 10000);
        //        console.log("Đã vào hàm _onClickShow", phoneNumber);

        },

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
    return
}

/**
 * Override of FieldPhone to use the DialingPanel to perform calls on clicks.
 */
Phone.include({
    events: Object.assign({}, Phone.prototype.events, {
        //'click': '_onClick',
        'click .phone': '_onClickPhone',
            'mouseout .phone': '_onMouseOut',
    }),

    init: function (){
        this._super.apply(this, arguments);
        this.get_token = {};
        this.cs_window = false;
        this.encrypt_phone = session.encrypt_phone;
    },

    start : function(){
        console.log(this);

        $(this.$el).data('res_id', this.res_id);
        $(this.$el).data('res_model', this.model);
        return this._super.apply(this, arguments);

    },

//    willStart: function () {
//    console.log('willStart');
//        var self = this;
//
//        var promises = [];
//        if(self.value){
//            var config = ajax.jsonRpc("/caresoft/encrypt_phone", 'call', {})
//            .then(function (result) {
//                if (result) {
//                    console.log('aaaaaaaaaaaa');
//                    console.log(result);
//                    self.encrypt_phone = result;
//                }
//            });
//            promises.push(self.encrypt_phone);
//        }
//        var parentInit = self._super.apply(self, arguments);
//        promises.push(parentInit);
//        return Promise.all(promises);
//    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * Called when the phone number is clicked.
     *
     * @private
     * @param {MouseEvent} ev
     */
    _onClick(ev) {
        ev.preventDefault();
        if (this.mode !== 'readonly') {
            return;
        }

        if(this.value && this.get_token){
            var $fieldPhone = this.$('.phone_tooltip');

            navigator.clipboard.writeText(this.value);
            this.$el.find('.tooltiptext')[0].innerHTML = 'Đã sao chép!';

//            setTimeout(function () {
//                $fieldPhone.hide();
//            }, 800);

//            // TÌm token trong db, uid và time
//            // Nếu hết time thì gọi sang caresoft
//            var token = this.get_token.token;
//            var link_caresoft = this.get_token.cs_url;
//
//            var href = link_caresoft + '?token=' + token + '&number=' + this.value;
//            console.log(href);
//            this.cs_window = window.open(href, '', 'menubar=no,toolbar=no,resizable=yes,scrollbars=yes,height=550,width=600');
//            //this.cs_window.document.write("<p>This is 'myWindow'</p>");
////            this.cs_window.onbeforeunload = function () {
////                alert('Test');
////            };
//            var self = this;
//            var timer = setInterval(function() {
//                if(self.cs_window.closed) {
//                    clearInterval(timer);
//                    console.log('Lưu log cuộc gọi');
//                }
//            }, 1000);

        }

    },

    /**
     * Reset the star display status.
     *
     * @private
     */
    _onMouseOut: function () {
        this.$el.find('.tooltiptext')[0].innerHTML = 'Click để gọi bằng Voice, có thể dùng máy bàn!';
    },

   _onClickSMS: function (ev) {
        ev.preventDefault();
        var self = this;
        var context = session.user_context;

        var crm_id = false;

        if (this.model == 'crm.phone.call'){
            context = _.extend({}, context, {
                default_res_model: this.model,
                default_res_id: parseInt(this.res_id),
                default_phone: this.value,
                default_crm_id: this.recordData.crm_id.res_id,
                default_contact_name: this.recordData.contact_name,
                default_company_id: this.recordData.company_id.res_id,
                default_name: this.recordData.subject,
                default_partner_id: this.recordData.partner_id.res_id,
            });
        } else if (this.model == 'crm.lead'){
            context = _.extend({}, context, {
                default_res_model: this.model,
                default_phone: this.value,
                default_name: "SMS",
                default_crm_id: parseInt(this.res_id),
                default_contact_name: this.recordData.contact_name,
                default_company_id: this.recordData.company_id.res_id,
                default_partner_id: this.recordData.partner_id.res_id,
            });
        } else if (this.model == 'res.partner'){
            context = _.extend({}, context, {
                default_res_model: this.model,
                default_name: "SMS",
                default_phone: this.value,
                default_contact_name: this.recordData.name,
                default_partner_id: parseInt(this.res_id),
            });
        }else{
            console.log('Update context');
        }


        return this.do_action({
            title: _t('Send SMS Text Message'),
            type: 'ir.actions.act_window',
            res_model: 'crm.sms',
            target: 'new',
            views: [[false, 'form']],
            context: context,
        }, {
            on_close: function () {
                //self.trigger_up('reload');
            }
            }
        );
    },

    _onClickOpenAccountCS: function(ev){
        ev.preventDefault();
        var self = this;
        ajax.jsonRpc("/caresoft/search-account", 'call', {
            res_model: this.model,
            value : this.value,
            res_id : parseInt(this.res_id),
        }).then(function (result) {
             if(result.status == 0){
                window.open(result.url, '_blank')

             }else {
                const content = result.message;
                                new Dialog(this, {
                                        size: 'medium',
                                        title: "Thông báo",
                                        $content: $('<div>'+content+'</div>'),
                                        buttons: [{
                                            text: _t("Đóng"),
                                            close: true,
                                        }],
                                    }).open();
             }
             //csCallout(self.value);

        });
    },

//    hiển thị số điện thoại
   _onClickShow: function (ev) {
        ev.preventDefault();
        if (this.mode !== 'readonly') {
            return;
        }
        // Hiển thị số điện thoại thực tế
        var phoneNumber = this.value;
//        Dialog.alert(this, phoneNumber, {
//            title: 'Số điện thoại',
//        });
//        this.do_notify("Đã sao chép số điện thoại khách hàng",_.str.sprintf(phoneNumber));
//        this.do_notify("Đã sao chép số điện thoại khách hàng", phoneNumber, true, 'o_partner_autocomplete_test_notify');
        var self = this; // Lưu trữ ngữ cảnh this
        var notification = self.do_notify("Đã sao chép số điện thoại khách hàng ", phoneNumber, true, 'o_partner_autocomplete_test_notify');

        setTimeout(function() {
            var closeButton = document.querySelector('[aria-label="Close"]');
            if (closeButton) {
                closeButton.click();
            }
        }, 10000);
//        console.log("Đã vào hàm _onClickShow", phoneNumber);

},

// in sdt rùi sao chép
_copyPhoneNumberToClipboard: function() {
    var phoneNumber = this.value;
    var tempInput = document.createElement("input");
    document.body.appendChild(tempInput);
    tempInput.value = phoneNumber;
    tempInput.select();
    document.execCommand("copy");
    document.body.removeChild(tempInput);
},

   _onVoice: function (ev) {
           ev.preventDefault();
        var self = this;

        if (this.mode !== 'readonly') {
            return;
        }
        var res_id = $('.o_field_phone').data('res_id');
        var res_model = $('.o_field_phone').data('res_model');
        console.log(res_id)
        console.log(res_model)
        ajax.jsonRpc("/caresoft/voice_token", 'call', {
            res_model : res_model,
            res_id : res_id,
        }).then(function (result) {
             csInit(result.token, result.domain);
             //csCallout(self.value);

        });
   },

   _onClickPhone: async function (ev) {
        ev.preventDefault();
        $(ev.currentTarget).parent().find('.o_field_phone').trigger('click');
        setTimeout(async function(){
            await $('.o_dial_enable_button').trigger("click");
            await $('.o_dial_ear_phone_button').trigger("click");
            await $('.o_dial_call_button').trigger('click');
        }, 2000);

//        var self = this;
//
//        if (this.mode !== 'readonly') {
//            return;
//        }
//
//        if(self.value){
//
//            console.log("ev");
//            console.log(ev);
//            var res_id = $('.o_field_phone').data('res_id');
//            var res_model = $('.o_field_phone').data('res_model');
//            var get_token = ajax.jsonRpc("/caresoft/token", 'call', {
//                res_model : res_model,
//                res_id : res_id,
//            })
//            .then(function (content) {
//                if (content) {
//                    self.get_token = content;
//                    if(self.value && self.get_token){
//                        if (content.status == 'error'){
//                            Dialog.alert(self, content.message, {
//                                title: 'Thông báo',
//                            });
//                        }else{
//                            // TÌm token trong db, uid và time
//                            // Nếu hết time thì gọi sang caresoft
//                            var token = self.get_token.token;
//                            var link_caresoft = self.get_token.cs_url;
//                            if (link_caresoft){
//                                var href = link_caresoft + '?token=' + token + '&number=' + self.value;
//
//                                self.cs_window = window.open(href, '', 'menubar=no,toolbar=no,resizable=yes,scrollbars=yes,height=550,width=600');
//                    //            this.cs_window.onbeforeunload = function () {
//                    //                alert('Test');
//                    //            };
//                                var timer = setInterval(function() {
//                                    if(self.cs_window.closed) {
//                                        clearInterval(timer);
//                                        // console.log('Mở log cuộc gọi ');
//                                    }
//                                }, 1000);
//                            } else{
//                                const content = `Chưa cấu hình IP Phone Caresoft. Vui lòng liên hệ phòng IT để được hỗ trợ.`;
//                                new Dialog(this, {
//                                        size: 'medium',
//                                        title: "Thông báo",
//                                        $content: $('<div>'+content+'</div>'),
//                                        buttons: [{
//                                            text: _t("Đóng"),
//                                            close: true,
//                                        }],
//                                    }).open();
//                            }
//                        }
//                    }
//                }
//            });
//        }

    },

    _renderReadonly: function () {
        var def = this._super.apply(this, arguments);

        var $phoneButton = $('<a>', {
            title: _t('Gọi điện thoại'),
            href: '',
            class: 'mr-1 d-inline-flex align-items-center o_field_phone_cs',
            html: $('<strong>', {class: 'fa fa-phone'}),
        });
        $phoneButton.before($('<i>', {class: 'fa fa-phone'}));
        $phoneButton.on('click', this._onClickPhone.bind(this));


        this.$el.addClass('phone_tooltip');
        this.$el.on('mouseout', this._onMouseOut.bind(this));
        var maskPhone;
        if (this.encrypt_phone == 'True'){
            maskPhone = this.maskPhoneNumber(this.value);
            //        phân quyền xem số điện thoại
            var self = this;
            session.user_has_group('call_center_cs.group_phone_display').then(function(has_group) {
                if (has_group) {
                    var $ShowButton = $('<a>', {
                        title: _t('Hiển thị số điện thoại'),
                        href: '',
                        class: 'ml-3 d-inline-flex align-items-center',
                        html: $('<strong>', {class: 'font-weight-bold ml-1'}),
//                        click: self._onClickShow.bind(self),
                    });
                    $ShowButton.on('click', function(ev) {
                        ev.preventDefault();
                        self._copyPhoneNumberToClipboard(); // copy số điện thoại
                        self._onClickShow(ev); // hiển thị số điện thoại
                    });
                    $ShowButton.prepend($('<i>', {class: 'fa fa-eye'}));
                    var $buttonContainer = $('<span/>', {class: 'my-button-container'});
                    $buttonContainer.append($ShowButton);
                    self.$el.append($buttonContainer);
                }
            });

        } else{
            maskPhone = this.value;
        }

        this.$el.attr('href', "#");
        this.$el.html(maskPhone +'<span class="tooltiptext">Click để gọi bằng Voice, có thể dùng máy điện thoại bàn</span>');
        this.$el = $('<span/>').append($phoneButton).append(this.$el);

        var $composerButton = $('<a>', {
            title: _t('Gửi tin nhắn'),
            href: '',
            class: 'ml-3 d-inline-flex align-items-center o_field_phone_sms',
            html: $('<small>', {class: 'font-weight-bold ml-1', html: 'SMS'}),
        });
        $composerButton.prepend($('<i>', {class: 'fa fa-mobile'}));
        $composerButton.on('click', this._onClickSMS.bind(this));

//        var $voice = $('<a>', {
//            title: _t('Gọi điện bằng máy IP Phone'),
//            href: '',
//            class: 'ml-3 d-inline-flex align-items-center o_field_phone_cs_voice',
//            html: $('<strong>', {class: 'fa fa-mobile'}),
//        });
//        $voice.before($('<i>', {class: 'fa fa-mobile'}));
//        $voice.on('click', this._onVoice.bind(this));

//        this.$el = $('<span/>').append(this.$el).append($voice).append($composerButton);
        this.$el = $('<span/>').append(this.$el).append($composerButton);

        var $composerButtonAccountCS = $('<a>', {
            title: _t('Mở account khách hàng trên caresoft'),
            href: '',
            class: 'ml-3 d-inline-flex align-items-center o_field_open_account_cs',
            html: $('<small>', {class: 'font-weight-bold ml-1', html: ''}),
        });
        $composerButtonAccountCS.prepend($('<i>', {class: 'fa fa-search'}));
        $composerButtonAccountCS.on('click', this._onClickOpenAccountCS.bind(this));
        this.$el = $('<span/>').append(this.$el).append($composerButtonAccountCS);
        return def;
    },

//    maskPhoneNumber: function (phoneNumber) {
//      // Kiểm tra xem số điện thoại có đủ 10 chữ số không
//      if (phoneNumber.length >= 10) {
//        // Sử dụng phép cắt để lấy 4 số cuối
//        var lastFourDigits = phoneNumber.slice(5);
//
//        // Tạo chuỗi "xxxxx" có độ dài bằng với 5 số cuối
//        var mask = "x".repeat(lastFourDigits.length);
//
//        // Thay thế 4 số cuối bằng chuỗi "xxxx"
//        var maskedNumber = phoneNumber.slice(0, 5) + mask;
//
//        return maskedNumber;
//      } else {
//        // Trả về số điện thoại không thay đổi nếu không đủ 10 chữ số
//        return phoneNumber;
//      }
//    }
//// Thay 4 số giữa
//    maskPhoneNumber: function (phoneNumber) {
//      // Kiểm tra xem số điện thoại có đủ 10 chữ số không
//      if (phoneNumber.length >= 10) {
//        // Giữ 4 số cuối
//        var slice_4 = phoneNumber.length - 4;
//        var slice_mid_4 = phoneNumber.length - 8;
//
//        var lastFourDigits = phoneNumber.slice(slice_4);
//        var middleFourDigits = phoneNumber.slice(slice_mid_4, slice_4);
//        var firstDigits = phoneNumber.slice(0, slice_mid_4);
//
//        // Tạo chuỗi "xxxx" có độ dài bằng với 4 số cuối
//        var mask = "x".repeat(middleFourDigits.length);
//
//        // Thay thế 4 số cuối bằng chuỗi "xxxx"
//        var maskedNumber = firstDigits + mask + lastFourDigits;
//
//        return maskedNumber;
//      } else {
//        // Trả về số điện thoại không thay đổi nếu không đủ 10 chữ số
//        return phoneNumber;
//      }
//    }
// Thay 4 số giữa, hiển thị 3 số cuối
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

});
