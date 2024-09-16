import qrcode
import pyotp
key = "AMAROWENFAITHKHALIDCONRADJIMJOHNWILLY"

uri = pyotp.totp.TOTP(key).provisioning_uri(name="Agri-Soko", issuer_name="OTP")
print(uri)


try:
    totp = pyotp.TOTP(key)
    hotp = pyotp.HOTP(key)
    qrcode.make(uri).save("Agri-Soko.png")
    print("QR code generated successfully.")
except Exception as e:
    print("Error generating QR code:", e)
