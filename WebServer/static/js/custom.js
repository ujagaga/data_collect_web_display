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

function clearData(){
    var del = window.confirm("Delete all data?");
    if(del == true){
        window.location.href = "/cleardata?dummy=" + Date.now();
    }
}

function toggleVar(name, value){
    key = getCookie("token");
    var newVal = '0';

    if (parseInt(value) == 0){
        newVal = '1';
    }
    url = "/setvar?key=" + key + "&dummy=" + Date.now() + "&N=" + name + "&V=" + newVal;

    var xmlHttp = new XMLHttpRequest();
    xmlHttp.open( "GET", url );
    xmlHttp.send( "null" );

    window.location.href = "/datactrl?dummy=" + Date.now();
}


function save_value(ele) {
    if(event.key === 'Enter') {
        key = getCookie("token");
        url = "/setvar?key=" + key + "&dummy=" + Date.now() + "&N=" + ele.name.replace("var_", "") + "&V=" + ele.value;
        console.log(url);
        var xmlHttp = new XMLHttpRequest();
        xmlHttp.open( "GET", url );
        xmlHttp.send( "null"  );

        window.location.href = "/datactrl?dummy=" + Date.now();
    }
}