from protocol import (
    validate_request,
    validate_action,
    make_response
)


# testing 'validate_request' function
def test_validate_valid_request(valid_request):
    assert validate_request(valid_request) is True


def test_validate_invalid_request(invalid_request):
    assert validate_request(invalid_request) is False


# testing 'validate_action' function
def test_validate_valid_action(valid_request):
    assert validate_action(valid_request) is True


def test_validate_invalid_action(invalid_action_request):
    assert validate_action(invalid_action_request) is False


# testing 'make_response' function
def test_make_response(
    valid_request,
    success_code,
    valid_response
):
    response = make_response(
        valid_request,
        success_code,
        data=valid_request.get('data')
    )

    assert response.get('action') == valid_response.get('action')
    assert response.get('data') == valid_response.get('data')
    assert response.get('user') == valid_response.get('user')
