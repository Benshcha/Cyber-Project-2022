


function init()
{
    canvas = $("#drawing")
    draw = SVG().addTo('#drawing').size(300, 300)
    doDraw = false
    svg = new mySVG(draw);

    let clearButton = document.createElement("button");
    clearButton.innerHTML = "Clear";
    clearButton.onclick = function () {
        svg.ClearCanvas()
    };
    clearButton.name = "Clear"
    $('#drawing-container').append(clearButton);

    lastPos = {x: undefined, y: undefined, width: undefined};
    pos = {x: undefined, y: undefined, width: undefined};
    width = undefined;

    currentPath = undefined;

    svg.addPath(currentPath)
}

init()


function getPos(e)
{
    pos = {x: undefined, y: undefined, width: undefined}
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
            borderWidths = {x: parseInt(svg.drawer.css("border-left-width")), y: parseInt(svg.drawer.css("border-top-width"))}
            pos.x=touch.pageX-touch.target.offsetLeft-borderWidths.x;
            pos.y=touch.pageY-touch.target.offsetTop-borderWidths.y;
            console.log(borderWidths)
        }
    }
    pos.width = width;
    return pos
}

// drawing on canvas ctx given touch/click event e
function FDraw(svg, cPath, e)
{
    pos = getPos(pos, e)
    newPoint = `L${pos.x} ${pos.y} `
    newPath = svg.draw.
    cPath.addPath()
    console.log(newPoint)
}

canvas.on('mousemove', e => {
    if (doDraw) 
    {
        FDraw(svg, currentPath, e)
    }
})


canvas.on('touchmove', e => {
    if (doDraw) 
    {
        // Prevents an additional mousedown event being triggered
        e.preventDefault();
        FDraw(svg, currentPath, e)
    }
})

// Regular
canvas.pressure({
    start: function(event){
        doDraw = true;
        pos = getPos(event)
        currentPath = svg.draw.path(pos)
    },
    end: function(event){
        doDraw = false;
        
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