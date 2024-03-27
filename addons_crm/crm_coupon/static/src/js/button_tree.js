odoo.define('crm.menu.tree', function(require) {
    "use strict";
    // var KanbanController = require("web.KanbanController");
    var ListController = require("web.ListController");
    var includeDict = {
        renderButtons: function () {
            this._super.apply(this, arguments);
            var self = this;
            $(document).on('click', '.create-coupon-group', function () {
                var rpc = require('web.rpc');
                var view_id = "crm.crm_case_tree_view_oppor"
                rpc.query({
                    model: 'crm.lead',
                    method: 'create_coupon_group',
                    args:[]
                })
                .then(function(r) {
                    console.log(r);
                    return self.do_action({
                        type: 'ir.actions.act_window',
                        res_model: "crm.group.customer",
                        res_id: r[5],
                        views: [[false, 'form']],
                        target: 'new'
                    });
                });
            });
        },
    };
    // KanbanController.include(includeDict);
    ListController.include(includeDict);
});