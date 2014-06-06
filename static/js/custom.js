$(document).ajaxComplete(function(e, xhr, settings) {
    var contentType = xhr.getResponseHeader("Content-Type");
    if (contentType == "application/javascript" || contentType == "application/json") {
        var json = $.parseJSON(xhr.responseText);

        $.each(json.django_messages, function (i, item) {
            console.log('ADDMESSAGE1');
            addMessage(item.message, item.extra_tags);
        });
    }
}).ajaxError(function(e, xhr, settings, exception) {
    addMessage("There was an error processing your request, please try again.", "error");
});

function addMessage(text, extra_tags) {
    if (extra_tags.indexOf('warning') != -1) {
        var div_class="alert alert-danger"
    } else if (extra_tags.indexOf('success') != -1){
        var div_class="alert alert-success"
    }else{
        var div_class="alert alert-info"
    }

    var message = $('<div class="'+div_class+'">'+text+'<a class="close" data-dismiss="alert">×</a></div>').hide().fadeIn(500);
    $("#messages").append(message);
    $(".page-tip").slideDown();
    setTimeout(function() {
        $('.alert').fadeOut('slow');
    }, 5000);
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

    var interval = Math.floor(seconds / 31536000);

    if (interval > 1) {
        return interval + " years";
    }
    interval = Math.floor(seconds / 2592000);
    if (interval > 1) {
        return interval + " months";
    }
    interval = Math.floor(seconds / 86400);
    if (interval > 1) {
        return interval + " days";
    }
    interval = Math.floor(seconds / 3600);
    if (interval > 1) {
        return interval + " hours";
    }
    interval = Math.floor(seconds / 60);
    if (interval > 1) {
        return interval + " minutes";
    }
    return Math.floor(seconds) + " seconds";
}

$(document).ready(function(){
    // messages timeout for 10 sec 
    setTimeout(function() {
        $('.alert').fadeOut('slow');
    }, 5000); // <-- time in milliseconds, 1000 =  1 sec

});
