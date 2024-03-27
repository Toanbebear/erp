odoo.define('survey_brand.custom', function (require) {
'use strict';
require('web.dom_ready');
var rpc = require('web.rpc');
var ajax = require('web.ajax');

$(document).ready(function(){
    var nbrChar = 0;
    var nbrSMS = 0;
    var encoding = '';
    _init();

    $(".content-sms").on('change keyup paste', function() {
        _init();
    });

    function _init(){
        if (_compute()){
            var info = '' + nbrChar + ' ký tự, khớp với ' + nbrSMS + ' SMS (' + encoding + ')';
            $('.sms-info').html(info);
        }

    };

    function _compute() {
        var content = $('.content-sms').val();
        if(content){
            encoding = _extractEncoding(content);
            nbrChar = content.length;
            nbrChar += (content.match(/\n/g) || []).length;
            nbrSMS = _countSMS(nbrChar, encoding);
            return true;
        }
        return false;
    };

    function _extractEncoding(content) {
        if (String(content).match(RegExp("^[@£$¥èéùìòÇ\\nØø\\rÅåΔ_ΦΓΛΩΠΨΣΘΞÆæßÉ !\\\"#¤%&'()*+,-./0123456789:;<=>?¡ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ§¿abcdefghijklmnopqrstuvwxyzäöñüà]*$"))) {
            return 'Không dấu';
        }
        return 'Có dấu';
    };

    function _countSMS () {
        if (nbrChar === 0) {
            return 0;
        }
        if (encoding === 'Có dấu') {
            if (nbrChar <= 70) {
                return 1;
            }
            return Math.ceil(nbrChar / 67);
        }
        if (nbrChar <= 160) {
            return 1;
        }
        return Math.ceil(nbrChar / 153);
    };

    $('.btn_shorten_url_clipboard').click(function(){
        $('#link_survey').select();
        document.execCommand("copy");
        $(this).attr('title', 'Copied');
    });

     $('.btn-start-survey').click(function(){
        //console.log('btn-start-survey');
    });

    $('.btn-send-sms-survey').click(function(){
         var content = $('.content-sms').val();
         var phone = $('#customer_phone_to').val();
         var brand_id = $('#brand_id').val();
         var company_id = $('#company_id').val();

         // Gửi sms
         ajax.jsonRpc("/survey_brand/survey/send-sms-survey-customer", 'call', {
            'brand': brand_id,
            'company': company_id,
            'phone': phone,
            'content': content,
        }).then(function (data) {
            if (data){
                if (data.code == 'OK'){
                    $('.btn-send-sms-survey').attr('disabled', true);
                    $('.btn-send-sms-survey').attr('title', 'Đã gửi SMS');
                    $('.message').html(data.message);
                }
            }
           else{
                //console.log('data2');
                //console.log(data);
           }
        });
    });

    $('.btn-create-survey').click(function(){
        var booking = $('input[name=booking_id]').val();
        var walkin = $('input[name=walkin_id]').val();
        var evaluation = $('input[name=evaluation_id]').val();
        var phone_call = $('input[name=phone_call_id]').val();
        var survey = $('input[name=survey_survey]:checked').val();
        var time = $('.control-time:checked').val();
        var group_service = $('.control-group-service:checked').val();
        window.location.href = "/survey_brand/survey/booking/" + booking + "/create-survey-customer/" + survey + '?group_service_id=' + group_service + '&time_id=' + time + '&walkin_id=' + walkin + '&evaluation_id=' + evaluation + '&phone_call_id=' + phone_call;
        return false;
    });

    $('.control-survey-survey').on('change', function(event) {
        //console.log('control-survey-survey');
    });

    // Chọn nhóm dịch vụ
    $('.control-group-service').change(function(){
        var time = $('.control-time:checked').val();
        var brand = $('#brand').val();
        var branch = $('#branch_id').val();
        filterSurvey(this.value,time,brand,branch);
    });

    // Tiêu chí
    $('.control-time').change(function(){
        var group_service = $('.control-group-service:checked').val();
        var brand = $('#brand').val();
        var branch = $('#branch_id').val();
        filterSurvey(group_service,this.value,brand,branch);
    });


    function filterSurvey(group_service, time, brand, branch){
        ajax.jsonRpc("/survey_brand/survey", 'call', {
            'group_service': group_service,
            'time': time,
            'brand': brand,
            'branch': branch,
        }).then(function (data) {
            if (data){
                 var datas = JSON.parse(data);
                if(datas['surveys']){
                    // Tìm thấy những bộ khảo sát phù hợp, chọn bộ khảo sát đầu tiên
                    var surveys =  datas['surveys'];
                    var surveys_html = '';
                    for(var index in surveys){
                        var survey = surveys[index];
					    surveys_html += '<div class="custom-control custom-radio">';
					    // Chọn bộ khảo sát đầu tiên
					    surveys_html += '<input type="radio" ' + (index == 0? 'checked="checked"': '') + ' id="survey_survey_' + survey['id'] + '" data-id=1 name="survey_survey" class="custom-control-input control-survey-survey" value="'+ survey['access_token'] +'"/>';
					    surveys_html += '<label for="survey_survey_' + survey['id'] + '" class="custom-control-label">' + survey['title'] +'</label>';
					    surveys_html += '</div>';
				    }
                    if(surveys_html){
                        $('#survey_survey_select').html(surveys_html);
                        $('.btn-start-survey').removeAttr('disabled');
                        $('.btn-create-survey').removeAttr('disabled');

                        // Gán event cho những thành phần mới
                        $('.control-survey-survey').on('change', function(event) {
                             var booking_id = $('#booking_id').val();
                             $('.js_surveyform').attr('data-submit', '/survey_brand/booking/' + booking_id + '/' + this.value);
                        });
                        $('.control-survey-survey').on('change', function(event) {
                             var walkin_id = $('#walkin_id').val();
                             $('.js_surveyform').attr('data-submit', '/survey_brand/walkin/' + walkin_id + '/' + this.value);
                        });
                        $('.control-survey-survey').on('change', function(event) {
                             var evaluation_id = $('#evaluation_id').val();
                             $('.js_surveyform').attr('data-submit', '/survey_brand/evaluation/' + evaluation_id + '/' + this.value);
                        });
                        $('.control-survey-survey').on('change', function(event) {
                             var evaluation_id = $('#phone_call_id').val();
                             $('.js_surveyform').attr('data-submit', '/survey_brand/phone_call/' + phone_call_id + '/' + this.value);
                        });
                    }else{
                        $('#survey_survey_select').html("<p class='text-danger text-center'><strong>Chưa có bộ khảo sát nào phù hợp</strong></p>");
                        $('.btn-start-survey').attr('disabled', true);
                        $('.btn-create-survey').attr('disabled', true);
                    }


                }
            }
           else{
            //  console.log(data);
           }
        });

    } // end filterSurvey

});

});
