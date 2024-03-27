function WebPush() {
    this.webSocket;

    this.url;
    this.requestDisconnect;
    this.id;
    this.onConnected;
    this.onDisconnected;
    this.onMessageReceived;
}

WebPush.prototype.onConnected = function () {
};
WebPush.prototype.onDisconnected = function () {
};
WebPush.prototype.onMessageReceived = function (msg) {
};

WebPush.prototype.connect = function (url, forceLongPolling) {
    var webPush = this;
    this.url = url;
    this.requestDisconnect = false;

    //fix IE AJAX cross domain
    $.support.cors = true;

    //setup disconnect khi chuyen trang
//    $(window).unload(function () {
//        webPush.close();
//    });
    $(window).on("beforeunload", function(event) {
//        alert("call");
//        console.log("this will be triggered");
        //event.preventDefault();
        webPush.close();
    });

    if (window.WebSocket && (forceLongPolling === undefined || !forceLongPolling)) {
		if(this.webSocket){
			this.webSocket.onopen = function (){};
			this.webSocket.onclose = function (){};
			this.webSocket.onerror = function (){};
			this.webSocket.onmessage = function (){};
			try{
				this.webSocket.close();
			}catch(e){}
		}


        this.webSocket = new WebSocket('wss://' + url + '/websocket');
        this.webSocket.onopen = this.onConnected;
        this.webSocket.onclose = this.onDisconnected;

        this.webSocket.onerror = function () {
            webPush.onDisconnected();
        };

        this.webSocket.onmessage = function (evt) {
            var msg = JSON.parse(evt.data);
            webPush.onMessageReceived(msg);
        };
        this.onMessageReceived;
    } else {
	cslog('use long polling');
        $.ajax({
            dataType: 'json',
            url: 'http://' + url + '/connect',
            data: {},
            cache: false, //fix loop IE
            success: function (data, textStatus, jqXHR) {
                if (data.r === 1) {
                    webPush.id = data.id;
                    webPush.onConnected();
                    webPush.poll(url);
                } else {
//					cslog('connect error: ' + data.r);
                    webPush.onDisconnected();
                }
            },
            error: function (jqXHR, textStatus, errorThrown) {
//				cslog('connect error: ' + textStatus);
//				cslog(errorThrown);
                webPush.onDisconnected();
            }
        });

    }
};

WebPush.prototype.poll = function (url) {
    var webPush = this;
    $.ajax({
        dataType: 'json',
        url: 'http://' + url + '/poll/' + webPush.id,
        cache: false, //fix loop IE
        data: {},
        success: function (data, textStatus, jqXHR) {
            if (data.r === 1) {
                if (data.list) {
                    for (var i = 0; i < data.list.length; i++) {
                        var msg_i = data.list[i];
                        webPush.onMessageReceived(msg_i);
                    }
                }

                if (!webPush.requestDisconnect) {
//					cslog('poll success: +++++++++++');
                    setTimeout(function () {
                        webPush.poll(url);
                    }, 1);
                } else {
                    webPush.onDisconnected();
                }
            } else {
//				cslog('poll error, code: ' + data.r);
                webPush.onDisconnected();
            }
        },
        error: function (jqXHR, textStatus, errorThrown) {
//			cslog('error: ' + textStatus);
            webPush.onDisconnected();
        },
        complete: function (jqXHR, textStatus) {
            if (textStatus === 'success') {
            }
        }
    });
};

WebPush.prototype.send = function (msg) {
//    cslog('send: ' + msg);
    var webPush = this;
    if (this.webSocket) {
        this.webSocket.send(JSON.stringify(msg));
    } else {
        $.ajax({
            dataType: 'json',
            url: 'http://' + webPush.url + '/send/' + webPush.id,
            type: 'POST',
            cache: false, //fix loop IE
            data: JSON.stringify(msg),
            success: function (data, textStatus, jqXHR) {
//                cslog('success send: ' + data);
                //webPush.onMessageReceived(data);
                //webPush.poll(url);
            },
            error: function (jqXHR, textStatus, errorThrown) {
                cslog('error send: ' + textStatus + "--" + errorThrown);
                //webPush.onDisconnected();
            }
        });
    }
};

WebPush.prototype.sendWait = function (msg, callback) {
    var webPush = this;
    if (this.webSocket) {
        this.waitForConnection(function () {
            webPush.webSocket.send(JSON.stringify(msg));
            if (typeof callback !== 'undefined') {
                callback();
            }
        }, 1000);
    } else {
        $.ajax({
            dataType: 'json',
            url: 'http://' + webPush.url + '/send/' + webPush.id,
            type: 'POST',
            cache: false, //fix loop IE
            data: JSON.stringify(msg),
            success: function (data, textStatus, jqXHR) {
                cslog('success send: ' + data);
                //webPush.onMessageReceived(data);
                //webPush.poll(url);
            },
            error: function (jqXHR, textStatus, errorThrown) {
                cslog('error send: ' + textStatus + "--" + errorThrown);
                //webPush.onDisconnected();
            }
        });
    }
};

WebPush.prototype.waitForConnection = function (callback, interval) {
    if (this.webSocket.readyState === 1) {
        callback();
    } else {
        var that = this;
        // optional: implement backoff for interval here
        setTimeout(function () {
            that.waitForConnection(callback, interval);
        }, interval);
    }
};

WebPush.prototype.close = function () {
    var webPush = this;

    if (this.webSocket) {
        this.webSocket.close();
    } else {
        this.requestDisconnect = true;

        cslog('chuyen nhe------------------');
        $.ajax({
            dataType: 'json',
            url: 'http://' + webPush.url + '/disconnect/' + webPush.id,
            type: 'GET',
            cache: false, //fix loop IE
            data: {},
            success: function (data, textStatus, jqXHR) {
//				cslog('success disconnect: ' + data);
                //webPush.onMessageReceived(data);
                //webPush.poll(url);
            },
            error: function (jqXHR, textStatus, errorThrown) {
//				cslog('error disconnect: ' + textStatus);
                //webPush.onDisconnected();
            }
        });
    }
};
