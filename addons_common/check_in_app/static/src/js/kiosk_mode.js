odoo.define('patient.kiosk_mode', function (require) {
"use strict";

var AbstractAction = require('web.AbstractAction');
var ajax = require('web.ajax');
var core = require('web.core');
var Session = require('web.session');

var QWeb = core.qweb;


var KioskMode = AbstractAction.extend({
    jsLibs: [
            'check_in_app/static/src/libs/js/datatables.min.js',
        ],
    cssLibs: [
            'check_in_app/static/src/libs/css/datatables.min.css',
            'check_in_app/static/src/libs/css/custom.css',
    ],
    events: {
        "click .o_hr_attendance_button_employees": function() {
            this.do_action('patient.patient_patient_action', {
                additional_context: {'no_group_by': true},
            });
        },
        "click .o_hr_attendance_back_button": function() {
            this.do_action('patient.patient_patient_action');

         },
         "click #btn-reload-data": function(){
                var str = $('#txt-check-in').val();
                this.get_data_table();


         },
         "click #btn-search-data": function(){
            var str = $('#txt-check-in').val();
                if (!str){
                    this.get_data_table();
                }else {
                    this.get_data_table(str);
                }
         },
//         "keyup #txt-check-in" : function(str){
//            str = $('#txt-check-in').val();
//            if (str != ""){
//                var xmlhttp = new XMLHttpRequest();
//                xmlhttp.onreadystatechange = function() {
//                    if (this.readyState == 4 && this.status == 200) {
//                         $('#data-check-in').html(this.responseText);
//                     }
//                };
//                xmlhttp.open("GET", "/get-data-check-in?q=" + str, true);
//                xmlhttp.send();
//            }
//            else {
//                const xmlhttp = new XMLHttpRequest();
//
//               xmlhttp.onload = function() {
//                   $('#data-check-in').html(this.responseText);
//                   console.log("data: " + this.responseText)
//               }
//               xmlhttp.open("GET", "/check-in-patient");
//               xmlhttp.send();
//            }


//         },
    },

    start: function () {

       $('#data-check-in').html("");
       const xmlhttp = new XMLHttpRequest();

//       xmlhttp.onload = function() {
//           $('#data-check-in').html(this.responseText);
//           console.log("data: " + this.responseText)
//       }
//       xmlhttp.open("GET", "/check-in-patient");
//       xmlhttp.send();
        var self = this;
        core.bus.on('barcode_scanned', this, this._onBarcodeScanned);
        self.session = Session;
        console.log(self.session)
        const company_id = this.session.user_context.allowed_company_ids[0];

        this.$el.html(QWeb.render("PtAttendanceKioskMode", {widget: this}));
        this.start_clock();
//        var def = this._rpc({
//                model: 'res.company',
//                method: 'search_read',
//                args: [[['id', '=', company_id]], ['name']],
//            })
//           .then(function (){
////                self.company_name = companies[0].name;
////                self.company_image_url = self.session.url('/web/image', {model: 'res.company', id: company_id, field: 'logo',});
//                self.$el.html(QWeb.render("PtAttendanceKioskMode", {widget: self}));
//                self.start_clock();
//            });
        // Make a RPC call every day to keep the session alive
        self._interval = window.setInterval(this._callServer.bind(this), (60*60*1000*24));
        var i = 0;
//        setInterval(function(){
//             $('#data-check-in').html("");
//               const xmlhttp = new XMLHttpRequest();
//
//               xmlhttp.onload = function() {
//                   $('#data-check-in').html(this.responseText);
//                   console.log("data: " + this.responseText)
//               }
//               xmlhttp.open("GET", "/check-in-patient");
//               xmlhttp.send();
//        },(30*1000))
        this.get_data_table();

        return Promise.all([ this._super.apply(this, arguments)]);
    },

    on_attach_callback: function () {
        // Stop polling to avoid notifications in kiosk mode
        this.call('bus_service', 'stopPolling');
        $('body').find('.o_ChatWindowHeader_commandClose').click();
    },

    get_data_table: function(query){
        $('.datatable').DataTable().clear();
        $('.datatable').DataTable().destroy();
        var datas = {}
        if (query) {
            datas['query'] = query
            console.log(query)
        }
        var columns = [{'data': [0]},
                        {'data': [1]},
                        {'data': [2]},
                        {'data': [3]},
                        {'data': [4]},
                        {'data': [5]},
                        {'data': [6]},
        ]
        return this.$('.datatable').DataTable({
            'processing': true,
            'serverSide': true,
            "searching": false,
            "ordering": false,
            'autoWidth': false,
            "bInfo": false,
            "lengthChange": false,
            'pageLength': 15,
            "language": {
                'paginate': {
                  'previous': '<span class="fa fa-arrow-left"></span>',
                  'next': '<span class="fa fa-arrow-right"></span>'
                }
              },
            'ajax': {
                        'url': "/datatable/get-data-checkin",
                        'type': "POST",
                        'dataType': "json",
                        'data': datas
            },
                    // 'columnDefs': columns,
           'aoColumns': columns,
        });
    },

    _onBarcodeScanned: function(barcode) {

       // location.reload();
        var self = this;
        var check_type = $('input[name="check-in-type"]:checked').val();
        core.bus.off('barcode_scanned', this, this._onBarcodeScanned);
        this._rpc({
                model: 'crm.check.in',
                method: 'attendance_scan',
                args: [barcode, check_type],
            })
            .then(function (result) {
                if (result.success) {
//                    self.do_action(result.action);
//                    console.log(result.action)
                    self.get_data_table();
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

core.action_registry.add('pt_attendance_kiosk_mode', KioskMode);

return KioskMode;

});
