// var callInfo = null;
// var callStatus = 'Offline';
// var enableVoice = false;
// var hasCall = false;
// var isRinging = false;
// var isAnswering = false;
// var isMute = false;
// var isHold = false;
// var deviceType;
// var holding = false;
// var isConnectToAgent = false;
// var isCallout = false;
// var disconnectAs = false;
var listTransferAgent;
var timeoutTransfer;
var transferRequest;
var timeoutToPing = 10; //s
var lastSentTime = new Date().getTime();
var ping = {objectId: 11111111};
var noRetry = 1;
var totalRetry = 0;
var retryTimeout = true;
var pingreq;


var BaseRequest = {
    agentId: '',
    extension: ''
};

var csUser;
var notification;

var csVoice = {
    callInfo: null,
    callStatus: 'Offline',
    enableVoice: false,
    hasCall: false,
    isRinging: false,
    isAnswering: false,
    isMute: false,
    isHold: false,
    deviceType: 1,
    holding: false,
    isConnectToAgent: false,
    isCallout: false,
    disconnectAs: false,
    sip_socket: "",
    sip_address: "",
    agentserver_socket: "",
    transferRequest: null
}

function CallInfo() {
    this.callId = "";
    this.caller = "";
    this.agentId = "";
    this.line = "";
    this.callDirection = "";
    this.callerName = "";
    this.callerId = "";
    this.tabIndex = "";
    this.startTime = "";
    this.endTime = "";
}

function checkMedia() {
    if (csVoice.deviceType == 1) {
        navigator.getUserMedia = navigator.getUserMedia || navigator.webkitGetUserMedia || navigator.mozGetUserMedia;
        if (navigator.getUserMedia) {
            navigator.getUserMedia({audio: true},
                function (stream) {
                    console.log("Accessed the Microphone");
                },
                function (err) {
                    console.log("Error: Cannot access the microphone");
                });
        } else {
            console.log("Error: Cannot access the microphone");
        }
    }
}

function sendAs(message) {
console.log(message);
console.log(csUser);
    BaseRequest.agentId = csUser.name;
    BaseRequest.extension = csUser.agent_id;
    // BaseRequest.sessionId = sessionStorage.getItem('session');//$("#sessionId").val();
    // BaseRequest.authenToken = $localStorage.token;
    $.extend(message, BaseRequest);

    agentWebPush.send(message);
    csLog('Client send: ' + JSON.stringify(message));
    lastSentTime = new Date().getTime();
}

function sendWaitAs(message) {
    BaseRequest.agentId = csUser.name;
    BaseRequest.extension = csUser.agent_id;
    $.extend(message, BaseRequest);

    agentWebPush.sendWait(message);
    lastSentTime = new Date().getTime();
}


function changeDevice(tempDeviceType, phoneNo) {
    csVoice.deviceType = tempDeviceType;

    var mess = {
        objectId: CHANGE_DEVICE_TYPE_REQUEST,
        deviceType: tempDeviceType,
        phoneNum: phoneNo
    }

    sendAs(mess);
}

function csInit(authToken, domain) {
    var data = {
        authToken: authToken,
        domain: domain
    }

    $.ajax({
        type: "GET",
        url: API_SERVER + "/api/login/check-partner",
        data: data,
        dataType: "text",
        success: function (response) {
            response = JSON.parse(response);
            if (response.code == 200) {
                csUser = {
                    name: response.user.username,
                    agent_id: response.user.agent_id,
                    extension: response.user.agent_id,
                    phone_no: response.user.phone_no,
                    role: response.user.role
                }
                initCsVoice(response.account.sip_server_url, response.account.sip_socket, response.account.agent_server_url);
                createWs(authToken);
            } else {
                csInitError(response.code);
            }
        }, error: function (response) {
            csInitError(response.code);
        }
    });
}

function reConfigDeviceType() {
    if (csUser.role == 6) { //extension
        changeDevice(4, "");
    } else if (csUser.role == 7) { //mobile
        changeDevice(3, "");
    } else if (csUser.role == 9) { //3c Softphone
        changeDevice(6, "");
    }
}

function csUnregister() {
    if (csVoice.deviceType == 1) {
        unregister();
    }
}

function isCsHasCall() {
    return csVoice.hasCall;
}

function initCsVoice(sip_address, sip_socket, agentserver) {
    csVoice.agentserver_socket = agentserver;
    csVoice.sip_address = sip_address;
    csVoice.sip_socket = sip_socket;
}

function csCallout(number) {
    if (csVoice.enableVoice == true) {
//        console.log("csVoice.deviceType..........................................................");
//        console.log(csVoice.deviceType);
        if (csVoice.deviceType != 2 && csVoice.deviceType != 1) {
            return "Vui lòng bật nút Máy bàn hoặc bật nút Tai nghe"
        }
        console.log("csVoice")
        console.log(csVoice)
        if (!csVoice.isCallout) {
            if (number == "" || !number.match(/^[0-9]{8,13}$/)) {
                if (number != "" && number.match(/^[0-9]{1,7}$/) && number.match(/^[1-9].*/)) {
                    if (csVoice.deviceType == 1) {
                        // GUI.buttonDialClick("sip:" + number + '@' + sip_address);
                        dial_call("sip:" + number + '@' + csVoice.sip_address);
                    } else {
                        console.log("error");
                    }
                } else {
                    console.log("wrong phone number");
                    return "Sai số"
                }
            } else {
//                console.log('Gọi lần 2');
//                console.log(csVoice);
//                console.log(csVoice.hasCall);
//                console.log(csVoice.isConnectToAgent);
//                console.log(number);
                if (!csVoice.hasCall && !csVoice.isConnectToAgent) {
                    csVoice.isCallout = true;
                    // isConnectToAgent = true;
                    // var number = msisdn(number);
                    callOutMsg = {telephoneNumber: number, objectId: OUT_CALL_REQUEST_ID, ticketId: '', callerId: ""};
                    sendAs(callOutMsg);
                    csVoice.isRinging = true;
                    if (csVoice.deviceType == 1) {
                        csVoice.isConnectingCall = true;
                    }
                    showCalloutInfo(number);
                    csVoice.isConnectToAgent = true;
                    csVoice.isCallout = true;
                    csVoice.hasCall = true;
                    csVoice.isRinging = true;
                    csVoice.missCall = false;
                    csVoice.isAnswering = false;
                    csVoice.isMute = false;
                    csVoice.isHold = false;
                    csVoice.callInfo = new CallInfo();
                    csVoice.callInfo.callId = "";
                    csVoice.callInfo.caller = number;
                    csVoice.callInfo.callerName = number;
                    csVoice.callInfo.line = " ";
                    csVoice.callInfo.callDirection = 2;
                    return "OK"
                } else {
                    console.log("Error callout");
                    return "Vui lòng tải lại trang, sử dụng nút Tải lại hoặc tổ hợp phím Ctrl + R hay phím F5"
                }
            }
        } else {
            return false;
//            return "Đang trong cuộc gọi"
        }
    } else {
        console.log("Enable voice to call");
        return "Vui lòng bật tính năng Voice trên ERP. Chuyển Off thành On";
    }
}

function changeCallStatus() {
    console.log('csVoice');
    console.log(csVoice);
    if (csVoice.callStatus != 'Online') {
        status = 'AVAILABLE';
        csVoice.callStatus = 'Online';
    } else {
        status = 'NOT AVAILABLE';
        csVoice.callStatus = 'Offline';
    }
    var message = {status: status, objectId: 2013};
    sendAs(message);
    return csVoice.callStatus;
}

function endCall() {
    if (csVoice.deviceType == 1) {
        csVoice.hasCall = false;
        csVoice.holding = false;
        isClearing = false;
        csVoice.isConnectToAgent = false;
        csVoice.isRinging = false;
        csVoice.isAnswering = false;
        csVoice.callInfo = null;
        terminate_call();

    } else {
        if (csVoice.isHold) {
            return;
        }
        var objectId = TERMINATE_CALL_OUT_REQUEST_ID;
//        console.log('....................');
//        console.log(csVoice);
//        console.log(csVoice.callInfo);

        if (csVoice.callInfo){
            if (csVoice.callInfo.callDirection == 1) {
                objectId = REMOVE_AGENT_REQUEST_ID;
            } else if (csVoice.callInfo.callDirection == 3) {
                objectId = TERMINATE_REQUEST_ID;
            }
            var interuptMsg = {callId: csVoice.callInfo.callId, removeAgentId: csVoice.callInfo.agentId, objectId: objectId};
            sendAs(interuptMsg);
        }else{
            // không thực hiện được cuộc gọi, ví dụ chưa gắn IP Phone
            console.log('Chưa có cuộc gọi');
        }
    }

}

function muteCall() {
    if (csVoice.isHold) {
        return;
    }
    var muteObjectID;
    if (csVoice.callInfo.callDirection == 1) {
        if (csVoice.isMute == true) {
            muteObjectID = UNMUTE_REQUEST_ID;
        } else {
            muteObjectID = MUTE_REQUEST_ID;
        }
    } else {
        alert("Comming soon.");
    }

    messageToSend = {callId: csVoice.callInfo.callId, callType: csVoice.callInfo.callDirection, objectId: muteObjectID};
    sendAs(messageToSend);
}

function holdCall() {
    var holdIdObject;
    if (csVoice.callInfo.callDirection == 1 || csVoice.callInfo.callDirection == 3) {
        if (csVoice.isHold == true) {
            holdIdObject = UN_HOLD_REQUEST_ID;
        } else {
            holdIdObject = HOLD_REQUEST_ID;
        }
    } else {
        if (!csVoice.isRinging) {
            if (csVoice.isHold == true) {
                holdIdObject = UN_HOLD_OUTCALL_REQUEST_ID;
            } else {
                holdIdObject = HOLD_OUTCALL_REQUEST_ID;
            }
        } else {
            return;
        }
    }
    holding = true;
    messageToSend = {callId: csVoice.callInfo.callId, callType: csVoice.callInfo.callDirection, objectId: holdIdObject};
    sendAs(messageToSend);
}

function onAcceptCall() {
    answer_call();
}

function csEnableCall() {
    var mess = {
        objectId: CONFIRM_ENABLE_VOICE_CHANNEL_REQUEST
    }
    sendAs(mess);
}

function createWs(token) {
    agentWebPush = new WebPush();
    agentWebPush.onConnected = function () {
//        var refresh = {objectId: 1010003, authenToken: token};
        var refresh = {objectId: 1010003, authenToken: token};
        sendAs(refresh);
        noRetry = 1;
        disconnectAs = false;
        csLog('Socket connected, logging in..');
    }
    agentWebPush.onDisconnected = function () {
        if ((noRetry <= totalRetry) && retryTimeout) {
            retryTimeout = false;
            setTimeout(function () {
                retryTimeout = true;
                noRetry++;
                reconnectAs();
                evalFn(csNotifyReconnecting, noRetry, totalRetry)
            }, 10000);
        }
        if (noRetry > totalRetry) {
            csLog('Disconnected from server due to network issue, please refresh your browser');
            evalFn(csOndisconnected);

        }
        disconnectAs = true;
    }

    agentWebPush.connect(csVoice.agentserver_socket, 0);

    agentWebPush.onMessageReceived = function (responseResult) {
        var objectId = responseResult.objectId;
        var status = responseResult.status;
        csLog(JSON.stringify(responseResult));

        try {
            switch (responseResult.objectId) {
                case CHANGE_AGENT_STATUS_RESPOND_ID:
                    if (status !== "OK") {
                        if (csVoice.callStatus == 'Online') {
                            csVoice.callStatus = 'Offline';
                        } else {
                            csVoice.callStatus = 'Online';
                        }
                    } else {
                        if (responseResult.agentStatus == 'AVAILABLE') {
                            csVoice.callStatus = 'Online';
                        } else {
                            csVoice.callStatus = 'Offline';
                        }
                    }
                    csShowCallStatus(csVoice.callStatus);

                    break;
                case CHANGE_DEVICE_TYPE_RESPONSE:
                    if (csVoice.deviceType == responseResult.oldDeviceType) {
                        return;
                    }
                    if (responseResult.result == 0) {
                        csVoice.deviceType = responseResult.oldDeviceType;
                    } else {
                        csVoice.deviceType = responseResult.newDeviceType;
                        if (responseResult.newDeviceType == 1) {
                            if (!ua || !ua.isRegistered()) {
                                init_ua(csUser.agent_id, csVoice.sip_address, csVoice.sip_socket);
                                checkMedia();
                            }
                        } else if (responseResult.oldDeviceType == 1) {
                            unregister();
                        }
                    }
                    csShowDeviceType(csVoice.deviceType);
                    break;
                case RING_AGENT_RESPOND_ID:
                    if (responseResult.extension == csUser.agent_id) {
                        if (csVoice.enableVoice == true) {
                            if (!csVoice.callInfo) {
                                csVoice.callInfo = new CallInfo();
                            }
                            csVoice.callInfo.callId = responseResult.callId;
                            csVoice.callInfo.caller = responseResult.caller;
                            csVoice.callInfo.callerName = responseResult.caller;
                            csVoice.callInfo.line = responseResult.line;
                            csVoice.callInfo.callDirection = responseResult.callDirection;
                            csVoice.callInfo.agentId = responseResult.extension;
                            csVoice.hasCall = true;
                            csVoice.isRinging = true;
                            csVoice.missCall = false;
                            csVoice.isAnswering = false;
                            csVoice.isMute = false;
                            csVoice.isHold = false;
                            csVoice.isCallout = false;
                            if (csVoice.deviceType != 1) {
                                csCallRinging(responseResult.caller);
                            }
                            csCurrentCallId(responseResult.callId);
                        }
                    }
                    break;
                case AGENT_ANSWER_RESPOND_ID:
                    if (responseResult.extension == csUser.agent_id) {
                        if (csVoice.enableVoice == true) {
                            if (csVoice.deviceType != 1) {
                                csVoice.isRinging = false;
                                csVoice.isAnswering = true;
                                csAcceptCall();
                            }
                        }
                    }
                    break;
                case AGENT_END_CALL_RESPOND_ID:
                    if (responseResult.extension == csUser.agent_id) {
                        if (csVoice.enableVoice == true) {
                            if (csVoice.deviceType != 1) {
                                csVoice.hasCall = false;
                                csVoice.holding = false;
                                isClearing = false;
                                if (csVoice.isAnswering == false) {
                                    csVoice.missCall = true;
                                    csVoice.isRinging = false;
                                } else {
                                    csVoice.isAnswering = false;
                                }
                                csVoice.callInfo = null;
                                csEndCall();
                            }
                        }
                    }
                    break;
                case MUTE_RESPOND_ID:
                    if (csVoice.enableVoice == true) {
                        csVoice.isMute = true;
                        csMuteCall();
                    }
                    break;
                case UNMUTE_RESPOND_ID:
                    if (csVoice.enableVoice == true) {
                        csVoice.isMute = false;
                        csUnMuteCall();
                    }
                    break;
                case HOLD_RESPOND_ID:
                case HOLD_OUTCALL_RESPONSE_ID:
                    if (csVoice.enableVoice == true) {
                        if (responseResult.status == "OK") {
                            csVoice.holding = false;
                            csVoice.isHold = true;
                        } else {
                            csVoice.holding = false;
                        }
                        csHoldCall();
                    }
                    break;
                case UNHOLD_RESPOND_ID:
                case UNHOLD_OUTCALL_RESPONSE_ID:
                    if (csVoice.enableVoice == true) {
                        if (responseResult.status == "OK") {
                            csVoice.isHold = false;
                            csVoice.holding = false;
                        } else {
                            csVoice.holding = false;
                        }
                        csUnHoldCall();
                    }
                    break;
                case OUT_CALL_RESPONSE_ID:
                    if (csVoice.enableVoice == true) {
                        var callOutStatus = responseResult.status;
                        if (callOutStatus.toUpperCase() === 'ERROR') {
                            showCalloutError(responseResult.errorCode, responseResult.sipCode);
                            csVoice.isConnectToAgent = false;
                            csVoice.hasCall = false;
                            csVoice.isRinging = false;
                            csVoice.isAnswering = false;
                            csVoice.callInfo = null;
                            csVoice.isCallout = false;
                        } else if (callOutStatus.toUpperCase() == "STARTING") {
                            if (responseResult.ipphone == csUser.agent_id) {
                                if (csVoice.callInfo == null) {
                                    csVoice.callInfo = new CallInfo();
                                    csVoice.isCallout = true;
                                    csVoice.callInfo.callId = responseResult.callId;
                                } else {
                                    csVoice.callInfo.callId = responseResult.callId;
                                }
                            }
                        } else if (callOutStatus.toUpperCase() === "RINGING") {
                            if (responseResult.ipphone == csUser.agent_id) {
                                if (csVoice.deviceType != 1) {
                                    csVoice.isConnectToAgent = false;
                                    csVoice.hasCall = true;
                                    csVoice.isRinging = true;
                                    csVoice.missCall = false;
                                    csVoice.isAnswering = false;
                                    csVoice.isMute = false;
                                    csVoice.isHold = false;
                                    csVoice.callInfo.caller = responseResult.telephoneNumber;
                                    csVoice.callInfo.callerName = responseResult.telephoneNumber;
                                    csVoice.callInfo.line = responseResult.line == "" ? " " : responseResult.line;
                                    csVoice.callInfo.callDirection = 2;
                                    csVoice.callInfo.agentId = responseResult.extension;
                                    showCalloutInfo(responseResult.telephoneNumber);
                                }
                                csCurrentCallId(responseResult.callId);
                            }
                        } else if (callOutStatus.toUpperCase() === "ANSWER") {
                            if (responseResult.ipphone == csUser.agent_id) {
                                if (csVoice.deviceType != 1) {
                                    csVoice.isRinging = false;
                                    csVoice.isAnswering = true;
                                }
                                csCustomerAccept();
                            }
                        } else if (callOutStatus.toUpperCase() === "ENDCALL") {
                            if (responseResult.ipphone == csUser.agent_id) {
                                if (csVoice.deviceType != 1) {
                                    csVoice.hasCall = false;
                                    csVoice.isConnectToAgent = false;
                                    csVoice.isRinging = false;
                                    csVoice.isAnswering = false;
                                    csVoice.holding = false;
                                    isClearing = false;
                                    csVoice.isAnswering = false;
                                    csVoice.isCallout = false;
                                    csVoice.callInfo = null;
                                }
                            }
                        } else if (callOutStatus.toUpperCase() === "TERMINATE") {
                            if (responseResult.ipphone == csUser.agent_id) {
                                if (csVoice.deviceType != 1) {
                                    csVoice.hasCall = false;
                                    csVoice.isConnectToAgent = false;
                                    csVoice.isRinging = false;
                                    csVoice.isAnswering = false;
                                    csVoice.holding = false;
                                    csVoice.isAnswering = false;
                                    csVoice.isCallout = false;
                                    csVoice.callInfo = null;
                                }
                            }
                        }
                    }
                    break;
                case ERROR_CALL_RESPONSE_ID:
                    if (responseResult.status != "OK") {
                        $.jGrowl($filter('translate')(responseResult.status), {theme: 'error'});
                    }
                    if (responseResult.status == ERROR_CODE_CALL_NOT_FOUND) {
                        csVoice.hasCall = false;
                        csVoice.missCall = false;
                        csVoice.isAnswering = false;
                        csVoice.isRinging = false;
                        csVoice.isMute = false;
                        csVoice.isHold = false;
                        csVoice.isCallout = false;
                        csVoice.callInfo = null;
                    }

                    break;
                case REFRESH_ID:
                    connected = true;
                    if (responseResult.agentStatus !== "AVAILABLE") {
                        csVoice.callStatus = 'Offline';
                    } else {
                        csVoice.callStatus = 'Online';
                    }
                    csShowCallStatus(csVoice.callStatus);
                    if (responseResult.isVoiceChannel == 1) {
                        csVoice.enableVoice = true;
                        if (responseResult.deviceType == 1) {
                            if (!ua || !ua.isRegistered()) {
                                init_ua(csUser.agent_id, csVoice.sip_address, csVoice.sip_socket);
                                checkMedia();
                            }
                        } else {

                        }
                        csVoice.deviceType = responseResult.deviceType;
                    } else {
                        csVoice.enableVoice = false;
                        csVoice.deviceType = responseResult.deviceType;
                    }
                    csShowEnableVoice(csVoice.enableVoice);
                    csShowDeviceType(csVoice.deviceType);
                    csInitComplete();
                    totalRetry = 20;
                    clearInterval(pingreq);
                    pingreq = setInterval(function () {
                        if (disconnectAs == true) {
                            clearInterval(pingreq);
                        } else {
                            var now = new Date().getTime() - lastSentTime;
                            var itv = Math.round(now / 1000);
                            if (itv > timeoutToPing) {
                                sendAs(ping);
                            }
                        }
                    }, 10000);
                    csLog('Logged in successful');
                    break;
                case LOGIN_RESPONSE_ID:
                    channelId = responseResult.channelId;

                    break;
                case ENABLE_VOICE_CHANNEL_RESPONSE:
                    if (responseResult.result == 1) {
                        csVoice.deviceType = responseResult.deviceType;
                        if (responseResult.deviceType == 1) {
                            totalRetry = 20;
                            if (!ua || !ua.isRegistered()) {
                                init_ua(csUser.agent_id, csVoice.sip_address, csVoice.sip_socket);
                            }
                        } else {
                            totalRetry = 20;
                        }
                        csVoice.enableVoice = true;
                        csShowEnableVoice(csVoice.enableVoice);
                    }

                    break;
                case CONFIRM_ENABLE_VOICE_CHANNEL_RESPONSE:
                    confirmEnableVoice = true;
                    break;
                case DISABLE_VOICE_CHANNEL_RESPONSE:
                    csVoice.enableVoice = false;
                    csShowEnableVoice(csVoice.enableVoice);
                    unregister();
                    break;
                case PING_ID:
                    sendAs(ping);
                    break;
                case RELOAD_AGENT_STATUS_RESPONSE_ID:
                    if (responseResult.agentStatus == "NO ANSWER") {
                        csVoice.callStatus = "No Answer";
                        csShowCallStatus(csVoice.callStatus);
                    }
                    break;
                case INTERNAL_CALL_RING_RESPONSE_ID:
                    if (csVoice.enableVoice == true) {
                        csVoice.isConnectToAgent = false;
                        csVoice.hasCall = true;
                        csVoice.isRinging = true;
                        csVoice.missCall = false;
                        csVoice.isAnswering = false;
                        csVoice.isMute = false;
                        csVoice.isHold = false;
                        csVoice.callInfo = new CallInfo();
                        csVoice.callInfo.callId = responseResult.callId;
                        csVoice.callInfo.caller = responseResult.called;
                        csVoice.callInfo.callerName = responseResult.called;
                        csVoice.callInfo.line = "";
                        csVoice.callInfo.callDirection = 3;
                        csVoice.callInfo.agentId = responseResult.called;
                    }

                    break;
                case INTERNAL_CALL_ANSWER_RESPONSE_ID:
                    if (csVoice.enableVoice == true) {
                        if (csVoice.deviceType != DEVICE_BROWSER) {
                            csVoice.isRinging = false;
                            csVoice.isAnswering = true;
                        }
                    }

                    break;
                case INTERNAL_CALL_END_RESPONSE_ID:
                    if (csVoice.enableVoice == true) {
                        if (csVoice.deviceType != DEVICE_BROWSER) {
                            csVoice.hasCall = false;
                            csVoice.isConnectToAgent = false;
                            csVoice.isRinging = false;
                            csVoice.isAnswering = false;
                            csVoice.holding = false;
                            isClearing = false;
                            csVoice.callInfo = null;
                        }
                    }
                    break;
                case TERMINATE_RESPOND_ID:
                    var callId = responseResult.callId;
                    var status = responseResult.status;
                    if (status != "OK") {
                        var errorMessage = getErrorMessage(status);
                        console.log('errorMessage');
                    } else {
                        var superAgent = responseResult.superAgent;
                        var terminatedAgent = responseResult.terminatedAgent;
                        //lay thong tin ve Agent extension
                        var currentAgentId = csUser.agent_id;
                        //neu du lieu nhan ve, ung voi man hinh cua Agent ra lenh ket thuc, thuong la Supervisor
                        //hien thi thong bao ket thuc cuoc goi thanh cong
                        if (currentAgentId != terminatedAgent) {
                            //neu du lieu nhan ve, ung voi man hinh cua Agent bi ket thuc cuoc goi,
                            // hien thi thong bao nguyen nhan vi sao cuoc goi bi ket thuc
                            $.jGrowl($filter('translate')('SUPER_TERMINATE_SUCCESSFUL', {superAgent: superAgent, call: callId}), {theme: 'notice'});
                        }
                    }

                    break;
                case AGENT_SEARCH_AGENT_RESPONSE_ID:
                    listTransferAgent = responseResult.listAgentSearch;
                    csListTransferAgent(listTransferAgent);
                    break;
                case TRANSFER_AGENT_TO_AGENT_RESPOND_ID:
                    var callId = responseResult.callId;
                    var status = responseResult.status;
                    var agentReceive = {superAgent: responseResult.superAgent, ipphone: responseResult.newAgent};
                    if (responseResult.dropAgent == csUser.agent_id) {
                        if (status != "OK") {
                            var errMessage = getErrorMessage("IPCCERR0013");
                            csTransferCallError(errMessage, agentReceive);
                        } else {
                            csTransferCallSuccess(agentReceive);
                        }
                    } else if (csUser.agent_id == responseResult.newAgent) {
                        if (status != "OK") {
                            var errorMessage = getErrorMessage(status);
                            csTransferCallError(errorMessage);
                        }
                    }
                    break;
                case TRANSFER_AGENT_TO_AGENT_CONFIRM_REQUEST_ID:
                    if (csVoice.enableVoice == true) {
                        csNewCallTransferRequest(responseResult);
                        csVoice.transferRequest = responseResult;
                        timeoutTransfer = setTimeout(function () {
                            responseTransferAgent(0);
                        }, 10000);
                    }
                    break;
                case TRANSFER_AGENT_TO_AGENT_CONFIRM_RESPONSE_ID:
                    if (responseResult.status == "OK") {
                        csTransferCallResponse("OK");
                    } else {
                        csTransferCallResponse("NOK");
                    }

                    break;
                case TRANFER_TO_ACD_RESPONSE:
                    if (responseResult.status == "OK") {
                        csTransferCallResponse("OK");
                    } else {
                        csTransferCallResponse("NOK");
                    }
                    break;
                case SURVEY_VOICE_RESPONSE_ID:
                    var status;
                    if (responseResult.status == "OK") {
                        status = true;
                    } else {
                        status = false;
                    }
                    evalFn(csTransferSurveyResponse, status)
                    break;
            }
        } catch (ex) {
            console.log(ex.message);
        }
    }
}

function evalFn(fn, ...arg) {
    if (typeof fn === 'function') {
        fn(...arg);
    }
}

function reconnectAs() {
    csLog('Lost connect to socket server,reconnecting....(' + noRetry + '/' + totalRetry + ')');
    if (csVoice.agentserver_socket) {
        // if ($scope.permission.VOICE_VIA_BROWSER) {
        // if ($scope.deviceType == DEVICE_BROWSER) {
        //     $window.location.reload();
        // } else {
        agentWebPush.connect(csVoice.agentserver_socket, 0);
        // }
    }
}

var getErrorMessage = function (errorCode) {
    if (errorCode == "IPCCERR0000") {
        return "CANNOT_FIND_THE_CALL";
    }
    if (errorCode == "IPCCERR0001") {
        return "AGENT_IS_NOT_AVAILABLE";
    }
    if (errorCode == "IPCCERR0002") {
        return "CANNOT_FIND_THE_AGENT";
    }
    if (errorCode == "IPCCERR0003") {
        return "AGENT_IS_IN_MUTE_OR_HOLD_STATUS";
    }
    if (errorCode == "IPCCERR0004") {
        return "AGENT_IS_NOT_IN_MUTE_STATUS";
    }
    if (errorCode == "IPCCERR0005") {
        return "AGENT_IS_NOT_IN_HOLD_STATUS";
    }

    if (errorCode == "IPCCERR0007") {
        return "NUMBER_OF_PARAMETERS_ARE_NOT_SATISFIED";
    }
    if (errorCode == "IPCCERR0008") {
        return "CANNOT_HOLD_THE_RINGING_CALL";
    }
    if (errorCode == "IPCCERR0009") {
        return "CANNOT_MUTE_THE_RINGING_CALL";
    }

    if (errorCode == "IPCCERR0011") {
        return "CANNOT_INTERCEPT_A_MUTING_CALL";
    }
    if (errorCode == "IPCCERR0012") {
        return "NOT_CHOOSE_TYPE_TRANSFER";
    }
    if (errorCode == "IPCCERR0013") {
        return "TRANSFER_CALL_FAILED";
    }
    if (errorCode == "IPCCERR0014") {
        return "NOT_IN_A_CALL";
    }
    if (errorCode == "IPCCERR0015") {
        return "COULD_NOT_GET_CALL_INFO";
    }

    return errorCode;
}

function hasCallRinging(phoneNumber) {
    if (csVoice.callInfo != null && csVoice.isCallout) {
        answer_call();
        csVoice.isConnectingCall = false;
    } else {
        csVoice.hasCall = true;
        csVoice.isRinging = true;
        csVoice.missCall = false;
        csVoice.isAnswering = false;
        csVoice.isMute = false;
        csVoice.isHold = false;
        if (!csVoice.callInfo) {
            csVoice.callInfo = new CallInfo();
        }
        csVoice.callInfo.caller = phoneNumber;
        csVoice.callInfo.callerName = phoneNumber;
        csVoice.callInfo.callDirection = 1;
    }
}

function isCsCallout() {
    return (csVoice.hasCall == true && csVoice.isCallout == true);
}

function acceptedCall() {
    if (!csVoice.isCallout) {
        csVoice.isRinging = false;
        csVoice.isAnswering = true;
    } else {
        csVoice.isRinging = false;
        csVoice.isAnswering = true;
        csVoice.isConnectToAgent = false;
    }
}

function endedCall() {
    if (!csVoice.isCallout) {
        csVoice.hasCall = false;
        csVoice.isConnectToAgent = false;
        csVoice.holding = false;
        isClearing = false;
        if (csVoice.isAnswering == false) {
            csVoice.missCall = true;
            csVoice.isRinging = false;
        } else {
            csVoice.isAnswering = false;
        }

    } else {
        csVoice.hasCall = false;
        csVoice.isConnectToAgent = false;
        csVoice.isRinging = false;
        csVoice.isAnswering = false;
        csVoice.holding = false;
        isClearing = false;
    }
    csVoice.isCallout = false;
    csVoice.callInfo = null;
}

function getTransferAgent() {
    var mess = {
        username: "",
        agentStatus: "AVAILABLE",
        callStatus: "READY",
        operation: "",
        timeInStatus: "",
        objectId: AGENT_SEARCH_AGENT_REQUEST_ID
    };
    sendAs(mess);
}

function csTransferCallAgent(ipphone) {
    var transfer = {agent: {ipPhone: ipphone}};
    transferCallAgent(1, transfer);
}

function csTransferCallAcd(queueId) {
    var transfer = {acd: {queueId: queueId}};
    transferCallAgent(2, transfer);
}

function transferCallAgent(type, transferInfo) {
    if (!csVoice.isAnswering) {
        csTransferCallError(getErrorMessage("IPCCERR0014"));
        return;
    }
    if (!csVoice.callInfo) {
        csTransferCallError(getErrorMessage("IPCCERR0015"));
        return;
    }
    if (type) {
        if (type == 1) {
            if (transferInfo.agent != "") {
                var mess = {
                    callId: csVoice.callInfo.callId,
                    newAgentId: transferInfo.agent.ipPhone,
                    dropAgentId: csVoice.callInfo.agentId,
                    objectId: TRANSFER_AGENT_TO_AGENT_CONFIRM_REQUEST_ID
                }
                sendAs(mess);
            }
        } else {
            if (transferInfo.acd != "") {
                var mess = {
                    callId: csVoice.callInfo.callId,
                    acdId: transferInfo.acd.queueId,
                    objectId: TRANSFER_TO_ACD_REQUEST_ID
                };
                sendAs(mess);
            }
        }
    } else {
        var errorMess = getErrorMessage("IPCCERR0012");
        csTransferCallError(errorMess);
    }
}

function responseTransferAgent(val) {
    clearTimeout(timeoutTransfer);
    var mess = {
        callId: csVoice.transferRequest.callId,
        dropAgentId: csVoice.transferRequest.dropAgentId,
        newAgentId: csVoice.transferRequest.newAgentId,
        status: val == 1 ? "OK" : "NOK",
        objectId: TRANSFER_AGENT_TO_AGENT_CONFIRM_RESPONSE_ID
    }
    sendAs(mess);
}

function csLog(message) {
    var debug = localStorage.getItem("csDebug");
    if (debug != 'off') {
        console.log(message);
        try {
          message = JSON.parse(message);
          console.log(message)
          var res_id = $('#call_button').data('res_id');

            if (message['ticketId'] == undefined || message['ticketId'] == null || message['ticketId'] == 'undefined' || message['isVoiceChannel'] == 0){
                return;
            }

            $.ajax({
                    url: '/create/phone-call-history',
                    type: 'POST',
                    data: {
                        message: JSON.stringify(message),
                        res_id : res_id,
                        model : $('#call_button').data('model')

                    }
                }).done(function(response) {
                   $('.oe_pager_refresh').trigger('click');
                });
        }
        catch(err) {
          return
        }




    }
}

/**
 * chuyen survey thoai
 * @param survey: obj {
 *     id : id survey,
 *     sipurl : sip url
 * }
 */
function transferSurvey(survey) {
    try {
        if (!survey) {
            throw new Error("missing survey info");
        }
        var mess = {
            callId: csVoice.callInfo.callId,
            ivrId: survey.id,
            sipUrl: survey.sipurl,
            objectId: SURVEY_VOICE_REQUEST_ID
        }
        sendAs(mess);
    } catch (err) {
        console.error(err);
    }
}