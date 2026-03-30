import uuid


def generate_share_code(document_id: int) -> str:
    """Generate a unique share code for a quiz.
    Format: quiz-{document_id}-{random_hex}
    """
    return f"quiz-{document_id}-{uuid.uuid4().hex[:8]}"
