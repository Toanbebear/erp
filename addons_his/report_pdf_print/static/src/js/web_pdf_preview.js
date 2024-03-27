odoo.define('report_pdf_print.report', function (require) {
    'use strict';

    var ActionManager = require('web.ActionManager');
    var core = require('web.core');
    var crash_manager = require('web.CrashManager');
    var framework = require('web.framework');
    var session = require('web.session');


    var _t = core._t;
    var _lt = core._lt;

    var wkhtmltopdf_state;

    ActionManager.include({
        _executeReportAction: function (action, options) {
            var self = this;
            action = _.clone(action);
            // Only valid for pdf report.
            if (action.report_type === 'qweb-pdf') {
                return this.call('report', 'checkWkhtmltopdf').then(function (state) {
                    var reportUrls = self._makeReportUrls(action);
                    var url = '';

                    if(reportUrls.pdf.indexOf("?") > -1){
                        url = reportUrls.pdf;
                    }else{
                        var ctx = JSON.parse(JSON.stringify(action.context));
                        ctx.active_domain = '';
                        url = reportUrls.pdf+"?context="+JSON.stringify(ctx);
                    }

                    printJS({printable: url, type:'pdf', showModal:true, modalMessage:_t('Retrieve content...')});

                    framework.unblockUI();
                });

            } else {
                return self._super(action, options);
            }

        }
    });

});