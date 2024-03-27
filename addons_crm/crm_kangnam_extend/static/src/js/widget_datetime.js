odoo.define('crm_kangnam_extend.datetime', function (require) {
"use strict";

    var basic_fields = require('web.basic_fields');
    var registry = require('web.field_registry');

    var DatetimeTree = basic_fields.FieldDateTime.extend({
       _renderReadonly: function () {
            if (this._formatValue(this.value)){
                const datetime = this._formatValue(this.value);

                const formattedDatetime = datetime
                  .slice(11, 16)
                  + "<br/>"
                  + datetime.slice(0, 10)

                console.log(formattedDatetime);

                this.$el.html(formattedDatetime);
            }else {
                 this.$el.html(this._formatValue(this.value));

            }
        },
    })
    registry.add('datetime_tree', DatetimeTree)

});