function Login(usernameObj, passwordObj)
{
    Username = usernameObj.value
    Password = passwordObj.value
    $.post(`Login Attempt`, `"Username": "${Username}"\n"Password" = "${Password}"`)
    console.log(Username, Password);
}