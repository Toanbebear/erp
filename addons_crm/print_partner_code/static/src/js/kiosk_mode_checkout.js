odoo.define('patient.kiosk_mode_checkout', function (require) {
"use strict";

var AbstractAction = require('web.AbstractAction');
var ajax = require('web.ajax');
var core = require('web.core');
var Session = require('web.session');

var QWeb = core.qweb;

var KioskMode = AbstractAction.extend({
    events: {
        "click .o_hr_attendance_button_employees": function() {
            this.do_action('patient.patient_patient_action', {
                additional_context: {'no_group_by': true},
            });
        },
        "click .o_hr_attendance_back_button": function() {
            this.do_action('patient.patient_patient_action');
         },
         "keyup #txt-check-out" : function(str){
            str = $('#txt-check-out').val();
            if (str != ""){
                var xmlhttp = new XMLHttpRequest();
                xmlhttp.onreadystatechange = function() {
                    if (this.readyState == 4 && this.status == 200) {
                         $('#data-check-out').html(this.responseText);
                     }
                };
                xmlhttp.open("GET", "/get-data-check-out?q=" + str, true);
                xmlhttp.send();
            }
            else {
                const xmlhttp = new XMLHttpRequest();

               xmlhttp.onload = function() {
                   $('#data-check-out').html(this.responseText);
                   console.log("data: " + this.responseText)
               }
               xmlhttp.open("GET", "/check-out-patient");
               xmlhttp.send();
            }


         },
    },

    start: function () {
       $('#data-check-out').html("");
       const xmlhttp = new XMLHttpRequest();

       xmlhttp.onload = function() {
           $('#data-check-out').html(this.responseText);
           console.log("data: " + this.responseText)
       }
       xmlhttp.open("GET", "/check-out-patient");
       xmlhttp.send();
        var self = this;
        core.bus.on('barcode_scanned', this, this._onBarcodeScanned);
        self.session = Session;
        console.log(self.session)
        this.$el.html(QWeb.render("PtAttendanceKioskModeCheckout", {widget: this}));
        this.start_clock();
//        const company_id = this.session.user_context.allowed_company_ids[0];
//        var def = this._rpc({
//                model: 'res.company',
//                method: 'search_read',
//                args: [[['id', '=', company_id]], ['name']],
//            })
//           .then(function (){
//                self.company_name = companies[0].name;
//                self.company_image_url = self.session.url('/web/image', {model: 'res.company', id: company_id, field: 'logo',});
//                self.$el.html(QWeb.render("PtAttendanceKioskModeCheckout", {widget: self}));
//                self.start_clock();
//            });
        // Make a RPC call every day to keep the session alive
        self._interval = window.setInterval(this._callServer.bind(this), (60*60*1000*24));
        return Promise.all([ this._super.apply(this, arguments)]);
    },

    on_attach_callback: function () {
        // Stop polling to avoid notifications in kiosk mode
        this.call('bus_service', 'stopPolling');
        $('body').find('.o_ChatWindowHeader_commandClose').click();
    },

    _onBarcodeScanned: function(barcode) {
        var self = this;
        core.bus.off('barcode_scanned', this, this._onBarcodeScanned);
        this._rpc({
                model: 'patient.patient',
                method: 'attendance_scan_checkout',
                args: [barcode, ],
            })
            .then(function (result) {
                if (result.success) {
//                    self.do_action(result.action);
                    const xmlhttp = new XMLHttpRequest();

                    xmlhttp.onload = function() {
                        $('#data-check-out').html(this.responseText);
                        console.log("data: " + this.responseText)
                    }
                    xmlhttp.open("GET", "/check-out-patient");
                    xmlhttp.send();
                    self.displayNotification({ title: result.success, type: 'success' });
                    core.bus.on('barcode_scanned', self, self._onBarcodeScanned);
                } else if (result.warning) {
                    self.displayNotification({ title: result.warning, type: 'danger' });
                    core.bus.on('barcode_scanned', self, self._onBarcodeScanned);
                }
            }, function () {
                core.bus.on('barcode_scanned', self, self._onBarcodeScanned);
            });
    },

    start_clock: function() {
        this.clock_start = setInterval(function() {this.$(".o_hr_attendance_clock").text(new Date().toLocaleTimeString(navigator.language, {hour: '2-digit', minute:'2-digit', second:'2-digit'}));}, 500);
        // First clock refresh before interval to avoid delay
        this.$(".o_hr_attendance_clock").show().text(new Date().toLocaleTimeString(navigator.language, {hour: '2-digit', minute:'2-digit', second:'2-digit'}));
    },

    destroy: function () {
        core.bus.off('barcode_scanned', this, this._onBarcodeScanned);
        clearInterval(this.clock_start);
        clearInterval(this._interval);
        this._super.apply(this, arguments);
    },

    _callServer: function () {
        // Make a call to the database to avoid the auto close of the session
        return ajax.rpc("/pt_attendance/kiosk_keepalive", {});
    },

});

core.action_registry.add('pt_attendance_kiosk_mode_checkout', KioskMode);

return KioskMode;

});
