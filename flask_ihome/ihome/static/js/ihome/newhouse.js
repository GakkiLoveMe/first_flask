function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

$(document).ready(function(){
    // $('.popup_con').fadeIn('fast');
    // $('.popup_con').fadeOut('fast');

    // 在页面加载完毕之后获取区域信息
    $.get("/api/v1.0/areas", function (resp) {
        if (resp.errno == "0") {
            // for (var i = 0; i< resp.data.length; i++) {
            //     var area = resp.data[i]
            //     $("#area-id").append('<option value="' + area.aid + '">'+ area.aname +'</option>')
            // }
            var html = template("areas-tmpl", {"areas": resp.data})
            $("#area-id").html(html)
        }
    })

    // 处理房屋基本信息提交的表单数据
    $("#form-house-info").submit(function (e) {
        e.preventDefault()

        var params = {}

        $(this).serializeArray().map(function (x) {
            params[x.name] = x.value
        })
        var facilitys = []
        $(":checkbox:checked[name=facility]").each(function (i, x) {
            facilitys.push(x.value)
        })
        params["facility"] = facilitys
        $.ajax({
            url: "/api/v1.0/houses",
            type: "post",
            contentType: "application/json",
            headers: {
                "X-CSRFToken": getCookie("csrf_token")
            },
            data: JSON.stringify(params),
            success: function (resp) {
                if (resp.errno == "0") {
                    $("#form-house-info").hide()
                    $("#form-house-image").show()
                    // 在上传房屋基本信息成功之后，去设置房屋的id，以便在上传房屋图片的时候使用
                    $("#house-id").val(resp.data.house_id)
                }else if (resp.errno == "4101") {
                    location.href = "/login.html"
                }else {
                    alert(resp.errmsg)
                }
            }
        })
    })

    // 处理图片表单的数据
    $("#form-house-image").submit(function (e) {
        e.preventDefault()

        var house_id = $("#house-id").val()

        $(this).ajaxSubmit({
            url: "/api/v1.0/houses/" + house_id + "/images",
            type: "post",
            headers:{
                "X-CSRFToken": getCookie("csrf_token")
            },
            success: function (resp) {
                if (resp.errno == "0") {
                    $(".house-image-cons").append('<img src="' + resp.data.url + '">')
                }
            }
        })
    })

})