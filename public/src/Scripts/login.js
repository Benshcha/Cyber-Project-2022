function Login(usernameObj, passwordObj)
{
    Username = usernameObj.value
    Password = passwordObj.value
    $.post(`Login`, `"Username": "${Username}"\n"Password" = "${Password}"`)
    console.log(Username, Password);
}