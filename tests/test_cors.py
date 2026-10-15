from api.main import parse_origins


def test_cleans_common_copy_paste_slips():
    raw = ' "https://haq-alpha.vercel.app/" , https://other.app ,, '
    assert parse_origins(raw) == ["https://haq-alpha.vercel.app", "https://other.app"]


def test_empty_is_empty():
    assert parse_origins("") == []
