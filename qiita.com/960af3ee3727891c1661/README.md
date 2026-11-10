---
title: "Issue Drafter で Issue の下書きをする"
url: "https://qiita.com/tamiroh/items/960af3ee3727891c1661"
created_at: "2026-11-10T00:34:02+09:00"
updated_at: "2026-11-10T00:39:39+09:00"
tags: ["GitHub", "個人開発", "Svelte", "TypeScript", "indexedDB"]
---

Issue Drafter という、GitHub Issue の下書きをブラウザ上で執筆できる環境を作ってみました。

下書きのデータはブラウザ内にリアルタイムで保存され、「Open on GitHub」で最終的に GitHub へ送信することができます。ローカルファーストを指向しています。

https://github.com/tamiroh/issue-drafter

## 使い方

[ここ](https://tamiroh.github.io/issue-drafter/)にアクセスするか、ローカルで `npm install && npm run dev` を叩いて起動し、「New draft」ボタンから以下の画面にまず行きます。

![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/1248726/df826978-f005-4a9a-ba0e-223e3481d18a.png)

リポジトリ名を指定するとテンプレートが選べるようになるので、所望のものを選択し、「Create draft」をクリックします。

![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/1248726/b0d15d52-b48f-4394-88b7-1a3ea08be649.png)

あとは Issue を書いていきましょう！

書き終わったら「Open on GitHub」をクリックして確認し、提出します。

![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/1248726/3c339060-97ca-4440-b749-b84a75035e37.png)


## なぜ作ったか

GitHub に Issue を投稿するとき、特に外部のリポジトリへ英語で提出する場合だと、念のためしっかり下書きをしたくなることがあります。私の場合特に慎重な性格というのもあって、

1. まず日本語で書く
1. 推敲する
1. 英訳する
1. 推敲する
1. 提出

というふうにじっくり時間をかけることが多いです。

以前は VSCode で執筆してたのですが、いちいちローカルにファイルを作ってエディタを立ち上げて……というのも面倒になってきました。確かに上記のような慎重なステップを経るものの、執筆というほど大それたものでもなく、一時的にブラウザ上で下書きできる環境が用意できればそれで十分でした。

## 技術構成

- 言語: TypeScript
- ビルド: Vite
- UI フレームワーク: Svelte
- エディタ: CodeMirror

特に捻りはないですが、Svelte をチョイスしてるのは今の時代少し珍しいと言えなくもないです。これは単に、最近久しく触ってなかったから触ろう、という以上の意味はありませんでしたが、React と比べて CSS の管理に悩まなくていいのは気楽で良かったです。

それよりも重要なポイントは、バックエンドを持たず、フロントエンドだけでアプリが完結してる点かと思います。これは、

- Draft を IndexedDB に保存する
- 実際に GitHub へ投稿するのは、GitHub への導線を設けるに留めアプリの責務外にする

という工夫によるものです。

## まとめ

自分用に作ったもので、特に誰かに教える予定は無かったのですが、便利に使っていたので紹介してみました。もし興味があったら使ってみてください。
