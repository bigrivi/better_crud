from passlib.context import CryptContext
pwd_context = CryptContext(schemes=['bcrypt'])


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_hashed_password(plain_password:str)->str:
    return pwd_context.hash(plain_password)