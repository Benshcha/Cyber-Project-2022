class Notebook {
	constructor(drawer, div) {
		this.changes = [];
		this.draw = drawer;
		this.div = div;
		this.cPath = null;
		this.cGroup = null;
		this.cPoints = [];
		this.options = { size: 1 };
	}

	setOptions(option, val) {
		this.options[option] = val;
	}

	// drawing on canvas ctx given touch/click event e
	DrawPos(e, sim = true) {
		pos = getPos(e);
		this.cPoints.push([pos.x, pos.y, pos.width]);

		let options = Object.assign({}, this.options, {
			simulatePressure: sim,
		});

		var outlinePoints = getStroke(this.cPoints, options);

		// vTODO: Still need to define new Change

		// if nb has cPath clear it
		if (this.cPath != null) {
			this.cGroup.clear();
		}

		nb.cPath = nb.cGroup.path(getSvgPathFromStroke(outlinePoints));
		nb.cPath.stroke({ opacity: 0 });
		nb.cPath.fill({ color: color });

		if (pos.x > this.div.width() - thresh) {
			this.div.width(this.div.width() + thresh * 10);
		}

		if (pos.y > this.div.height() - thresh) {
			this.div.height(this.div.height() + thresh * 10);
		}
		// nb.cPath.attr("stroke-width", width);
	}

	EraseGroup(target) {
		let group = target.parentElement;
		if (group.nodeName != "g") {
			return;
		}

		let groupID = group.getAttribute("id");
		console.log("deleting group: " + groupID);
		let data = ["e", { type: "g", id: groupID }];
		this.changes.push(data);
		group.remove();
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
	currentGroupID = data["currentGroupID"];
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
		createNotebook(newTitle, newDescription, currentGroupID);
		currentGroupID = 0;
		$("#addnb-container").show();
	});
}

function createNotebook(newTitle, newDescription, newGroupID) {
	var textResp = POST(
		`SAVENEWNB`,
		"text/json",
		JSON.stringify({
			svgData: draw.svg(),
			title: newTitle,
			description: newDescription,
			currentGroupID: newGroupID,
		}),
		(resp) => {
			console.log(resp);
			BuildNotebookList();
			currentNotebook = JSON.parse(resp.responseText)["data"]["id"];
			$(".online").show();
		}
	);
}

function SaveCurrentNotebook(nb) {
	// var count = 0;
	var resp = POST(
		`/SAVE/${currentNotebook}`,
		"svg",
		JSON.stringify(nb.changes),
		(resp) => {
			console.log(resp);
			loadNotebook(currentNotebook);
		}
	);
	nb.changes = [];
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
var color = "black";
var thresh = 20;
var currentGroupID = 0;
var isPen = true;
var isEraser = false;

function map(value, low1, high1, low2, high2) {
	return low2 + ((high2 - low2) * (value - low1)) / (high1 - low1);
}

const midPoint = 0.5;
const midPointVal = 0.5;
const maxVal = 1;
const minVal = 0;
presMap = (w) => {
	// if (0 <= w && w <= midPoint) {
	// 	console.log(`lower -> ${w}`);
	// 	return map(w, 0, midPoint, minVal, midPointVal);
	// } else if (midPoint < w && w <= 1) {
	// 	console.log(`upper -> ${w}`);
	// 	return map(w, midPoint, 1, midPointVal, maxVal);
	// }
	return w;
};

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
	draw = SVG("#drawingSvg").addTo("#drawing").size("100%", "100%");
	svg = $("#drawingSvg");
	doDraw = false;
	nb = new Notebook(draw, svg);
	nb.setOptions("size", 5);

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

	DrawPreview(5);
}

function ChooseEraser() {
	isPen = false;
	$("#eraser").css("filter", "invert(0)");
	isEraser = true;
	$("#pen").css("filter", "invert(1)");
	console.log("Switched to eraser");
}

function ChoosePen() {
	isEraser = false;
	$("#pen").css("filter", "invert(0)");
	isPen = true;
	$("#eraser").css("filter", "invert(1)");
	console.log("Switched to pen");
}

function getPos(e) {
	pos = { x: null, y: null, width: null };
	pos.x = e.offsetX;
	pos.y = e.offsetY;

	pos.width = presMap(width);
	return pos;
}

$(document).ready(function () {
	init();

	var simState = false;
	canvas.on("mousemove", (e) => {
		if (doDraw) {
			simState = true;
		}
	});

	canvas.on("touchmove", (e) => {
		if (e.touches.length === 1) {
			if (doDraw) {
				e.preventDefault();
				simState = false;
			}
		} else {
			doDraw = false;
			nb.cGroup.remove();
		}
	});

	canvas.on("pointermove", (e) => {
		if (doDraw) {
			if (isPen) {
				nb.DrawPos(e, (sim = simState));
			} else if (isEraser) {
				nb.EraseGroup(e.target);
			}
		}
	});

	// Regular
	$.pressureConfig({ polyfillSpeedUp: 10000, preventSelect: true });
	canvas.pressure({
		start: function (event) {
			doDraw = true;

			if (isPen) {
				pos = getPos(event, nb.div);
				var g = nb.draw.group();
				if (currentNotebook == "") {
					currentGroupID += 1;
					g = g.id(currentGroupID);
				}
				nb.cGroup = g;
				nb.cPoints = [];

				width = event.pressure;
				nb.DrawPos(event);
			}
		},
		end: function (event) {
			let t;
			let svgData;
			
			doDraw = false;

			if (currentNotebook !== "") {
				if (isPen) {
					t = "a";
					svgData = nb.cGroup.svg();
					nb.changes.push([t, svgData]);
				}
				SaveCurrentNotebook(nb);
			}
		},
		change: function (force, event) {
			width = force;
		},
		unsupported: function () {
			this.innerHTML = `Sorry! Check the devices and browsers`;
		},
	});

	setInterval(() => {
		if (currentNotebook != "") {
			SaveCurrentNotebook();
		}
	}, 0.1);
});

var collapsed = false;

function collapseSidebar() {
	if (!collapsed) {
		$(":root").css("--mainbody-width", "100vw");
		$(":root").css("--button-radius", "0");
		$("#collapse-sidebar").css("transform", "rotate(180deg)");
		$("#collapse-sidebar").css("top", "50%");
		$("#collapse-sidebar").css("left", "0");
	} else {
		$(":root").css("--mainbody-width", "85vw");
		$(":root").css("--button-radius", "1.5rem");
		$("#collapse-sidebar").css("transform", "rotate(0deg)");
		$("#collapse-sidebar").css("top", "50%");
		$("#collapse-sidebar").css("left", "calc(var(--sidebar-width)");
	}
	collapsed = !collapsed;
}