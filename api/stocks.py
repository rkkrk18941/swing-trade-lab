"""
Vercel Serverless Function: 日本株データ取得API
yfinanceを使って株価データを返す
"""
from http.server import BaseHTTPRequestHandler
import json
import yfinance as yf
from datetime import datetime, timedelta
import traceback

# 主要銘柄リスト（東証コード → yfinance形式）
DEFAULT_TICKERS = [
    "7203","6758","9984","8306","6861","4063","6501","7974",
    "8035","6723","4519","6594","6367","4568","7741","6981",
    "9433","9432","6902","3382","8058","6098","4661","2802",
    "6762","7267","9983","6857","4543","7751",
]

TICKER_NAMES = {
    "7203":"トヨタ自動車","6758":"ソニーG","9984":"ソフトバンクG",
    "8306":"三菱UFJFG","6861":"キーエンス","4063":"信越化学",
    "6501":"日立製作所","7974":"任天堂","8035":"東京エレクトロン",
    "6723":"ルネサス","4519":"中外製薬","6594":"日本電産",
    "6367":"ダイキン工業","4568":"第一三共","7741":"HOYA",
    "6981":"村田製作所","9433":"KDDI","9432":"NTT",
    "6902":"デンソー","3382":"セブン&iHD","8058":"三菱商事",
    "6098":"リクルートHD","4661":"OLC","2802":"味の素",
    "6762":"TDK","7267":"ホンダ","9983":"ファーストリテイリング",
    "6857":"アドバンテスト","4543":"テルモ","7751":"キヤノン",
}

def fetch_stock_data(ticker_code, period="1y"):
    """1銘柄の株価データを取得"""
    symbol = f"{ticker_code}.T"
    try:
        tk = yf.Ticker(symbol)
        df = tk.history(period=period, auto_adjust=True)
        if df.empty:
            return None
        
        records = []
        for idx, row in df.iterrows():
            records.append({
                "date": idx.strftime("%Y-%m-%d"),
                "open": round(row["Open"]),
                "high": round(row["High"]),
                "low": round(row["Low"]),
                "close": round(row["Close"]),
                "volume": int(row["Volume"]),
            })
        
        return {
            "ticker": ticker_code,
            "name": TICKER_NAMES.get(ticker_code, ticker_code),
            "data": records,
            "lastUpdate": datetime.now().isoformat(),
        }
    except Exception as e:
        return {"ticker": ticker_code, "error": str(e), "data": []}


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """GET /api/stocks?tickers=7203,6758&period=1y"""
        try:
            # Parse query params
            from urllib.parse import urlparse, parse_qs
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)
            
            tickers_param = params.get("tickers", [None])[0]
            period = params.get("period", ["1y"])[0]
            
            if tickers_param:
                tickers = [t.strip() for t in tickers_param.split(",")]
            else:
                tickers = DEFAULT_TICKERS
            
            # Limit to prevent timeout (Vercel has 10s limit on free)
            tickers = tickers[:10]
            
            results = []
            for tk in tickers:
                data = fetch_stock_data(tk, period)
                if data:
                    results.append(data)
            
            response = {
                "stocks": results,
                "count": len(results),
                "period": period,
                "timestamp": datetime.now().isoformat(),
                "tickerNames": TICKER_NAMES,
                "availableTickers": DEFAULT_TICKERS,
            }
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
            self.send_header("Cache-Control", "s-maxage=3600, stale-while-revalidate=86400")
            self.end_headers()
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode("utf-8"))
            
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            error_resp = {"error": str(e), "trace": traceback.format_exc()}
            self.wfile.write(json.dumps(error_resp).encode("utf-8"))
    
    def do_OPTIONS(self):
        """CORS preflight"""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
