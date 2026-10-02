# 古文明國家節日（埃及・伊拉克・印度）

把埃及、伊拉克、印度三國的國定假日與節慶合併成一份行事曆，節日名稱為繁體中文，可在 iPhone／Mac 行事曆直接訂閱。

## 訂閱網址

```
https://altpagnellowu566-svg.github.io/ancient-holidays/ancient-holidays.ics
```

iPhone：行事曆 App → 下方「行事曆」→ 左下「加入行事曆」→「加入訂閱行事曆」→ 貼上網址。

## 運作方式

- 資料來源：Google 日曆公開的埃及、伊拉克、印度節慶假日。
- `build.py` 下載三份來源，把節日名稱翻成繁體中文，同一天的相同節日合併成一筆，例如「開齋節（埃及、伊拉克）」。
- GitHub Actions 每週一自動重新產生，並發布到 GitHub Pages。
