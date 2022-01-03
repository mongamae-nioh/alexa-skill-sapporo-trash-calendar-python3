# 概要
- Alexaスキル「札幌ごみなげカレンダー」をpython3系で作り直したもの
- LamndaでPython2系のサポートが終了するため3系へ移行

# 改修するときは
- Lambdaのバージョンを発行する(エイリアス作成でもOK）
- 作成したバージョン（orエイリアス）のトリガーへAlexaスキルIDを追加する
  - これをしないとSkillManifestErrorが出るので注意
- 開発中のスキルのエンドポイントへそのバージョンを指定する（エイリアス指定でもOK）
- コードを書いてask deployする
  - [Error]: CliError: The security token included in the request is invalid.エラーが発生することがある
  - ask configureで初期設定を行い再度デプロイする
- 必要に応じて認定審査
