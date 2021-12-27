var canvas = $("#myCanvas");
var ctx = canvas[0].getContext("2d");
var lastPos = {x: undefined, y: undefined, width: undefined};
var pos = {x: undefined, y: undefined, width: undefined};
var width;
var draw = false;


// varLineRounded : draws a line from A(x1,y1) to B(x2,y2)
// that starts with a w1 width and ends with a w2 width.
// relies on fillStyle for its color.
// ctx is a valid canvas's context2d.
function varLineRounded(ctx, x1, y1, x2, y2, w1, w2) {
    var dx = (x2 - x1),  shiftx = 0;
    var dy = (y2 - y1),  shifty = 0;
    w1 /= 2;   w2 /= 2; // we only use w1/2 and w2/2 for computations.    
    // length of the AB vector
    var length = Math.sqrt(dx**2 + dy**2);
    console.log("dx, dy = " + [dx, dy])
    if (!length) return 0; // exit if zero length
    dx /= length ;    dy /= length ;
    shiftx = - dy * w1 ;  // compute AA1 vector's x
    shifty =   dx * w1 ;  // compute AA1 vector's y
    var angle = Math.atan2(shifty, shiftx);
    ctx.moveTo(x1 + shiftx, y1 + shifty);
    ctx.arc(x1,y1, w1, angle, angle+Math.PI); // draw A1A2
    shiftx =  - dy * w2 ;  // compute BB1 vector's x
    shifty =    dx * w2 ;  // compute BB1 vector's y
    ctx.quadraticCurveTo((x1 + x2)/2, (y1 + y2)/2, x2 - shiftx, y2 - shifty); // draw A2B1
    ctx.arc(x2,y2, w2, angle+Math.PI, angle); // draw A1A2  
    return 1;
}

ctx.strokeStyle = "black";
// ctx.lineWidth = 10;


function ClearCanvas(ctx)
{
    ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
    console.log('Cleared Canvas')
}


function Fdraw(ctx, e)
{
    lastPos.x = pos.x;
    lastPos.y = pos.y;
    lastPos.width = pos.width;
    if (!e.touches)
    {
        pos.x = e.offsetX;
        pos.y = e.offsetY;
    }
    else 
    {
        if (e.touches.length == 1) { // Only deal with one finger
            var touch = e.touches[0]; // Get the information for finger #1
            touch.target.offsetLeft;
            borderWidths = {x: parseInt(canvas.css("border-left-width")), y: parseInt(canvas.css("border-top-width"))}
            pos.x=touch.pageX-touch.target.offsetLeft-borderWidths.x;
            pos.y=touch.pageY-touch.target.offsetTop-borderWidths.y;
            console.log(borderWidths)
        }
    }
    pos.width = width;
    varLineRounded(ctx, lastPos.x, lastPos.y, pos.x, pos.y, lastPos.width, pos.width);
    ctx.stroke(); 
    ctx.fill()
}

canvas.on('mousemove', e => {
    if (draw) 
    {
        Fdraw(ctx, e)
    }
})


canvas.on('touchmove', e => {
    if (draw) 
    {
        // Prevents an additional mousedown event being triggered
        e.preventDefault();
        Fdraw(ctx, e)
    }
})

// Regular
canvas.pressure({
    start: function(event){
        draw = true;
        ctx.beginPath();
    },
    end: function(event){
        draw = false;
        ctx.closePath();
        lastPos = {x: undefined, y: undefined, width: undefined};
        pos = {x: undefined, y: undefined, width: undefined};
    },
    change: function(force, event){
        // width = Pressure.map(force, 0, 1, 3, 10);
        width = force*10
    },
    unsupported: function(){
        this.innerHTML = 'Sorry! Check the devices and browsers'
    }
});