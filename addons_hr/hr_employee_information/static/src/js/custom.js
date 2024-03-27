odoo.define('hr_employee_information.custom', function (require) {
'use strict';
require('web.dom_ready');
var rpc = require('web.rpc');
var ajax = require('web.ajax');
$(document).ready(function(){


  // Initialize select2

    // Khi chọn loại kỹ năng sl_skill_type
//    $('.sl_skill_type').change(change_skill(event));

    $('.sl_skill_type').change(function(event){
        // Check input( $( this ).val() ) for validity here
        // alert($(this).val());
        var type = $(this).val();
        var data = $('#data_skills').val();

        data = JSON.parse(data);


        if(type){

            var index_data = $(this).data('id');



            // Đổ dữ liệu cho Kỹ năng
            var skills_data = data[type]['skills'];
            var selectSkills = $('#skill__' + index_data);

            if(selectSkills.prop) {
              var options = selectSkills.prop('options');

            }
            else {
              var options = selectSkills.attr('options');
            }
            $('option', selectSkills).remove();

            $.each(skills_data, function(val, text) {
                options[options.length] = new Option(text, val);
            });

            // Đổ dữ liệu cho Level
            var levels_data = data[type]['levels'];
            var selectLevel = $('#ability__' + index_data);

            if(selectLevel.prop) {
              var options = selectLevel.prop('options');

            }
            else {
              var options = selectLevel.attr('options');
            }
            $('option', selectLevel).remove();

            $.each(levels_data, function(val, text) {
                options[options.length] = new Option(text, val);
            });
        }

    });
   // Khi bấm nút thêm
  $('#btn_add_relation').click(function(event){

      var number = $('#tbl_employee_relations_row tbody tr');


      var new_index = number.length ;
      var name_content = $('<th><input type="text" name="name__'+ new_index +'" style="width: 100%;"></th>');

      var select_content = '<select name="family_relations__'+ new_index +'" style="width: 100%;">';
      select_content += '<option value="father">Bố</option>';
      select_content += '<option value="mother">Mẹ</option>';
      select_content += '<option value="wife">Vợ</option>';
      select_content += '<option value="husband">Chồng</option>';
      select_content += '<option value="son">Con trai</option>';
      select_content += '<option value="daughter">Con gái</option>';
      select_content += '<option value="other">Khác</option>';
      select_content += '</th>';
      var th_select = $('<th></th>').append(select_content);

      var birth_content = $('<th><input type="number" name="birth__'+ new_index +'" style="width: 100%;"></th>');

      var btn_delete_relation = $('<th><button data-id="'+ new_index +'" name="btn_delete_relation__'+ new_index +'" id="btn_delete_relation__'+ new_index +'" type="button" class="button_delete_relations">xóa</button></th>');

      var occupation_content = $('<th><input type="text" name="occupation__'+ new_index +'" style="width: 100%;"></th>');


      var tr = $('<tr id="tr_delete_relation__'+ new_index +'" class="employee_relations_row" data-id="'+ new_index +'">');;   // Create with jQuery
      tr.append(th_select);
      tr.append(name_content);
      tr.append(birth_content);
      tr.append(occupation_content);
      tr.append(btn_delete_relation);

      $('#tbl_employee_relations_row > tbody').append(tr);



      $('.button_delete_relations').click(function(event){

        var employee_relations_row = $('#tr_delete_relation__' + $(this).data('id'));

        employee_relations_row.remove();
       });
   });

  $('.button_delete_relations').click(function(event){

    var employee_relations_row = $('#tr_delete_relation__' + $(this).data('id'));

    employee_relations_row.remove();
    });




   $('#btn_add_work_experience').click(function(event){

      var number = $('#tbl_employee_work_experience_row tbody tr');


      var new_index = number.length ;

      var start_date_content = $('<th><input type="month" name="start_date__'+ new_index +'" style="width: 100%;"></th>');

      var end_date_content = $('<th><input type="month" name="end_date__'+ new_index +'" style="width: 100%;"></th>');

      var company_content = $('<th><input type="text" name="name_company__'+ new_index +'" style="width: 100%;"></th>');

      var reason_to_leave_content = $('<th><input type="text" name="reason_to_leave__'+ new_index +'" style="width: 100%;"></th>');

      var btn_delete_work_experience = $('<th><button data-id="'+ new_index +'" name="btn_delete_work_experience__'+ new_index +'" id="btn_delete_work_experience__'+ new_index +'" type="button" class="button_delete_work_experience">xóa</button></th>');

      var tr = $('<tr id="employee_work_experience_row_infor__'+ new_index +'" class="employee_work_experience_row_infor" data-id="'+ new_index +'">');;   // Create with jQuery
      tr.append(start_date_content);
      tr.append(end_date_content);
      tr.append(company_content);
      tr.append(reason_to_leave_content);
      tr.append(btn_delete_work_experience);

      $('#tbl_employee_work_experience_row > tbody').append(tr);

      $('.button_delete_work_experience').click(function(event){

        var employee_work_experience_row = $('#employee_work_experience_row_infor__' + $(this).data('id'));

        employee_work_experience_row.remove();
       });

   });

  $('.button_delete_work_experience').click(function(event){

    var employee_work_experience_row = $('#employee_work_experience_row_infor__' + $(this).data('id'));

    employee_work_experience_row.remove();
   });


   $('#btn_add_skill').click(function(event){

      var number = $('#tbl_employee_skill_row tbody tr');


      // Lấy dữ liệu của skills
//      var skills = [
//        {id: 1, name: 'Test'},
//        {id: 2, name: 'Test 1'},
//      ];

      var skills = $('#list_skills').val();
      skills = JSON.parse(skills);

      var new_index = number.length ;

      var select_type_skill = '<th><select name="type_skill__'+ new_index +'" data-id="'+ new_index +'"  class="sl_skill_type" style="width: 100%;">';
      var options_type_skill = '';
      for(var i=0; i< skills.length; i++){
        options_type_skill += '<option name="'+ skills[i]['id'] +'" value="'+ skills[i]['id'] +'">'+ skills[i]['name'] +'</option>';
      }
      select_type_skill += options_type_skill;
      select_type_skill += '</select></th>';

      var select_skill = '<th><select id="skill__'+ new_index +'"  name="skill__'+ new_index +'" class="sl_skill" style="width: 100%;"></th>';

      var select_ability = '<th><select id="ability__'+ new_index +'" name="ability__'+ new_index +'" class="sl_level" style="width: 100%;"></th>';

      var btn_delete_skills = $('<th><button data-id="'+ new_index +'" name="btn_delete_skill__'+ new_index +'" id="btn_delete_skill__'+ new_index +'" type="button" class="button_delete_skills">xóa</button></th>');

      var tr = $('<tr id="employee_skill_row__'+ new_index +'" class="employee_skill_row" data-id="'+ new_index +'">');;   // Create with jQuery
      tr.append(select_type_skill);
      tr.append(select_skill);
      tr.append(select_ability);
      tr.append(btn_delete_skills);

      $('#tbl_employee_skill_row > tbody').append(tr);

      $('.button_delete_skills').click(function(event){
        var employee_skills_row = $('#employee_skill_row__' + $(this).data('id'));

        employee_skills_row.remove();
       });

//      $('.sl_skill_type').on('change', change_skill(event));
    $('.sl_skill_type').change(function(event){
            // Check input( $( this ).val() ) for validity here
            // alert($(this).val());
            var type = $(this).val();
            var data = $('#data_skills').val();

            data = JSON.parse(data);


            if(type){

                var index_data = $(this).data('id');




                // Đổ dữ liệu cho Kỹ năng
                var skills_data = data[type]['skills'];

                var selectSkills = $('#skill__' + index_data);

                if(selectSkills.prop) {
                  var options = selectSkills.prop('options');

                }
                else {
                  var options = selectSkills.attr('options');
                }
                $('option', selectSkills).remove();

                $.each(skills_data, function(val, text) {
                    options[options.length] = new Option(text, val);
                });

                // Đổ dữ liệu cho Level
                var levels_data = data[type]['levels'];
                var selectLevel = $('#ability__' + index_data);

                if(selectLevel.prop) {
                  var options = selectLevel.prop('options');

                }
                else {
                  var options = selectLevel.attr('options');
                }
                $('option', selectLevel).remove();

                $.each(levels_data, function(val, text) {
                    options[options.length] = new Option(text, val);
                });
            }

        });

    $('.button_delete_skills').click(function(event){
        var employee_skills_row = $('#employee_skill_row__' + $(this).data('id'));

        employee_skills_row.remove();
       });


   });

   $('#sl_state').change(function(event){
        // Check input( $( this ).val() ) for validity here
        // alert($(this).val());

        var data = $('#sl_state').val();

        var state_id = $(this).val();


        rpc.query({
                route: "/information-employee/state/" + state_id,
            }).then(function (data) {
                $('#district').html('');

                // Fill data vao district
                for (const [key, value] of Object.entries(data)) {

                  var opt = $('<option>').text(value)
                   .attr('value', key);
                   $('#district').append(opt);
                }
            });

        $('#district').change(function(event){
            // Check input( $( this ).val() ) for validity here
            // alert($(this).val());

            var data = $('#district').val();
            var district_id = $(this).val();


            rpc.query({
                    route: "/information-employee/district/" + district_id,
                }).then(function (data) {
                    $('#sl_wards').html('');

                    // Fill data vao district
                    for (const [key, value] of Object.entries(data)) {

                      var opt = $('<option>').text(value)
                       .attr('value', key);
                       $('#sl_wards').append(opt);
                    }
                });
            $('#sl_wards').change(function(event){

                var state = $('#sl_state option:selected').text().trim();
                var district = $('#district option:selected').text().trim();
                var wards = $('#sl_wards option:selected').text().trim();

                var emergency_contact = '';
                if(wards){
                    emergency_contact += wards + ', ';
                }
                if(district){
                    emergency_contact += district + ', ';
                }
                if(state){
                    emergency_contact += state;
                }


                $('#emergency_contact').val(emergency_contact);
            });
        });





    });



  })


});
