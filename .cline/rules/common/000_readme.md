---
プロンプト：
# リポジトリ品質確認プロンプト V2

あなたは優れたコードレビューとリポジトリ構造分析の専門家です。以下のチェックリストに沿って、リポジトリ全体の品質確認を行ってください。各項目について「✅」（問題なし）、「❌」（問題あり）、「⚠️」（一部問題あり）のいずれかで評価し、問題がある場合は具体的な改善提案を提示してください。

## チェックリスト

### 📝 README. md の品質確認
- [ ] タイトルは中央揃えになっているか
- [ ] ヘッダー画像は中央揃えになっているか(既にヘッダー画像がある場合はそれを使用すること)
- [ ] 技術スタックのバッジが適切に配置され、中央揃えになっているか
- [ ] 各セクションに絵文字が活用され、可読性が向上しているか
- [ ] ドキュメントは適切に分割されて、それぞれに適切にリンクされているか
- [ ] インストール手順が明確に記載されているか
- [ ] 使用方法が明確に記載されているか
- [ ] スクリーンショットや図が適切に使用されているか

### 📚 ドキュメンテーション全体の一貫性
- [ ] 各階層に README. md が存在するか（なければ作成が必要）
- [ ] 各階層の README. md が適切に上位階層の README. md を参照しているか
- [ ] 各 README. md の内容が重複せず、適切に分割されているか
- [ ] 各 README. md が重くなりすぎていないか、適切にファイル分割されているか
- [ ] 分割されたファイルに適切にリンクが貼られているか
- [ ] 全てのドキュメントで一貫した用語が使用されているか
- [ ] リポジトリ全体でのドキュメントの構造が論理的か

### 🔒 環境設定とセキュリティ
- [ ] `.env` や環境変数が適切に使用されているか
- [ ] 直接コード内にAPIキーやパスワードなどの機密情報が記載されていないか
- [ ] `.gitignore` ファイルに `.env` が適切に記載されているか
- [ ] `.env.example` が存在し、必要な環境変数の例が記載されているか

### 💻 コード品質
- [ ] コードコメントは適切に記載されているか
- [ ] 命名規則が一貫しているか
- [ ] 未使用のコードやコメントアウトされたコードが放置されていないか

### 📂 プロジェクト構造
- [ ] フォルダ構造が論理的で理解しやすいか
- [ ] 依存関係が適切に管理されているか

## 出力形式

以下のような形式でチェックリストの結果を出力してください：

### 📝 README. md の品質確認
- [✅/❌/⚠️] タイトルは中央揃えになっているか
  - 問題点と改善提案（問題がある場合）
- [✅/❌/⚠️] ヘッダー画像は中央揃えになっているか
  - 問題点と改善提案（問題がある場合）
- ...（以下同様）

### 📚 ドキュメンテーション全体の一貫性
- [✅/❌/⚠️] 各階層に README. md が存在するか
  - 問題点と改善提案（問題がある場合）
- [✅/❌/⚠️] 各階層の README. md が適切に上位階層の README. md を参照しているか
  - 問題点と改善提案（問題がある場合）
- ...（以下同様）

（他のセクションも同様の形式で）

### 🔍 総評
リポジトリの現在の状態に関する簡潔な総評と、優先して対応すべき最重要の改善点3つを提示してください。

### 📝 具体的な修正例
最も重要な改善点について、具体的なコードやマークダウンの修正例を提示してください。

#### README. md 階層構造確認
以下の点を特に注意して確認してください：
1. 各ディレクトリに README. md があるか確認し、なければ作成を提案する
2. 各 README. md が上位の README. md を適切に参照しているか確認し、重複を避ける
3. README. md が長すぎる場合は、適切なファイル分割とリンク設定を提案する

---

このチェックリストに沿って、リポジトリ全体を分析し、開発サイクルのクロージング処理として必要な改善点を明確にしてください。