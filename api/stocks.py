from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            import yfinance as yf
            df = yf.download("7203.T", period="1mo", auto_adjust=True, progress=False)
            result = {"rows": len(df), "columns": list(df.columns) if not df.empty else [], "empty": df.empty}
            if not df.empty:
                last = df.iloc[-1]
                result["last"] = {"close": round(float(last["Close"])), "date": str(df.index[-1].date())}
            self.send_response(200)
            self.send_header("Content-Type","application/json")
            self.send_header("Access-Control-Allow-Origin","*")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
        except Exception as ex:
            self.send_response(200)
            self.send_header("Content-Type","application/json")
            self.send_header("Access-Control-Allow-Origin","*")
            self.end_headers()
            self.wfile.write(json.dumps({"error":str(ex),"type":type(ex).__name__}).encode())
