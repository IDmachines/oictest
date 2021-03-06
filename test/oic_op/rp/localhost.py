import copy
import default
from sslconf import *

HOST = "localhost"
PORT = 8088
BASE = "https://%s:%d/" % (HOST, PORT)

CLIENT = {
    "base_url": BASE,
    "srv_discovery_url": "https://localhost:8092/",
    "webfinger_subject": "diana@localhost:8092",
    "login_hint": "diana",
    "ui_locales": "se",
    "claims_locales": "se",
    "acr_values": ["1"],
    "client_info": {
        "application_type": "web",
        "application_name": "OIC test tool",
        "contacts": ["roland.hedberg@umu.se"],
        "redirect_uris": ["%sauthz_cb" % BASE],
        "post_logout_redirect_uris": ["%slogout" % BASE],
    },
    "key_export_url": "%sexport/jwk_%%s.json" % BASE,
}

for arg in ["keys", "behaviour", "preferences"]:
    CLIENT[arg] = copy.deepcopy(default.CLIENT[arg])