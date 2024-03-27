odoo.define('sci_smart_button.smart_button_list', function (require) {
'use strict';

    var ListRenderer = require('web.ListRenderer');



    ListRenderer.include({


        events : _.extend({}, ListRenderer.prototype.events,{
            "click .btn-smart-parent" : "_onclick_btn_smart_parent",
            "click .btn-smart-child" : "_onclick_btn_smart_child",
            "click #btn-send-feedback" : "_onclick_btn_send_feedback",
            "click .close-popup-feedback" : "_close_popup_feedback",
        }),



    });





});
