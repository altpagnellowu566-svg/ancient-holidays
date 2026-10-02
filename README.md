# 繁體中文假日行事曆

可在 iPhone／Mac 行事曆直接訂閱的假日行事曆，節日名稱皆為繁體中文。

## 訂閱網址

古文明國家節日（埃及、伊拉克、印度合併）：

```
https://altpagnellowu566-svg.github.io/ancient-holidays/ancient-holidays.ics
```

台灣節慶假日：

```
https://altpagnellowu566-svg.github.io/ancient-holidays/taiwan-holidays.ics
```

iPhone：行事曆 App → 下方「行事曆」→ 左下「加入行事曆」→「加入訂閱行事曆」→ 貼上網址。

## 運作方式

- 資料來源：Google 日曆公開的埃及、伊拉克、印度、台灣節慶假日。
- `build.py` 下載各來源。三個古文明國家的節日名稱翻成繁體中文，同一天的相同節日合併成一筆，例如「開齋節（埃及、伊拉克）」；台灣的來源本身就是繁體中文，直接沿用。
- GitHub Actions 每週一自動重新產生，並發布到 GitHub Pages。
