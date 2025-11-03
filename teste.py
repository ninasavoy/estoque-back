import jwt

SECRET_KEY = "chave-secreta"
ALGORITHM = "HS256"
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOjMsImV4cCI6MTc2MTM1NzA1MX0.cEFTyOcDXEboMAIA1BT71f-K-UETIb8AgWCkQihZCzA"

print(jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM]))