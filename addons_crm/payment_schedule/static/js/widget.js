odoo.define('crm_base.StatementNotificationWidget', function (require) {
    "use strict";

    var basicFields = require('web.basic_fields');
    var core = require('web.core');
    var config = require('web.config');
    var session = require('web.session');
    var fieldRegistry = require('web.field_registry');
    var _t = core._t;

    var StatementNotificationWidget = basicFields.FieldChar.extend({
        supportedFieldTypes: ['char'],

        _renderReadonly: function () {
            this._super.apply(this, arguments);
            this.show_notification = session.show_notification;
            var show_notification = this.value;
            if (show_notification) {
                // Hiển thị thông báo nếu show_notification có giá trị
                var notification = this.do_notify("Lịch trình thanh toán tiếp theo là ngày", show_notification, true, 'o_partner_autocomplete_test_notify');
                setTimeout(function() {
                    var closeButton = document.querySelector('[aria-label="Close"]');
                    if (closeButton) {
                        closeButton.click();
                    }
                }, 10000);
            }
        }
    });

    fieldRegistry.add('statement_notification_widget', StatementNotificationWidget);

    return StatementNotificationWidget;
});