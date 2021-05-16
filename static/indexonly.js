var i = -1;
var speed = 50;

function typeWriter(txt) {
  if (i < txt.length) {
    document.getElementById("title").innerHTML += txt.charAt(i);
    i++;
    setTimeout(typeWriter, speed, txt=txt);
  }
}

function clear() {
    document.getElementById("title").innerHTML = "";
}

clear()
typeWriter("Track your rick rolls_")
