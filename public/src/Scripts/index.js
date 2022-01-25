
class Notebook
{
    constructor(drawer, div)
    {
        this.draw = drawer
        this.div = div
        this.cPath = null
        this.cGroup = null
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

function getCookie(name) {
    var nameEQ = name + "=";
    var ca = document.cookie.split(';');
    for(var i=0;i < ca.length;i++) {
        var c = ca[i];
        while (c.charAt(0)==' ') c = c.substring(1,c.length);
        if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
    }
    return null;
}



function BuildNotebookList(userID)
{
    /*
    <div class="notebook-block" onclick='console.log("Pressed Notebook 1")'>
        <div class="notebook-title">Notebook 1:</div>
        <div class="notebook-discription">This is a cool notebook</div>
    </div>
    */
    respJson = JSON.parse(GET(`NotebookList/${userID['username']}`, "text/json"));
    errCode = respJson['code'];
    nbList = respJson['data'];
    console.log(nbList);

    nbListDiv = $("#notebookList")
    for (var nbAttr of nbList)
    {
        nbblock = $(`<div class="notebook-block" id=${nbAttr['id']}>
        <div class="notebook-title">${nbAttr['title']}</div>
        <div class="notebook-description">${nbAttr['description']}</div>
    </div>`)

        nbblock.click(() => console.log(`Pressed Notebook ${nbAttr['title']}`))
        nbListDiv.append(nbblock)
    }
}

function init()
{
    userIDstring = getCookie('user_auth');

    if (userIDstring != null)
    {
        userID = JSON.parse(userIDstring)
        isLoggedIn = Login(userID['username'], userID['password'])
        if (isLoggedIn)
        {
            $("#loginButton").hide()
            $("#logoutButton").show()
            $("#welcome").text(`Hi ${userID['username']}!`);
            BuildNotebookList(userID);
        }
    }
    canvas = $("#drawing");
    draw = SVG('#drawingSvg').addTo('#drawing').size("100%", 700);
    svg = $("#drawingSvg");
    doDraw = false;
    nb = new Notebook(draw, canvas);

    lastPos = {x: null, y: null, width: null};
    pos = {x: null, y: null, width: null};
    width = null;
}

function getPos(e, div)
{
    pos = {x: null, y: null, width: null}
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
            borderWidths = {x: parseInt(div.css("border-left-width")), y: parseInt(div.css("border-top-width"))}
            var br = div[0].getBoundingClientRect();
            pos.x=touch.clientX - br.left - borderWidths.x;
            pos.y=touch.clientY - br.top - borderWidths.y;
        }
    }
    pos.width = width;
    return pos
}

$(document).ready(function() {
    

    init()

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
            
            lastPos = {x: null, y: null, width: null};
            pos = {x: null, y: null, width: null};


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
})