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

function http_get_request(url){

    console.log("REQUESTING: " + url);
    var retVal = "ERR";
    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
        console.log(this.readyState + " | " + this.status + " | " + xhttp.responseText);
    };
    xhttp.open("GET", url, true);
    xhttp.send();
}

function saveVar(name, value) {
    key = getCookie("token");
    var url = "/setvar?key=" + key + "&N=" + name + "&V=" + value;
    url = url.replaceAll(' ', '%20');

    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {

        if (xhttp.readyState == 4 && xhttp.status == 200){
            location.reload();
        }
    };
    xhttp.open("GET", url, true);
    xhttp.send();
}

function saveVarSchedule(value) {
    key = getCookie("token");
    var url = "/setvarschedule?key=" + key + "&V=" + value;
    url = url.replaceAll(' ', '%20');

    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {

        if (xhttp.readyState == 4 && xhttp.status == 200){
            location.reload();
        }
    };
    xhttp.open("GET", url, true);
    xhttp.send();
}

function toggleVar(name, caller){
    var value = 0;
    if(caller.checked){
        value = 1;
    }
    saveVar(name, value);
}

function applyVarSchedule(name){
    var checked = document.getElementById("tgl_" + name.replace(" ", "%20%")).checked;
    active = 0;
    if(checked){
        active = 1;
    }
    var onTime = document.getElementById("sch_on_" + name).value;
    var duration = document.getElementById("sch_off_" + name).value;
    var repeat = 0;
    if(document.getElementById("sch_rep_" + name).checked){
        repeat = 1;
    }
    var currentTime = new Date();
    var currentTimestamp = currentTime.getHours() + ":" + currentTime.getMinutes();
    var data = {"n": name, "h": onTime, "d": duration, "r": repeat, "t": currentTimestamp, "a": active}
    var value = JSON.stringify(data);
    saveVarSchedule(value);
}

function process_apply_button(ele){
    var inputId = ele.id.replace("btn_", "var_");
    var name = ele.id.replace("btn_", "").replaceAll("%20%", " ");

    var value = document.getElementById(inputId).value;
    saveVar(name, value);
}

function process_schedule(variable_name){
     var applyBtnId = "btn_apply_" + variable_name;
    document.getElementById(applyBtnId).style.display = "block";
}

function process_keypress(ele) {
    var applyBtnId = ele.id.replace("var_", "btn_");
    if(event.key === 'Enter') {
        var name = ele.id.replace("var_", "").replaceAll("%20%", " ");
        saveVar(name, ele.value);
    }else{
        // Show apply button
        console.log(applyBtnId);
        document.getElementById(applyBtnId).style.display = "block";
    }
}

$(document).ready(function() {
    var status_text = $("#status").val();
    var status = "Connection Status: " + status_text;
    $("#status-info").text(status);
    if(status_text == "Connected"){
        $("#status-info").addClass("st-Connected");
        $("#status-info").removeClass("st-Disconnected");
    }else{
        $("#status-info").removeClass("st-Connected");
        $("#status-info").addClass("st-Disconnected");
    }

    var lastTs = parseInt($("#last_ts").val(), 10) * 1000;
    if(lastTs > 0){
        var utcTs = new Date().getTime();
        var elapsed = Math.floor((utcTs - lastTs) / 1000);
        var h = Math.floor(elapsed / 3600);
        var rem = elapsed % 3600;
        var m = Math.floor(rem / 60);
        var s = rem % 60;

        var lastDate = new Date(lastTs);
        var dateFormat = {year: 'numeric', month: 'long', day: 'numeric' };

        var status = " Last update at: " +  lastDate.toLocaleDateString("en-US", dateFormat) + ", " +
        lastDate.toLocaleTimeString("en-US") + " Elapsed:" + h + ":" + m + ":" + s;

        $("#status-ts").text(status);
    }else{
        var status = " Last update time unknown."
        $("#status-ts").text(status);
    }

});
