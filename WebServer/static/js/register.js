function validateEmail(email)
{
    var re = /^(([^<>()[\]\\.,;:\s@\"]+(\.[^<>()[\]\\.,;:\s@\"]+)*)|(\".+\"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
    return re.test(email);
}

$(document).ready(function() {
    $(':input[type="submit"]').prop('disabled', true);
    $('input[type="text"]').keyup(function() {
    if(validateEmail($(this).val())) {
        $(':input[type="submit"]').prop('disabled', false);
    }else{
        $(':input[type="submit"]').prop('disabled', true);
    }
    });
 });