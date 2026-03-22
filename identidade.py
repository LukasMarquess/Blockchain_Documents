from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization

def gerar_chaves():
    """Gera um par de chaves RSA."""
    privada = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    publica = privada.public_key()
    return privada, publica

def assinar_dados(chave_privada, dados_string):
    """Assina uma string de dados e retorna a assinatura em hexadecimal."""
    assinatura = chave_privada.sign(
        dados_string.encode(),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    return assinatura.hex()

def exportar_chave_publica(chave_publica):
    """Converte a chave pública para string PEM para enviar via JSON."""
    pem = chave_publica.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return pem.decode('utf-8')