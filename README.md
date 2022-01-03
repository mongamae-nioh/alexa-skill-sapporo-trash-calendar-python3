# 概要
- Alexaスキル「札幌ごみなげカレンダー」をpython3系で作り直したもの
- LamndaでPython2系のサポートが終了するため3系へ移行

# 改修するときは
## 別環境で開発するには
- ask smapi export-package -s {skillId} -g {stage} で開発環境へスキルをクローン
  - skill-packageディレクトリが作成される
  - stageはlive or development
- git cloneで開発環境へLambdaのコードをクローン
- ask initでASKの初期設定
  - .ask, ask-resources.jsonが作成される
  - 詳細は[Qiita](https://qiita.com/takara328/items/d0c593c0a37668e6a953)参照 

## 改修
- ソースコードを変更してask deploy
  - Lambdaの更新で ResourceConflictException が発生するがデプロイは問題なくできていそう
    - デプロイ先としてLambdaのバージョン、エイリアスが指定できない仕様らしいので、${LATEST}にデプロイされる
      - .ask/ask-states.jsonで検証したが以下のエラーがでた
        - Current operation does not support versions other than $LATEST. Please set the version to $LATEST or do not set a version in your request.
    - なのでlive環境のエンドポイントは必ずバージョンかエイリアスを付与したものを指定する
    - バージョン、エイリアス未指定 = ${LATEST} なのでlive環境に影響しないようにLambdaの修正ができなくなるので注意
  - [Error]: CliError: The security token included in the request is invalid.エラーが発生することがある
    - ask configureで初期設定を行い再度デプロイする
- Lambdaのバージョンを発行する(エイリアス作成でもOK）
- 作成したバージョン（orエイリアス）のトリガーへAlexaスキルIDを追加する
  - これをしないとSkillManifestErrorが出るので注意
- 開発中のスキルのエンドポイントへそのバージョンを指定する（エイリアス指定でもOK）
- 認定審査
