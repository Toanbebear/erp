odoo.define('sci_smart_button.smart_button_calendar', function (require) {
'use strict';

    var CalendarRenderer = require('web.CalendarRenderer');
    CalendarRenderer.include({


        events : _.extend({}, CalendarRenderer.prototype.events, {
            "click .btn-smart-parent" : "_onclick_btn_smart_parent",
            "click .btn-smart-child" : "_onclick_btn_smart_child",
            "click #btn-send-feedback" : "_onclick_btn_send_feedback",
            "click .close-popup-feedback" : "_close_popup_feedback",
        }),

        /**
         * @override
         */


    });




});
