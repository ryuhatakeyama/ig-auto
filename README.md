# Instagram カルーセル自動投稿

畠山龍｜建設会社の採用SNS のカルーセル投稿を、毎日 日本時間 7:07 に自動で投稿する仕組みです。

## 全体の流れ
1. 毎週土曜：Claude が翌週7本分の投稿データ（`content/queue/日付.json`）を作って追加する
2. 追加されると：GitHub Actions がスライド画像（1080×1350 の JPEG）を自動で作る → `docs/img/日付/`
3. 画像は GitHub Pages で公開される（Instagram の API は公開URLの画像しか受け付けないため）
4. 毎朝 7:07：GitHub Actions がその日のデータを Instagram にカルーセル投稿し、`content/posted/` に移す
5. 毎月1日・15日：Instagram のアクセストークン（有効期限60日）を自動で延長する

投稿を止めたい日があれば、`content/queue/` からその日のファイルを消すだけです。
内容を直したいときは、そのファイルの文字を書き換えて保存すれば画像も作り直されます。

## フォルダ
- `content/queue/` これから投稿するもの（1日1ファイル）
- `content/posted/` 投稿済み
- `docs/img/` 自動で作られる画像
- `scripts/render.py` 画像を作る
- `scripts/publish.py` Instagram に投稿する
- `CONTENT_RULES.md` 投稿づくりのルール（毎週の自動作成で使う）

## 最初の設定
`設定手順.md` を見てください。
