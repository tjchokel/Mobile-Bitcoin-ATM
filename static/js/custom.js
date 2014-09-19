var ALERT_FADEOUT_TIME = 10000;
$(document).ajaxComplete(function(e, xhr, settings) {
    var contentType = xhr.getResponseHeader("Content-Type");
    if (contentType == "application/javascript" || contentType == "application/json") {
        var json = $.parseJSON(xhr.responseText);

        $.each(json.django_messages, function (i, item) {
            addMessage(item.message, item.extra_tags);
        });
    }
}).ajaxError(function(e, xhr, settings, exception) {
    if (settings.url.search('freegeoip.net') >= 0) {
        console.log(settings.url+' Error');
    }
    else if (settings.url.search('geobytes.com') >= 0) {
        console.log(settings.url+' Error');
    }
    else if (settings.url.search('/get-bitcoin-price') >= 0) {
        console.log(settings.url+' Error');
    }
    else {
      addMessage("There was an error processing your request, please try again.", "error");
    }
});

function addMessage(text, extra_tags) {
    if (extra_tags.indexOf('warning') != -1) {
        var div_class="alert alert-danger"
    } else if (extra_tags.indexOf('success') != -1){
        var div_class="alert alert-success"
    }else{
        var div_class="alert alert-info"
    }

    var message = $('<div class="'+div_class+'">'+text+'<button type="button" class="close" data-dismiss="alert">×</button></div>').hide().fadeIn(500);
    $("#messages").append(message);
    $(".page-tip").slideDown();
    setTimeout(function() {
        $('.alert').not('.nofadeout').fadeOut('slow');
    }, ALERT_FADEOUT_TIME);
}

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}
$.ajaxSetup({
    crossDomain: false, // obviates need for sameOrigin test
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type)) {
            var csrftoken = $.cookie('csrftoken');
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});

function timeSince(date) {

    var seconds = Math.floor((new Date() - date) / 1000);

    //Only want seconds for translation reasons, but keeping in case we change

    // var interval = Math.floor(seconds / 31536000);

    // if (interval > 1) {
    //     return interval + " years";
    // }
    // interval = Math.floor(seconds / 2592000);
    // if (interval > 1) {
    //     return interval + " months";
    // }
    // interval = Math.floor(seconds / 86400);
    // if (interval > 1) {
    //     return interval + " days";
    // }
    // interval = Math.floor(seconds / 3600);
    // if (interval > 1) {
    //     return interval + " hours";
    // }
    // interval = Math.floor(seconds / 60);
    // if (interval > 1) {
    //     return interval + " minutes";
    // }
    // return Math.floor(seconds) + " seconds";
    return Math.floor(seconds);
}

function timeUntil(date) {

    var seconds = Math.floor((date - new Date()) / 1000);
    if (seconds <= 0){
        return 0;
    }

    var interval = Math.floor(seconds / 31536000);

    interval = Math.floor(seconds / 60);
    var mins_and_seconds = "";
    if (interval > 1) {
         mins_and_seconds = interval + " minutes, ";
    }
    seconds = seconds - (interval * 60)
    mins_and_seconds = mins_and_seconds + Math.floor(seconds) + " seconds";
    return mins_and_seconds;
}

function hideLongString(string){
    front_chars_to_show = 15;
    string_len = string.length;
    if (string_len <= front_chars_to_show){
        return string;
    }
    var pre_string = "";
    var post_string = "";
    var i = 0;
    while (i < string_len){
        if (i < front_chars_to_show - 1){
            pre_string += string.charAt(i);
        }else{
            post_string += string.charAt(i);
        }
        i = i + 1;
    }
    html = '<a class="long-string-toggle" style="cursor:pointer;">';
    html += pre_string;
    html += '<span id="ellipsis">...</span><span id="post-string" style="display:none;">';
    html += post_string;
    html += '<span></a>';
    return html;
}

$(document).ready(function(){
    // messages timeout for 10 sec 
    setTimeout(function() {
        $('.alert').not('.nofadeout').fadeOut('slow');
    }, ALERT_FADEOUT_TIME); // <-- time in milliseconds, 1000 =  1 sec

    $(".long-string-toggle").click(function() {
        $("#ellipsis").toggle();
        $("#post-string").toggle();
    })
});
