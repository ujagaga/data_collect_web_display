var socket;

function getCookie(cname) {
  let name = cname + "=";
  let decodedCookie = decodeURIComponent(document.cookie);
  let ca = decodedCookie.split(';');
  for(let i = 0; i <ca.length; i++) {
    let c = ca[i];
    while (c.charAt(0) == ' ') {
      c = c.substring(1);
    }
    if (c.indexOf(name) == 0) {
      return c.substring(name.length, c.length);
    }
  }
  return "";
}

function toggleVar(name, caller){
    key = getCookie("token");
    var value = 0;
    if(caller.checked){
        value = 1;
    }
    console.log("toggleVar " + name + ":" + value);
    socket.emit('setvar', key, name, value);
}

function saveVar(name, value) {
    key = getCookie("token");
    socket.emit('setvar', key, name, value);
}

function process_apply_button(ele){
    var inputId = ele.id.replace("btn_", "var_");
    var name = ele.id.replace("btn_", "").replaceAll("%20%", " ");

    var value = document.getElementById(inputId).value;
    saveVar(name, value);
    ele.style.display = "none";
}

function process_keypress(ele) {
    var applyBtnId = ele.id.replace("var_", "btn_");
    if(event.key === 'Enter') {
        var name = ele.id.replace("var_", "").replaceAll("%20%", " ");
        saveVar(name, ele.value);
        document.getElementById(applyBtnId).style.display = "none";
    }else{
        // Show apply button
        console.log(applyBtnId);
        document.getElementById(applyBtnId).style.display = "block";
    }
}

$(document).ready(function(){
    socket = io.connect('/websocket');

    socket.on('var_set', function(msg) {
        try {
            var resp = JSON.parse(msg);

            if(resp.hasOwnProperty('name')){
                var varId = "var_" + resp.name.replaceAll(" ", "%20%");
                var checked = resp.value != 0;

                document.getElementById(varId).checked = checked;
                document.getElementById(varId).value = resp.value;
            }generate
        }
        catch (e) {
            console.log("Error parsing json: " + msg);
            console.log(e);
        }
    });

});