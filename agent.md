# OSINT CTF 自律解答エージェント設計書（agent.md）

## 目的

CTF（Capture The Flag）における **OSINT問題を自律的に解析・解答するAIエージェント** を開発する。

- 入力：文章、画像、URL、SNSアカウント、ユーザ名、位置情報の断片など
- 出力：
  - 推論過程（どの情報から何を調べたか）
  - 最終的なCTFフラグ候補
- 技術スタック：
  - Python
  - LangChain（Agent / Tool / Memory）
  - LLM（OpenAI / OpenRouter 等）
  - Web API / スクレイピング / 画像解析

まずは **Single Agent** で開始し、段階的に **Multi-Agent構成** に進化させる。

---

## フェーズ構成

### Phase 1：単一OSINT Agent（MVP）

#### Agent名

**OSINT-Agent**

#### 役割

- 問題文を理解
- 必要なOSINT調査タスクを計画
- ツールを順次実行
- 情報を統合して仮説を立てる
- フラグ形式に整形して出力

#### 処理フロー

1. 入力解析（テキスト / URL / 画像）
2. 問題タイプ分類（人物特定 / 場所特定 / 時系列 / SNS追跡 など）
3. 調査計画生成（Chain of Thought）
4. ツール実行ループ
5. 仮説検証
6. フラグ生成

---

## Phase 1 Agent に組み込むツール

### 1. Text Analysis Tool

- 問題文から
  - 固有名詞
  - 時間
  - 場所
  - アカウント名
  - ドメイン を抽出

技術：

- spaCy / LLM parsing

---

### 2. Web Search Tool

- キーワード検索
- サイト限定検索
- ドメイン逆引き

技術：

- Bing Search API / SerpAPI
- LangChain Tool

---

### 3. URL Investigation Tool

- WhoIs
- DNS
- サイト構造解析
- 過去のスナップショット

技術：

- python-whois
- Wayback Machine API

---

### 4. SNS OSINT Tool

- ユーザ名横断検索
- 投稿内容解析
- 位置情報・時刻推定

対象：

- X (Twitter)
- Instagram
- GitHub
- Reddit

技術：

- 公開API / スクレイピング

---

### 5. Image OSINT Tool

- EXIF解析
- 画像内文字認識（OCR）
- 画像特徴抽出

技術：

- Pillow
- ExifTool
- Tesseract OCR
- LLM Vision

---

### 6. Geolocation Tool

- 画像・文章から位置推定
- 地名曖昧検索

技術：

- Google Maps API / OpenStreetMap

---

### 7. Memory / Evidence Store

- 調査結果を構造化保存
- 再利用可能にする

形式：

```json
{
  "source": "twitter",
  "fact": "写真は大阪駅周辺",
  "confidence": 0.8
}
```

---

## Phase 2：役割分担型マルチエージェント

### エージェント構成

#### 1. Planner Agent

- 問題を分解
- 調査戦略を立案

#### 2. Web Research Agent

- Web検索・リンク探索専門

#### 3. SNS Agent

- アカウント追跡・人物特定

#### 4. Image Analysis Agent

- 画像解析・位置特定

#### 5. Validator Agent

- 情報の矛盾検出
- 仮説検証

#### 6. Flag Formatter Agent

- CTF形式に正規化

---

## エージェント間通信

- LangGraph / LangChain Multi-Agent
- JSONベースメッセージ

例：

```json
{
  "task": "analyze_image",
  "input": "image_01.jpg",
  "expected_output": "location"
}
```

---

## Phase 3：自律性強化

- ツール選択の自己最適化
- 成功/失敗ログによる改善
- CTFジャンル別プロンプト学習

---

## 非機能要件

- ログ完全保存（再現性）
- 手動介入可能（Human-in-the-loop）
- Webアプリ化（FastAPI + React）

---

## 想定ユースケース

- CTF練習用OSINTアシスタント
- 情報処理安全確保支援士（OSINT学習）
- Red Team訓練

---

## 今後の相談ポイント

- 実データ取得の法的配慮
- API制限対策
- 推論過程の可視化UI
- RAGとの統合（過去CTF問題DB）

---

## 次のアクション

1. Phase 1 Agent を LangChain で実装
2. Tool Interface 定義
3. サンプルOSINT問題で検証
4. agent.md を更新

---

（このファイルは開発の設計書として使用する）
