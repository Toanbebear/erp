odoo.define('web_image.image_cloud', function (require) {
    "use strict";

    var core = require('web.core');
    var BasicFields = require('web.basic_fields');
    var FormController = require('web.FormController');
    var Registry = require('web.field_registry');
    var utils = require('web.utils');
    var session = require('web.session');
    var field_utils = require('web.field_utils');
    var AbstractField = require('web.AbstractField');

    var _t = core._t;
    var qweb = core.qweb;
    var _lt = core._lt;

    var config = require('web.config');
    var datepicker = require('web.datepicker');
    var dom = require('web.dom');
    var Domain = require('web.Domain');
    var DomainSelector = require('web.DomainSelector');
    var DomainSelectorDialog = require('web.DomainSelectorDialog');
    var framework = require('web.framework');
    var py_utils = require('web.py_utils');
    var view_dialogs = require('web.view_dialogs');
    var time = require('web.time');
    var ColorpickerDialog = require('web.ColorpickerDialog');

    require("web.zoomodoo");



    var FieldImageCloud = BasicFields.FieldBinaryImage.extend({

    init : function(params){
            this._super.apply(this, arguments);
            this.result = [];

        },

    _render: function () {
        var self = this;
        var url = this.placeholder;


        var image_drive = this.record['data']['image_link']
//        if (image_drive){
//            url = image_drive;
//        }else{
        if (this.value) {
            if (!utils.is_bin_size(this.value)) {
                // Use magic-word technique for detecting image type
                url = 'data:image/' + (this.file_type_magic_word[this.value[0]] || 'png') + ';base64,' + this.value;
//                url = 'https://drive.scigroup.com.vn/s/ywYppsB6scmHP7S/download';
                console.log(1)
            }
//            else if (utils.is_bin_size(this.value)){
//                url = 'https://drive.scigroup.com.vn/s/ywYppsB6scmHP7S/download';
//            }
            else {
                var field = this.nodeOptions.preview_image || this.name;
                var unique = this.recordData.__last_update;
                url = this._getImageUrl(this.model, this.res_id, field, unique);
                console.log(2)
            }
        }

        if (image_drive){
            url = image_drive;
        }
//         url = 'https://drive.scigroup.com.vn/s/ywYppsB6scmHP7S/download';
        var $img = $(qweb.render("FieldImageCloud-img", {widget: this, url: url}));


        // override css size attributes (could have been defined in css files)
        // if specified on the widget
        var width = this.nodeOptions.size ? this.nodeOptions.size[0] : this.attrs.width;
        var height = this.nodeOptions.size ? this.nodeOptions.size[1] : this.attrs.height;
        if (width) {
            $img.attr('width', width);
            $img.css('max-width', width + 'px');
        }
        if (height) {
            $img.attr('height', height);
            $img.css('max-height', height + 'px');
        }
        this.$('> img').remove();
        this.$el.prepend($img);
        $img.one('error', function () {
            $img.attr('src', self.placeholder);
            self.do_warn(_t("Image"), _t("Could not display the selected image."));
        });

        this.$el.addClass('remove_o_field_empty');

    },

    });

    Registry.add('image_cloud', FieldImageCloud);

});
