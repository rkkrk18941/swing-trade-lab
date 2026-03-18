from http.server import BaseHTTPRequestHandler
import json

NAMES = {
    "7203":"トヨタ","6758":"ソニーG","9984":"ソフトバンクG","8306":"三菱UFJ","6861":"キーエンス",
    "4063":"信越化学","6501":"日立","7974":"任天堂","8035":"東京エレクトロン","6723":"ルネサス",
    "4519":"中外製薬","6594":"ニデック","6367":"ダイキン","4568":"第一三共","7741":"HOYA",
    "6981":"村田製作所","9433":"KDDI","9432":"NTT","6902":"デンソー","3382":"セブン&i",
    "8058":"三菱商事","6098":"リクルート","4661":"OLC","2802":"味の素","6762":"TDK",
    "7267":"ホンダ","9983":"ファストリ","6857":"アドバンテスト","4543":"テルモ","7751":"キヤノン",
    "8031":"三井物産","8001":"伊藤忠","8766":"東京海上","8411":"みずほFG","8316":"三井住友FG",
    "9434":"ソフトバンク","6326":"クボタ","4503":"アステラス","4502":"武田薬品","6971":"京セラ",
    "7832":"バンナムHD","4578":"大塚HD","6301":"コマツ","7269":"スズキ","5108":"ブリヂストン",
    "6504":"富士電機","6702":"富士通","6752":"パナソニック","7011":"三菱重工","8015":"豊田通商",
    "9020":"JR東日本","9022":"JR東海","2914":"JT","4452":"花王","4901":"富士フイルム",
    "5401":"日本製鉄","6273":"SMC","6506":"安川電機","6645":"オムロン","6701":"NEC",
    "6920":"レーザーテック","6954":"ファナック","6976":"太陽誘電","7012":"川崎重工","7013":"IHI",
    "7201":"日産","7270":"SUBARU","7733":"オリンパス","7951":"ヤマハ","8002":"丸紅",
    "8053":"住友商事","8267":"イオン","8591":"オリックス","8604":"野村HD","8630":"SOMPO",
    "8750":"第一生命","9101":"日本郵船","9104":"商船三井","9107":"川崎汽船","9201":"JAL",
    "9202":"ANA","9501":"東京電力","9613":"NTTデータ","9735":"セコム","9843":"ニトリHD",
    "2413":"エムスリー","2502":"アサヒGHD","2503":"キリンHD","4385":"メルカリ","4507":"塩野義",
    "4523":"エーザイ","4911":"資生堂","5020":"ENEOS","9766":"コナミG","3407":"旭化成",
    "4021":"日産化学","4307":"NRI","4684":"オービック","3038":"神戸物産","3092":"ZOZO",
}

ALL = list(NAMES.keys())

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            import yfinance as yf
            from urllib.parse import urlparse, parse_qs
            params = parse_qs(urlparse(self.path).query)
            
            bi = int(params.get("batch",["0"])[0])
            sz = 10
            tickers = ALL[bi*sz:(bi+1)*sz]
            
            if not tickers:
                self._ok({"stocks":[],"batch":bi})
                return

            syms = " ".join([t+".T" for t in tickers])
            df = yf.download(syms, period="6mo", auto_adjust=True, threads=True, progress=False)
            
            stocks = []
            for tk in tickers:
                try:
                    if len(tickers)==1:
                        sub=df
                    else:
                        sub=df.xs(tk+".T",axis=1,level=1)
                    rows=[]
                    for idx,row in sub.iterrows():
                        c=float(row["Close"])
                        if c!=c: continue
                        rows.append({"date":idx.strftime("%Y-%m-%d"),"open":round(float(row["Open"])),"high":round(float(row["High"])),"low":round(float(row["Low"])),"close":round(c),"volume":int(float(row.get("Volume",0))) if row.get("Volume",0)==row.get("Volume",0) else 0})
                    if len(rows)>20:
                        stocks.append({"ticker":tk,"name":NAMES.get(tk,tk),"data":rows})
                except: pass
            
            self._ok({"stocks":stocks,"batch":bi,"total":len(ALL),"batches":(len(ALL)+sz-1)//sz})
        except Exception as ex:
            self.send_response(500)
            self.send_header("Content-Type","application/json")
            self.send_header("Access-Control-Allow-Origin","*")
            self.end_headers()
            self.wfile.write(json.dumps({"error":str(ex)}).encode())

    def _ok(self,data):
        self.send_response(200)
        self.send_header("Content-Type","application/json")
        self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Cache-Control","s-maxage=3600, stale-while-revalidate=86400")
        self.end_headers()
        self.wfile.write(json.dumps(data,ensure_ascii=False).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Access-Control-Allow-Methods","GET, OPTIONS")
        self.end_headers()
