import http.client
import json
import pyotp


def send_otp(phone_number, username):
    print("Sending OTP...")  # Add this line for debugging
    key = "AMAROWENFAITHKHALIDCONRADJIMJOHNWILLY"
    totp = pyotp.TOTP(key)
    conn = http.client.HTTPSConnection("e19152.api.infobip.com")

    payload = json.dumps(
        {
            "messages": [
                {
                    "destinations": [{"to": phone_number}],
                    "from": "ServiceSMS",
                    "text": f"Agri-Soko 🥀,\n\nThis is a message from Agri-Soko Team 👨‍🌾 \n\n{username}, your OTP is {totp.now()}.",
                }
            ]
        }
    )

    headers = {
        "Authorization": "App 2cdd8a8afd40c31fa397de1f62cf2828-a39ba047-59d6-42da-bfb1-dca953d0032c",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    conn.request("POST", "/sms/2/text/advanced", payload, headers)
    res = conn.getresponse()
    data = res.read()
    print(data.decode("utf-8"))  # Print response for debugging
