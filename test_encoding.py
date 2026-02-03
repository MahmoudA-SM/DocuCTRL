def test_utf8_roundtrip():
    text = "\u0645\u0631\u062d\u0628\u0627 \U0001F30D \u2014 \u0627\u062e\u062a\u0628\u0627\u0631"
    encoded = text.encode("utf-8")
    decoded = encoded.decode("utf-8")
    assert decoded == text