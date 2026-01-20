def test_utf8_roundtrip():
    text = "مرحبا 🚀"
    encoded = text.encode("utf-8")
    decoded = encoded.decode("utf-8")
    assert decoded == text
