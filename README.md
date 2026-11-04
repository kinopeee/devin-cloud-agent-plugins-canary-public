# Devin Cloud Agent Plugins Canary — 公開再現用

公開URL: <https://github.com/kinopeee/devin-cloud-agent-plugins-canary-public>

Agent Plugins 1.0.0 の Skills / stdio MCP と、Devin 固有の SessionStart Hook を区別して観測する最小構成です。元の非公開実験の3条件を、新しい履歴で複製しています。非公開リポジトリ名・セッションURL・元のコミットID・元の履歴は公開物に含めていません。B の取得先と固定SHAだけを公開版に変更し、Canary本体は変更していません。

## 3ブランチと宣言

各ブランチの `plugins/canary-plugin/` は同一です。条件を変えるのは `.devin/config.json` のみです。

### A — `condition-a-local`

```json
{
  "requiredPlugins": ["./plugins/canary-plugin"]
}
```

### B — `condition-b-git-subdir`

```json
{
  "requiredPlugins": [
    {
      "source": "git-subdir",
      "url": "https://github.com/kinopeee/devin-cloud-agent-plugins-canary-public.git",
      "path": "plugins/canary-plugin",
      "sha": "<PUBLIC_FIXTURE_SHA>"
    }
  ]
}
```

`<PUBLIC_FIXTURE_SHA>` は説明用のプレースホルダーです。Bブランチの実ファイルには、この公開リポジトリ内のfixtureコミットの40桁SHAを固定しています。正確な値は [Bの設定](https://github.com/kinopeee/devin-cloud-agent-plugins-canary-public/blob/condition-b-git-subdir/.devin/config.json) を参照してください。固定先の `plugins/canary-plugin/` と各条件のCanary本体は同一です。

### C — `condition-c-control`

`.devin/config.json` を置かず、プラグインを宣言しません。Canaryのファイル自体は他条件と同じように存在します。

## 新規 Cloud セッションでの再現手順

1. **条件ごとに別の新規Cloudセッション／VMを作成**します。既存セッションでのbranch切り替えは自動読み込みの測定に使いません。
2. 初期リポジトリ指定は空にし、Canaryプラグインが未インストールで、`/tmp/canary-hook` も存在しないことを確認します。既存環境を削除して対照を作るのではなく、汚染のない新規環境を使用します。
3. 対象branchを、最初のcloneから直接指定します。下記の `<BRANCH>` を上記の3つのbranch名のいずれかに置き換えます。

   ```sh
   git clone --branch <BRANCH> --single-branch \
     https://github.com/kinopeee/devin-cloud-agent-plugins-canary-public.git
   ```

4. リポジトリsetup後、branch・HEAD・宣言を確認し、自動読み込みを待ってから再確認します。前回はA/Bで30秒を2回、Cで30秒を1回待ちました。これは保証されたロード期限ではありません。
5. MCPサーバー／ツール一覧で `canary_env` を探し、**実際のツールが登録されている場合だけ**呼び出して返り値を保存します。見つからない場合は「環境変数未取得」であり、`null` 返却とは区別します。
6. `/tmp/canary-hook` の存在・内容・mtimeを確認します。
7. `skill_search(source="plugins", keywords=["canary"])` 等のプラグイン用スキルカタログに `canary-plugin:canary` が出るかを確認します。**checkoutのSKILL.mdを直接読んだ結果は成功の証拠にしません。**
8. 日時・結果・エラー表示を記録します。自動読み込み測定中は、手動インストール、MCPの手動登録・起動、Hookの手動実行、環境変数の手動設定を行いません。診断用の手動stdio起動は、別の結果として扱います。

## 期待結果と過去の実測結果

以下は **2026-11-05に元の非公開fixtureを各条件1回、新規Cloudセッションで測定した結果**です。公開版を新規Cloudセッションで再測定した結果ではありません。元のセッションURLと非公開コミットIDは除外しました。

| 条件／最終観測日時 JST（UTC） | 期待：MCP／Hook／Skill | 実測：`canary_env` | 実測：`/tmp/canary-hook` | 実測：プラグインスキルカタログ | エラー表示 |
| --- | --- | --- | --- | --- | --- |
| A／2026-11-05 02:04:51 +09:00（2026-11-04 17:04:51Z） | 呼び出し可能／存在／表示 | 未検出、呼び出せず。返り値なし・環境変数未取得 | 存在せず | `canary-plugin:canary` 表示あり | 自動ローダーのエラー表示は観測されず |
| B／2026-11-05 02:04:47 +09:00（2026-11-04 17:04:47Z） | 呼び出し可能／存在／表示 | 未検出、呼び出せず。返り値なし・環境変数未取得 | 存在せず | 待機後に `canary-plugin:canary` 表示あり | 自動ローダーのエラー表示は観測されず |
| C／2026-11-05 02:03:59 +09:00（2026-11-04 17:03:59Z） | 未検出／存在せず／非表示 | 未検出、呼び出し未実施 | 存在せず | 非表示 | 自動ローダーのエラー表示は観測されず |

MCP/Hook未出現の原因は未特定で、Cloud全体の非対応とは断定していません。新規セッションで初回cloneした際のrepository setupを測定しており、最初のエージェントターンより前にプラグインを事前配置した実験ではありません。

## 最小構成と検証

- `plugin.json` はルート直下に `$schema` と `name` のみ。
- `skills/canary/SKILL.md` は `name` / `description` のfrontmatterのみ。
- `mcp.json` のstdioサーバーは `python3` と `args: ["${PLUGIN_ROOT}/canary_server.py"]`。cwdとenvは未指定です。
- Agent Plugins 1.0.0 §7.2.1では、cwd省略時はプラグインルート。§9では、クライアントが `PLUGIN_ROOT` / `PLUGIN_DATA` を供給し、args内の予約プレースホルダーを展開します。これらを設定しない生のシェルコマンドとは意味が異なります。
- `canary_env` はこの2つの環境変数だけを返します。外部通信・依存パッケージはありません。
- `hooks.json` はSessionStartで `/tmp/canary-hook` にUTC日時を書きます。HooksはDevin固有拡張で、Agent Pluginsのコアスキーマ検証対象ではありません。

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-validation.txt
.venv/bin/python scripts/validate_manifest.py
python3 -m unittest discover -s tests -v
```

公式スキーマを `schemas/1.0.0/` にvendorしています。検証日時・validator・スキーマURL・SHA-256・結果は `results/schema-validation.json` に記録しています。自動テストの成功はCloud自動読み込み成功の証拠にはしません。

## 公式資料

- [Agent Plugins 1.0.0仕様（MCP・環境変数）](https://github.com/agentplugins/agent-plugins-spec/blob/main/spec/1.0.0.md)
- [plugin schema](https://agent-plugins.org/schemas/1.0.0/plugin.schema.json) / [MCP schema](https://agent-plugins.org/schemas/1.0.0/mcp.schema.json)
- [Devin Plugins](https://docs.devin.ai/cli/extensibility/plugins/overview)
- [SessionStart HookのCloud動作](https://docs.devin.ai/cli/extensibility/hooks/lifecycle-hooks#sessionstart)
