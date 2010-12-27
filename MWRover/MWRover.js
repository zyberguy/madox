/*
MWRover - Mecanum Wheel Rover Base
http://www.madox.net/

MWRover Axes

         F
       _____
   [\]|2   0|[/]
L     |     |      R
   [/]|3___1|[\]
       
         B

Browser Axes
 o-x
 |
 y

DeviceMotion Axes
 y
 | 
 o-x
 
*/

//Mapping Table for Wheel Motion Directions 
var F   = [1,1,-1,-1];
//var B   = [-1,-1,1,1];
var R   = [1,-1,1,-1];
//var L   = [-1,1,-1,1];
var CW  = [-1,-1,-1,-1];
//var CCW = [1,1,1,1];
var servoPositions = [0,0,0,0];
var servoPositionCentre = [1500,1500,1500,1500]

var docMinSize = 100;
var mouseOriginX = 0;
var mouseOriginY = 0;
var servoCentre = 1500;
var servoRange = 500;
var servoRangeMin = servoCentre-servoRange;
var servoRangeMax = servoCentre+servoRange;
var servoX = 0;
var servoY = 0;
var servoThreshold = 25;
var lastCommandTime = 0;
var eventsFired = 0;

var targetBall = null;
var targetBallSize = 20;
var originBall = null;
var originBallSize = 20;

function mouseDown(evt){
  //Start
  var cursorPos = getCoords(evt);
  mouseOriginX = cursorPos[0];
  mouseOriginY = cursorPos[1];
  document.onmousemove = document.ontouchmove = mouseMove;
  originBall.style.left = (cursorPos[0]-originBallSize/2) + "px";
  originBall.style.top = (cursorPos[1]-originBallSize/2) + "px";
  return false;
}

function mouseUp(evt){
  //Stop
  mouseCapture = false;
  //Don't care, just stop the servos now
  document.getElementById("debug").innerHTML = "STOPPED";
  sendCommand(servoPositionCentre);
  document.onmousemove = document.ontouchmove = null;
  return false;
}

function getCoords(evt){
  var coords = [];
  if(evt.touches && evt.touches.length){
    coords[0]=evt.touches[0].clientX;
    coords[1]=evt.touches[0].clientY;
  } else {
    coords[0]=evt.clientX;
    coords[1]=evt.clientY;
  }
  return coords;
}
function mouseMove(evt){
  //Calculate difference to start position
  var cursorPos = getCoords(evt);
  
  servoX = servoRange * (cursorPos[0] - mouseOriginX)/docMinSize;
  servoY = servoRange * (cursorPos[1] - mouseOriginY)/docMinSize;
  
  date = new Date();
  currentTime = date.getTime();
  //Limit command rate to 4Hz to avoid spamming the controller
  if(currentTime-lastCommandTime > 250){
    for(x in servoPositions){
      servoPositions[x] = -F[x] * servoY + -R[x] * servoX + servoCentre;
      servoPositions[x] = ((servoPositions[x] < servoRangeMin) ? servoRangeMin : ((servoPositions[x] > servoRangeMax) ? servoRangeMax : servoPositions[x]));
    }
    lastCommandTime = currentTime;
    eventsFired += 1;
    document.getElementById("debug").innerHTML = servoPositions + "\n" + eventsFired;
    sendCommand(servoPositions);
    targetBall.style.left = (cursorPos[0]-targetBallSize/2) + "px";
    targetBall.style.top = (cursorPos[1]-targetBallSize/2) + "px";    
  }

  return false;
}


var commandSend = getXMLHttpObject(); 
if(commandSend==null){
    alert("Meh won't work here");
}

function sendCommand(commandPositions){
  var PostString = "";
  //Get all input fields
  for(x in commandPositions){
    if(PostString != ""){
      PostString += "&";
    }
    PostString = PostString += x + "=" + commandPositions[x];
  }
  //Send the request
  //commandSend.open('POST', "./command/", true);
  commandSend.open('POST', "./command/", false);
  commandSend.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
  //DataSend.setRequestHeader("Content-length", PostString.length);
  commandSend.send(PostString);  
}

function getXMLHttpObject(){
  var xmlHttp=null;
  try {
    //New Browsers, Firefox, Safari, IE7+, Chrome
    xmlHttp=new XMLHttpRequest();
  } catch (e) {
    // Old IE, Should I give up on this @#%!?
    try{
      xmlHttp=new ActiveXObject("Msxml2.XMLHTTP");
    } catch (e) {
      xmlHttp=new ActiveXObject("Microsoft.XMLHTTP");
    }
  }
  return xmlHttp;
}

function init(){
  //Using Legacy Events for widest support of browsers and platforms
  document.onmousedown = document.ontouchstart = mouseDown;
  document.onmouseup = document.ontouchend = mouseUp;
  targetBall = document.getElementById("targetball");
  originBall = document.getElementById("originball");
  docMinSize = (document.documentElement.clientWidth < document.documentElement.clientHeight?document.documentElement.clientWidth:document.documentElement.clientHeight);
  targetBallSize = 2 * Math.round(docMinSize / 20);
  originBallSize = 2 * Math.round(docMinSize / 20);
  targetBall.style.height = targetBallSize + "px";
  targetBall.style.width = targetBallSize + "px";
  originBall.style.height = originBallSize + "px";
  originBall.style.width = originBallSize + "px";
}
