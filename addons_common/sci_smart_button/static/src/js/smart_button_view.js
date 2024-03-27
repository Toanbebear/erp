odoo.define('sci_smart_button.smart_button_view', function (require) {
'use strict';

    var AbstractView = require('web.AbstractView');
    var AbstractRenderer = require('web.AbstractRenderer');
    var core = require('web.core');
    var QWeb = core.qweb;
    var session = require('web.session');
    var rpc = require('web.rpc');

    AbstractRenderer.include({
        cssLibs: [
            '/sci_smart_button/static/libs/fonts/boxicons.css',
        ],

        init: function (parent, state,params) {
                var def = this._super.apply(this, arguments);
                this.params = params;
        },

        start: function () {
            var self = this;

            return this._super.apply(this, arguments).then(function () {
                if (self.params.smart_button){
                    var button_smart = self.$el.append($(QWeb.render('smart_button')))
                }
            });
        },

        _onclick_btn_smart_parent : function(ev){
            $(ev.currentTarget).toggleClass('active_btn_smart_parent');
            $('.o_content_smart_button_child_box').tooltip('show');
            if ($(ev.currentTarget).hasClass('active_btn_smart_parent')){
//                $(ev.currentTarget).html('<i class="fa fa-caret-right"/>');
                $('.o_content_smart_button_child').toggleClass('o_content_smart_button_child_active');
            }else {
//                $(ev.currentTarget).html('<i class="fa fa-caret-left"/>');
                $('.o_content_smart_button_child').toggleClass('o_content_smart_button_child_active');
            }
        },

        _onclick_btn_smart_child : function(ev){
            var data_btn_smart_child = $(ev.currentTarget).data('btn-child');
            if (data_btn_smart_child == 'feedback'){
                this._handle_feedback();
            }
        },
        _handle_feedback : function(){
            var box_feedback = $('.o_smart_button_feedback').toggle('d-none');


        },

        _onclick_btn_send_feedback: function(e){

            var send_feedback_event =  this._sendFeedback();

        },

        _close_popup_feedback : function () {
            $(".btn-smart-child[data-btn-child='feedback']").trigger('click');
        },
        _sendFeedback: function(e, content, rating){
            var content = $('#contentFeedback').val();
            var rating = $("input[name='rating']:checked").val();
            var self = this;
            var link = window.location.href
            var email = session.username
            console.log(this)
            return this._rpc({
                route: "/sci-smart-button/feedback/create",
                params: {
                    user_id : session.uid,
                    name : session.name,
                    rating : rating,
                    content: content,
                    link : link,
                    email : email,
                    viewType : this.params.arch.tag
                }
            }).then(function(data){
                if (JSON.parse(data).status == 'ok'){
                    self.do_notify('Thông báo', 'Cảm ơn bạn đã gửi phản hồi cho chúng tôi!');
                    self._reset_form_feedback();
                    $(".btn-smart-child[data-btn-child='feedback']").trigger('click');
                    setTimeout(function() {
                      $(".btn-smart-parent").trigger('click');
                    }, 400);
                }
            });
        },
        _reset_form_feedback () {
            var content = $('#contentFeedback').val('');
            var rating = $("#rating-5").prop('checked', true);
        }

    })


    AbstractView.include({

        init: function (viewInfo, params) {
            var def = this._super.apply(this, arguments);
            this.params = params;
            this.rendererParams['smart_button'] = false;
            if (params.action && params.action.target === 'current'){
                this.rendererParams['smart_button'] = true
            }
            return def;
        },

    })



});
