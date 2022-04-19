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

function loadNotebook(notebookID, isCode = false) {
	// $("#drawingSvg").remove()
	$(".online").show();
	if (currentNotebook != "") {
		$(`#Notebook${currentNotebook}`).css({
			"background-color": "var(--default-notebookList-background)",
		});
		$(`#Notebook${currentNotebook} .notebook-title`).css({
			"background-color": "var(--default-title)",
		});
	}

	if (!isCode) {
		var notebookDataString = GET(`Notebook/${notebookID}`, "text/json");
		var notebookData = JSON.parse(notebookDataString);
		nbcode = notebookData["data"]["code"];
	} else {
		var notebookDataResp = $.ajax({
			url: `Notebook`,
			type: "GET",
			data: { nb: notebookID },
			async: false,
		});
		var notebookData = notebookDataResp.responseJSON;
	}
	var data = notebookData["data"];
	var svgData = data["NotebookData"];
	currentGroupID = data["currentGroupID"];
	draw.clear();
	// draw.svg(svgData);
	$("#drawingSvg").html($(svgData).html());
	$(`#Notebook${notebookID}`).css({ "background-color": "#fd4448" });
	$(`#Notebook${notebookID} .notebook-title`).css({
		"background-color": "#f21c21",
	});
	currentNotebook = `${notebookID}`;
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

		nbblock.on("click", (e) => {
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
			// svgData: draw.svg(),
			svgData: "",
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
	let attrcode = attr["nb"];

	// var count = 0;
	if (attrcode != undefined) {
		addedurl = `?nb=${attrcode}`;
	} else if (nbcode != null) {
		addedurl = `?nb=${nbcode}`;
	} else {
		addedurl = `${currentNotebook}`;
	}
	var resp = $.ajax({
		url: `/SAVE/${addedurl}`,
		type: "POST",
		contentType: "svg",
		data: JSON.stringify(nb.changes),
		complete: (resp) => {
			console.log(resp);
		},
	});
	nb.changes = [];
}

var nbcode = null;
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
var collapsed = false;
var attr = {};
var updateInterval = 1000;

var NBcode = undefined;

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
			$(".user").show();
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

	window.location.search
		.substr(1)
		.split("&&")
		.forEach((eq) => {
			let eqt = eq.split("=");
			attr[eqt[0]] = eqt[1];
		});

	if (attr["nb"] != undefined) {
		loadNotebook(attr["nb"], true);
		collapseSidebar();
	}
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
					currentGroupID += 1; // TODO: Change
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
		if (isUpdating) {
			checkGlobaly();
		}
	}, updateInterval);
});

function checkGlobaly() {
	if (attr["nb"] != undefined) {
		checkUpdates(attr["nb"]);
	} else if (nbcode != null) {
		checkUpdates(nbcode);
	}
}

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

checkingUpdates = false;
function checkUpdates(code) {
	if (checkingUpdates) {
		return;
	}

	checkingUpdates = true;
	// create random id code
	updateIDCode = Math.random().toString(36).substring(2, 15);
	console.log("sending update request");
	$.ajax({
		method: "GET",
		url: `UPDATE`,
		data: { code: code },
		accepts: "text/json",
		complete: function (resp) {
			if (resp.status == 200) {
				let data = JSON.parse(resp.responseText);
				console.log("Recieved Update!");
				if (data["command"] == "a") {
					let newGroup = draw.svg(data["data"]);

					// Remove groups we know are not updated to the server
					let groups = $("#drawingSvg g");
					if (groups.length > 0) {
						for (let i = 0; i < groups.length; i++) {
							let g = groups[i];
							if (g.id == "") {
								g.remove();
							}
						}
					}
				} else if (data["command"] == "e") {
					console.log(
						"Recieved Erase! erasing group " + data["data"]
					);
					$(`${data["data"]["type"]}#${data["data"]["id"]}`).remove();
				}
			} else if (resp.status == 400) {
				console.log("Update failed: Bad Request");
			}
			checkingUpdates = false;
		},
	});
}

var notebookLinkID = "";
function ShareClick() {
	if (NBcode === null || currentNotebook != notebookLinkID) {
		NBcode = RequestLink(currentNotebook);
		notebookLinkID = currentNotebook;
	}

	shareHidden = !shareHidden;
	console.log(shareHidden);
	if (shareHidden) {
		$("#share-button-content").hide();
	} else {
		$("#share-button-content").show();
	}
	const ShareContainer = $("#share-button-container");

	$(document).on("click", function (e) {
		if (
			ShareContainer[0] !== e.target &&
			!ShareContainer[0].contains(e.target)
		) {
			if (!shareHidden) {
				shareHidden = !shareHidden;
				$("#share-button-content").hide();
			}
		}
	});
}

function copy(selector) {
	navigator.clipboard.writeText($(selector).text()).then(
		() => {
			console.log("Copied to clipboard");
		},
		() => {
			console.log("Failed to copy");
		}
	);
}

function displayShareLink(code) {
	let currentURL = $(location).attr("href");
	$("#share-button-content").html(
		`<div onclick="copy('#shareLink')" target="_blank">Link: <a id="shareLink"> ${currentURL}?nb=${code} </a>
		</div>
		`
	);
	$("#generate-link").hide();
}

function RequestLink(nbID) {
	$.ajax({
		type: "GET",
		url: `/api/notebook/code?nbID=${nbID}`,
		complete: (data) => {
			data = data.responseJSON;
			console.log(data);
			code = data.code;
			if (code != null) {
				displayShareLink(code);
			}
		},
		async: false,
	});
	return code;
}

function generateLink() {
	resp = $.ajax({
		type: "POST",
		url: `/api/notebook/create`,
		data: currentNotebook,
		contentType: "text/json",
		complete: (data) => {
			console.log("data: ", data);
			code = data.responseJSON["code"];
			nbcode = code;
			displayShareLink(code);
		},
	});
}

var isUpdating = true;

function toggleUpdate() {
	isUpdating = !isUpdating;
}