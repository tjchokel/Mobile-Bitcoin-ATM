// QRCODE reader Copyright 2011 Lazar Laszlo
// http://www.webqr.com

var gCtx = null;
var gCanvas = null;
var c=0;
var stype=0;
var gUM=false;
var webkit=false;
var moz=false;
var v=null;

var imghtml='<div id="qrfile">'+
    '<div id="imghelp"><div id="help-message" style="color:green; display:inline;">Click below to take a photo:</div>'+
    '<input type="file" onchange="handleFiles(this.files)"/>'+
    '</div>'+
'</div>';

var vidhtml = '<video id="v" style="width:420px;" autoplay></video>';
// var vidhtml = '<video id="v" autoplay></video>';

function dragenter(e) {
  e.stopPropagation();
  e.preventDefault();
}

function dragover(e) {
  e.stopPropagation();
  e.preventDefault();
}
function drop(e) {
  e.stopPropagation();
  e.preventDefault();

  var dt = e.dataTransfer;
  var files = dt.files;
  if(files.length>0)
  {
    handleFiles(files);
  }
  else
  if(dt.getData('URL'))
  {
    qrcode.decode(dt.getData('URL'));
  }
}

function handleFiles(f)
{   
    $('#help-message').after('<span id="image-spinner">&nbsp;&nbsp;<a class="active has-spinner"><span class="spinner"><i class="fa fa-spinner fa-spin"></i></span></a></span>');
    var o=[];
    
    for(var i =0;i<f.length;i++)
    {
        var reader = new FileReader();
        reader.onload = (function(theFile) {
        return function(e) {
            gCtx.clearRect(0, 0, gCanvas.width, gCanvas.height);

            qrcode.decode(e.target.result);
        };
        })(f[i]);
        reader.readAsDataURL(f[i]); 
    }
}

function isMobileDevice() {
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)
}

function initCanvas(w,h)
{
    gCanvas = document.getElementById("qr-canvas");
    gCanvas.style.width = w + "px";
    gCanvas.style.height = h + "px";
    gCanvas.width = w;
    gCanvas.height = h;
    gCtx = gCanvas.getContext("2d");
    gCtx.clearRect(0, 0, w, h);
}


function captureToCanvas() {
    if(stype!=1)
        return;
    if(gUM)
    {
        try{
            gCtx.drawImage(v,0,0);
            try{
                qrcode.decode();
            }
            catch(e){       
                console.log(e);
                setTimeout(captureToCanvas, 300);
            };
        }
        catch(e){       
                console.log(e);
                setTimeout(captureToCanvas, 300);
        };
    }
}

function htmlEntities(str) {
    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function read(a)
{
    if (a.indexOf('bitcoin:') > -1){
        a = a.replace('bitcoin:', '');
    }
    a = a.replace(/\?.*$/,"");
    updateBitcoinAddress(a);
}   

function isCanvasSupported(){
  var elem = document.createElement('canvas');
  return !!(elem.getContext && elem.getContext('2d'));
}
function success(stream) {

    if(webkit)
        v.src = window.webkitURL.createObjectURL(stream);
    else
    if(moz)
    {
        v.mozSrcObject = stream;
        v.play();
    }
    else
        v.src = window.URL.createObjectURL(stream);
    gUM=true;
    setTimeout(captureToCanvas, 300);
}
        
function error(error) {
    gUM=false;
    return;
}

function hasGetUserMedia() {
  return !!(navigator.getUserMedia || navigator.webkitGetUserMedia ||
            navigator.mozGetUserMedia || navigator.msGetUserMedia);
}

function load()
{   
    // if on mobile device
    if( isMobileDevice() ) {
        initCanvas(400, 300);
        qrcode.callback = read;
        document.getElementById("mainbody").style.display="inline";
        setimg();
    } else if(isCanvasSupported() && window.File && window.FileReader) {
        initCanvas(400, 300);
        qrcode.callback = read;
        document.getElementById("mainbody").style.display="inline";
        setwebcam();
        // setimg();
    } else{
        document.getElementById("mainbody").style.display="inline";
        document.getElementById("mainbody").innerHTML='<p id="mp1">QR code scanner for HTML5 capable browsers</p><br>'+
        '<br><p id="mp2">sorry your browser is not supported</p><br><br>'+
        '<p id="mp1">try <a href="http://www.mozilla.com/firefox"><img src="firefox.png"/></a> or <a href="http://chrome.google.com"><img src="chrome_logo.gif"/></a> or <a href="http://www.opera.com"><img src="Opera-logo.png"/></a></p>';
    }
}

function sourceSelected(audioSource, videoSource) {
  var constraints = {
    audio: false,
    video: {
      optional: [{sourceId: videoSource}]
    }
  };
  navigator.getUserMedia  = navigator.getUserMedia ||
                          navigator.webkitGetUserMedia ||
                          navigator.mozGetUserMedia ||
                          navigator.msGetUserMedia;
  navigator.getUserMedia(constraints, success, error);
}

function setwebcam()
{
    console.log('setwebcam');
    document.getElementById("result").innerHTML='<span style="color:green;">Please allow access to your device camera</span>';
    if(stype==1)
    {
        setTimeout(captureToCanvas, 500);    
        return;
    }
    var n=navigator;
    document.getElementById("outdiv").innerHTML = vidhtml;
    v=document.getElementById("v");

    // var videoSource = null;
    // for (var i = 0; i != sourceInfos.length; ++i) {
    //     var sourceInfo = sourceInfos[i];
    //     if (sourceInfo.kind === 'video') {
    //       console.log(sourceInfo.id, sourceInfo.label || 'camera');

    //       videoSource = sourceInfo.id;
    //     }
    // }

    // if(n.getUserMedia)
    //     n.getUserMedia({
    //         video: 
    //             {
    //                 optional: [{sourceId: videoSource}]
    //             }, 
    //         audio: false
    //     }, success, error);
    // else
    // if(n.webkitGetUserMedia)
    // {
    //     webkit=true;
    //     n.webkitGetUserMedia({video: 
    //             {
    //                 optional: [{sourceId: videoSource}]
    //             }, 
    //         audio: false
    //     }, success, error);
    // }
    // else
    // if(n.mozGetUserMedia)
    // {
    //     moz=true;
    //     n.mozGetUserMedia({video: 
    //             {
    //                 optional: [{sourceId: videoSource}]
    //             }, 
    //         audio: false
    //     }, success, error);
    // }

    MediaStreamTrack.getSources(function(sourceInfos) {
      var audioSource = false;
      var videoSource = null;

      for (var i = 0; i != sourceInfos.length -1; ++i) {
        var sourceInfo = sourceInfos[i];
        if (sourceInfo.kind === 'video') {
          console.log(sourceInfo.id, sourceInfo.label || 'camera');

          videoSource = sourceInfo.id;
        }
      }

      sourceSelected(audioSource, videoSource);
    });

    //document.getElementById("qrimg").src="qrimg2.png";
    //document.getElementById("webcamimg").src="webcam.png";
    // document.getElementById("qrimg").style.opacity=0.2;
    // document.getElementById("webcamimg").style.opacity=1.0;

    stype=1;
    setTimeout(captureToCanvas, 300);
}
function setimg()
{
    document.getElementById("result").innerHTML="";
    if(stype==2)
        return;
    document.getElementById("outdiv").innerHTML = imghtml;
    //document.getElementById("qrimg").src="qrimg.png";
    //document.getElementById("webcamimg").src="webcam2.png";
    // document.getElementById("qrimg").style.opacity=1.0;
    // document.getElementById("webcamimg").style.opacity=0.2;
    var qrfile = document.getElementById("qrfile");
    qrfile.addEventListener("dragenter", dragenter, false);  
    qrfile.addEventListener("dragover", dragover, false);  
    qrfile.addEventListener("drop", drop, false);
    stype=2;
}
