odoo.define('survey_base.custom', function (require) {
'use strict';
require('web.dom_ready');
var rpc = require('web.rpc');
var ajax = require('web.ajax');
$(document).ready(function(){

  // Initialize select2
  $("#user").select2();

  $( ".multi_box").each(function(){
    $(this).select2();
  })

//  // Read selected option
//  $('#submit_user').click(function(){
//    var userid = $('#user').val();
//    if(!userid){
//        alert("Bạn chưa chọn người làm khảo sát!");
//        return false;
//    }
//  });
});

$('#customer_phone').change(function(){
    ajax.jsonRpc("/survey/get-name", 'call', {
        'phone': this.value,
    }).then(function (data) {
        if (data){
            $('#customer_name').val(data);
        }
       else{
            $('#customer_name').val('');
       }
    });

//console.log(this.value);
//    rpc.query({
//            model: 'res.partner',
//            method: 'search_read',
//            args: [[['phone','=',this.value]], ['name']],
//        })
//        .then(function (result){
//            if (result[0]){
//            $('#customer_name').val(result[0].name);
//            }
//            else{
//            $('#customer_name').val('');
//            }
//        });
});

$('input[type=checkbox][name=department]').change(function(){
//$('#1').change(function(){
    if($(this).is(':checked')) {

        console.log($(this).val());
         $('input[type=checkbox][id='+ $(this).val()+']').prop('checked',true);
        // Checkbox is checked..
        //console.log('this.checked');
        //console.log(this);
    } else {
        // Checkbox is not checked..
        // $('input[type=checkbox][name=2_5_14_1]').prop('checked',false);
         $('input[type=checkbox][id='+ $(this).val()+']').prop('checked',false);
    }
});


});