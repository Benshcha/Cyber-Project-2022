class Notebook {
	constructor(drawer, div) {
		this.changes = "";
		this.draw = drawer;
		this.div = div;
		this.cPath = null;
		this.cGroup = null;
		this.cPoints = [];
		this.groups = [];
	}

	// drawing on canvas ctx given touch/click event e
	DrawPos(e, sim = true) {
		pos = getPos(e, this.div);

		this.cPoints.push([pos.x, pos.y, pos.width]);

		var outlinePoints = getStroke(this.cPoints, {
			simulatePressure: sim,
		});

		// Still need to define new Change

		// if nb has cPath clear it
		if (this.cPath != null) {
			this.cGroup.clear();
		}

		nb.cPath = nb.cGroup.path(getSvgPathFromStroke(outlinePoints));
		// nb.cPath.attr("stroke-width", width);
	}
}

// function ShowShare() {
// 	var container = $("#share-button-container");
// 	$(document).click(function (e) {
// 		if (container[0] !== e.target && !container[0].contains(e.target)) {
// 			$("#share-button-content").hide();
// 		}
// 	});
// }

function getCookie(name) {
	var nameEQ = name + "=";
	var ca = document.cookie.split(";");
	for (var i = 0; i < ca.length; i++) {
		var c = ca[i];
		while (c.charAt(0) == " ") c = c.substring(1, c.length);
		if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length, c.length);
	}
	return null;
}

function loadNotebook(notebookID) {
	$(".online").show();
	console.log(`pressed ${notebookID}`);
	if (currentNotebook != "") {
		$(`#Notebook${currentNotebook}`).css({
			"background-color": "var(--default-notebookList-background)",
		});
		$(`#Notebook${currentNotebook} .notebook-title`).css({
			"background-color": "var(--default-title)",
		});
	}
	var jsonString = GET(`Notebook/${notebookID}`, "text/json");
	var notebookData = JSON.parse(jsonString);
	var data = notebookData["data"];
	var svgData = data["NotebookData"];
	draw.clear();
	draw.svg(svgData);
	$(`#Notebook${notebookID}`).css({ "background-color": "#fd4448" });
	$(`#Notebook${notebookID} .notebook-title`).css({
		"background-color": "#f21c21",
	});
	currentNotebook = notebookID;
}

function BuildNotebookList() {
	var respJson = JSON.parse(GET(`NotebookList`, "text/json"));
	var errCode = respJson["code"];
	var nbList = respJson["data"];
	console.log(nbList);

	const nbListDiv = $("#notebookList");

	if (errCode == 1) {
		return 1;
	}
	nbListDiv.html("");
	currentNotebook = "";
	for (var nbAttr of nbList) {
		var nbblock = $(`<div class="notebook-block" id=Notebook${nbAttr["id"]}>
        <div class="notebook-title">${nbAttr["title"]}</div>
        <div class="notebook-description">${nbAttr["description"]}</div>
    </div>`);

		nbListDiv.append(nbblock);

		nbblock.click((e) => {
			var notebookID = e.currentTarget.id.slice(8);
			loadNotebook(notebookID);
		});
	}
}

function RequestDataNewNotebook() {
	const nbListDiv = $("#notebookList");
	$("#addnb-container").hide();
	var newNBBlock = $(`<div class="notebook-block" id="new-notebook-block">
        <div class="notebook-title"><textarea class="new-title" id="new-notebook-title"> </textarea></div>
        <div class="notebook-description"><textarea class="new-description" id="new-notebook-description"> </textarea></div>
        <button id="complete-add">Add</button>
    </div>`);

	nbListDiv.append(newNBBlock);

	$("#complete-add").click(function (e) {
		e.preventDefault();
		var newTitle = $("#new-notebook-title").val();
		var newDescription = $("#new-notebook-description").val();
		createNotebook(newTitle, newDescription);
		$("#addnb-container").show();
	});
}

function createNotebook(newTitle, newDescription) {
	var textResp = POST(
		`SAVENEWNB`,
		"text/json",
		JSON.stringify({
			svgData: svg.html(),
			title: newTitle,
			description: newDescription,
		}),
		(resp) => {
			console.log(resp);
			BuildNotebookList();
			currentNotebook = JSON.parse(resp.responseText)["data"]["id"];
			$(".online").show();
		}
	);
}

function SaveCurrentNotebook() {
	// var count = 0;

	var resp = POST(`/SAVE/${currentNotebook}`, "svg", nb.changes, (resp) => {
		nb.changes = "";
		console.log(resp);
	});
}

var userIDstring;
var isLoggedIn;
var canvas;
var draw;
var nb;
var pos;
var svg;
var userID;
var width;
var borderWidths;
var doDraw = false;
var currentNotebook = "";

function init() {
	userIDstring = getCookie("user_auth");

	if (userIDstring != null) {
		userID = JSON.parse(userIDstring);
		isLoggedIn = Login(userID["username"], userID["password"]);
		if (isLoggedIn) {
			$("#loginButton").hide();
			$("#logoutButton").show();
			$("#welcome").text(`Hi ${userID["username"]}!`);
			BuildNotebookList();
			$("#addNB").show();
		}
	}
	canvas = $("#drawing");
	draw = SVG("#drawingSvg").addTo("#drawing").size("100%", 700);
	svg = $("#drawingSvg");
	doDraw = false;
	nb = new Notebook(draw, canvas);

	pos = { x: null, y: null, width: null };
	width = null;

	$(document).bind("keydown", function (e) {
		if (e.which === 83 && e.ctrlKey) {
			e.preventDefault();
			if (currentNotebook == "") {
				RequestDataNewNotebook();
			} else {
				SaveCurrentNotebook();
			}
		}
	});
}

function ChooseEraser() {
	// TODO: Choose eraser
	console.log("Erasing!");
}

function ChoosePen() {
	// TODO: Choose pen
	console.log("Penning!");
}

function getPos(e, div) {
	pos = { x: null, y: null, width: null };
	if (!e.touches) {
		pos.x = e.offsetX;
		pos.y = e.offsetY;
	} else {
		if (e.touches.length == 1) {
			// Only deal with one finger
			var touch = e.touches[0]; // Get the information for finger #1
			touch.target.offsetLeft;
			borderWidths = {
				x: parseInt(div.css("border-left-width")),
				y: parseInt(div.css("border-top-width")),
			};
			var br = div[0].getBoundingClientRect();
			pos.x = touch.clientX - br.left - borderWidths.x;
			pos.y = touch.clientY - br.top - borderWidths.y;
		}
	}
	pos.width = width;
	return pos;
}

$(document).ready(function () {
	init();

	canvas.on("mousemove", (e) => {
		if (doDraw) {
			nb.DrawPos(e);
		}
	});

	canvas.on("touchmove", (e) => {
		if (doDraw) {
			// Prevents an additional mousedown event being triggered
			if (e.touches.length == 1) {
				e.preventDefault();
				nb.DrawPos(e, (sim = false));
			}
		}
	});

	// Regular
	canvas.pressure({
		start: function (event) {
			doDraw = true;
			pos = getPos(event, nb.div);
			var g = nb.draw.group();
			nb.cGroup = g;

			width = 1;
			nb.cPoints = [[pos.x, pos.y, pos.width]];
		},
		end: function (event) {
			doDraw = false;

			pos = { x: null, y: null, width: null };

			nb.changes += nb.cGroup.svg();

			// if (currentNotebook !== "") {
			// 	SaveCurrentNotebook();
			// }
			nb.groups.push(nb.cGroup);
		},
		change: function (force, event) {
			// width = Pressure.map(force, 0, 1, 3, 10);
			width = force;
		},
		unsupported: function () {
			this.innerHTML = "Sorry! Check the devices and browsers";
		},
	});
});
