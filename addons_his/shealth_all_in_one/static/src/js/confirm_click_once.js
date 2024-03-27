odoo.define('shealth_all_in_one.confirm_click_once', function (require) {
"use strict";

    var Dialog = require('web.Dialog');
    var dom = require('web.dom');

    var ConfirmClickOnce = Dialog.include({
        set_buttons: function (buttons) {
            var self = this;
            this.$footer.empty();
            _.each(buttons, function (buttonData) {
                var $button = dom.renderButton({
                    attrs: {
                        class: buttonData.classes || (buttons.length > 1 ? 'btn-default' : 'btn-primary'),
                        disabled: buttonData.disabled,
                    },
                    icon: buttonData.icon,
                    text: buttonData.text,
                });
                $button.on('click', function (e) {
                    var def;
                    if (buttonData.click) {
                        def = buttonData.click.call(self, e);
                        if ($button.hasClass('btn-save-new') || $button.hasClass('btn-save-close')) {
                            // Không disable
                        }else{
                            $button.attr('disabled', "true");
                        }
                    }
                    if (buttonData.close) {
                        $.when(def).always(self.close.bind(self));
                    }
                });
                self.$footer.append($button);
            });
        },

    });
});
