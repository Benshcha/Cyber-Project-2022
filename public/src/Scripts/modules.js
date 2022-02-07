function setCookie(name, value, days) {
	var expires = "";
	if (days) {
		var date = new Date();
		date.setTime(date.getTime() + days * 24 * 60 * 60 * 1000);
		expires = "; expires=" + date.toUTCString();
	}
	document.cookie =
		name + "=" + (JSON.stringify(value) || "") + expires + "; path=/";
}

function deleteCookie(name) {
	document.cookie = name + "=; expires=Thu, 01 Jan 1970 00:00:01 GMT;";
}

function GET(file, type) {
	var resp = $.ajax({
		type: "GET",
		url: file,
		async: false,
		dataType: type,
	});
	return resp.responseText;
}

function POST(file, type, data, complete = null) {
	var resp = $.ajax({
		type: "POST",
		url: file,
		async: true,
		// dataType: type,
		contentType: type,
		data: data,
		complete: complete,
	});
	console.log(`Post resp = ${resp.responseText}`);
	return resp.responseText;
}

function Login(Username, Password) {
	setCookie("user_auth", { username: Username, password: Password }, 10);

	var respJson = JSON.parse(GET("LOGIN", "text/json"));
	var errCode = respJson["code"];

	return !errCode;
}

function SignUp(Username, Password, confirmPass) {
	/**
	 * Takes username, password and confirm password and tries to sign up.
	 * returns: A json file containing the error code at "errCode" and the description of the error at "description"
	 */
	if (confirmPass === Password) {
		var resp = $.ajax({
			type: "POST",
			url: `SIGNUP`,
			async: false,
			dataType: "text/json",
			data: `{"username":  "${Username}", "password": "${Password}"}`,
		});
		var respJson = JSON.parse(resp.responseText);
		return respJson;
	} else {
		$("#signup_instructions").html("Passwords do not match!");
	}
}

// Turn the points returned from perfect-freehand into SVG path data.

function getSvgPathFromStroke(stroke) {
	if (!stroke.length) return "";

	const d = stroke.reduce(
		(acc, [x0, y0], i, arr) => {
			const [x1, y1] = arr[(i + 1) % arr.length];
			acc.push(x0, y0, (x0 + x1) / 2, (y0 + y1) / 2);
			return acc;
		},
		["M", ...stroke[0], "Q"]
	);

	// d.push("Z");
	return d.join(" ");
}
