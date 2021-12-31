
class Notebook
{
    constructor(drawer)
    {
        this.draw = drawer
        this.cPath = undefined
        this.cGroup = undefined
        this.groups = []
    }

    // drawing on canvas ctx given touch/click event e
    DrawPos(e)
    {
        lastPos = pos
        pos = getPos(e)
        var lastPoint = `${lastPos.x},${lastPos.y}`
        var newPoint = `${pos.x},${pos.y} `
        nb.cPath = nb.cGroup.path(`M${lastPoint} L${newPoint}`)
        nb.cPath.attr('stroke-width', width)
        console.log(newPoint)
    }
}

function init()
{
    canvas = $("#drawing")
    draw = SVG().addTo('#drawing').size("100%", 700)
    doDraw = false
    nb = new Notebook(draw);

    let clearButton = document.createElement("button");
    clearButton.innerHTML = "Clear";
    clearButton.onclick = function () {
        nb.ClearCanvas()
    };
    clearButton.name = "Clear"
    $('#drawing-container').append(clearButton);

    lastPos = {x: undefined, y: undefined, width: undefined};
    pos = {x: undefined, y: undefined, width: undefined};
    width = undefined;
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
            borderWidths = {x: parseInt(nb.drawer.css("border-left-width")), y: parseInt(nb.drawer.css("border-top-width"))}
            pos.x=touch.pageX-touch.target.offsetLeft-borderWidths.x;
            pos.y=touch.pageY-touch.target.offsetTop-borderWidths.y;
            console.log(borderWidths)
        }
    }
    pos.width = width;
    return pos
}



canvas.on('mousemove', e => {
    if (doDraw) 
    {
        nb.DrawPos(e)
    }
})


canvas.on('touchmove', e => {
    if (doDraw) 
    {
        // Prevents an additional mousedown event being triggered
        e.preventDefault();
        nb.DrawPos(e)
    }
})

// Regular
canvas.pressure({
    start: function(event){
        doDraw = true;
        pos = getPos(event)

        console.log(nb.draw)
        g = nb.draw.group()
        nb.cGroup = g
        nb.cPath = nb.cGroup.path(`M${pos.x} ${pos.y} `)
    },
    end: function(event){
        doDraw = false;
        
        lastPos = {x: undefined, y: undefined, width: undefined};
        pos = {x: undefined, y: undefined, width: undefined};


        nb.groups.push(nb.cGroup)
    },
    change: function(force, event){
        // width = Pressure.map(force, 0, 1, 3, 10);
        width = force*10
    },
    unsupported: function(){
        this.innerHTML = 'Sorry! Check the devices and browsers'
    }
});