
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


function loadNotebook(notebookID)
{
    console.log(`pressed ${notebookID}`);
    if (currentNotebook != "")
    {
        $(`#Notebook${currentNotebook}`).css({"background-color": "var(--default-notebookList-background)"});
        $(`#Notebook${currentNotebook} .notebook-title`).css({"background-color": "var(--default-title)"});
    }
    var jsonString = GET(`Notebook/${notebookID}`, "text/json");
    var notebookData = JSON.parse(jsonString);
    var data = notebookData['data'];
    var svgData = data['NotebookData'];
    draw.clear();
    draw.svg(svgData);
    $(`#Notebook${notebookID}`).css({"background-color": "#fd4448"});
    $(`#Notebook${notebookID} .notebook-title`).css({"background-color": "#f21c21"})
    currentNotebook = notebookID;
}


function BuildNotebookList(userID)
{
    respJson = JSON.parse(GET(`NotebookList/#id=${userID['username']}`, "text/json"));
    errCode = respJson['code'];
    nbList = respJson['data'];
    console.log(nbList);

    nbListDiv = $("#notebookList")
    currentNotebook = ""
    for (var nbAttr of nbList)
    {
        nbblock = $(`<div class="notebook-block" id=Notebook${nbAttr['id']}>
        <div class="notebook-title">${nbAttr['title']}</div>
        <div class="notebook-description">${nbAttr['description']}</div>
    </div>`);
    
        nbListDiv.append(nbblock);

        nbblock.click((e) => {
            notebookID = e.currentTarget.id.slice(8);
            loadNotebook(notebookID);
        })
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

    $(document).bind('keydown', function(e) {
        if (e.which === 83 && e.ctrlKey) {
            e.preventDefault();
            alert("save");
        }
    })
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