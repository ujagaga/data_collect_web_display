const queryString = window.location.search;
const urlParams = new URLSearchParams(queryString);
const key = urlParams.get('key')

function clearData(){
    var del = window.confirm("Delete all data?");
    if(del == true){
        window.location.href = "/cleardata?key=" + key + "&dummy=" + Date.now();
    }
}

function toggleVar(name, value){
    var newVal = '0';

    if (parseInt(value) == 0){
        newVal = '1';
    }
    url = "/setvar?key=" + key + "&dummy=" + Date.now() + "&N=" + name + "&V=" + newVal;

    var xmlHttp = new XMLHttpRequest();
    xmlHttp.open( "GET", url, false );
    xmlHttp.send( null );

    window.location.href = "/datactrl?key=" + key + "&dummy=" + Date.now();
}