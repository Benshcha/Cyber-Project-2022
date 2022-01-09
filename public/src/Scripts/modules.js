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
    ans = respJson[0]
    if (ans == 0)
    {
        setCookie('user_auth', {'username': Username, 'password': Password}, 10)
    }

    return !ans

}

function SignUp(Username, Password, confirmPass)
{
    if (confirmPass === Password)
    {
        $.post(`Login Attempt`, `"Username": "${Username}"\n"Password" = "${Password}"`);
        console.log(Username, Password);
    }
    else
    {
        $('#signup_instructions').html("Passwords do not match!");
    }
}