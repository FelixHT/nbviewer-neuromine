#-----------------------------------------------------------------------------
#  Copyright (C) 2013 The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------
from tornado import web
from tornado.log import app_log
from tornado.escape import url_escape

from .utils import transform_ipynb_uri, url_path_join

from .providers import (
    provider_handlers,
    provider_uri_rewrites,
)
from .providers.base import (
    BaseHandler,
    format_prefix,
)

#from .security import passwd_check

from urllib.parse import urlparse

import hashlib
from ipython_genutils.py3compat import cast_bytes, str_to_bytes, cast_unicode

def passwd_check(hashed_passphrase, passphrase):
    """Verify that a given passphrase matches its hashed version.

    Parameters
    ----------
    hashed_passphrase : str
        Hashed password, in the format returned by `passwd`.
    passphrase : str
        Passphrase to validate.

    Returns
    -------
    valid : bool
        True if the passphrase matches the hash.

    Examples
    --------
    >>> passwd_check('sha1:0e112c3ddfce:a68df677475c2b47b6e86d0467eec97ac5f4b85a',
    ...              'mypassword')
    True

    >>> passwd_check('sha1:0e112c3ddfce:a68df677475c2b47b6e86d0467eec97ac5f4b85a',
    ...              'anotherpassword')
    False
    """
    try:
        algorithm, salt, pw_digest = hashed_passphrase.split(':', 2)
    except (ValueError, TypeError):
        return False

    try:
        h = hashlib.new(algorithm)
    except ValueError:
        return False

    if len(pw_digest) == 0:
        return False

    h.update(cast_bytes(passphrase, 'utf-8') + cast_bytes(salt, 'ascii'))

    #app_log.info(h.hexdigest())
    #app_log.info(pw_digest)
    #app_log.info("YES" if h.hexdigest() == pw_digest else "NO")

    return h.hexdigest() == pw_digest
#-----------------------------------------------------------------------------
# Handler classes
#-----------------------------------------------------------------------------

class Custom404(BaseHandler):
    """Render our 404 template"""
    def prepare(self):
        super(BaseHandler, self).prepare()
        raise web.HTTPError(404)


class IndexHandler(BaseHandler):
    """Render the index"""
    @web.authenticated
    def get(self):
        self.finish(self.render_template(
            'index.html',
            title=self.frontpage_setup.get('title', None),
            subtitle=self.frontpage_setup.get('subtitle', None),
            text=self.frontpage_setup.get('text', None),
            show_input=self.frontpage_setup.get('show_input', True),
            sections=self.frontpage_setup.get('sections', [])))


class FAQHandler(BaseHandler):
    """Render the markdown FAQ page"""
    @web.authenticated
    def get(self):
        self.finish(self.render_template('faq.md'))


class CreateHandler(BaseHandler):
    """handle creation via frontpage form

    only redirects to the appropriate URL
    """
    uri_rewrite_list = None

    def post(self):
        value = self.get_argument('gistnorurl', '')
        redirect_url = transform_ipynb_uri(value, self.get_provider_rewrites())
        app_log.info("create %s => %s", value, redirect_url)
        self.redirect(url_path_join(self.base_url, redirect_url))

    def get_provider_rewrites(self):
        # storing this on a class attribute is a little icky, but is better
        # than the global this was refactored from.
        if self.uri_rewrite_list is None:
            # providers is a list of module import paths
            providers = self.settings['provider_rewrites']

            type(self).uri_rewrite_list = provider_uri_rewrites(providers)
        return self.uri_rewrite_list

class LoginHandler(BaseHandler):

    def _redirect_safe(self, url, default=None):
        """Redirect if url is on our PATH
        Full-domain redirects are allowed if they pass our CORS origin checks.
        Otherwise use default (self.base_url if unspecified).
        """
        if default is None:
            default = self.base_url
        # protect chrome users from mishandling unescaped backslashes.
        # \ is not valid in urls, but some browsers treat it as /
        # instead of %5C, causing `\\` to behave as `//`
        url = url.replace("\\", "%5C")
        parsed = urlparse(url)
        if parsed.netloc or not (parsed.path + '/').startswith(self.base_url):
            # require that next_url be absolute path within our path
            allow = False
            # OR pass our cross-origin check
            if parsed.netloc:
                # if full URL, run our cross-origin check:
                origin = '%s://%s' % (parsed.scheme, parsed.netloc)
                origin = origin.lower()
                if self.allow_origin:
                    allow = self.allow_origin == origin
                elif self.allow_origin_pat:
                    allow = bool(self.allow_origin_pat.match(origin))
            if not allow:
                # not allowed, use default
                self.log.warning("Not allowing login redirect to %r" % url)
                url = default
        self.redirect(url)


    def _render(self, message=None):
        self.write(self.render_template(
            'login.html',
             next=url_escape(self.get_argument('next', default=self.base_url)),
             message=message))

    @property
    def hashed_password(self):
        return self.settings['password_setup']

    def passwd_check(self, a, b):
        return passwd_check(a, b)

    def get(self):
        self._render()

    def post(self):
        typed_password = self.get_argument('password', default=u'')
 
        if not passwd_check(self.hashed_password, typed_password):
            #app_log.info("NO")
            self.set_status(401)
            self._render('Invalid credentials')
        else:
            #app_log.info("YES")
            self.set_secure_cookie("user", 'set')
            next_url = self.get_argument('next', default=self.base_url)
            self._redirect_safe(next_url)


#class LogoutHandler(BaseHandler):
#    def get(self):
#        self.clear_cookie("user")
#        self.redirect("/login")


#-----------------------------------------------------------------------------
# Default handler URL mapping
#-----------------------------------------------------------------------------

def format_handlers(formats, urlspecs, **handler_settings):
    """
    Tornado handler URLSpec of form (route, handler_class, initalize_kwargs)
    https://www.tornadoweb.org/en/stable/web.html#tornado.web.URLSpec
    kwargs passed to initialize are None by default but can be added
    https://www.tornadoweb.org/en/stable/web.html#tornado.web.RequestHandler.initialize
    """
    urlspecs = [
        (prefix + url, handler, {
            "format": format,
            "format_prefix": prefix
        })
        for format in formats
        for url, handler, initialize_kwargs in urlspecs
        for prefix in [format_prefix + format]
    ]
    for handler_setting in handler_settings:
        if handler_settings[handler_setting]:
            # here we modify the URLSpec dict to have the key-value pairs from
            # handler_settings in NBViewer.init_tornado_application
            for urlspec in urlspecs:
                urlspec[2][handler_setting] = handler_settings[handler_setting]
    return urlspecs

def init_handlers(formats, providers, base_url, localfiles, **handler_kwargs):
    """
    `handler_kwargs` is a dict of dicts: first dict is `handler_names`, which
    specifies the handler_classes to load for the providers, the second
    is `handler_settings` (see comments in format_handlers)
    Only `handler_settings` should get added to the initialize_kwargs in the
    handler URLSpecs, which is why we pass only it to `format_handlers`
    but both it and `handler_names` to `provider_handlers`
    """
    handler_settings = handler_kwargs['handler_settings']

    pre_providers = [
        ('/login', LoginHandler, {}),
        (r'/?', IndexHandler, {}),
        ('/index.html', IndexHandler, {}),
        (r'/faq/?', FAQHandler, {}),
        (r'/create/?', CreateHandler, {}),
        ('/localfile', IndexHandler, {}),

        # don't let super old browsers request data-uris
        (r'.*/data:.*;base64,.*', Custom404, {}),
    ]

    post_providers = [
        (r'/(robots\.txt|favicon\.ico)', web.StaticFileHandler, {})
    ]

    # Add localfile handlers if the option is set
    if localfiles:
        # Put local provider first as per the comment at
        # https://github.com/jupyter/nbviewer/pull/727#discussion_r144448440.
        providers.insert(0, 'nbviewer.providers.local')

    handlers = provider_handlers(providers, **handler_kwargs)

    raw_handlers = (
        pre_providers +
        handlers +
        format_handlers(formats, handlers, **handler_settings) +
        post_providers
    )

    new_handlers = []
    for handler in raw_handlers:
        pattern = url_path_join(base_url, handler[0])
        new_handler = tuple([pattern] + list(handler[1:]))
        new_handlers.append(new_handler)
    new_handlers.append((r'.*', Custom404, {}))

    return new_handlers
