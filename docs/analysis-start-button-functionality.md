# 分析開始ボタン機能ドキュメント

## 概要
Social Listening Dashboardの分析開始ボタン（🚀 分析開始）の詳細な機能仕様書です。このボタンは新しいソーシャルメディア分析タスクを開始するために使用されます。

## 基本情報
- **ボタンID**: なし（onclick属性で直接関数呼び出し）
- **ボタンクラス**: `btn-analyze`
- **トリガー関数**: `startAnalysis()`
- **配置場所**: 分析コントロールセクション内（データ検索ボタンの隣）
- **ボタンテキスト**: "🚀 新規分析開始"
- **機能タイプ**: 非同期処理（async function）
- **視覚的識別**: オレンジグラデーション、ホバー時の光沢エフェクト

## 機能詳細

### 1. メイン機能
分析開始ボタンをクリックすると、`startAnalysis()` 関数が実行され、指定されたキーワードに基づいて新しいソーシャルメディア分析タスクを開始します。

### 2. 前処理・入力検証

#### 2.1 キーワード必須チェック
```javascript
const keywords = document.getElementById('keywordInput').value;
if (!keywords) {
    alert('キーワードを入力してください');
    return;
}
```

**仕様**:
- キーワード入力フィールドが空の場合、分析を開始しません
- アラートメッセセージで入力を促します
- 処理を中断して関数を終了します

#### 2.2 UI状態の変更
```javascript
const button = event.target;
const originalText = button.textContent;
button.textContent = '🔄 分析中...';
button.disabled = true;
```

**仕様**:
- ボタンテキストを "🚀 分析開始" → "🔄 分析中..." に変更
- ボタンを無効化（disabled = true）
- 元のテキストを保存（処理完了後の復元用）

### 3. API呼び出し

#### 3.1 エンドポイント
- **URL**: `/api/v1/analyze`
- **メソッド**: `POST`
- **Content-Type**: `application/json`

#### 3.2 リクエストボディ
```javascript
{
    keywords: keywords.split(',').map(k => k.trim()),
    platforms: selectedPlatforms,  // ユーザー選択に基づく
    max_posts_per_platform: 50
}
```

**パラメータ詳細**:
- **keywords**: 
  - キーワード入力フィールドの値をカンマで分割
  - 各キーワードの前後の空白を除去（trim）
  - 配列として送信
- **platforms**: 
  - **動的選択**: プラットフォーム選択ドロップダウンの値に基づく
  - 特定プラットフォーム選択時: `[selected_platform]`
  - 全プラットフォーム選択時: `["twitter", "youtube", "reddit"]`
- **max_posts_per_platform**: 
  - 固定値: 50
  - プラットフォームごとの最大投稿取得数

#### 3.3 キーワード処理例
```javascript
// 入力: "AI, 機械学習 , ChatGPT"
// 処理後: ["AI", "機械学習", "ChatGPT"]
keywords.split(',').map(k => k.trim())
```

### 4. レスポンス処理

#### 4.1 成功時の処理
```javascript
if (response.ok) {
    alert(`分析を開始しました。\nタスクID: ${result.task_id}\n推定時間: ${result.estimated_time}`);
    
    // Poll for results
    setTimeout(() => loadData(), 5000);
}
```

**成功レスポンスの内容**:
- **task_id**: 分析タスクの一意識別子
- **estimated_time**: 分析完了までの推定時間

**UI更新**:
- アラートでタスクIDと推定時間を表示
- 5秒後に `loadData()` を実行してダッシュボードを更新

#### 4.2 エラー時の処理
```javascript
} else {
    throw new Error(result.detail || 'Unknown error');
}
```

**エラーハンドリング**:
- APIからのエラーレスポンスを例外として投げる
- `result.detail` がある場合はそれを使用、なければ 'Unknown error'

#### 4.3 例外処理
```javascript
} catch (error) {
    showError('分析の開始に失敗しました: ' + error.message);
}
```

**例外時の動作**:
- `showError()` 関数を呼び出してユーザーにエラーを表示
- エラーメッセージに具体的なエラー内容を含める

### 5. 後処理（Finally Block）

#### 5.1 UI状態の復元
```javascript
} finally {
    button.textContent = originalText;
    button.disabled = false;
}
```

**必ず実行される処理**:
- ボタンテキストを元の "🚀 分析開始" に戻す
- ボタンの無効化を解除（enabled状態に戻す）
- 成功・失敗に関わらず必ず実行

### 6. 分析タスクのライフサイクル

#### 6.1 タスク開始フロー
1. **入力検証**: キーワードの存在確認
2. **UI更新**: ボタン状態変更（分析中表示）
3. **API呼び出し**: 分析タスクの開始要求
4. **結果通知**: タスクIDと推定時間の表示
5. **自動更新**: 5秒後にダッシュボード更新
6. **UI復元**: ボタン状態を元に戻す

#### 6.2 非同期処理の特徴
- **非ブロッキング**: 他のUI操作を妨げない
- **プログレス表示**: ボタンテキストで進行状況を表示
- **自動ポーリング**: 結果取得のための自動更新

### 7. エラーメッセージ表示

#### 7.1 showError()関数の動作
```javascript
function showError(message) {
    // Remove existing error messages
    const existingErrors = document.querySelectorAll('.error');
    existingErrors.forEach(error => error.remove());
    
    // Create new error message
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error';
    errorDiv.textContent = message;
    
    // Insert after header
    const header = document.querySelector('.header');
    header.parentNode.insertBefore(errorDiv, header.nextSibling);
    
    // Auto-remove after 5 seconds
    setTimeout(() => errorDiv.remove(), 5000);
}
```

**エラー表示の特徴**:
- 既存のエラーメッセージを削除
- ヘッダー下部に新しいエラーメッセージを表示
- 5秒後に自動的にメッセージを削除
- CSSクラス `error` を適用（赤背景での表示）

### 8. 分析対象プラットフォーム

#### 8.1 対応プラットフォーム
| プラットフォーム | 識別子 | 取得投稿数上限 |
|------------------|--------|----------------|
| Twitter | "twitter" | 50件 |
| YouTube | "youtube" | 50件 |
| Reddit | "reddit" | 50件 |

#### 8.2 総取得投稿数
- **最大**: 150件（50件 × 3プラットフォーム）
- **実際**: プラットフォームでの検索結果に依存

### 9. 使用例とシナリオ

#### 9.1 基本的な使用例
```
1. キーワード欄に「ChatGPT」と入力
2. 🚀 分析開始ボタンをクリック
3. ボタンが「🔄 分析中...」に変化
4. アラート表示：「分析を開始しました。タスクID: abc123 推定時間: 2分」
5. 5秒後にダッシュボードが自動更新
6. ボタンが「🚀 分析開始」に戻る
```

#### 9.2 複数キーワードの例
```
入力: "AI, 人工知能, 機械学習"
→ 3つのキーワードで横断的に分析開始
```

#### 9.3 エラーシナリオ
```
1. キーワード未入力でボタンクリック
   → アラート：「キーワードを入力してください」

2. API通信エラー
   → エラーメッセージ：「分析の開始に失敗しました: ネットワークエラー」

3. サーバーエラー（500番台）
   → エラーメッセージ：「分析の開始に失敗しました: Internal Server Error」
```

### 10. セキュリティ考慮事項

#### 10.1 入力データの処理
- **XSS対策**: キーワードはAPIに送信される前にトリム処理のみ
- **インジェクション対策**: サーバーサイドでの適切な検証が必要
- **データサイズ制限**: 現在はクライアントサイドに制限なし

#### 10.2 API認証
- 現在のコードでは認証トークンの送信なし
- 実装時は適切な認証ヘッダーの追加を推奨

### 11. パフォーマンス考慮事項

#### 11.1 重複実行防止
- ボタン無効化により、分析中の重複実行を防止
- `finally`ブロックで確実にボタンを再有効化

#### 11.2 タイムアウト処理
- 現在はフェッチAPIのデフォルトタイムアウトを使用
- 長時間実行される可能性のある分析では、カスタムタイムアウトの設定を推奨

#### 11.3 メモリ使用量
- 大量のキーワード処理時のメモリ使用量に注意
- 推奨キーワード数の制限設定を検討

### 12. 監視・ログ

#### 12.1 現在のログ出力
```javascript
console.log('Search keyword:', keyword); // loadData()内
```

#### 12.2 推奨追加ログ
- 分析開始時のキーワード・パラメータ
- API応答時間
- エラー詳細情報
- タスクID追跡

### 13. 今後の改善案

#### 13.1 UI/UX改善
1. **プログレスバー**: 分析進行状況の視覚的表示
2. **キャンセル機能**: 分析中止ボタンの追加
3. **履歴表示**: 過去の分析タスク一覧
4. **通知機能**: 分析完了時のブラウザ通知

#### 13.2 機能拡張
1. **スケジュール分析**: 定期実行の設定
2. **カスタムパラメータ**: プラットフォーム選択、取得件数調整
3. **分析タイプ**: 感情分析以外の分析オプション
4. **結果フィルタ**: 分析結果の詳細フィルタリング

#### 13.3 技術改善
1. **WebSocket**: リアルタイム進行状況更新
2. **Service Worker**: オフライン対応
3. **バッチ処理**: 複数キーワードの効率的処理
4. **キャッシュ機能**: 類似分析の高速化

### 14. API仕様詳細

#### 14.1 期待されるレスポンス形式
```json
// 成功時
{
    "task_id": "abc123-def456-ghi789",
    "estimated_time": "2分",
    "status": "started",
    "message": "分析を開始しました"
}

// エラー時
{
    "detail": "キーワードが無効です",
    "error_code": "INVALID_KEYWORDS",
    "status": "error"
}
```

#### 14.2 HTTPステータスコード
- **200**: 分析開始成功
- **400**: リクエストパラメータエラー
- **401**: 認証エラー
- **429**: レート制限エラー
- **500**: サーバー内部エラー

### 15. テストケース

#### 15.1 正常系テスト
1. 単一キーワードでの分析開始
2. 複数キーワードでの分析開始
3. 日本語キーワードでの分析開始
4. 英語キーワードでの分析開始

#### 15.2 異常系テスト
1. 空文字でのボタンクリック
2. 特殊文字のみでの分析開始
3. 極端に長いキーワードでの分析開始
4. ネットワーク切断時の分析開始

#### 15.3 UI状態テスト
1. ボタン無効化の確認
2. テキスト変更の確認
3. エラーメッセージ表示の確認
4. 復元処理の確認

### 16. UI改善とユーザビリティ

#### 16.1 ボタンデザインの差別化
2025年6月29日のUI改善により、以下の視覚的差別化を実装：

**分析開始ボタンの特徴**:
- **カラー**: オレンジグラデーション（#FF6B35 → #F7931E）
- **ホバー効果**: 光沢エフェクト、上下移動、影の強調
- **ボタンテキスト**: "🚀 新規分析開始"
- **説明**: "新しい分析タスクを開始します（時間がかかります）"

**データ検索ボタンとの違い**:
- データ検索: 緑色グラデーション、"🔍 データ検索"
- 分析開始: オレンジ色グラデーション、"🚀 新規分析開始"

#### 16.2 ユーザー向け説明の追加
```html
<div class="button-descriptions">
    <div class="button-help">
        <div class="help-item">
            <strong>🔍 データ検索:</strong> 既存のデータベースから条件に合致する投稿を即座に検索・表示します（高速）
        </div>
        <div class="help-item">
            <strong>🚀 新規分析開始:</strong> リアルタイムでSNSから新しいデータを収集・分析します（数分かかります）
        </div>
    </div>
</div>
```

#### 16.3 レスポンシブデザイン
- **デスクトップ**: 横並び配置
- **モバイル**: 縦並び配置、フルワイズボタン
- **説明テキスト**: 画面サイズに応じた調整

#### 16.4 アクセシビリティ向上
- **ツールチップ**: ボタンホバー時の詳細説明
- **視覚的フィードバック**: 実行中の状態表示改善
- **キーボードナビゲーション**: tabindex対応
- **カラーコントラスト**: WCAG準拠のコントラスト比

---

**更新日**: 2025年6月29日  
**バージョン**: 1.0  
**作成者**: Social Listening Team  
**関連ドキュメント**: 
- [検索ボタン機能ドキュメント](./search-button-functionality.md)
- [API仕様書](../api/README.md)

### 17. Twitter API制限対策（2025年6月29日追加）

#### 17.1 問題の背景
Twitter APIのレート制限により、以下の問題が発生していました：
- プラットフォーム選択に関係なく常にTwitter APIが呼び出される
- 頻繁なレート制限エラー（Rate limit exceeded. Sleeping for 901 seconds）
- 意図しないAPI使用量の増加

#### 17.2 実装された解決策
**プラットフォーム選択の動的制御**:
```javascript
// プラットフォーム選択を取得
const platformSelect = document.getElementById('platformSelect').value;
let selectedPlatforms;

if (platformSelect) {
    // 特定のプラットフォームが選択されている場合
    selectedPlatforms = [platformSelect];
} else {
    // 全プラットフォームが選択されている場合
    selectedPlatforms = ["twitter", "youtube", "reddit"];
}
```

#### 17.3 動作パターン
| プラットフォーム選択 | 送信されるplatforms配列 | Twitter API使用 |
|---------------------|------------------------|----------------|
| 全プラットフォーム | `["twitter", "youtube", "reddit"]` | ✅ 使用 |
| Twitter | `["twitter"]` | ✅ 使用 |
| YouTube | `["youtube"]` | ❌ 使用しない |
| Reddit | `["reddit"]` | ❌ 使用しない |

#### 17.4 ユーザー向けガイダンス
**分析開始時の確認メッセージ改善**:
```javascript
const platformText = selectedPlatforms.length === 1 ? 
    selectedPlatforms[0] : 
    `${selectedPlatforms.length}つのプラットフォーム`;

alert(`分析を開始しました。\nタスクID: ${result.task_id}\n対象: ${platformText}\n推定時間: ${result.estimated_time}`);
```

#### 17.5 API使用量最適化のベストプラクティス
1. **既存データ優先**: まず🔍データ検索で既存データを確認
2. **プラットフォーム選択**: Twitter以外のプラットフォームを活用
3. **適切なタイミング**: 重要なキーワードやブランド監視時のみTwitter分析を実行
4. **頻度制限**: 同一キーワードでの連続分析を避ける

#### 17.6 監視・アラート
- レート制限発生時のログ監視
- API使用量の定期的な確認
- ユーザーへの適切なガイダンス表示

---
