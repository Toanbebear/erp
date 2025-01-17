odoo.define('my_module.my_widget', function (require) {
    "use strict";

    var core = require('web.core');
    var common = require('web.form_common');
    var FieldMany2ManyTags = core.form_widget_registry.get('many2many_tags');
    var _t = core._t;

    var MyFieldMany2ManyTags = FieldMany2ManyTags.extend({
        get_badge_id: function(el){
            if ($(el).hasClass('badge')) return $(el).data('id');
            return $(el).closest('.badge').data('id');
        },
        events: {
            'click .o_delete': function(e) {
                e.stopPropagation();
                this.remove_id(this.get_badge_id(e.target));
            },
            'click .badge': function(e) {
                e.stopPropagation();
                var self = this;
                var record_id = this.get_badge_id(e.target);
                new common.FormViewDialog(self, {
                    res_model: self.many2one.field.relation,
                    res_id: record_id,
//                    context: self.dataset.context,
                    context: form_view_ref': 'sci_accounting.view_account_payment_transfer_adjustment_form,
                    title: _t('Open: ') + self.many2one.string,
                    readonly: self.many2one.get('effective_readonly')
                }).on('write_completed', self, function() {
                    self.dataset.cache[record_id].from_read = {};
                    self.dataset.evict_record(record_id);
                    self.render_value();
                }).open();
            }
        }
    });
    core.form_widget_registry.add('my_many2many_tags', MyFieldMany2ManyTags);

    return {
        MyFieldMany2ManyTags: MyFieldMany2ManyTags
    };

});