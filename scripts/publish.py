"""今日（日本時間）の投稿を Instagram にカルーセルで投稿する。
必要な環境変数: IG_USER_ID, IG_ACCESS_TOKEN, PAGES_BASE（例 https://ユーザー名.github.io/リポジトリ名）"""
import os, json, time, datetime, pathlib, shutil, sys, urllib.request, urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent
API = "https://graph.instagram.com/v23.0"
UID, TOKEN, BASE = os.environ["IG_USER_ID"], os.environ["IG_ACCESS_TOKEN"], os.environ["PAGES_BASE"].rstrip("/")

def call(method, path, **params):
    params["access_token"] = TOKEN
    data = urllib.parse.urlencode(params).encode()
    url = f"{API}/{path}"
    req = urllib.request.Request(url, data=data, method="POST") if method == "POST" else urllib.request.Request(url + "?" + data.decode())
    try:
        with urllib.request.urlopen(req, timeout=60) as r: return json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"API error {e.code}: {e.read().decode()}")

def wait_ready(cid):
    for _ in range(30):
        if call("GET", cid, fields="status_code").get("status_code") == "FINISHED": return
        time.sleep(5)
    sys.exit(f"container {cid} not ready")

def main():
    today = (datetime.datetime.utcnow() + datetime.timedelta(hours=9)).strftime("%Y-%m-%d")
    f = ROOT / "content" / "queue" / f"{today}.json"
    if not f.exists():
        print("今日の投稿はありません", today); return
    post = json.loads(f.read_text())
    n = len(post["slides"])
    if not 2 <= n <= 10: sys.exit("カルーセルは2〜10枚にしてください")
    children = []
    for i in range(1, n + 1):
        url = f"{BASE}/img/{today}/{i:02d}.jpg"
        c = call("POST", f"{UID}/media", image_url=url, is_carousel_item="true")["id"]
        children.append(c)
    for c in children: wait_ready(c)
    car = call("POST", f"{UID}/media", media_type="CAROUSEL", children=",".join(children), caption=post["caption"])["id"]
    wait_ready(car)
    res = call("POST", f"{UID}/media_publish", creation_id=car)
    print("投稿しました", today, res)
    shutil.move(str(f), ROOT / "content" / "posted" / f.name)

if __name__ == "__main__":
    main()
