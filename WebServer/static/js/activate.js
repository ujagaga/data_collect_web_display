function validatePassword()
{
    var pass1 = $("#password1").val();
    var pass2 = $("#password2").val();
    var status = $("#status_msg");

    if((pass1.length > 0) && (pass2.length > 0)){
        if(pass1 != pass2){
            status.text("ERROR: Passwords do not match!");
        }else if(pass1.length < 6){
            status.text("ERROR: Password must be at least 6 characters long.");
        }else{
            status.text("");
            return true;
        }
    }else{
        status.text("");
    }
    return false;
}

$(document).ready(function() {
    $(':input[type="submit"]').prop('disabled', true);
    $('input[type="password"]').keyup(function() {
        if(validatePassword()) {
            $(':input[type="submit"]').prop('disabled', false);
        }else{
            $(':input[type="submit"]').prop('disabled', true);
        }
    });
 });