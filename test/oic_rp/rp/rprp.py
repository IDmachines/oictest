import copy
import importlib
import logging
from urlparse import parse_qs
import argparse
from mako.lookup import TemplateLookup
from oic.oauth2 import rndstr, ResponseError

from oic.oic import Client, AuthorizationRequest, AuthorizationResponse
from oic.utils.authn.client import CLIENT_AUTHN_METHOD
from oic.utils.http_util import Response, get_post
from oic.utils.http_util import Redirect
from oic.utils.http_util import ServiceError
from oic.utils.http_util import NotFound

__author__ = 'roland'

LOGGER = logging.getLogger("")
LOGFILE_NAME = 'rprp.log'
hdlr = logging.FileHandler(LOGFILE_NAME)
base_formatter = logging.Formatter(
    "%(asctime)s %(name)s:%(levelname)s %(message)s")

hdlr.setFormatter(base_formatter)
LOGGER.addHandler(hdlr)
LOGGER.setLevel(logging.DEBUG)

SERVER_ENV = {}
LOOKUP = TemplateLookup(directories=['templates', 'htdocs'],
                        module_directory='modules',
                        input_encoding='utf-8',
                        output_encoding='utf-8')


#noinspection PyUnresolvedReferences
def static(environ, start_response, logger, path):
    logger.info("[static]sending: %s" % (path,))

    try:
        text = open(path).read()
        if path.endswith(".ico"):
            start_response('200 OK', [('Content-Type', "image/x-icon")])
        elif path.endswith(".html"):
            start_response('200 OK', [('Content-Type', 'text/html')])
        elif path.endswith(".json"):
            start_response('200 OK', [('Content-Type', 'application/json')])
        elif path.endswith(".jwt"):
            start_response('200 OK', [('Content-Type', 'application/jwt')])
        elif path.endswith(".txt"):
            start_response('200 OK', [('Content-Type', 'text/plain')])
        elif path.endswith(".css"):
            start_response('200 OK', [('Content-Type', 'text/css')])
        else:
            start_response('200 OK', [('Content-Type', "text/plain")])
        return [text]
    except IOError:
        resp = NotFound()
        return resp(environ, start_response)


def opresult_fragment(environ, start_response):
    resp = Response(mako_template="opresult_repost.mako",
                    template_lookup=LOOKUP,
                    headers=[])
    argv = {}
    return resp(environ, start_response, **argv)


def flow_list(environ, start_response, flows, done):
    resp = Response(mako_template="flowlist.mako",
                    template_lookup=LOOKUP,
                    headers=[])
    argv = {"base": CONF.BASE, "flows": flows, "done": done}

    return resp(environ, start_response, **argv)


def run_flow(client, index, session):

    if index < len(session["flow"]["flow"]):
        for action, args in session["flow"]["flow"][index:]:
            session["index"] += 1  # next to run

            if action == "discover":
                if args:
                    session["issuer"] = client.discover(args)
                else:
                    session["issuer"] = client.discover(CONF.ISSUER)
            elif action == "provider_info":
                client.provider_config(session["issuer"])
            elif action == "registration":
                client.register(client.provider_info["registration_endpoint"])
            elif action == "authn_req":
                session["state"] = rndstr()
                url, body, ht_args, csi = client.request_info(
                    AuthorizationRequest, method="GET", request_args=args,
                    state=session["state"])
                return Redirect(str(url))
            elif action == "token_req":
                _args = copy.deepcopy(args)
                _args["state"] = session["state"]
                _args["request_args"] = {
                    "redirect_uri": client.redirect_uris[0]}
                client.do_access_token_request(**_args)
            elif action == "userinfo_req":
                client.do_user_info_request(**args)

    session["done"].append(session["item"])
    return None


def application(environ, start_response):
    session = environ['beaker.session']

    path = environ.get('PATH_INFO', '').lstrip('/')
    if path == "robots.txt":
        return static(environ, start_response, LOGGER, "static/robots.txt")

    if path.startswith("static/"):
        return static(environ, start_response, LOGGER, path)

    if path.startswith("export/"):
        return static(environ, start_response, LOGGER, path)

    try:
        _cli = session["client"]
    except KeyError:
        _cli = session["client"] = Client(
            client_authn_method=CLIENT_AUTHN_METHOD)
        _cli.allow["issuer_mismatch"] = True
        for arg, val in CONF.CLIENT_INFO.items():
            setattr(_cli, arg, val)
        session["done"] = []

    if path == "":  # list
        return flow_list(environ, start_response, FLOWS.FLOWS, session["done"])
    elif path in FLOWS.FLOWS.keys():
        session["flow"] = FLOWS.FLOWS[path]
        session["index"] = 0
        session["item"] = path
        try:
            resp = run_flow(_cli, session["index"], session)
        except Exception as err:
            resp = ServiceError("%s" % err)
            return resp(environ, start_response)
        else:
            if resp:
                return resp(environ, start_response)
            else:
                return flow_list(environ, start_response, FLOWS.FLOWS,
                                 session["done"])
    elif path in ["authz_cb", "authz_post"]:
        if path != "authz_post":
            args = session["flow"]["flow"][session["index"]-1][1]
            if not args["response_type"] == ["code"]:
                return opresult_fragment(environ, start_response)

        # Got a real Authn response
        ctype = "urlencoded"
        if path == "authz_post":
            query = parse_qs(get_post(environ))
            info = query["fragment"][0]
        else:
            info = environ["QUERY_STRING"]

        LOGGER.info("Response: %s" % info)
        try:
            _cli = session["client"]
            response = _cli.parse_response(AuthorizationResponse, info, ctype,
                                           session["state"], keyjar=_cli.keyjar)
        except ResponseError as err:
            LOGGER.error("%s" % err)
            resp = ServiceError("%s" % err)
            return resp(environ, start_response)
        else:
            pass

        try:
            resp = run_flow(_cli, session["index"], session)
        except Exception as err:
            resp = ServiceError("%s" % err)
            return resp(environ, start_response)
        else:
            if resp:
                return resp(environ, start_response)
            else:
                return flow_list(environ, start_response, FLOWS.FLOWS,
                                 session["done"])


if __name__ == '__main__':
    from beaker.middleware import SessionMiddleware
    from cherrypy import wsgiserver

    parser = argparse.ArgumentParser()
    parser.add_argument('-f', dest='flows')
    parser.add_argument(dest="config")
    cargs = parser.parse_args()

    # global ACR_VALUES
    # ACR_VALUES = CONF.ACR_VALUES

    session_opts = {
        'session.type': 'memory',
        'session.cookie_expires': True,
        'session.auto': True,
        'session.timeout': 900
    }

    FLOWS = importlib.import_module(cargs.flows)
    CONF = importlib.import_module(cargs.config)

    SERVER_ENV.update({"template_lookup": LOOKUP, "base_url": CONF.BASE})

    SRV = wsgiserver.CherryPyWSGIServer(('0.0.0.0', CONF.PORT),
                                        SessionMiddleware(application,
                                                          session_opts))

    if CONF.BASE.startswith("https"):
        from cherrypy.wsgiserver import ssl_pyopenssl

        SRV.ssl_adapter = ssl_pyopenssl.pyOpenSSLAdapter(
            CONF.SERVER_CERT, CONF.SERVER_KEY, CONF.CA_BUNDLE)

    LOGGER.info("RP server starting listening on port:%s" % CONF.PORT)
    print "RP server starting listening on port:%s" % CONF.PORT
    try:
        SRV.start()
    except KeyboardInterrupt:
        SRV.stop()