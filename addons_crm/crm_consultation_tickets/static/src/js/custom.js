odoo.define('crm_consultation_tickets.custom', function (require) {
'use strict';
require('web.dom_ready');
var rpc = require('web.rpc');
var ajax = require('web.ajax');
var core = require('web.core');
var qweb = core.qweb;
var Dialog = require('web.Dialog');
$(document).ready(function(){

 $('.add-service').click(function(event){
    var data_service = $('#data_service').val();
    data_service = JSON.parse(data_service);

    var number = $('.content-body tr');

    var new_index = number.length ;
    var index = new_index + 1;

    var select_service = '<select name="service__'+ index +'" data-id="'+ index +'"  class="sl_service" style="width: 100%;">';

    for(var i=0; i< data_service.length; i++){
        select_service += '<option name="'+ data_service[i]['id'] +'" value="'+ data_service[i]['id'] +'">'+ data_service[i]['name'] +'</option>';
    }
    select_service += '</select>';

    var html_content = '<tr id="row_info__' + index + '"  data-id="'+ index +'">';
    html_content += '<td class="text-center">' + index + '</td>';
    html_content += '<td>' + select_service + '</td>';
    html_content += '<td>';

    html_content += '<div>';
        html_content += '<div>';
        html_content += '<label style="width:100%"><i class="fa fa-heart-o"/> Mong muốn</label>';
        html_content += '<textarea rows="4" style="width:100%" type="text" name="desire__' + index + '"></textarea>';
        html_content += '</div>';

        html_content += '<div class="pt-3">';
        html_content += '<label  style="width:100%"><i class="fa fa-dashboard"/> Tình trạng</label>';
        html_content += '<textarea rows="4" style="width:100%" type="text" name="health_status__' + index + '"></textarea>';
        html_content += '</div>';

        html_content += '<div class="pt-3">';
        html_content += '<label  style="width:100%"><i class="fa fa-check-square-o"/> Mức độ cải thiện</label>';
        html_content += '<textarea rows="4" style="width:100%" type="text" name="level_of_improvement__' + index + '"></textarea>';
        html_content += '</div>';

        html_content += '<div class="pt-3">';
        html_content += '<label  style="width:100%"><i class="fa fa-calendar"/> Lịch trình</label>';
        html_content += '<textarea style="width:100%" type="text" name="schedule__' + index + '"></textarea>';
        html_content += '</div>';

        html_content += '<div class="pt-3">';
        html_content += '<label  style="width:100%"><i class="fa fa-calendar"/> Chế độ bảo hành</label>';
        html_content += '<textarea style="width:100%" type="text" name="warranty__' + index + '"></textarea>';
        html_content += '</div>';

        html_content += '<div class="pt-3">';
        html_content += '<label  style="width:100%"><i class="fa fa-home"/> Sản phẩm sử dụng tại nhà</label>';
        html_content += '<textarea style="width:100%" type="text" name="product_for_home_use__' + index + '"></textarea>';
        html_content += '</div>';

        html_content += '<div class="pt-3">';
        html_content += '<label style="width:100%"><i class="fa fa-pencil"/> Tư vấn</label>';
        html_content += '<textarea rows="4" style="width:100%" type="text" name="consultation__' + index + '"></textarea>';
        html_content += '</div>';

        html_content += '<div class="pt-3">';
        html_content += '<label style="width:100%"><i class="fa fa-pencil"/> Kết luận</label>';
        html_content += '<textarea rows="4" style="width:100%" type="text" name="note__' + index + '"></textarea>';
        html_content += '</div>';

    html_content += '</div>';


    html_content += '</td>';

    html_content += '<td class="text-center">';
      html_content += '<div class="text-center">';
      html_content += '<input class="confirm text-center" name="confirm_service__' + index + '" type="checkbox"/>';
      html_content += '</div>';
      html_content += '<div class="text-center">';
      html_content += '<a class="text-danger remove-service" data-id="' + index + '" style="margin-top:10px"><i class="fa fa-trash-o"/></a>';
      html_content += '</div>';
    html_content += '</td>';

    var tr = $(html_content);
    $('.content-body').append(tr);

    $('.remove-service').click(function(event){
        var self = this;
          Dialog.confirm(this, "Bạn chắc chắn muốn xóa dịch vụ này?", {
            confirm_callback: function () {
                $('#row_info__' + $(self).data('id')).remove();
            },
        });
    });


    $( ".sl_service").each(function(){
        $(this).select2();
    })

   });

  $('.remove-service').click(function(event){
    var self = this;
          Dialog.confirm(this, "Bạn chắc chắn muốn xóa dịch vụ này?", {
            confirm_callback: function () {
                $('#row_info__' + $(self).data('id')).remove();
            },
        });
   });


  $( "#consulting_doctor").each(function(){
    $(this).select2();
  });
  $( "#source_id").each(function(){
    $(this).select2();
  })



  // Initialize select2
   // Khi bấm nút thêm
//  $('#btn_add_service').click(function(event){
//
//      var data_service = $('#data_service').val();
//      data_service = JSON.parse(data_service);
//
//      var number = $('#tbl_crm_consultation_tickets_row tbody tr');
//
//      var new_index = number.length ;
//
//      var select_service = '<th style="vertical-align: middle;"><select name="service__'+ new_index +'" data-id="'+ new_index +'"  class="sl_service" style="width: 100%;">';
//
//      var options_service = '';
//
//      for(var i=0; i< data_service.length; i++){
//
//        options_service += '<option name="'+ data_service[i]['id'] +'" value="'+ data_service[i]['id'] +'">'+ data_service[i]['name'] +'</option>';
//      }
//      select_service += options_service;
//      select_service += '</select></th>';
//
//      var desire = $('<th><textarea type="text" name="desire__'+ new_index +'" style="width: 100%;"/></th>');
//
//      var health_status = $('<th><textarea type="text" name="health_status__'+ new_index +'" style="width: 100%;"/></th>');
//
//      var level_of_improvement = $('<th><textarea type="text" name="level_of_improvement__'+ new_index +'" style="width: 100%;"/></th>');
//
//      var schedule = $('<th><textarea type="text" name="schedule__'+ new_index +'" style="width: 100%;"/></th>');
//
//      var products_home_use = $('<th><textarea type="text" name="products_home_use__'+ new_index +'" style="width: 100%;"/></th>');
//
//      var note = $('<th><textarea type="text" name="note__'+ new_index +'" style="width: 100%;"/></th>');
//
//      var confirm = $('<th><textarea type="checkbox" name="confirm__'+ new_index +'" style="width: 100%;"/></th>');
//
//
//      var btn_delete_service = $('<th style="vertical-align: middle;"><button data-id="'+ new_index +'" name="btn_delete_service__'+ new_index +'" id="btn_delete_service__'+ new_index +'" type="button" class="button_delete_service fa fa-trash"></button></th>');
//
//
//
//      var tr = $('<tr id="tr_delete_service__'+ new_index +'" class="crm_consultation_tickets_row" data-id="'+ new_index +'">');;   // Create with jQuery
//      tr.append(select_service);
//      tr.append(desire);
//      tr.append(health_status);
//      tr.append(level_of_improvement);
//      tr.append(schedule);
//      tr.append(products_home_use);
//      tr.append(note);
//      tr.append(confirm);
//      tr.append(btn_delete_service);
//
//      $('#tbl_crm_consultation_tickets_row > tbody').append(tr);
//
//
//
//      $('.button_delete_service').click(function(event){
//
//        var crm_consultation_row = $('#tr_delete_service__' + $(this).data('id'));
//
//        crm_consultation_row.remove();
//       });
//   });
//
//  $('.button_delete_service').click(function(event){
//
//    var crm_consultation_row = $('#tr_delete_service__' + $(this).data('id'));
//
//    crm_consultation_row.remove();
//    });
//
//
    $('.know-source').click(function() {
      $('.know-source').not(this).prop('checked', false);
    });

//    $("textarea").each(function () {
//      this.setAttribute("style", "height:" + (this.scrollHeight) + "px;overflow-y:hidden;");
//    }).on("input", function () {
//      this.style.height = "auto";
//      this.style.height = (this.scrollHeight) + "px";
//    });

    })

//  $('.sl_service').click(function(event){
//      var data_service = $('#data_service').val();
//      data_service = JSON.parse(data_service);
//      console.log(data_service)
//      console.log('data_service')
//      $( ".js-data-example-ajax" ).select2({
//        data : data_service
//     })
//  })


});
