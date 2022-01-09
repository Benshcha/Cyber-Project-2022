function signUpPress (usernameID, passwordID, con_passwordID, instructionID)
{
    const signUpResp = SignUp($(`#${usernameID}`)[0].value, $(`#${passwordID}`)[0].value, $(`#${con_passwordID}`)[0].value);
    
    if (!signUpResp['errCode'])
    {
        window.location.replace('/');
    }
    else
    {
        discription = signUpResp['discription']
        $(`#${instructionID}`).html(discription);
        console.error(discription);
    }
    
}