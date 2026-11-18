"""
Middleware helpers for Chama Digital.
Ensures CSRF and session cookies function reliably both in local HTTP
development and when served behind HTTPS reverse proxies (such as preview iframes).
"""


from chama_digital.db_bootstrap import ensure_database_ready


class AutoInitializeDatabaseMiddleware:
    """Ensures SQLite tables and initial seed data exist before handling requests."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ensure_database_ready()
        return self.get_response(request)


class ProxyAwareCookieMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.is_secure():
            for cookie_name in ('sessionid', 'csrftoken'):
                if cookie_name in response.cookies:
                    response.cookies[cookie_name]['samesite'] = 'None'
                    response.cookies[cookie_name]['secure'] = True
        return response
