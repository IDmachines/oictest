#!/usr/bin/env python

import json

from default import DEFAULT

info = DEFAULT.copy()

info["provider"] = {"dynamic": "https://seed.gluu.org"}

info["interaction"] = [
    {
        "matches": {
            "url": "https://seed.gluu.org/oxauth/login.seam"
        },
        "page-type": "login",
        "control": {
            "type": "form",
            "set": {"loginForm:username": "mike",
                    "loginForm:password": "secret"}
        }
    },
    {
        "matches": {
            "url": "https://seed.gluu.org/oxauth/authorize.seam"
        },
        "page-type": "user-consent",
        "control": {
            "type": "form",
            "click": "authorizeForm:allowButton"
        }
    }
]

print json.dumps(info)