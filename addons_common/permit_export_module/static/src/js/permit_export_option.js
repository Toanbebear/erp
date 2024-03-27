odoo.define('permit_export_option.permit_export_option', function (require) {
"use strict";

var Sidebar = require('web.Sidebar');
var core = require('web.core');
var _t = core._t;
var _lt = core._lt;
    Sidebar.include({
        start: function () {
            var self = this;
            var def;
            var export_label = _t("Export");
            def = this.getSession().user_has_group('permit_export_module.group_permit_export_button').then(function(has_group) {
                if (!has_group)
                {
                    self.items['other'] = $.grep(self.items['other'], function(i){
                        return i && i.label && i.label != export_label;
                    });
                }
            });
            return Promise.resolve(def).then(this._super.bind(this));
        },
    });
});
