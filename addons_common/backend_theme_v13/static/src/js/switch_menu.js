odoo.define('backend_theme_v13.switch_menu', function (require) {
    "use strict";

    var SwitchCompanyMenu = require('web.SwitchCompanyMenu');
    var session = require('web.session');

    var core = require('web.core');
    var qweb = core.qweb;

    SwitchCompanyMenu.include({
        events: {
        'click .dropdown-item[data-menu] div.log_into': '_onSwitchCompanyClick',
        'click .dropdown-item[data-menu] div.toggle_company': '_onToggleCompanyClick',
        'click .dropdown-item[data-menu] div.toggle_all_company': '_onToggleAllCompanyClick',
        'click .menu-switch-apply': '_onApplyAllCompanyClick',
        },

        init: function () {
            this._super.apply(this, arguments);
            this.allowed_company_ids = [];
            this.current_company_id = 0;
        },

        start: function () {
            var def = this._super.apply(this, arguments);
            this.$('.dropdown-menu').append(qweb.render('SwitchCompanyMenuAction'));
        },

        _onToggleCompanyClick: function (ev) {
            ev.stopPropagation();
            var dropdownItem = $(ev.currentTarget).parent();
            var companyID = dropdownItem.data('company-id');
            var allowed_company_ids = this.allowed_company_ids;
            var current_company_id = allowed_company_ids[0];
            if (dropdownItem.find('.fa-square-o').length) {
                allowed_company_ids.push(companyID);
                dropdownItem.find('.fa-square-o').removeClass('fa-square-o').addClass('fa-check-square');
            } else {
                allowed_company_ids.splice(allowed_company_ids.indexOf(companyID), 1);
                dropdownItem.find('.fa-check-square').addClass('fa-square-o').removeClass('fa-check-square');
            }
            this.allowed_company_ids = allowed_company_ids;
            this.current_company_id = current_company_id;
        },

        _onApplyAllCompanyClick: function (ev) {
            ev.stopPropagation();
            session.setCompanies(this.current_company_id, this.allowed_company_ids);
        },
    });
});
    
