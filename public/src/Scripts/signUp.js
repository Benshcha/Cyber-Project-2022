function signUpPress (usernameID, passwordID, con_passwordID, instructionID)
{
    const signUpResp = SignUp($(`#${usernameID}`)[0].value, $(`#${passwordID}`)[0].value, $(`#${con_passwordID}`)[0].value);
    
    if (!signUpResp['code'])
    {
        window.location.replace('/login.html');
    }
    else
    {
        description = signUpResp['description']
        $(`#${instructionID}`).html(description);
        console.error(description);
    }
    
}