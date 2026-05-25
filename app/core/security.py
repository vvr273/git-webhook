import hashlib
import hmac


def verify_github_signature(raw_body: bytes, signature_header: str | None, secret: str) -> bool:
    if not signature_header or not signature_header.startswith("sha256="):
        return False

    provided_signature = signature_header.split("=", 1)[1]
    expected_signature = hmac.new(
        secret.encode("utf-8"),
        msg=raw_body,
        digestmod=hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(provided_signature, expected_signature)
