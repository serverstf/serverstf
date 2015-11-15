define ->
    return _ =
        "name": "SignIn"
        "dependencies": ["Modal"]
        "controller": (Modal) ->
            Modal.title = "Sign in with Steam"
