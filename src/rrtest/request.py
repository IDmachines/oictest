import requests
import copy
import urllib

from oic.oauth2 import URL_ENCODED
from oic.oauth2 import Message
from oic.oic import AuthorizationRequest
from oictest.check import CheckEndpoint

__author__ = 'rolandh'

DUMMY_URL = "https://remove.this.url/"

class Request(object):
    request = ""
    method = ""
    content_type = URL_ENCODED
    accept = None
    lax = False
    _request_args = {}
    _request_param = False
    _kw_args = {}
    _tests = {"post": [], "pre": []}

    def __init__(self, conv):
        self.request_args = copy.deepcopy(self._request_args)
        self.request_param = copy.deepcopy(self._request_param)
        self.kw_args = copy.deepcopy(self._kw_args)
        self.conv = conv
        self.conv.req = self
        self.trace = conv.trace
        self.tests = copy.deepcopy(self._tests)

    def construct_request(self, client, **cargs):
        """
        Construct the request to send to the OP
        :param client: A client (RP) instance
        :param cargs: Extra keyword arguments
        :return:
            url - which url to send the request to
            body - The message to send in the HTTP body
            ht_args - HTTP headers arguments
        """
        if not self.request:
            request = None
        elif isinstance(self.request, basestring):
            request = self.conv.msg_factory(self.request)
        else:
            request = self.request

        try:
            kwargs = self.kw_args.copy()
        except KeyError:
            kwargs = {}

        try:
            _mod = cargs["kwargs_mod"]
        except KeyError:
            pass
        else:
            kwargs.update(_mod)
            del cargs["kwargs_mod"]

        e_arg = {}
        for key in ["endpoint", "http_authz"]:
            try:
                e_arg[key] = kwargs[key]
            except KeyError:
                e_arg[key] = ""
            else:
                del kwargs[key]

        try:
            kwargs["request_args"] = self.request_args.copy()
            try:
                kwargs["request_args"].update(cargs["request_args"])
            except KeyError:
                pass
            else:
                del cargs["request_args"]
            _req = kwargs["request_args"].copy()
        except KeyError:
            _req = {}

        kwargs.update(cargs)

        if request == AuthorizationRequest:
            try:
                if self.request_param:
                    kwargs["request_param"] = self.request_param
            except KeyError:
                pass

        if request:
            if request.__name__ == "RegistrationRequest":
                kwargs["request_args"].update(client.behaviour)
            elif request.__name__ == "AuthorizationRequest":
                try:
                    _ruri = kwargs["request_args"]["redirect_uri"]
                except KeyError:
                    pass
                else:
                    if _ruri == "":
                        kwargs["request_args"]["redirect_uri"] = DUMMY_URL

            cis = getattr(client, "construct_%s" % request.__name__)(request,
                                                                     **kwargs)
            # Remove parameters with None value
            # for key, val in cis.items():
            #     if val is None:
            #         del cis[key]

            if request == AuthorizationRequest:
                try:
                    cis['acr_values'] = client.behaviour['default_acr_values']
                except KeyError:
                    pass

            setattr(self.conv, request.__name__, cis)
            try:
                cis.lax = self.lax
            except AttributeError:
                pass
        else:
            cis = Message()

        if "authn_method" in kwargs:
            h_arg = client.init_authentication_method(cis, **kwargs)
        else:
            h_arg = {}

        if request:
            _kwargs = {"method": self.method, "request_args": _req,
                       "content_type": self.content_type,
                       "accept": self.accept}

            if e_arg["endpoint"]:
                _kwargs["endpoint"] = e_arg["endpoint"]

            try:
                extras = self.conv.client_config["extra_args"][self.request]
            except KeyError:
                pass
            else:
                for key, val in extras.items():
                    if val is None:
                        val = getattr(self.conv.client, key)
                    cis[key] = val

            url, body, ht_args, cis = client.uri_and_body(
                request, cis, **_kwargs)
            self.conv.cis.append(cis)
            if h_arg:
                for key in h_arg:
                    if key in ht_args:
                        ht_args[key].update(h_arg[key])
                    else:
                        ht_args[key] = h_arg[key]
            # if ht_add:
            #     ht_args.update({"headers": ht_add})
        else:
            ht_args = h_arg
            url = e_arg["endpoint"]
            body = ""

        if request and request.__name__ == "AuthorizationRequest":
            try:
                if kwargs["request_args"]["redirect_uri"] == DUMMY_URL:
                    _str = "redirect_uri=%s" % urllib.quote_plus(DUMMY_URL)
                    # Can be first or last
                    if url.find("&"+_str):
                        url = url.replace("&"+_str, "")
                    else:
                        url = url.replace(_str+"&", "")
            except KeyError:
                pass

        self.conv.last_url = url
        if e_arg["http_authz"]:
            ht_args["auth"] = e_arg["http_authz"]

        self.trace.request("URL: %s" % url)
        self.trace.request("BODY: %s" % body)
        for param in ["headers", "auth"]:
            try:
                self.trace.request("%s: %s" % (param.upper(), ht_args[param]))
            except KeyError:
                pass

        return url, body, ht_args

    def do_request(self, client, url, body, ht_args):
        response = client.http_request(url, method=self.method, data=body,
                                       **ht_args)

        self.trace.reply("RESPONSE: %s" % response)
        self.trace.reply("CONTENT: %s" % response.text)
        try:
            self.trace.reply("REASON: %s" % response.reason)
        except AttributeError:
            pass
        if response.status_code in [301, 302]:
            self.trace.reply("LOCATION: %s" % response.headers["location"])
        try:
            self.trace.reply("COOKIES: %s" % requests.utils.dict_from_cookiejar(
                response.cookies))
        except AttributeError:
            self.trace.reply("COOKIES: %s" % response.cookies)

        return url, response, response.text

    def call_setup(self):
        pass

    def __call__(self, location, response="", content="", features=None,
                 **cargs):
        _client = self.conv.client
        self.call_setup()
        url, body, ht_args = self.construct_request(_client, **cargs)

        return self.do_request(_client, url, body, ht_args)

    def update(self, dic):
        _tmp = {"request": self.request_args.copy(), "kw": self.kw_args}
        for key, val in self.rec_update(_tmp, dic).items():
            setattr(self, "%s_args" % key, val)

    def rec_update(self, dic0, dic1):
        res = {}
        for key, val in dic0.items():
            if key not in dic1:
                res[key] = val
            else:
                if isinstance(val, dict):
                    res[key] = self.rec_update(val, dic1[key])
                else:
                    res[key] = dic1[key]

        for key, val in dic1.items():
            if key in dic0:
                continue
            else:
                res[key] = val

        return res

    def set_request_args(self, dic):
        for key, val in dic.items():
            self.request_args[key] = val
            if key in self.conv.client.behaviour:
                self.conv.client.behaviour[key] = val


class GetRequest(Request):
    method = "GET"


class PostRequest(Request):
    method = "POST"
    tests = {"pre": [CheckEndpoint], "post": []}


class Response(object):
    response = ""
    _tests = {}

    def __init__(self):
        self.tests = copy.deepcopy(self._tests)

    def __call__(self, conv, response):
        pass


class UrlResponse(Response):
    where = "url"
    ctype = "urlencoded"


class BodyResponse(Response):
    where = "body"
    ctype = "json"


class ErrorResponse(BodyResponse):
    response = "ErrorResponse"


class PlainResponse(Response):
    where = "body"
    ctype = "text"
    empty_is_ok = True


class Process(object):
    pass


