"""今日（日本時間）の投稿を Instagram にカルーセルで投稿する。
必要な環境変数: IG_ACCESS_TOKEN, PAGES_BASE（例 https://ユーザー名.github.io/リポジトリ名）
任意: IG_USER_ID（未設定なら自動で探す）, IG_API_HOST（既定 graph.facebook.com。Instagramログインのトークンなら graph.instagram.com）"""
import os, json, time, datetime, pathlib, shutil, sys, urllib.request, urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent
API = f"https://{os.environ.get('IG_API_HOST') or 'graph.facebook.com'}/v23.0"
TOKEN = os.environ["IG_ACCESS_TOKEN"]
BASE = os.environ.get("PAGES_BASE", "").rstrip("/")
UID = os.environ.get("IG_USER_ID", "")

def call(method, path, **params):
    params["access_token"] = TOKEN
    data = urllib.parse.urlencode(params).encode()
    url = f"{API}/{path}"
    req = urllib.request.Request(url, data=data, method="POST") if method == "POST" else urllib.request.Request(url + "?" + data.decode())
    try:
        with urllib.request.urlopen(req, timeout=60) as r: return json.load(r)
    except urllib.error.HTTPError as e:
        msg = f"API error {e.code}: {e.read().decode()[:500]}"
        print(f"::error::{msg}")
        sys.exit(msg)

def find_accounts():
    """このトークンで投稿できる Instagram アカウントを探す"""
    found = {}
    def get(path, **p):
        try: return call("GET", path, **p)
        except SystemExit as e:
            print(f"  ({path}: {str(e)[:200]})"); return {}
    for pg in get("me/accounts", fields="name,instagram_business_account{id,username}").get("data", []):
        ig = pg.get("instagram_business_account")
        if ig: found[ig["id"]] = ig.get("username", "")
    for b in get("me/businesses", fields="id,name").get("data", []):
        for edge in ("owned_instagram_accounts", "instagram_accounts"):
            for ig in get(f"{b['id']}/{edge}", fields="id,username").get("data", []):
                found[ig["id"]] = ig.get("username", "")
    if not found and "graph.instagram.com" in API:
        me = get("me", fields="user_id,username")
        if me: found[me.get("user_id") or me.get("id")] = me.get("username", "")
    return found

def wait_ready(cid):
    for _ in range(30):
        if call("GET", cid, fields="status_code").get("status_code") == "FINISHED": return
        time.sleep(5)
    sys.exit(f"container {cid} not ready")

def main():
    global UID
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        if UID:
            print("IG_USER_ID で確認:", call("GET", UID, fields="id,username"))
            return
        accts = find_accounts()
        print("投稿できるInstagramアカウント:", accts or "見つかりません（トークンの権限・割り当てを確認）")
        return
    if not UID:
        accts = find_accounts()
        if len(accts) != 1: print("::error::Instagramアカウントを特定できません"); sys.exit(f"Instagramアカウントを特定できません: {accts}。IG_USER_ID を登録してください")
        UID = next(iter(accts))
    today = (datetime.datetime.utcnow() + datetime.timedelta(hours=9)).strftime("%Y-%m-%d")
    f = ROOT / "content" / "queue" / f"{today}.json"
    if not f.exists():
        print("今日の投稿はありません", today); return
    post = json.loads(f.read_text())
    # 二重投稿の防止：直近の投稿に同じキャプションがあれば投稿済みとみなす
    head = post["caption"][:40]
    recent = call("GET", f"{UID}/media", fields="caption,timestamp", limit="5").get("data", [])
    if any((m.get("caption") or "").startswith(head) for m in recent):
        print("すでに投稿済みです", today)
        (ROOT / "content" / "posted").mkdir(parents=True, exist_ok=True)
        shutil.move(str(f), ROOT / "content" / "posted" / f.name)
        return
    n = len(post["slides"])
    if not 2 <= n <= 10:
        print("::error::カルーセルは2〜10枚にしてください"); sys.exit(1)
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
    (ROOT / "content" / "posted").mkdir(parents=True, exist_ok=True)
    shutil.move(str(f), ROOT / "content" / "posted" / f.name)

if __name__ == "__main__":
    main()
