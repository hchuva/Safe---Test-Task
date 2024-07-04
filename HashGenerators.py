import hashlib

# Hash generators for different algorithms

class MD5Generator:

    @staticmethod
    def hashFile(data: str):
        return hashlib.md5(data.encode()).hexdigest()

class SHA256Generator:

    @staticmethod
    def hashFile(data: str):
        return hashlib.sha256(data.encode()).hexdigest()

class SHA512Generator:

    @staticmethod
    def hashFile(data: str):
        return hashlib.sha512(data.encode()).hexdigest()