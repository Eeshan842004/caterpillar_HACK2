from shiftmate.security.pin import hash_pin, verify_pin


def test_pin_parity_vector():
    pin = "1234"
    salt = "000102030405060708090a0b0c0d0e0f"
    expected_hex = "dfada071ff247e6bec37736dbed1ba93a58af89aa081176a1a026cac038223be"

    calc = hash_pin(pin, salt, iterations=20000)
    assert calc == expected_hex
    assert verify_pin(pin, salt, expected_hex, iterations=20000)
    assert not verify_pin("9999", salt, expected_hex, iterations=20000)
