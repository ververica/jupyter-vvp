from vvpmagics import VvpMagics


def test_connect_vvp_calls_namespaces_endpoint_if_none_given():
    magic_line = "localhost -p 8080"
    magics = VvpMagics()

    response = magics.connect_vvp(magic_line)

    assert not len(response['namespaces']) == 0


def test_connect_vvp_creates_session_if_namespace_given():
    magic_line = "localhost -n default"
    magics = VvpMagics()

    session = magics.connect_vvp(magic_line)

    assert session.get_namespace() == "default"

