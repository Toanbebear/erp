odoo.define('copy_char.CopyChar', function (require) {
"use strict";
// import packages
    var core = require('web.core');
    var basic_fields = require('web.basic_fields');
    var registry = require('web.field_registry');

    var qweb = core.qweb;
    var _t = core._t;
    var _lt = core._lt;

    var CopyClipboardCustom = {
        /**
         * @override
         */
        destroy: function () {
            this._super.apply(this, arguments);
            if (this.clipboard) {
                this.clipboard.destroy();
            }
        },

        //--------------------------------------------------------------------------
        // Private
        //--------------------------------------------------------------------------

        /**
         * Instatiates the Clipboad lib.
         */
        _initClipboard: function () {
            var self = this;
            var $clipboardBtn = this.$('.o_clipboard_button');
            $clipboardBtn.tooltip({title: _t('Copied !'), trigger: 'manual', placement: 'right'});
            this.clipboard = new ClipboardJS($clipboardBtn[0], {
                text: function () {
                    if(typeof self.value === 'object' && self.value !== null){
                        return self.value.data.display_name.trim();
                    }else{
                        return self.value.trim();
                    }
                },
                // Container added because of Bootstrap modal that give the focus to another element.
                // We need to give to correct focus to ClipboardJS (see in ClipboardJS doc)
                // https://github.com/zenorocha/clipboard.js/issues/155
                container: self.$el[0]
            });
            this.clipboard.on('success', function () {
                _.defer(function () {
                    $clipboardBtn.tooltip('show');
                    _.delay(function () {
                        $clipboardBtn.tooltip('hide');
                    }, 800);
                });
            });
        },
        /**
         * @override
         */
        _render: function () {
            this._super.apply(this, arguments);
            this.$el.addClass('o_field_copy_char');
        },
        /**
         * @override
         */
        _renderReadonly: function () {
            this._super.apply(this, arguments);
            if(this.value){
                this.$el.append($(qweb.render(this.clipboardTemplate)));
                this._initClipboard();
            }
        }
    };

    // widget implementation
    var CopyChar = basic_fields.FieldChar.extend(CopyClipboardCustom,{
        description: _lt("Sao chép ký tự"),
        clipboardTemplate: 'CopyChar',
    });

    registry.add('copy_char', CopyChar); // add our "copy_char" widget to the widget registry
});