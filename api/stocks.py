"""
Vercel Serverless: 日本株データ取得API（150銘柄対応・高速版）
"""
from http.server import BaseHTTPRequestHandler
import json
import yfinance as yf
from datetime import datetime
import traceback

TICKER_NAMES = {
    "7203":"トヨタ","6758":"ソニーG","9984":"ソフトバンクG","8306":"三菱UFJ","6861":"キーエンス",
    "4063":"信越化学","6501":"日立","7974":"任天堂","8035":"東京エレクトロン","6723":"ルネサス",
    "4519":"中外製薬","6594":"ニデック","6367":"ダイキン","4568":"第一三共","7741":"HOYA",
    "6981":"村田製作所","9433":"KDDI","9432":"NTT","6902":"デンソー","3382":"セブン&i",
    "8058":"三菱商事","6098":"リクルート","4661":"OLC","2802":"味の素","6762":"TDK",
    "7267":"ホンダ","9983":"ファストリ","6857":"アドバンテスト","4543":"テルモ","7751":"キヤノン",
    "8031":"三井物産","8001":"伊藤忠","8766":"東京海上","8411":"みずほFG","8316":"三井住友FG",
    "9434":"ソフトバンク","6326":"クボタ","4503":"アステラス","4502":"武田薬品","6971":"京セラ",
    "7832":"バンナムHD","3659":"ネクソン","4578":"大塚HD","6301":"コマツ","7269":"スズキ",
    "5108":"ブリヂストン","6504":"富士電機","6702":"富士通","6752":"パナソニック","7011":"三菱重工",
    "8015":"豊田通商","9020":"JR東日本","9021":"JR西日本","9022":"JR東海","2914":"JT",
    "3086":"Jフロント","3099":"三越伊勢丹","4452":"花王","4901":"富士フイルム","5401":"日本製鉄",
    "5713":"住友金属鉱","5802":"住友電工","6103":"オークマ","6273":"SMC","6305":"日立建機",
    "6479":"ミネベアミツミ","6506":"安川電機","6586":"マキタ","6645":"オムロン","6701":"NEC",
    "6724":"セイコーエプソン","6753":"シャープ","6758":"ソニーG","6841":"横河電機","6869":"シスメックス",
    "6920":"レーザーテック","6952":"カシオ","6954":"ファナック","6976":"太陽誘電","7012":"川崎重工",
    "7013":"IHI","7201":"日産","7211":"三菱自","7261":"マツダ","7270":"SUBARU",
    "7272":"ヤマハ発","7309":"シマノ","7731":"ニコン","7733":"オリンパス","7735":"SCREENホールディングス",
    "7752":"リコー","7762":"シチズン","7911":"凸版","7912":"大日本印刷","7951":"ヤマハ",
    "8002":"丸紅","8053":"住友商事","8113":"ユニ・チャーム","8233":"高島屋","8252":"丸井G",
    "8267":"イオン","8303":"新生銀","8308":"りそなHD","8309":"三井住友トラスト","8354":"ふくおかFG",
    "8591":"オリックス","8601":"大和証券G","8604":"野村HD","8630":"SOMPO","8725":"MS&AD",
    "8750":"第一生命","8795":"T&DHD","9001":"東武鉄道","9005":"東急","9007":"小田急",
    "9008":"京王","9009":"京成","9064":"ヤマトHD","9101":"日本郵船","9104":"商船三井",
    "9107":"川崎汽船","9143":"SGHD","9201":"JAL","9202":"ANA","9301":"三菱倉庫",
    "9501":"東京電力","9502":"中部電力","9503":"関西電力","9531":"東京ガス","9532":"大阪ガス",
    "9602":"東宝","9613":"NTTデータ","9735":"セコム","9766":"コナミG","9843":"ニトリHD",
    "2413":"エムスリー","2502":"アサヒGHD","2503":"キリンHD","2801":"キッコーマン",
    "3038":"神戸物産","3092":"ZOZO","3288":"オープンハウス","3349":"コスモス薬品",
    "3405":"クラレ","3407":"旭化成","3436":"SUMCO","4004":"昭和電工","4005":"住友化学",
    "4021":"日産化学","4042":"東ソー","4043":"トクヤマ","4151":"協和キリン","4183":"三井化学",
    "4188":"三菱ケミカル","4307":"NRI","4385":"メルカリ","4507":"塩野義","4523":"エーザイ",
    "4612":"日本ペイント","4631":"DIC","4684":"オービック","4689":"Zホールディングス",
    "4911":"資生堂","4922":"コーセー","5019":"出光興産","5020":"ENEOS","5101":"横浜ゴム",
}

ALL_TICKERS = list(TICKER_NAMES.keys())

def fetch_batch(tickers, period="6mo"):
    symbols = " ".join([t + ".T" for t in tickers])
    try:
        df = yf.download(symbols, period=period, auto_adjust=True, threads=True, progress=False)
        if df.empty:
            return []
    except Exception:
        return []

    results = []
    for tk in tickers:
        sym = tk + ".T"
        try:
            if len(tickers) == 1:
                sub = df
            else:
                sub = df.xs(sym, axis=1, level=1) if hasattr(df.columns, 'levels') else df

            records = []
            for idx, row in sub.iterrows():
                try:
                    c = float(row["Close"])
                    if c != c:
                        continue
                    records.append({
                        "date": idx.strftime("%Y-%m-%d"),
                        "open": round(float(row["Open"])),
                        "high": round(float(row["High"])),
                        "low": round(float(row["Low"])),
                        "close": round(c),
                        "volume": int(float(row["Volume"])) if row["Volume"] == row["Volume"] else 0,
                    })
                except Exception:
                    continue

            if len(records) > 30:
                results.append({
                    "ticker": tk,
                    "name": TICKER_NAMES.get(tk, tk),
                    "data": records,
                })
        except Exception:
            continue

    return results


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            from urllib.parse import urlparse, parse_qs
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)

            tickers_param = params.get("tickers", [None])[0]
            period = params.get("period", ["6mo"])[0]
            batch_idx = params.get("batch", [None])[0]

            if tickers_param:
                tickers = [t.strip() for t in tickers_param.split(",")]
            elif batch_idx is not None:
                idx = int(batch_idx)
                batch_size = 50
                start = idx * batch_size
                tickers = ALL_TICKERS[start:start + batch_size]
            else:
                tickers = ALL_TICKERS[:50]

            results = fetch_batch(tickers, period)

            response = {
                "stocks": results,
                "count": len(results),
                "total_available": len(ALL_TICKERS),
                "period": period,
                "timestamp": datetime.now().isoformat(),
                "tickerNames": TICKER_NAMES,
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
            self.wfile.write(json.dumps({"error": str(e), "trace": traceback.format_exc()}).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
