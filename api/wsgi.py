try:
    from api.index import app
except ImportError:
    from index import app

# WSGI 엔트리 포인트
def application(environ, start_response):
    return app(environ, start_response) 