odoo.define('crm_advise.ListRenderer', function (require) {
"use strict";

var ListRenderer = require('web.ListRenderer');

var DECORATIONS = [
    'decoration-bf',
    'decoration-it',
    'decoration-danger',
    'decoration-info',
    'decoration-muted',
    'decoration-primary',
    'decoration-success',
    'decoration-warning',
    'decoration-orange'
];

ListRenderer.include({

     init: function (parent, state, params) {
        this._super.apply(this, arguments);
        this.columnInvisibleFields = params.columnInvisibleFields;
        this.rowDecorations = _.chain(this.arch.attrs)
            .pick(function (value, key) {
                return DECORATIONS.indexOf(key) >= 0;
            }).mapObject(function (value) {
                return py.parse(py.tokenize(value));
            }).value();
        this.hasSelectors = params.hasSelectors;
        this.selection = params.selectedRecords || [];
        this.pagers = []; // instantiated pagers (only for grouped lists)
        this.isGrouped = this.state.groupedBy.length > 0;
        this.groupbys = params.groupbys;
    },
    _setDecorationClasses: function (record, $tr) {
        _.each(this.rowDecorations, function (expr, decoration) {
            var cssClass = decoration.replace('decoration', 'text');
            $tr.toggleClass(cssClass, py.PY_isTrue(py.evaluate(expr, record.evalContext)));
        });
    },
})


});
