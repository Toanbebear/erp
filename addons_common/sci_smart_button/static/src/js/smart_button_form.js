odoo.define('sci_smart_button.smart_button', function (require) {
'use strict';

    var FormRenderer = require('web.FormRenderer');
    FormRenderer.include({


        events : _.extend({}, FormRenderer.prototype.events, {
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
