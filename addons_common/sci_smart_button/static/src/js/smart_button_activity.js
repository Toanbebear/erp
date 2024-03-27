odoo.define('sci_smart_button.smart_button_activity', function (require) {
'use strict';

    var ActivityRenderer = require('mail.ActivityRenderer');



    ActivityRenderer.include({


        events : _.extend({}, ActivityRenderer.prototype.events,{
            "click .btn-smart-parent" : "_onclick_btn_smart_parent",
            "click .btn-smart-child" : "_onclick_btn_smart_child",
            "click #btn-send-feedback" : "_onclick_btn_send_feedback",
            "click .close-popup-feedback" : "_close_popup_feedback",
        }),



    });





});
