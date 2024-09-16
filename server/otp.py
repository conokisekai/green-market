import pyotp

key = "AMAROWENFAITHKHALIDCONRADJIMJOHNWILLY"
totp = pyotp.TOTP(key)
hotp = pyotp.HOTP(key)


while True:
    code = input("Enter code: ")
    if totp.verify(code):
        print("Access granted")
        break
    else:
        print("Access denied")


