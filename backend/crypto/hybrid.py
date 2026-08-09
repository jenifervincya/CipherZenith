"""
Backend wrapper for the CipherZenith cryptography module.
"""

from cipherzenith_crypto.hybrid.hybrid_scheme import (
    encrypt,
    switch_algorithm,
)

from cipherzenith_crypto.pqc.dilithium import (
    sign_transaction,
    verify_transaction,
)

__all__ = [
    "encrypt",
    "switch_algorithm",
    "sign_transaction",
    "verify_transaction",
]