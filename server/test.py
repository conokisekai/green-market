import http.client
import json

conn = http.client.HTTPSConnection("e19152.api.infobip.com")
payload = json.dumps(
    {
        "messages": [
            {
                "destinations": [
                    {"to": "254768171426"},
                    {"to": "254721601031"},
                    {"to": "254707707863"},
                ],
                "from": "ServiceSMS",
                "text": "Hello,\n\nThis is a test message from Infobip. Have a nice day!",
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
print(data.decode("utf-8"))
