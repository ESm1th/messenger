from routes import resolve


def test_resolve():
    routes = [
        {'action': 'make_string', 'controller': str()},
    ]
    controller = resolve('make_string', routes=routes)
    assert controller is str()


def test_resolve_none():
    controller = resolve('not supported')
    assert controller is None
