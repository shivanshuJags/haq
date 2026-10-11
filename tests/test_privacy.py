from core.privacy import redact


def test_removes_aadhaar_with_spaces():
    text, removed = redact("Mera aadhaar 1234 5678 9012 hai")
    assert "1234" not in text
    assert removed == ["Aadhaar number"]


def test_removes_uk_national_insurance_number():
    text, removed = redact("My NI number is QQ 12 34 56 C")
    assert "12 34 56" not in text
    assert "National Insurance number" in removed


def test_removes_pan():
    text, removed = redact("PAN: ABCDE1234F")
    assert "ABCDE1234F" not in text
    assert removed == ["PAN number"]


def test_keeps_normal_numbers():
    # Ages, incomes and years must survive — we need them for eligibility
    message = "Main 20 saal ki hoon, income 150000 hai, 2024 mein admission liya"
    text, removed = redact(message)
    assert text == message
    assert removed == []
