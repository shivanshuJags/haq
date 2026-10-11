"""US-203: keep sensitive identifiers out of the system.

Haq never needs ID numbers to check eligibility. If someone types one anyway,
we replace it before the text goes anywhere (model, logs), and tell them.
"""
import re

PATTERNS = {
    # Aadhaar: 12 digits, often written as 1234 5678 9012
    "Aadhaar number": re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"),
    # PAN: 5 letters, 4 digits, 1 letter
    "PAN number": re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b", re.IGNORECASE),
    # UK National Insurance number: 2 letters, 6 digits, 1 letter A-D.
    # Deliberately loose on the letters: better to hide a mistyped number than leak a real one.
    "National Insurance number": re.compile(r"\b[A-Z]{2}\s?\d{2}\s?\d{2}\s?\d{2}\s?[A-D]\b", re.IGNORECASE),
    # Bank account / card numbers: 13+ digits in a row
    "account or card number": re.compile(r"\b\d{13,19}\b"),
}


def redact(text: str) -> tuple[str, list[str]]:
    """Return the text with ID numbers replaced, plus the names of what was removed."""
    removed = []
    for label, pattern in PATTERNS.items():
        text, count = pattern.subn(f"[{label} removed]", text)
        if count:
            removed.append(label)
    return text, removed
