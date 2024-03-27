odoo.define('print_partner_code.kiosk_mode', function (require) {
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
         "click #btn-reload-data": function(){
                var str = $('#txt-check-in').val();
                this.clear_data_table();
         },
         "click #btn-delete-record": function(){
                var str = $('#txt-check-in').val();
                this.delete_record();
         },
         "click #btn_print": function(){
                var str = $('#txt-check-in').val();
                this.print_partner_code();
         },
         "click #btn-search-data": function(){
            var str = $('#txt-check-in').val();
            var self = this;
                if (!str){
                    this.get_data_table();
                }else {
                    this.get_data_table(str);
                }
         },
    },

    start: function () {
        $('#data_print_partner_code').html("");
        var self = this;
        self.session = Session;
        const company_id = this.session.user_context.allowed_company_ids[0];
        this.$el.html(QWeb.render("PrintPartnerCodeKioskMode", {widget: this}));
        this.get_data_table();
        return Promise.all([ this._super.apply(this, arguments)]);
    },

    clear_data_table: function(query){
        var self = this;
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
        ]
        return this.$('.datatable').DataTable({
            'processing': true,
            'serverSide': true,
            "searching": false,
            "ordering": false,
            'autoWidth': false,
            "bInfo": false,
            "bPaginate": false,
            "lengthChange": false,
            'pageLength': 15,
            "language": {
                'paginate': {
                  'previous': '<span class="fa fa-arrow-left"></span>',
                  'next': '<span class="fa fa-arrow-right"></span>'
                }
              },
            'ajax': {
                        'url': "/datatable/clear-data-qr",
                        'type': "POST",
                        'dataType': "json",
                        'data': datas
            },
                    // 'columnDefs': columns,
           'aoColumns': columns,
           'drawCallback' : function(data){
                console.log("data");
                console.log(data.json.success);
                console.log(data.json);
                if(data.json.success == 1){
                    self.displayNotification({ title: 'Một lần chỉ thêm tối đa 14 khách hàng', type: 'danger' });
                }else {
                    $('#txt-check-in').val('');
                }
           }
        });
    },

    get_data_table: function(query){
        var self = this;
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
        ]
        return this.$('.datatable').DataTable({
            'processing': true,
            'serverSide': true,
            "searching": false,
            "ordering": false,
            'autoWidth': false,
            "bInfo": false,
            "bPaginate": false,
            "lengthChange": false,
            'pageLength': 15,
            "language": {
                'paginate': {
                  'previous': '<span class="fa fa-arrow-left"></span>',
                  'next': '<span class="fa fa-arrow-right"></span>'
                }
              },
            'ajax': {
                        'url': "/datatable/get-data-qr",
                        'type': "POST",
                        'dataType': "json",
                        'data': datas
            },
                    // 'columnDefs': columns,
           'aoColumns': columns,
           'drawCallback' : function(data){
                console.log("data");
                console.log(data.json.success);
                console.log(data.json);
                if(data.json.success == 1){
                    self.displayNotification({ title: 'Một lần chỉ thêm tối đa 14 khách hàng', type: 'danger' });
                }else {
                    $('#txt-check-in').val('');
                }

                $('.b').on('click', function(e){

                    self._rpc({
                        route: '/datatable/delete-record-qr',
                        params: {
                            id: $(e.currentTarget).data('id'),
                        },

                    }).then(function(result){
                           self.get_data_table();
                    });
                })
           }
        });
    },

    print_partner_code: function() {
        this.do_action('print_partner_code.action_print_partner_code');
    },

    destroy: function () {
        this._super.apply(this, arguments);
    },

});

core.action_registry.add('print_partner_code_kiosk_mode', KioskMode);

return KioskMode;

});
