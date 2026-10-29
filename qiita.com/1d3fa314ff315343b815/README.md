---
title: "Flow で React 書いてみた 2026"
url: "https://qiita.com/tamiroh/items/1d3fa314ff315343b815"
created_at: "2026-10-28T19:50:48+09:00"
updated_at: "2026-10-28T21:16:38+09:00"
tags: ["React", "flow", "flowtype", "TypeScript"]
---

## Flow とは？

React はこの記事を読む方ならご存知だと思います。しかし Flow となると、ぐっと認知度は下がるのではないでしょうか？

実際、TypeScript が事実上の標準となった今、Flow の名を聞くことは非常にまれになってきていると思います。

ではFlow とは何なのかというと、これは Meta が開発している JavaScript の「方言」です。

https://flow.org/

公式ページで真っ先に書かれている通り、現在その見た目はかなり TypeScript に酷似しています。

```typescript
type User = {
  readonly name: string,
  readonly age: number,
  readonly metadata: unknown,
};
function get<K extends keyof User>(user: User, key: K): User[K] {
  return user[key];
}
declare const user: User;
const age: number = get(user, 'age');
```

……少しややこしいのですが、Flow は TypeScript と違って独立した言語を自称していません。あくまで型のシンタックスを含んだ JavaScript の方言であり、拡張子も `.js` です。

## Flow で React を書いてみたいと思った

Flow と React は共に Meta により開発されています。そして React のコードベース自体が、Flow により記述されています。

https://github.com/react/react

実際にファイルを開いてみると、`.js` 拡張子なのに TypeScript みたいな記述が見られますね。そして冒頭に `@flow` というコメントが書かれています。これが Flow です。

https://github.com/react/react/blob/main/packages/react/src/ReactHooks.js

さらに面白いことに、Flow には React 固有の構文がいくつか用意されています。一望してみましょう。


```jsx
// @flow
import * as React from 'react';
import {useState, useRef} from 'react';

// ---------------------------------------------
// hook 構文により React Hook を定義
// ---------------------------------------------

// 通常の関数と区別され、Hook の呼び出し規則を型検査できる
hook useCounter(initial: number) {
  const [count, setCount] = useState(initial);
  return {count, increment: () => setCount(c => c + 1)};
}

// ---------------------------------------------
// component 構文により React コンポーネントを定義
// ---------------------------------------------

// Props は引数として宣言でき、デフォルトで readonly
component Item(label: string) {
  return <li>{label}</li>;
}

// renders* で描画可能なコンポーネントを型レベルで制約
// * は 0 個以上、? は 0〜1 個、無印はちょうど 1 個
component List(children: renders* Item) {
  return <ul>{children}</ul>;
}

// Item を描画することを保証するコンポーネント
component SpecialItem() renders Item {
  return <Item label="Special" />;
}

// ジェネリクスにも対応
// ref は特別な引数として宣言でき、forwardRef を明示する必要がない
// (実は React 19 だと TypeScript でもこう書けますが)
component Button<T>(
  value: T,
  onClick: (T) => void,
  ref: React.RefSetter<HTMLButtonElement>,
) {
  return <button ref={ref} onClick={() => onClick(value)}>Click</button>;
}

// コンポーネントから Props 型を抽出
type ButtonProps = React.PropsOf<Button<number>>;

// コンポーネント自体の型も表現できる
type ItemComponent = component(label: string);

// ---------------------------------------------
// 上記を組み合わせる
// ---------------------------------------------

export default component App() {
  const {count, increment} = useCounter(0);
  const buttonRef = useRef<HTMLButtonElement | null>(null);

  return (
    <>
      <List>
        <Item label="Normal" />
        <SpecialItem />
        {/* <div>Invalid</div> は型エラー */}
      </List>
      <Button value={count} onClick={increment} ref={buttonRef} />
    </>
  );
}
```

面白いですね！

React が JavaScript に持ち込んだ独自の意味論を、言語構文と型システムに取り込んでいます。

さらに Flow は、React のルールに反する書き方や、React アプリケーションでバグにつながりやすいパターンを静的に検出します。例えば、コンポーネントには以下の制約があります。

- 戻り値が `React.Node` に代入可能であることが必須
- すべての分岐で明示的に `return` することが必須
- `this` 使用禁止
- 別のコンポーネントや Hook の内部で定義してはいけない
- 通常の関数として呼び出してはいけない

Hook も同様に専用の制約があり、条件付き呼び出しなどが検出されます。

## TypeScript より全体的に厳格寄りなのも良さそう

TypeScript ユーザー向けの解説は以下に充実しています。

https://flow.org/en/docs/flow-vs-typescript/

充実しすぎてかなり長いので、普段から React + TypeScript のコードベースを保守している筆者の観点で、特に興味深いと思った **「Flow にあって TypeScript に無いもの」** をピックアップしてみます。

### `as` による型アサーションが厳格

TypeScript の `as` はエスケープハッチとして便利なのですが、明らかに不安全な型アサーションも通してしまいます。

例えば、以下のコードは TypeScript ではコンパイルエラーになりません。

```typescript
const user = {id: 1} as {
  id: number;
  name: string;
};

user.name.toUpperCase(); // 実行時エラー 💥
```

Flow ではこのような型アサーションは型エラーです。型アサーションであっても、元の型から代入可能な型への変換しか許可しません。

一応、`as any as Foo` と書くことで型検査をごまかすことは可能ですが、この抜け穴すらも、Flow 組み込みの `unclear-type` という lint ルールにより阻止することが可能です。

### Opaque Type がある

TypeScript では、例えば `UserId` と `PostId` を同じ `string` で表現しつつも誤って混同しないように Branded Type というテクニックが使われます。

```typescript
type UserId = string & {readonly __brand: 'UserId'};
type PostId = string & {readonly __brand: 'PostId'};
```

ただ、これはどことなく無理やりというか、ハッキーな感じがします。構造的型システムを採用する TypeScript ではこうしたイディオムに頼らざるを得ない場面があります。

一方 Flow では、これを Opaque Type として素直に表現できます。

```typescript
// @flow
export opaque type UserId = string;

export function createUserId(value: string): UserId {
  return value;
}
```

定義したファイルの内部では `UserId` を `string` として扱うことができますが、外部からは基底型が隠蔽されます（だから、Opaque = 不透明 なんです）。

したがって、外部から通常の `string` を `UserId` に代入することはできませんし、上述の型アサーションの制限によって `as UserId` による迂回も阻止されます。

Branded Type を専用の言語機能として、より素直で堅牢に実現できるわけですね！

### `this` の扱いが厳格

JavaScript では、メソッドを取り出すと `this` の参照が失われてしまう場合があります。

```javascript
class Counter {
  count = 0;

  increment() {
    return ++this.count;
  }
}

const counter = new Counter();
const increment = counter.increment;

increment(); // 実行時エラー 💥
```

TypeScript ではこのコードは通りますが、Flow では型エラーです。

現代の React でクラスコンポーネントを書くことはもうほとんど無いので、この地雷を踏み抜く機会もずいぶんと減りましたが、とはいえこれは JavaScript でクラスを扱う上では非常に典型的な罠です。コンパイルタイムで弾かれるのは良いことですね。

### 型ガード関数の実装が正しいかを検証する

TypeScript のユーザー定義型ガード関数は、宣言された型が実装と一致しているかまでは保証しません。

例えば、次のコードは TypeScript では型エラーになりません。

```typescript
type User = {
  id: string;
  name: string;
};

function isUser(value: unknown): value is User {
  return typeof value === 'object' && value !== null;
}
```

が、これは `User` のプロパティを一切検証してないので、明らかに不十分です。

Flow は型ガード関数の実装を検証するので、これは型エラーになります。

型ガード関数は型アサーションと並び、TypeScript では型安全性の一部を開発者自身が保証しなければならない、危ういポイントです。Flow ではその実装まで型検査の対象になるというのは安心感があります。

### オブジェクト型がデフォルトで Exact

TypeScript のオブジェクトは基本的に「開かれている」ので、定義されてないプロパティが存在しても許容されます。

```typescript
type User = {name: string};

const raw = {
  name: 'Alice',
  age: 20,
};

const user: User = raw; // OK
```

Flow では上記は型エラーです。

というのも、Flow では `{ name: string }` はデフォルトで Exact Object Type となるため、余計なプロパティの存在を拒否するからです。

余分なプロパティを許容したい場合は、次のように明示します。

```typescript
type User = {name: string, ...};
```

これにより、型に宣言されてないプロパティが実際には存在した、という事態を型検査のレベルで排除できます。例えば、オブジェクトの全プロパティを列挙する処理などですね。

無論、実際に React + TypeScript でコードを書く上で、オブジェクト型が Exact ではないことにより困ることは比較的稀なのですが、TypeScript との対比で特に厳格に見える点として注目の価値はあります。

### エラー抑制の対象を限定できる

TypeScript には `@ts-expect-error` がありますが、基本的には次の行で発生する型エラーをすべて抑制します。

Flow では、エラーコードを指定して抑制対象を限定することができます。

```typescript
// @flow

const obj = {name: 'Alice'};

// $FlowFixMe[prop-missing]
const age = obj.age;
```

`FixMe` と書かせるのはセンスいいですね。

### `match` によるパターンマッチング

Flow には、TypeScript には無い `match` 構文が存在します。

```typescript
// @flow
type Result =
  | {type: 'success', value: number}
  | {type: 'error', message: string};

declare const result: Result;

const text = match (result) {
  {type: 'success', const value} => `Value: ${value}`,
  {type: 'error', const message} => `Error: ${message}`,
};
```

素敵ですね！

`switch` と違って式として扱うことができ、パターンマッチと値の取り出しを同時に行えます。

さらに網羅性も型検査されるため、ユニオン型に新しいバリアントが追加されたとき、対応する処理を書き忘れるとコンパイルエラーになります。

もちろん TypeScript でも、

- [ts-pattern](https://github.com/gvergnaud/ts-pattern) を使用する
- `switch` を使いつつ `never` で網羅性を強制する

などの選択肢がありますが、構造的なパターンマッチと網羅性チェックを簡潔な専用構文で表現できるのは十分に魅力的です。

### 可変配列が不変 (invariant)

TypeScript では、可変配列の要素型が共変 (covariant) として扱われます。なので以下はコンパイルを通りますが、実行時にエラーとなります。

```typescript
const numbers: number[] = [1, 2, 3];
const values: (number | string)[] = numbers;

values.push('hello');

numbers[3].toFixed(); // 実行時エラー 💥
```

Flow では、可変配列を不変 (invariant) として扱うため最初の代入は拒否されます。

## 書いてみた

実際に書いてみた成果物です。動かすのは[こちら](https://tamiroh.github.io/spiral-explorer/)から。

[ウラム螺旋](https://ja.wikipedia.org/wiki/%E3%82%A6%E3%83%A9%E3%83%A0%E3%81%AE%E8%9E%BA%E6%97%8B)という、自然数を渦巻き状に配置し、素数だけ強調表示したフィールドを閲覧できるアプリです。題材自体は、そのときポッと思いついただけで深い意図は無いです。

https://github.com/tamiroh/spiral-explorer

技術構成は下記の通りです。

- **ビルド:** Vite + Babel（`@rolldown/plugin-babel` 経由）
    - Flow 自体は型検査のみで、実行可能な JavaScript にするためには、今回の Vite 中心の構成だと Babel + `@rolldown/plugin-babel` が必要でした
    - Babel 以外にも [flow-remove-types](https://flow.org/en/docs/tools/flow-remove-types/) という軽量な型シンタックス除去ツールも提供されています
- **フォーマッター:** Prettier
    - プラグインとして `@prettier/plugin-hermes` を導入する必要があります
    - あと今回はなんとなく、Meta 社内のスタイルに少し寄せてます
- **リンター:** ESLint
    - ESLint パーサーとして `flow-eslint` を導入する必要があります

今回のアプリケーションの場合、グリッドの座標と画面上の連続的な座標の二種類を使う必要があり、構造的型付けだとどちらも `{x: number, y: number}` となって型システム上区別がつかないので、Opaque type を使用しています。

画面上の連続的な座標:

https://github.com/tamiroh/spiral-explorer/blob/0774d6140d21b9177805a6b0c2f8f0b3795e6563/src/math.js#L8-L15

グリッド座標:

https://github.com/tamiroh/spiral-explorer/blob/0774d6140d21b9177805a6b0c2f8f0b3795e6563/src/patterns.js#L11-L18

あとはこんな感じで、React 固有の構文をいくらか触っています。

https://github.com/tamiroh/spiral-explorer/blob/0774d6140d21b9177805a6b0c2f8f0b3795e6563/src/renderer.js#L275-L298

https://github.com/tamiroh/spiral-explorer/blob/0774d6140d21b9177805a6b0c2f8f0b3795e6563/src/App.jsx#L54-L216

## ハマったところ・微妙なところ

上記で Flow をかなり褒めたので、今度は実際に書いてみてハマったところや微妙なところについて述べます。

### react-dom 19 の型定義が無い

一番驚いた点です。

react-dom のバージョン 19.x（最新版）の型定義が存在しません（2026 年 10 月時点）。

TypeScript でいうところの [DefinitelyTyped](https://github.com/definitelytyped/definitelytyped) に相当するリポジトリとして [flow-typed](https://github.com/flow-typed/flow-typed) が存在します。するのですが、react-dom について存在するのは v16 から v18 までで、最新の v19 はありません。

なお、react-dom ではなく react の型定義は Flow に内蔵されているので、こちらは問題無しでした。とはいえ、react-dom の型定義が公式に存在しないのは予想外で、手書きする必要に迫られました。実際、[必要な範囲だけ手書きしました。](https://github.com/tamiroh/spiral-explorer/blob/main/flow-typed/react-dom.js)

### サードパーティの型定義が明確に不足してる

react-dom に限らず、全般的に型定義が不足していたり、更新されず放置されたりしています。これは Flow を採用する上ではおそらく最大の障壁だと思います。

上述の通り、サードパーティの型定義の中心リポジトリは [flow-typed](https://github.com/flow-typed/flow-typed) ですが、README で公式も認めている通り、更新が鈍化してきています。日々様々なパッケージが現れ更新されていく中でこの状況は、Flow に手を出しにくい大きな要因になるでしょう。

### 公式で推奨される ESLint ルールが ESLint v10 に追従できてない

Flow 公式の ESLint セットアップでは [eslint-plugin-ft-flow](https://github.com/flow-typed/eslint-plugin-ft-flow) が推奨されますが、これは最新の v10 に追従できていません。Flat config にも正式対応しておらず、公式の設定例もすでにレガシーな `.eslintrc` 形式で書かれています。

### GitHub 上でシンタックスハイライトが崩壊する

地味ではあるものの残念なポイントです。

Flow の拡張子は `.js` ないし `.jsx` なので、GitHub 上ではそのまま JavaScript として扱われてしまいます。が、普通の JavaScript にはまったく無いシンタックスが次々に登場するので、シンタックスハイライトが崩れてしまいます。

### 世の中が TypeScript 前提になってる

Flow はまったく悪くないのですが、世の中すでに TypeScript 前提の世界になっています。今回作ったリポジトリで言えば、Vite 自身は Flow に対応してないため、追加で下記の依存が必要となります。

| パッケージ名 | 何に使うか |
|---|---|
| @rolldown/plugin-babel | Vite / Rolldown と Babel の連携 |
| @babel/core | Babel 本体 |
| @babel/preset-flow | Flow の型注釈を除去 |
| flow-parser | component・hook・match などを解析 |

……ちょっと多いですよね！

JavaScript（の方言）であるにもかかわらず、JavaScript のツールを使うためにこれだけの依存が `devDependencies` に入り込んでくるのは、少し重たいです。昨今のサプライチェーン攻撃の増加を考えると、依存はなるべく減らしたいのが本音。

一応、[SWC](https://swc.rs/docs/usage/flow) を代わりに使えば依存を減らすことができるのですが、これは Meta から独立したサードパーティなので、新しい構文が追加されたときの追従状況や互換性には注意する必要があります。そしてそもそも、TypeScript であればこういったツールチェーンの選定に悩まされなくていいところを、Flow では考える必要が出てきます。こういった面でやはり TypeScript に比べるとやや不利になると感じます。

## まとめ

### 良かったこと

- Flow で React を書いてみたら、Flow の言語としての世界に魅力を感じた
- React 独自の意味論を言語構文と型システムに取り込んでいるのはとても面白い
- 型アサーションの厳格さや Opaque Type など、TypeScript 単体では実現できなかったり、できたとしても工夫の必要な部分が素直に書けるのも素晴らしい

### 気になったこと

- しっかりアプリケーションを組む用途を考えるとエコシステムの弱さが気になる
- Flow の思想に惹かれる部分もあるが、実際のプロダクトで TypeScript の代わりに採用できるかというと正直厳しい

### 結論

- とはいえ、TypeScript が事実上の標準となった現代でも進化し続けている Flow の動向は気になるし、今後もウォッチしていきたい
- それはそうと、[JavaScript に `match` が来るのはまだでしょうか？](https://github.com/tc39/proposal-pattern-matching)
