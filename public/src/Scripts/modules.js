function setCookie(name,value,days) {
    var expires = "";
    if (days) {
        var date = new Date();
        date.setTime(date.getTime() + (days*24*60*60*1000));
        expires = "; expires=" + date.toUTCString();
    }
    document.cookie = name + "=" + (JSON.stringify(value) || "")  + expires + "; path=/";
}

function deleteCookie(name) {
    document.cookie = name + '=; expires=Thu, 01 Jan 1970 00:00:01 GMT;';
  }

function GET(file, type)
{
    var resp = $.ajax({
        type: 'GET',
        url: file,
        async: false,
        dataType: type
    });
    return resp.responseText;
}

function POST(file, type, data, complete = null) {
	var resp = $.ajax({
		type: "POST",
		url: file,
		async: true,
		dataType: type,
		data: data,
		complete: complete,
	});
	return resp.responseText;
}

function Login(Username, Password)
{
    setCookie('user_auth', {'username': Username, 'password': Password}, 10);
   
    respJson = JSON.parse(GET('LOGIN', "text/json"));
    errCode = respJson['code'];

    return !errCode;

}

function SignUp(Username, Password, confirmPass){
    /**
     * Takes username, password and confirm password and tries to sign up.
     * returns: A json file containing the error code at "errCode" and the description of the error at "description"
     */
    if (confirmPass === Password)
    {
        resp = $.ajax({
            type: "POST",
            url: `SIGNUP`,
            async: false,
            dataType: "text/json",
            data: `{"username":  "${Username}", "password": "${Password}"}`,
        });
        respJson = JSON.parse(resp.responseText)
        return (respJson)
    }
    else
    {
        $('#signup_instructions').html("Passwords do not match!");
    }
}