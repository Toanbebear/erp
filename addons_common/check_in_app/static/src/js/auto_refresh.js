//$(document).ready(function() {
//    function oe_pager_refresh() {
//        $('.oe_pager_refresh').trigger('click');
//    }
//    console.log(model)
//    // Đặt lịch chuyển đổi trạng thái hiển thị view sau mỗi 5 giây
//    setInterval(oe_pager_refresh, 5000); // 5000 milliseconds = 5 giây
//});

$(document).ready(function() {
    var modelValue = 'crm.check.in'
    function oe_pager_refresh() {
        $('.oe_pager_refresh').trigger('click');
        // Hàm để lấy giá trị của tham số "model" từ URL

            var currentURL = window.location.href;
            var modelIndex = currentURL.indexOf("model=");

            if (modelIndex > -1) {
                // Nếu tìm thấy chuỗi "model=" trong URL
                var endIndex = currentURL.indexOf("&", modelIndex);
                if (endIndex === -1) {
                    endIndex = currentURL.length;
                }
                modelValue = currentURL.substring(modelIndex + 6, endIndex); // 6 là độ dài của chuỗi "model="

            }
    }

    if (modelValue == 'crm.check.in') {
        console.log("Giá trị của tham số 'model' trong URL:", modelValue);
        setInterval(oe_pager_refresh, 5000);
    }



    // Đặt lịch chuyển đổi trạng thái hiển thị view sau mỗi 5 giây
//    setInterval(oe_pager_refresh, 5000); // 5000 milliseconds = 5 giây
});



//$(document).ready(function() {
//    function oe_pager_refresh() {
//        $('.oe_pager_refresh').trigger('click');
//    }
//
//    // Hàm kiểm tra và đặt lịch chuyển đổi trạng thái hiển thị view sau mỗi 5 giây
//    function checkAndView() {
//        // Kiểm tra xem người dùng có đang ở view "crm_check_in_list_tree_view" không
//        if (window.location.href.indexOf("/web#view=crm_check_in.crm_check_in_list_tree_view") > -1) {
//            // Nếu đúng view, đặt lịch chuyển đổi
//            setInterval(oe_pager_refresh, 5000);
//        }
//    }
//
//    // Kiểm tra và đặt lịch chuyển đổi khi trang web được nạp và khi URL thay đổi
//    checkAndView();
//    $(window).on('hashchange', checkAndView);
//});




//$(document).ready(function() {
//    // Hàm để chuyển đổi trạng thái hiển thị view sau mỗi 5 giây
//    function toggleView() {
//        odoo.define('auto.refresh.checkin', function (require) {
//            "use strict";
//            var rpc = require('web.rpc');
//
//            // Gọi phương thức toggle_tree_view_state thông qua hàm RPC
//            rpc.query({
//                model: 'crm.check.in', // Thay thế bằng tên model của bạn
//                method: 'toggle_tree_view_state',
//            }).then(function(result) {
//                console.log("View state toggled");
//            });
//        });
//    }
//
//    // Đặt lịch chuyển đổi trạng thái hiển thị view sau mỗi 5 giây
//    setInterval(oe_pager_refresh, 5000); // 5000 milliseconds = 5 giây
//});




