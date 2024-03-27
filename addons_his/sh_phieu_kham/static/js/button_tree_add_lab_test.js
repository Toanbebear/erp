odoo.define('walkin.add.lab.test', function(require) {
    "use strict";
    var ListController = require("web.ListController");
    var session = require('web.session');
    var includeDict = {
        renderButtons: function () {
            this._super.apply(this, arguments);
            var self = this;
            $(document).on('click', '.add_config_labtest', function () {
                var rpc = require('web.rpc');
                console.log(self)
                console.log(session)
                console.log("===================")
                rpc.query({
                    route: '/add/lab-test',
                    params: {
                    walkin_id: self.initialState.context.active_id,
                    uid: self.initialState.context.uid,
                    company_id: self.initialState.context.default_institution,
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