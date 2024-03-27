odoo.define('web_monetary_format.web_monetary_format', function (require) {
    "use strict";

    var core = require('web.core');
    var BasicFields = require('web.basic_fields');
    var FormController = require('web.FormController');
    var Registry = require('web.field_registry');
    var utils = require('web.utils');
    var session = require('web.session');
    var field_utils = require('web.field_utils');

    var _t = core._t;
    var QWeb = core.qweb;

    var FieldMonetaryFormat = BasicFields.FieldMonetary.extend({

        events: _.extend({}, BasicFields.FieldMonetary.prototype.events, {
            'click': '_onClick',
            'keyup': '_onKeyup',
            'blur': '_onBlur',
        }),

        _onClick: function (event) {
            event.stopPropagation();
        },
        _onBlur: function (event) {
            event.stopPropagation();
        },
        _onKeyup: function (event) {
            event.stopPropagation();
            var number = this._formatNumber(event.target.value);
            this.$('input.o_input').val(number);
        },
        _formatNumber: function (n) {
          return n.replace(/\D/g, "").replace(/\B(?=(\d{3})+(?!\d))/g, _t.database.parameters.thousands_sep)
        }


    });

    Registry.add('monetary_format', FieldMonetaryFormat);

});
