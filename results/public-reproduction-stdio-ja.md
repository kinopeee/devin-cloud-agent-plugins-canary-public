# 公開再現用リポジトリとCloud stdio MCP手動起動の記録

**診断結果：公開版の条件Aで、stdioサーバーの手動起動とJSON-RPC応答を確認しました。CloudによるMCP自動登録・自動起動を確認した結果ではありません。**

公開リポジトリ：<https://github.com/kinopeee/devin-cloud-agent-plugins-canary-public>

## 公開内容と検査

- `condition-a-local` / `condition-b-git-subdir` / `condition-c-control` の3ブランチを公開。既定ブランチはAです。
- 元の非公開リポジトリは変更せず、ファイルを複製して新しい公開用履歴を作成しました。社内メールを含むコミット本文、非公開リポジトリへの参照、非公開セッションURL、元のコミットIDは公開履歴に含めていません。
- BのURLは公開リポジトリへ変更し、取得SHAを公開fixtureコミット `a0517234ab0d79f3aaa119e550d15f33265baaff` に固定しました。Canary本体のGit treeは元の3条件と同一です。
- 公開対象の全到達可能コミットのファイル・メタデータについて、トークン形式、秘密鍵、認証入りURL、既知の環境内secret値、社内名・メール、個人ホームパス、非公開参照を検査し、除去後の対象に該当を検出していません。目視確認も実施しましたが、あらゆる機密情報の不存在を数学的に保証するものではありません。
- 公式スキーマ検証は `plugin.json` / `mcp.json` ともPASS。ローカルテスト3件、Python構文検査、差分の空白検査も成功しています。
- 認証ヘッダーなしのGitHub API取得でHTTP 200・`private: false`を確認しました。
- [README](../README.md) に3条件の宣言、新規Cloudセッションから対象branchを直接cloneする手順、期待結果と過去実測結果の比較表を記載しています。比較表は元の非公開fixtureでの測定であり、公開版を新規Cloudセッション3件で再測定したものではありません。

## 手動起動の実測

| 記録項目 | 実測値 |
| --- | --- |
| 開始日時 | **2026-11-05 02:29:52.404615 JST** / **2026-11-04 17:29:52.404615 UTC** |
| 終了日時 | 2026-11-04 17:29:52.441791 UTC |
| 対象 | 公開リポジトリの `condition-a-local` |
| 測定コミット | [1acf30d8f0f8f7b79574ca3efc9d0c22e8fbf551](https://github.com/kinopeee/devin-cloud-agent-plugins-canary-public/commit/1acf30d8f0f8f7b79574ca3efc9d0c22e8fbf551)（後続コミットは記録・READMEのみ） |
| 実行環境 | このDevin CloudセッションのLinux VM、カーネル `6.8.0-1060-aws` |
| インタプリタ | `python3`、**CPython 3.12.16**。コマンド名・引数を分離し、shellを介さず起動 |
| 設定に書かれたコマンド | `python3` |
| 設定に書かれた引数 | `["${PLUGIN_ROOT}/canary_server.py"]` |
| 設定のcwd / env | どちらも未指定。設定ファイルは変更していません |
| 実際のcwd | `/tmp/devin-canary-stdio/plugins/canary-plugin`（仕様の既定値：plugin root） |
| 実際のargv | `["python3", "/tmp/devin-canary-stdio/plugins/canary-plugin/canary_server.py"]` |
| `PLUGIN_ROOT` | `/tmp/devin-canary-stdio/plugins/canary-plugin`（診断用に手動供給） |
| `PLUGIN_DATA` | `/var/tmp/devin-canary-plugin-data`（診断用に作成した専用・書込可能ディレクトリ。手動供給） |
| その他の環境変数 | Cloudシェルの環境を継承。設定のenv上書きはなし。secretを避けるため全環境のダンプは記録しません |
| 起動・待受 | 起動成功。initialize応答後、stdinを閉じる前にもプロセスが生存していました |
| MCP通信 | initialize → initialized通知 → tools/list → tools/call（`canary_env`）に成功。JSON-RPC応答3件 |
| 標準出力 | JSON-RPC応答3行のみ。initializeにサーバー情報、tools/listに `canary_env`、tools/callに下記の実値 |
| 標準エラー | **空文字列 `""`、0バイト** |
| 終了 | stdin EOF後に正常終了、**終了コード0** |
| Hook出力 | `/tmp/canary-hook` は診断前後とも存在せず。手動Hook実行なし |
| MCP登録 | 手動登録なし。Cloudのツールカタログではなく、起動した子プロセスのstdin/stdoutへ直接JSON-RPCを送受信 |

`canary_env` の返り値のtext部分をJSONとして復元した値：

```json
{
  "PLUGIN_ROOT": "/tmp/devin-canary-stdio/plugins/canary-plugin",
  "PLUGIN_DATA": "/var/tmp/devin-canary-plugin-data"
}
```

設定・要求・応答・stdout・stderr・終了コードの機械可読記録：[manual-stdio.json](manual-stdio.json)。

## コマンドと仕様の解釈

公開版Aを次のように直接cloneした後に診断しました。

```sh
git clone --branch condition-a-local --single-branch \
  https://github.com/kinopeee/devin-cloud-agent-plugins-canary-public.git \
  /tmp/devin-canary-stdio
```

`mcp.json` にはcwd / envの明示指定がありません。[Agent Plugins 1.0.0 §7.2.1と§9](https://github.com/agentplugins/agent-plugins-spec/blob/main/spec/1.0.0.md) に従い、省略cwdはplugin root、予約変数はクライアントが供給、args内の予約変数は起動前に展開、と解釈しました。今回はそのクライアント側の準備だけを診断用に手動で行いました。

実効コマンドは以下です。このプロセスのstdinから上記のJSON-RPCを送信しました。

```sh
cd /tmp/devin-canary-stdio/plugins/canary-plugin
PLUGIN_ROOT=/tmp/devin-canary-stdio/plugins/canary-plugin \
PLUGIN_DATA=/var/tmp/devin-canary-plugin-data \
  python3 /tmp/devin-canary-stdio/plugins/canary-plugin/canary_server.py
```

**予約変数の値は手動診断の値であり、Cloudローダーから取得した値ではありません。** MCPの手動登録やHookの手動実行はしていません。確認できたのは、このVMのPythonとCanary本体が、指定の起動条件を与えたときにstdioで正常動作することまでです。CloudがMCPを自動接続しなかった原因、Cloudでの予約変数注入、SessionStart Hookの自動実行は、この診断では未確認です。
