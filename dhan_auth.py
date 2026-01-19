# dhan_auth.py

# -------------------------------------------------
# DHAN AUTH CONFIG
# -------------------------------------------------

ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzY4ODgzMzc1LCJpYXQiOjE3Njg3OTY5NzUsInRva2VuQ29uc3VtZXJUeXBlIjoiU0VMRiIsIndlYmhvb2tVcmwiOiIiLCJkaGFuQ2xpZW50SWQiOiIxMTAxNDI2NjY0In0.8sozms12KIV6f_gOsNhX4AgHiwrSH9_c5W_IOdSlzTwPi9adXwQZx1AS5fpX4vMNfaUoem3nEv_0KC9AoSTavQ"   # 🔴 paste your Dhan access token here
CLIENT_ID = "1101426664"  # your Dhan client ID

# -------------------------------------------------
# HEADER BUILDER
# -------------------------------------------------
def get_dhan_headers():
    return {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "access-token": ACCESS_TOKEN,
        "client-id": CLIENT_ID
    }
