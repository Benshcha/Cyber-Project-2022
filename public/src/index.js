
class Notebook
{
    constructor(drawer, div)
    {
        this.draw = drawer
        this.div = div
        this.cPath = undefined
        this.cGroup = undefined
        this.groups = []
    }

    // drawing on canvas ctx given touch/click event e
    DrawPos(e)
    {
        lastPos = pos
        pos = getPos(e, this.div)
        var lastPoint = `${lastPos.x},${lastPos.y}`
        var newPoint = `${pos.x},${pos.y} `
        nb.cPath = nb.cGroup.path(`M${lastPoint} L${newPoint}`)
        nb.cPath.attr('stroke-width', width)
    }
}

function init()
{
    canvas = $("#drawing")
    draw = SVG('#drawingSvg').addTo('#drawing').size("100%", 700)
    svg = $("#drawingSvg")
    doDraw = false
    nb = new Notebook(draw, canvas);

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

function getPos(e, div)
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
            borderWidths = {x: parseInt(nb.div.css("border-left-width")), y: parseInt(nb.div.css("border-top-width"))}
            var br = div[0].getBoundingClientRect();
            pos.x=touch.clientX - br.left - borderWidths.x;
            pos.y=touch.clientY - br.top - borderWidths.y;
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
        if (e.touches.length == 1){
            e.preventDefault();
            nb.DrawPos(e)
        }
    }
})

// Regular
canvas.pressure({
    start: function(event){
        doDraw = true;
        pos = getPos(event, nb.div)
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