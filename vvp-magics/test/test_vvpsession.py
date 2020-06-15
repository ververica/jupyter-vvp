from vvpmagics import VvpMagics


def test_get_namespace_returns_namespace():
    namespace = "default"
    magic_line = "localhost -n {}".format(namespace)
    magics = VvpMagics()

    session = magics.connect_vvp(magic_line)

    assert session.get_namespace() == "default"


def test_get_namespace_info_returns_namespace():
    namespace = "default"
    magic_line = "localhost -n {}".format(namespace)
    magics = VvpMagics()

    session = magics.connect_vvp(magic_line)

    assert session.get_namespace_info()['name'] == "namespaces/default"
