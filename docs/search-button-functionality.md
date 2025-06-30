# 検索ボタン機能ドキュメント

## 概要
Social Listening Dashboardの検索ボタン（🔍 検索）の詳細な機能仕様書です。

## 基本情報
- **ボタンID**: なし（onclick属性で直接関数呼び出し）
- **ボタンクラス**: `btn-search`
- **トリガー関数**: `loadData()`
- **配置場所**: 分析コントロールセクション内
- **ボタンテキスト**: "🔍 データ検索"
- **視覚的識別**: 緑グラデーション、ホバー時の影とアニメーション

## 機能詳細

### 1. メイン機能
検索ボタンをクリックすると、`loadData()` 関数が実行され、以下の4つの処理が並列で実行されます：

1. **感情分析サマリーの読み込み** (`loadSentimentSummary()`)
2. **投稿データの読み込み** (`loadPosts()`)
3. **チャートデータの更新** (`loadCharts()`)
4. **トレンドトピックの読み込み** (`loadTrendingTopics()`)

### 2. 検索パラメータ

#### 取得される入力値
- **キーワード**: `keywordInput` フィールドの値
- **プラットフォーム**: `platformSelect` の選択値
- **感情フィルター**: `sentimentSelect` の選択値

#### パラメータの処理
```javascript
const keyword = document.getElementById('keywordInput').value;
const platform = document.getElementById('platformSelect').value;
const sentiment = document.getElementById('sentimentSelect').value;
```

### 3. API呼び出し

#### 3.1 感情分析サマリー API
- **エンドポイント**: `/api/v1/sentiment/summary`
- **デフォルトパラメータ**: `days=7`
- **追加パラメータ**:
  - `keywords`: キーワードが入力されている場合
  - `platform`: プラットフォームが選択されている場合

```javascript
let url = '/api/v1/sentiment/summary?days=7';
if (keyword) url += `&keywords=${encodeURIComponent(keyword)}`;
if (platform) url += `&platform=${platform}`;
```

#### 3.2 投稿データ API
- **エンドポイント**: `/api/v1/posts`
- **デフォルトパラメータ**: `limit=20`
- **追加パラメータ**:
  - `keyword`: キーワードが入力されている場合
  - `platform`: プラットフォームが選択されている場合
  - `sentiment`: 感情フィルターが選択されている場合

```javascript
let url = '/api/v1/posts?limit=20';
if (keyword) url += `&keyword=${encodeURIComponent(keyword)}`;
if (platform) url += `&platform=${platform}`;
if (sentiment) url += `&sentiment=${sentiment}`;
```

#### 3.3 トレンドトピック API
- **エンドポイント**: `/api/v1/trending-topics`
- **パラメータ**: 
  - `days`: `trendingDays` セレクトボックスの値
  - `limit=10`: 固定値

### 4. UI更新

#### 4.1 統計カードの更新
- **総投稿数**: `totalPosts` 要素
- **ポジティブ投稿**: `positivePosts` 要素 + パーセンテージ
- **ネガティブ投稿**: `negativePosts` 要素 + パーセンテージ
- **ニュートラル投稿**: `neutralPosts` 要素 + パーセンテージ

#### 4.2 投稿テーブルの更新
- **テーブル**: `postsTableBody` 要素
- **表示項目**: プラットフォーム、内容、投稿者、感情、日時
- **最大表示件数**: 20件

#### 4.3 チャートの更新
- **感情分布チャート**: ドーナツチャート形式
- **プラットフォーム別チャート**: 積み上げ棒グラフ形式

#### 4.4 トレンドトピックの更新
- **表示形式**: カード形式
- **表示情報**: トピック名、言及数、プラットフォーム、感情分布、トレンドスコア

### 5. 自動実行タイミング

#### 5.1 ページ読み込み時
```javascript
document.addEventListener('DOMContentLoaded', function() {
    setupEventListeners();
    loadData(); // 初回実行
    setInterval(loadData, 30000); // 30秒間隔で自動更新
});
```

#### 5.2 Enterキー押下時
```javascript
function handleKeyPress(event) {
    if (event.key === 'Enter') {
        loadData();
    }
}
```

#### 5.3 フィルター変更時
- プラットフォーム選択変更時
- 感情フィルター変更時
- キーワード入力時（500ms遅延、2文字以上）

### 6. エラーハンドリング

#### 6.1 成功時の表示
```javascript
showSuccess('データの読み込みが完了しました');
```

#### 6.2 エラー時の表示
```javascript
showError('データの読み込みに失敗しました: ' + error.message);
```

#### 6.3 読み込み中の表示
- 統計カード: "-" 表示
- 投稿テーブル: "データを読み込み中..." 表示
- トレンドトピック: "トレンドトピックを読み込み中..." 表示

### 7. フィルター状態の表示

現在のフィルター状態は `currentFilters` 要素に表示されます：
```html
<div id="currentFilters" class="filter-status">
    <small>🔍 現在のフィルター: 全データ</small>
</div>
```

### 8. レスポンス処理

#### 8.1 感情分析サマリーの処理
```javascript
document.getElementById('totalPosts').textContent = data.total_posts;

if (data.sentiment_breakdown) {
    const positive = data.sentiment_breakdown.positive || {count: 0, percentage: 0};
    const negative = data.sentiment_breakdown.negative || {count: 0, percentage: 0};
    const neutral = data.sentiment_breakdown.neutral || {count: 0, percentage: 0};
    
    // 各要素を更新
}
```

#### 8.2 投稿データの処理
- 投稿が存在する場合：テーブル行を動的生成
- 投稿が存在しない場合："データがありません" 表示
- エラーの場合："エラーが発生しました" 表示

### 9. パフォーマンス最適化

#### 9.1 並列処理
```javascript
await Promise.all([
    loadSentimentSummary(),
    loadPosts(),
    loadCharts(),
    loadTrendingTopics()
]);
```

#### 9.2 デバウンス処理
キーワード入力時は500msの遅延を設けて、連続入力時のAPI呼び出しを制限：

```javascript
let timeoutId;
keywordInput.addEventListener('input', function() {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => {
        if (this.value.length === 0 || this.value.length > 2) {
            loadData();
        }
    }, 500);
});
```

### 10. セキュリティ考慮事項

#### 10.1 XSS対策
- キーワードのエンコード: `encodeURIComponent(keyword)`
- 投稿内容の表示時はエスケープ処理を推奨

#### 10.2 入力検証
- キーワード長制限（現在は制限なし）
- 特殊文字のフィルタリング（現在は実装なし）

### 11. 使用例

#### 基本的な検索
1. キーワード欄に「AI」と入力
2. 検索ボタンをクリック
3. AI関連の投稿データが表示される

#### フィルター付き検索
1. キーワード欄に「機械学習」と入力
2. プラットフォーム選択で「Twitter」を選択
3. 感情フィルターで「ポジティブ」を選択
4. 検索ボタンをクリック
5. Twitter上の機械学習に関するポジティブな投稿のみが表示される

### 12. 今後の改善案

1. **リアルタイム検索**: キーワード入力と同時に検索結果を更新
2. **検索履歴**: 過去の検索キーワードを保存・再利用
3. **高度なフィルター**: 日付範囲、投稿者、影響力などの追加フィルター
4. **検索結果のエクスポート**: CSV、PDF形式でのデータ出力
5. **検索パフォーマンス指標**: API応答時間、結果件数の表示
6. **検索候補**: キーワード入力時の自動補完機能

---

**更新日**: 2025年6月29日  
**バージョン**: 1.0  
**作成者**: Social Listening Team
