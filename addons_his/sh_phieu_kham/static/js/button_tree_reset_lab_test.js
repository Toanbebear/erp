odoo.define('walkin.reset.lab.test', function(require) {
    "use strict";
    var ListController = require("web.ListController");
    var session = require('web.session');
    var includeDict = {
        renderButtons: function () {
            this._super.apply(this, arguments);
            var self = this;
            $(document).on('click', '.reset_all_labtest', function () {
                var rpc = require('web.rpc');
                rpc.query({
                    route: '/reset/lab-test',
                    params: {
                    walkin_id: self.initialState.context.active_id,
                    uid: self.initialState.context.uid,
                },
                })
                .then(function(r) {
                    $('.oe_pager_refresh').trigger('click');
                });
            });
        },
    };
    ListController.include(includeDict);
});