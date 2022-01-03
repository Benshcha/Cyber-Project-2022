function Login(usernameObj, passwordObj)
{
    Username = usernameObj.value
    Password = passwordObj.value
    $.post(`Login`, `Username = ${Username}\nPassword = ${Password}`)
    console.log(Username, Password);
}