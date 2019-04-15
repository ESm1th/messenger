from routes import resolve


def test_resolve(routes, controller):
    resolved = resolve('echo', routes=routes)
    assert resolved == controller


def test_resolve_none():
    resolved = resolve('not supported')
    assert resolved is None
