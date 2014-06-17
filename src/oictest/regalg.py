__author__ = 'roland'

REGISTERED_JWS_ALGORITHMS = {
    "HS256": "Required",
    "HS384": "Optional",
    "HS512": "Optional",
    "RS256": "Recommended",
    "RS384": "Optional",
    "RS512": "Optional",
    "ES256": "Recommended+",
    "ES384": "Optional",
    "ES512": "Optional",
    "PS256": "Optional",
    "PS384": "Optional",
    "PS512": "Optional",
    "none": "Optional",
}

REGISTERED_JWE_alg_ALGORITHMS = {
    "RSA1_5": "Required",
    "RSA-OAEP": "Optional",
    "RSA-OAEP-256": "Optional",
    "A128KW": "Recommended",
    "A192KW": "Optional",
    "A256KW": "Recommended",
    "dir": "Recommended",
    "ECDH-ES": "Recommended+",
    "ECDH-ES+A128KW": "Recommended",
    "ECDH-ES+A192KW": "Optional",
    "ECDH-ES+A256KW": "Recommended",
    "A128GCMKW": "Optional",
    "A192GCMKW": "Optional",
    "A256GCMKW": "Optional",
    "PBES2-HS256+A128KW": "Optional",
    "PBES2-HS384+A192KW": "Optional",
    "PBES2-HS512+A256KW": "Optional"
}

REGISTERED_JWE_enc_ALGORITHMS = {
    "A128CBC-HS256": "Required",
    "A192CBC-HS384": "Optional",
    "A256CBC-HS512": "Required",
    "A128GCM": "Recommended",
    "A192GCM": "Optional",
    "A256GCM": "Recommended"
}

REGISTERED_ALGORITHMS = REGISTERED_JWS_ALGORITHMS.keys()
REGISTERED_ALGORITHMS.extend(REGISTERED_JWE_alg_ALGORITHMS.keys())
REGISTERED_ALGORITHMS.extend(REGISTERED_JWE_enc_ALGORITHMS.keys())

MTI_JWS_ALG = ["RS256", "none"]
MTI_JWE_ALG = []
MTI_JWE_ENC = ["A128CBC-HS256"]

# Self-issued OP request RSA1_5