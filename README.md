# HappyFlyData

HappyFly 明信片與飾品地點的公開更新資料。HappyFly 主程式維持在原本的私人儲存庫，本專案僅包含資料與發布工具。

## 更新資料

1. 更新 `sources/postcard-spots.json` 或 `sources/pure-points-category-updatable.json`，保留 `schemaVersion: 1`。
2. 明信片沿用同一個 `id`，避免影響使用者收藏；飾品類別可新增 `icon` 欄位指定 Emoji。
3. 提交到 `main`。GitHub Actions 的 **Publish catalogs** 會驗證資料並發布，不需要建置或更新 IPA。
4. 在 Actions 確認工作執行成功；版本清單在 `/catalog/manifest.json`。有無效座標、重複 ID 或遺失分類引用時，工作會失敗，原先發布版本繼續提供。

使用者需先安裝支援遠端更新的 HappyFly 新版。進入對應列表時，App 先顯示離線資料，並在檢查間隔到期時確認遠端版本。4.9（23）起，成功檢查後間隔五分鐘，失敗後一分鐘可再試；下載的新資料會在下次進入列表時套用。使用者不必自行匯入檔案。4.8 的間隔仍為六小時／十五分鐘，需安裝新版 App 才能縮短間隔。

只有這些資料會發布到 Pages，無須將 GitHub 存取金鑰放進 App。

## 本機驗證

```sh
python3 scripts/publish-catalogs.py --source-dir sources --output-dir _site
```

僅使用 Python 標準函式庫。生成的檔案有 SHA-256 與大小資訊，供 App 驗證。資料格式仍為 v1；新增不相容格式或 App 功能需要新版程式。復原錯誤更新時，將來源 JSON 還原到已知良好版本並提交即可。

明信片包含原始社群貼文來源及圖片網址；分類與座標不代表遊戲即時狀態，圖片網址可能過期。遠端更新不會自動蒐集來源資料，維護者仍須整理及更新 JSON。

## 首次部署

在 Settings → Pages 將 Source 設成 **GitHub Actions**，執行 **Publish catalogs**。正式版本清單：

https://bearbo888.github.io/HappyFlyData/catalog/manifest.json
