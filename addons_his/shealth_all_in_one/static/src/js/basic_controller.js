odoo.define('shealth_all_in_one.BasicController', function (require) {
"use strict";

    var BasicController = require('web.BasicController');
    var core = require('web.core');
    var Dialog = require('web.Dialog');
    var _t = core._t;

    BasicController.include({
        canBeDiscarded: function (recordID) {
            var self = this;
            if (!this.isDirty(recordID)) {
                return Promise.resolve(false);
            }

            var model_change = recordID.split("_")[0];
            if(model_change == this.modelName){
                var message = _t("Bản ghi đã được sửa đổi, các thay đổi của bạn sẽ bị mất. Bạn có muốn tiếp tục?");
            }else{
                var message = _t("Bản ghi đã được sửa đổi và các giá trị bạn nhập đang không hợp lệ (các trường bôi đỏ). Bạn có muốn hủy bỏ bản ghi đang lỗi này?");
            }

            var def;
            def = new Promise(function (resolve, reject) {
                var dialog = Dialog.confirm(self, message, {
                    title: _t("Thông báo"),
                    confirm_callback: resolve.bind(self, true),
                    cancel_callback: reject,
                });
                dialog.on('closed', def, reject);
            });
            return def;
        },
    });
});
	
