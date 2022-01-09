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

function Login(Username, Password)
{
    resp = $.ajax({
        type: 'POST',
        url: 'LOGIN',
        async: false,
        dataType: "text/json",
        data: `{"username":  "${Username}", "password": "${Password}"}`,
    })
    respJson = JSON.parse(resp.responseText)
    errCode = !respJson[0]
    if (errCode)
    {
        setCookie('user_auth', {'username': Username, 'password': Password}, 10)
    }

    return errCode

}

function SignUp(Username, Password, confirmPass){
    /**
     * Takes username, password and confirm password and tries to sign up.
     * returns: A json file containing the error code at "errCode" and the discription of the error at "discription"
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