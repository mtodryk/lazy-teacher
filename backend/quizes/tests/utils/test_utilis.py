import re
import uuid
import pytest
from quizes.utils import generate_share_code

def test_generate_share_code_format():
    code = generate_share_code(42)
    assert code.startswith("quiz-42-")
    assert re.fullmatch(r"quiz-42-[0-9a-f]{8}", code)

def test_generate_share_code_uniqueness():
    c1 = generate_share_code(7)
    c2 = generate_share_code(7)
    assert c1 != c2

def test_generate_share_code_uses_uuid(monkeypatch):
    monkeypatch.setattr(uuid, "uuid4", lambda: uuid.UUID("12345678-1234-5678-1234-567812345678"))
    assert generate_share_code(5) == "quiz-5-12345678"