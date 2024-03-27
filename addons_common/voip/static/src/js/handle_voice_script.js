$(window).bind('beforeunload', function (e) {
// Không cần hiện thông báo
//    if (1 == 1) {
//        return 'abc';
//    }
});

$(window).bind('unload', function () {
    csUnregister();
    if (csVoice.enableVoice) {
        reConfigDeviceType();
    }
});

// kết thúc cuộc gọi ra/vào
function csEndCall() {
//    console.log("Call is ended===================================================================");
//    console.log(csVoice.isCallout);
//    console.log(csVoice);
//    document.getElementById('phoneNo').innerHTML = "";
    $('#transferCall').attr('disabled', 'disabled');
    $('#transferCallAcd').attr('disabled', 'disabled');
    $('#transferSurvey').attr('disabled', 'disabled');
        // Cho phép cuộc gọi mới
    csVoice.isCallout = false;

    // Ẩn nút Hủy, bật nút Gọi
    $('.o_dial_end_call_button').addClass('o_hidden');
    $('.o_dial_call_button').removeClass('o_hidden');
}

// đổ chuông trình duyệt của agent khi gọi vào
// đổ chuông tới khách hàng khi gọi ra
function csCallRinging(phone) {
    console.log("Has a new call to customer: " + phone);
//    document.getElementById('phoneNo').innerHTML = phone + ' đang gọi ...';
}

// cuộc gọi vào được agent trả lời
function csAcceptCall() {
    console.log("Call is Accepted");
//    document.getElementById('phoneNo').innerHTML = "Đang trả lời";
    $('#transferCall').removeAttr('disabled');
    $('#transferCallAcd').removeAttr('disabled');
    $('#transferSurvey').removeAttr('disabled');

}

// cuộc gọi ra được khách hàng trả lời
function csCustomerAccept() {
    console.log("csCustomerAccept");
//    console.log("Xử lý đang trả lời");
//    console.log("Hủy cuộc gọi");
//    console.log(csVoice.isCallout);
//    console.log(csVoice);
    // Cho phép cuộc gọi mới
    csVoice.isCallout = false;
    document.getElementById('phoneNo').innerHTML = "Khách hàng có phản hồi";
}

function csMuteCall() {
    console.log("Call is muted");
}

function csUnMuteCall() {
    console.log("Call is unmuted")
}

function csHoldCall() {
    console.log("Call is holded");
}

function csUnHoldCall() {
    console.log("Call is unholded");
}

function showCalloutInfo(number) {
    console.log("callout to " + number);
}

function showCalloutError(errorCode, sipCode) {
    console.log("callout error " + errorCode + " - " + sipCode);
    // Chuyển trạng thái của call
}

function csShowEnableVoice(enableVoice) {
    console.log(`Voice active status : ${enableVoice}`);
    if (enableVoice) {
        $('#enable').attr('disabled', 'disabled');
    } else {
        $('#enable').removeAttr('disabled');
    }
    var text;
    if (enableVoice){
        text = 'On';
        $(".o_dial_enable_button i.fa-circle").css("color", "green");
        $(".o_dial_enable_button span").html(text);
        $(".o_dial_enable_button").prop("title", text);
        $(".o_dial_enable_button").prop("aria-label", text);
    }else{
        text = 'Off';
        $(".o_dial_enable_button i.fa-circle").css("color", "gray");
        $(".o_dial_enable_button span").html(text);
        $(".o_dial_enable_button").prop("title", text);
        $(".o_dial_enable_button").prop("aria-label", text);
    }
}

function csShowDeviceType(type) {
    console.log(`Current device: ${type}`);

    if (type == 1){
        $(".o_dial_ear_phone_button i.fa-headphones").css("color", "green");
    }else{
        $(".o_dial_ear_phone_button i.fa-headphones").css("color", "gray");
    }

    if (type == 2){
        $(".o_dial_transfer_button i.fa-fax").css("color", "green");
    }else{
        $(".o_dial_transfer_button i.fa-fax").css("color", "gray");
    }


}

function csShowCallStatus(status) {
    console.log("csShowCallStatus........................................");
    $('#onOffIncicator').text(status);
    console.log(status);
//    $(".o_dial_enable_button i.fa-circle").css("color", "green");
}

function csInitComplete() {
    console.log("csInitComplete");
}

function csCurrentCallId(callId) {
    console.log("csCurrentCallId: " + callId);
}

function csInitError(error) {
    console.log("csInitError: " + error);
    // Không hiện dialog

}

function csListTransferAgent(listTransferAgent) {
    console.log(listTransferAgent);
}

function csTransferCallError(error, tranferedAgentInfo) {
    console.log('Transfer call failed,' + error);
}

function csTransferCallSuccess(tranferedAgentInfo) {
    console.log('transfer call success');
}

function csNewCallTransferRequest(transferCall) {
    console.log('new call transfer');
    console.log(transferCall);
//    document.getElementById('phoneNo').innerHTML = transferCall.dropAgentId + ' chuyển cg cho bạn';
    $('#transferResponseOK').removeAttr('disabled');
    $('#transferResponseReject').removeAttr('disabled');
}

function csTransferCallResponse(status) {
    $('#transferResponseOK').attr('disabled', 'disabled');
    $('#transferResponseReject').attr('disabled', 'disabled');
    console.log(status);
}

function csNotifyReconnecting(noretry, totalRetry) {
    console.log('reconnecting from custom js......');
}

function csOndisconnected() {
    console.log('disconnected from custom js !!!!!!!!');
}

