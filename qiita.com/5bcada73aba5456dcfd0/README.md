---
title: "Web ブラウザ上で Local LLM 同士がお喋りするサイトを作った"
url: "https://qiita.com/tamiroh/items/5bcada73aba5456dcfd0"
created_at: "2026-09-20T23:58:26+09:00"
updated_at: "2026-09-21T16:19:05+09:00"
tags: ["AI", "生成AI", "Chrome", "LocalLLM", "LLM"]
---

Local LLM 同士が延々とお喋りを続け、人間も会話に混ざることができるサイトを作りました。今のところは PC 版の Chrome でのみ動きます。

AI はクラウドではなくローカルで動作するので、すべての会話はプライベートです。以下のリンクからどうぞ（※ 開くとすぐに開始するのでご注意ください）。

https://tamiroh.github.io/ai2ai/

![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/1248726/557de552-5a30-48bd-a99c-a4319b8af19d.png)

## なぜ作ったのか

Chrome 148 で [Prompt API](https://developer.chrome.com/docs/ai/prompt-api?hl=ja) という、Web ブラウザ上から Local LLM モデル (Gemini Nano) に自然言語で指示を送ることができる JavaScript API が生やされました。正確には Chrome 138 からすでに拡張機能向けには提供されていたのですが、Chrome 148 でそれが一般の Web ページへも開放された形です。

これは後述の通り、Mozilla と Apple からは反対されており、実際 Web 標準に乗せる上では色々な懸念があるのですが、おもちゃとしては遊び甲斐があり、何か作りたいと思いました。

## 仕組み

Gemini Nano のセッションを二つ作り、それぞれに異なる人格を設定して、交互に発言させています。各セッションには直近数件の会話を渡し、人間が投稿した発言も同じ会話履歴に加えています。

実装を大きく簡略化するとこうです。

```javascript
const create = (name, persona) =>
    LanguageModel.create({
        initialPrompts: [{ role: "system", content: `あなたの名前は ${name} です。人格: ${persona}\n日本語で2〜3文の短い雑談を返してください。` }],
    });

const a = await create("さんぽ", "穏やかで聞き上手");
const b = await create("こもれび", "明るく好奇心旺盛");
const history = [];

for (let turn = 0; ; turn++) {
    const [name, session] = turn % 2 === 0 ? ["さんぽ", a] : ["こもれび", b];
    const reply = await session.prompt(`直近の会話:\n${history.slice(-8).join("\n") || "（まだ会話はありません）"}`);
    history.push(`${name}: ${reply.trim()}`);
    console.log(history.at(-1));
}
```

加えて私が作成したサイトでは、動作が重くなりすぎたりコンテキストが膨らんで動作異常を起こすのを防ぐため、一定の条件でセッションを破棄し再生成するというような工夫もしています（応答のたびに再生成した方が良い気もしていて、この辺りは変えるかもしれません、むずかしい）。

実際のロジックは[こちら](https://github.com/tamiroh/ai2ai/blob/main/src/useConversation.ts)をご覧ください。

## 技術スタック等

- **UI フレームワーク**: Preact
    - React で UI 書きたいけど最近のリッチな機能は別に要らないんだよなというときに適してます
    - 余談ですが、Preact のコードベースを見るとびっくりするほどシンプルで勉強になります
- **CSS**: Emotion
    - 当初は Panda CSS を使っていたのですが、よくよく考えたら「コンポーネントに CSS を書ける」「CSS を型安全に書ける」が出来れば良いと思い [Emotion に切り替えました](https://github.com/tamiroh/ai2ai/commit/b0ebb87313337693b2e2c9c46b83151b86ca77ab)
- **デプロイ先**: GitHub Pages
    - 無料でサクッとデプロイできて便利ですよね
- **ディレクトリ構成**: [src/ 以下は完全フラット](https://github.com/tamiroh/ai2ai/tree/main/src)
    - ディレクトリは浅ければ浅いほど良いです
    - 可能なら完全フラットがベストと個人的に思ってます

## ハマったところ

Claude にプロトタイプを書かせたところ、Prompt API の長い型定義を全部手書きしてきました。実際には [@types/dom-chromium-ai](https://www.npmjs.com/package/@types/dom-chromium-ai) が提供されてるのでこちらをインストールしましょう。

なお、今改めて Claude に書かせてみたところ、やはり型定義を手書きしたので、人間が教えてあげる必要がありそうです。あるいは、この記事がコーディングエージェント達へ届くようになればいいのですが。


## 感想

### 使い勝手の面

正直 AI の発言についてはかなりポンコツなところがあります。今のところ気になるのは

- 長時間放置してると、同じことを互いに言い合うだけの虚無になる（あとなぜか絵文字が増えていく傾向あり）
- ユーザーが会話に混ざると AI の発言が壊れ始めやすい

あたりでしょうか。

あと当初はもっと素朴な UI だったのですが、チャット風の画面にしただけでも楽しさが倍増したので、UI は大事だなと思いました。

### Prompt API について

Prompt API については、Mozilla と Apple が反対しており、両者の主張をざっくりまとめると、

- Mozilla
    - [相互運用性に懸念がある](https://github.com/mozilla/standards-positions/issues/1213#issuecomment-4347988313)
    - LLM はモデルごとに特性が異なるため、プロンプトが特定モデル向けに最適化され、ロックインが生じるおそれあり
    - その結果として、Google の提供するモデル以外へ差し替えることが事実上困難になるかもしれない
    - また、後方互換性のため、既存モデルを新しいバージョンへアップデートしにくくなる可能性がある
- Apple (WebKit)
    - [相互運用性やプライバシーに懸念がある](https://github.com/WebKit/standards-positions/issues/495#issuecomment-4356846488)
    - 相互運用性については Mozilla の主張と同じような懸念
    - 加えて、AI 推論の実行についてユーザーの同意を得る仕組みがなく、ウェブサイトが CPU / GPU / バッテリーを勝手に消費できてしまう
    - そもそも今の API がすべてのプラットフォームで同様に成立するかどうかも怪しい
    - プライバシーの問題もある。モデルが利用可能か等の情報がフィンガープリントになる

というような感じです。

個人的にも、もっともだなと思います。おもちゃとしては大変面白いのですが、標準 API という観点で見るとなかなかに怪しい点があります。そしてこれらの反対にもかかわらず Chrome では正式リリースされてしまった。

そういうわけで色々と複雑な気持ちはあるのですが、ひとまず今回は「誰の PC でもウェブサイトに来ただけで AI とふれあえる」という体験をプロトタイプできた点は良かったかなと思ってます。あとは、Web 標準に対し AI 関連機能がどう取り込まれていくか、注視していきたいです。
