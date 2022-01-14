var popupMsg = "";

function showPopup(){
    if(popupMsg.length > 1){
        alert(popupMsg);
    }
}

document.addEventListener('DOMContentLoaded', function() {
    var popup = document.getElementById("popup")
    if(popup){
        popupMsg = popup.value
        setTimeout(showPopup, 1000);
    }
}, false);