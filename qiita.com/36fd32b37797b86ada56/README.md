---
title: "【PHP8】match 式のこれまでとこれから"
url: "https://qiita.com/tamiroh/items/36fd32b37797b86ada56"
created_at: "2022-12-25T18:37:11+09:00"
updated_at: "2026-08-30T23:50:16+09:00"
tags: ["PHP", "パターンマッチ", "switch", "match", "PHP8"]
---

PHPer のみなさん、`match` は好きでしょうか？

私は結構好きです。

というのも、`switch` だと以下のように書く必要があるものを……

```php
$say = "";

switch (idate("w")) {
    case 0:
        $say = "weekend!";
        break;
    case 1:
    case 2:
    case 3:
    case 4:
    case 5:
        $say = "weekday :(";
        break;
    case 6:
        $say = "weekend!";
}

echo "Today is $say";
```

`match` では以下の通り短く記述することができるからです。

```php
$say = match (idate("w")) {
    0 => "weekend!",
    1, 2, 3, 4, 5 => "weekday :(",
    6 => "weekend!",
    default => "",
};

echo "Today is $say";
```

コード量が少ないのはもちろんのこと、変数の代入操作などが減って処理の見通しがより良いですし、バグが入り込む余地も減りました。`match` は可読性と安全性に強く貢献する構文と言えます。

しかし `match` が取り入れられるまでには少しの紆余曲折がありました。この記事では、`match` が導入されるまでの経緯から、`match` の今後までを追っていきます。

## 元々は `switch` の拡張として構想された

`match` に至るまでの道筋を過去に辿っていくと、以下の RFC にたどり着きます。これが `match` の直接の起源とみて良いと思います。

https://wiki.php.net/rfc/switch-expression-and-statement-improvement

https://externals.io/message/107551#107553

この RFC で提案されたのは、`switch` 文の改善と `switch` 式の導入です。具体的には下記の通りになります。

```php
// switch 文の改善
switch (date("w")) {
    case 0:
        $say = "weekend!";
        break;
    case 1, 2, 3, 4, 5:
        $say = "weekday :(";
        break;
    case 6:
        $say = "weekend!";
}
echo "Today is $say";

// switch 式の導入
$say = switch (date("w")): string {
    case 0 => "weekend!";
    case 1, 2, 3, 4, 5 => "weekday :(";
    case 6 => "weekend!";
};
echo "Today is $say";
```

見ての通りですが、ここではまだ `match` というキーワードは登場していません。あくまで `switch` のままです。一方、ここでは従来の `switch` とは異なり 4 つの新しい要素が導入されています。

:::note info
念の為の確認ですが、**式**と**文**の違いは大丈夫でしょうか？

**式**とは値を表すもので、変数に代入することができます。例えば上記の `switch` 式は合致したケースの値を表し、`$say` 変数に代入することができます。

一方で**文**とは処理の 1 ステップであり、値を表すものではありません。したがって式のように変数に代入することはできません。

ここでは簡潔かつ一般的な説明に留めますが、PHP における式と文についてもう少し知りたい場合は例えば以下の資料を参照してみるとよいでしょう。

- [PHPの文と式 - Qiita](https://qiita.com/tadsan/items/bd761ec3d33cc2c65cdf#%E5%BC%8Fexpression-expr%E3%81%A8%E3%81%AF%E4%BD%95%E3%81%8B)
- [PHP: 式 - Manual](https://www.php.net/manual/ja/language.expressions.php)

:::

### 1. コンマ区切りによる複数値の指定

従来の `switch` では、複数の値に合致する `case` を実現するには以下の通りに記述する必要がありました。

```php
switch (date("w")) {
    case 0:
        $say = "weekend!";
        break;
    case 1:
    case 2:
    case 3:
    case 4:
    case 5:
        $say = "weekday :(";
        break;
    case 6:
        $say = "weekend!";
}
echo "Today is $say";
```

これだとコードが縦に伸びて見づらいですね。これがこの RFC では以下の通りに書き直すことができます。

```php
switch (date("w")) {
    case 0:
        $say = "weekend!";
        break;
    case 1, 2, 3, 4, 5:
        $say = "weekday :(";
        break;
    case 6:
        $say = "weekend!";
}
echo "Today is $say";
```

カンマで複数値をまとめて指定することで記述量が減り、見やすくなりました。

### 2. `switch` の式としての利用

記事の冒頭で挙げた `switch` によるコードを見てみると、すべての `case` で `$say` 変数に値を格納し、それを `echo` で出力する際に埋め込んでいることがわかります。しかし `switch` 式を利用すれば、`switch` そのものが値を返すがゆえに以下の通りに書き直せます。

```php
$say = switch (date("w")) {
    case 0 => "weekend!";
    case 1, 2, 3, 4, 5 => "weekday :(";
    case 6 => "weekend!";
};
echo "Today is $say";
```

より記述が簡素になり、`$say` への代入忘れや意図しない上書きなどのトラブルが発生する余地も無くなりました。

:::note info
ただし従来の `switch` 文とは異なり、この `switch` 式は一つの `case` で複数行を記述できません。

この制約は将来的に緩和していく旨が RFC には書かれていますが、後述する通りこの部分の仕様を決めるのは厄介です。
:::

### 3. 返り値の型の指定

`switch` を式として利用する場合に返り値を指定可能とし、型が異なる場合は `RuntimeException` を発生させます。

```php 
$say = switch (date("w")): string { // string 型を返すことを明示
    case 0 => "weekend!";
    case 1, 2, 3, 4, 5 => "weekday :(";
    case 6 => "weekend!";
};
echo "Today is $say";
```

上記の例のように、`switch` から返す値の型は同じであることが多いため、仕様としては妥当と言えそうです。

### 4. いずれにも合致しない場合の実行時エラー

いずれの `case` にも合致しない場合、`RuntimeException` を発生させます。

```php 
$date = "dummy!";
$say = switch ($date): string { 
    case 0 => "weekend!";
    case 1, 2, 3, 4, 5 => "weekday :(";
    case 6 => "weekend!";
};
// RuntimeException が発生
```

これにより、`switch` でしばしば生じる値の考慮漏れに気付きやすくなります。

## 上記 RFC の内容整理と改良

上記の RFC はしばらく荒削りな Draft のままで放置されていました。それを引き継ぐかたちで新たに登場したのが以下の RFC です。

https://wiki.php.net/rfc/switch_expression

https://externals.io/message/109383#109383

この RFC で実現される構文を見てみましょう。

```php
// switch 文
switch (date("w")) {
    case 0:
        $say = "weekend!";
        break;
    case 1, 2, 3, 4, 5:
        $say = "weekday :(";
        break;
    case 6:
        $say = "weekend!";
}
echo "Today is $say";

// switch 式
$say = switch (date("w")) {
    0 => "weekend!";
    1, 2, 3, 4, 5 => "weekday :(";
    6 => "weekend!";
};
echo "Today is $say";
```

`case` が消えてるなどの若干の差分はありますが、前回の RFC と似ていますね。

ここでもまだ `match` は登場せず、あくまで `switch` の拡張にとどまっています。しかし仕様はより深く検討され、他のアプローチとの比較やエッジケースでの動作が明確に説明されています。加えて[実装](https://github.com/php/php-src/pull/5308)まで用意され、PHP 言語に導入する準備は一通り揃えられたかたちです。

この RFC はその後どうなったのでしょうか？

## `switch` から野心的な `match` へ

なんと、前回の RFC から 2 週間ほどで方針は大きく変更されました。その結果として、`switch` とはまた別の構文として `match` が提案されました。

https://wiki.php.net/rfc/match_expression

https://externals.io/message/109590

上記のディスカッションによれば、前回の RFC に対しては主に 3 つの反論があったようです。

1. **ここで示される `switch` の挙動は従来のそれを大きく逸脱しており、もはや `switch` キーワードを使うべきではない**
2. **暗黙の型変換による問題を解決できていない**
3. **RFC の構成が十分に練られていない**

確かに前回の RFC は、`switch` に対して多くの役割を押し付け過ぎなきらいがありました。その一方で暗黙の型変換に起因する問題へ言及しつつも解決には至ってなかったという点で仕様に中途半端さがあったのも否めません。これは結局後方互換性を維持するための苦肉の策でしたが、より仕様を洗練させるために思い切って `match` という新たなキーワードを導入するのは合理的です。

早速、提案された `match` の仕様を見てみましょう。下記の通りです。

```php
match ($condition) {
    1 => {
        foo();
        bar();
    },
    2 => baz(),
}
 
$result = match ($condition) {
    1, 2 => foo(),
    3, 4 => bar(),
    default => baz(),
};
```

`match` を日頃使っている方々なら分かるでしょうが、この仕様は今の `match` とはいくつかの点で異なります。実際のところ PHP 8.0.0 で導入された `match` はよりシンプルなバージョンなのですが、これについては後述します。

ここで提案された `match` には主に二つの側面があります。順番に見ていきましょう。

### 1. `switch` の上位互換としての `match`

元を辿れば、`match` を提案する動機の最たるものが従来の `switch` に対する数々の不満です。そのことを踏まえ、本 RFC では従来の `switch` が出来ることを完全に内包しつつも改善するような仕様が打ち立てられました。具体的な仕様を `switch` が抱える課題ごとに見ていきましょう。

#### 課題 1. `==` で値が比較されるために意図しない結果になることがある

`switch` は `==` で[緩やかに値を比較](https://www.php.net/manual/ja/types.comparisons.php#types.comparisions-loose)します。この場合、暗黙的に型変換が生じるために不可解な挙動を見せることがあります。例えば以下の通りです。

```php
switch ('foo') {
    case 0:
        echo "Oh no!\n";
        break;
}

// 出力結果: Oh no!
```

一方、`match` は常に `===` で[厳密に値を比較](https://www.php.net/manual/ja/types.comparisons.php#type.comparisons-strict)するため、上記のような問題は起こりません。

```php
match ('foo') {
    0 => {
        echo "Oh no!\n";
    },
}

// 出力結果:
```

:::note info
PHP 8.0.0 以降では `==` の挙動が改善され、このような結果にはなりません。詳しくは[比較演算子ページ](https://www.php.net/manual/ja/language.operators.comparison.php)冒頭の「警告」を参照ください 。なお、switch 文が値の比較に `==` を利用するのは現在の最新の PHP においても同様です。
上記では、RFC が提出された当時の極端な例として挙げています。
:::

#### 課題 2. 一時変数を介して値を渡す必要のあるケースが存在する

`switch` は文です。したがって値を返すためには一時変数を媒介する必要があります。

```php
switch (1) {
    case 0:
        $y = 'Foo';
        break;
    case 1:
        $y = 'Bar';
        break;
    case 2:
        $y = 'Baz';
        break;
}
 
echo $y;

//> Bar
```

しかしこれにより余計な行が増えてコードの見通しが悪くなりますし、途中で一時変数が上書きされるなどのトラブルも起こり得ます。

一方 `match` は式であるため、一時変数は不要です。

```php
echo match (1) {
    0 => 'Foo',
    1 => 'Bar',
    2 => 'Baz',
};

//> Bar
```

#### 課題 3. 値の考慮漏れに気づきにくい

以下のコードでは、`switch` 文は `$fruit` の値に応じて標準出力を切り替えます。

```php
class Fruit {
    public const APPLE = 1;
    public const GRAPE = 2;
    public const ORANGE = 3;
}

$fruit = Fruit::ORANGE; // Fruit の定数を格納する変数

// Fruit::ORANGE が case として存在しない
switch ($fruit) {
    case Fruit::APPLE:
        echo "apple";
        break;
    case Fruit::GRAPE:
        echo "grape";
        break;
}

// 出力結果:
```

見ての通り `Fruit::ORANGE` の考慮漏れがあるため `$fruit = Fruit::ORANGE` の場合は何も出力されません。しかしエラーや警告は発生しないため気づくのが難しいでしょう。

一方、`match` はいずれの `case` にもマッチしない場合に実行時エラーを発生させます。これにより、`case` の考慮漏れに気づきやすくなります。

```php
class Fruit {
    public const APPLE = 1;
    public const GRAPE = 2;
    public const ORANGE = 3;
}

$fruit = Fruit::ORANGE;

match ($fruit) {
    Fruit::APPLE => ...,
    Fruit::GRAPE => ...,
}

// Fatal error: Uncaught UnhandledMatchError
```

#### 課題 4. 意図しないフォールスルーによるバグ

`switch` は `break` をしない場合直下の `case` にフォールスルーしますが、これがしばしばバグの元となります。例えば、以下のコードでは `break` を書き忘れているために意図しないフォールスルーが発生しています。

```php
$fruit = Fruit::APPLE;

switch ($fruit) {
    case Fruit::APPLE:
        echo "apple";
        // break を忘れている
    case Fruit::GRAPE:
        echo "grape";
        break;
}

// 出力結果: applegrape
```

一方、`match` は各 `=>` の末尾で暗黙的に `break` を行うので上記の心配がありません。

```php
match ($x) {
    1, 2 => {
        // 1 または 2
    },
    3, 4 => {
        if ($x === 3) {
            // 3
        }
        // 3 または 4
    },
}
```

### 2. パターンマッチの可能性を秘めた `match`

上記 1 では、この RFC で提案される `match` が `switch` の上位互換となることを説明しました。

ところで、`match` はなぜ `match` という名前なのでしょうか？

一般に関数型と呼ばれる言語にある程度習熟している方々なら、`match` というキーワードを聞くとパターンマッチを連想するかと思われます。ここでは例として Scala の `match` 式を挙げましょう。

```scala
import scala.util.Random

val x: Int = Random.nextInt(10)

x match {
  case 0 => "zero"
  case 1 => "one"
  case 2 => "two"
  case _ => "other"
}
```

これはさきほどの RFC での `match` と見た目や動作がかなり似ています。つまり、`case` で示された値と `x` がマッチするかを判定し、マッチすれば `=>` の横の値を評価します。では、以下ではどうでしょう。

```scala
val l = List("A", "B", "C")

l match {
  case List("A", b, c) =>
    println("A", b, c)
  case _ =>
    println("other")
}

```

上記では `l` の `List` としての構造がマッチするかどうかまでを判定の基準としています。さらに変数 `b` と `c` で `List` の要素を捕捉し、`println` で出力までしています。

ここで深く言及するのは避けますが、パターンマッチはスカラー値同士の単なる比較を超えた実に様々な機能を提供するものです。そして今回の RFC で `match` というキーワードを選んだのも、これを PHP に取り入れたいという野望ゆえです。ここに、`switch` の単なる改善・拡張からの脱却を見ることができるでしょう。

しかし今回の RFC では、上で述べたようなリッチなパターンマッチ機能をサポートしません。それは将来的なプランとして別途切り出されています。提案者は実際にいくつか実装を試みたようですが[^6]、パターンマッチはそれ自体のみで十分すぎるほど考慮することが多く、今回の RFC には収めるべきではないと判断したようです[^7]。

## よりシンプルな `match` v2 へ

上述の `match` 式の仕様は `switch` の弱点を克服するもので、加えてパターンマッチへの展望を示した点で野心的でした。しかしそれゆえ仕様が複雑で、結果として RFC は却下されてしまいます[^4]。

これで終わるかと思いきや、なんとまたその一ヶ月後には機能縮小版の `match` v2 が RFC として提出されます。

https://wiki.php.net/rfc/match_expression_v2

https://externals.io/message/110243#110243

コード例を見てみましょう。

```php
match ($condition) {
    1 => foo(),
    2 => baz(),
};

$result = match ($condition) {
    1, 2 => foo(),
    3, 4 => bar(),
    default => baz(),
};
```

上記の通り、基本的には v1 からブロックによる複数行のサポートなどを削ぎ落としたものです。そしてご存知の通り、この v2 が結果としてマージされ、PHP 8.0.0 でリリースされました🎉

## `match` のこれから

ここまでで `match` が PHP に導入されるまでの流れを大まかに追ってきました。`match` は現時点でも十分有用ですが、見ての通り当初の目論見を完全に果たしたとはいえません。`match` は今後どのように進化していくのでしょうか？

### 1. パターンマッチを導入する

:::note info
**2026 年 7 月追記**
以下で説明しているパターンマッチの構文とステータスは、主に 2022 年の執筆時点のものです。その後 [RFC は大幅に改訂され、議論や実装も進展している](https://externals.io/message/129490)ため、現在の提案内容とは異なる部分があります。
:::

第一に挙げられるのは、やはりパターンマッチでしょう。これについてはまだ Draft で実装も存在しませんが、以下の通り RFC が公開されています。

https://wiki.php.net/rfc/pattern-matching

ここで提案されているのは最小限のパターンマッチ機能で、具体的には `is` というキーワードを導入しようというものです。これにより、`match` については以下の記法が可能となります。

```php
$result = match ($somevar) is {
    Foo => 'foo',
    Bar => 'bar',
    Baz|Beep => 'baz',
};
```

一方、`is` は `bool` を評価する二項演算子としても機能します。例えば以下のようなバリエーションがあります。

```php
$foo is string;    // is_string($foo) と等価
$foo is int|float; // is_int($foo) || is_float($foo) と等価
$foo is Request;   // $foo instanceof Request と等価
$foo is User|int;  // $foo instanceof User || is_int($foo) と等価
$foo is ?array;    // is_array($foo) || is_null($foo) と等価

$foo is 5;         // $foo === 5 と等価
$foo is 'yay PHP'; // $foo === 'yay PHP' と等価

class Point {
  public function __construct(public int $x, public int $y, public int $z) {}
}
$p = new Point(3, 4, 5);
$p is Point {x: 3}; // $p instanceof Point && $p->x === 3; と等価
$p is Point {y: 37, x: 2,}; // $p instanceof Point && $p->y === 37 && $p->x === 2; と等価
```

### 2. `(true)` を省略可能にする

`match` を日頃書く方なら共感できるでしょうが、`match` ではしばしば以下のような書き方になることがあります。

```php
$age = 65;

echo match (true) {
    0 <= $age && $age < 18 => "child",
    18 <= $age && $age < 65 => "adult",
    65 <=  $age => "elderly",
};
```

ここでは、カッコの中で指定された値との単純な比較ではなく、単に式を評価した結果 `true` になるものがマッチするという形式になっています。しかしこの場合 `(true)` を省略して、以下のようにも書き換えたくなるでしょう。

```php
$age = 65;

echo match {
    0 <= $age && $age < 18 => "child",
    18 <= $age && $age < 65 => "adult",
    65 <=  $age => "elderly",
};
```

これを実現するというのが `match` の将来的な展望として存在します。

……実のところ `match` がリリースされた直後に以下の通り同様の RFC が実装付きで提出されましたが、残念ながら現時点では放置されています。

https://wiki.php.net/rfc/short-match

`match` v1 の投票では、この点については賛成 16 反対 4 で事実上の可決となっているため、今後早いうちに実装されることを期待したいですね。

https://wiki.php.net/rfc/match_expression

![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/1248726/7d760694-599e-a1e4-8a88-6dadaae26113.png)


### 3. ブロックによる複数行サポートを導入する

最初に `match` が提案された際、特に仕様の複雑さを高めていたのがブロックの存在でした。加えて、ブロックから値を返す方法についてはこの時点で意見がまとまらず別途検討予定とするなどの仕様の中途半端さもありました。ゆえに当初 `match` は否決され、最終的なバージョンではブロックの仕様が削除されたわけです。

現時点ではブロックについて検討が進んでいないようです。しかし私見ですが、`match` という名前に込められた野心を考えるとやはりブロックくらいは欲しいところです。実際、上で挙げた Scala の場合 `match` の各ケースは複数行を記述可能で、仕様として突飛であるわけでも無いはずです。そして日々 `match` を使っていて複数行書きたくなる場面もしばしばです。

……ただし、ブロック内から値を返す方法については確かに決めるのが難しそうです。実際、当初は以下の案が提案されており[^return-block]、

```php
// セミコロンが省略された行を返す
$y = match ($x) {
    0 => {
        foo();
        bar();
        baz() // この値が返却される
    },
};
```

議論の中でその他以下の案も出されましたが、結局意見がまとまりませんでした。

```php
// <= で返す
$y = match ($x) {
    0 => {
        foo();
        bar();
        <= baz(); // この値が返却される
    },
};
 
// pass で返す
$y = match ($x) {
    0 => {
        foo();
        bar();
        pass baz(); // この値が返却される
    },
};
 
// セミコロンの有無に関わらず常に最後の行を返す
$y = match ($x) {
    0 => {
        foo();
        bar();
        baz(); // この値が返却される
    },
};
```

<details><summary>「あれ？」と思った方向けの補足</summary><div>

「あれ？」と思った方がいるかもしれません。少なくとも私は思いました、**単純に `return` でいいのではと。**

```php
$y = match ($x) {
    0 => {
        foo();
        bar();
        return baz(); // この値が返却される
    },
};
```

ブロックから値を返すという挙動なら、`return` が真っ先に思い浮かぶかと思いますし、一番馴染んでいるように思えます。しかし [Match Expression の初期段階の RFC](https://wiki.php.net/rfc/match_expression?rev=1587476559#blocks) を見てみると、ここでの `return` の仕様はすぐ外側の関数からの `return` をするという挙動で定義されていました。

```php
function test() {
    $y = match ($x) {
        0 => {
            foo();
            bar();
            // baz() が test() から返却される、$y に代入されることはない
            return baz();
        },
    };
}
```

RFC の作者は、`match` 式の `return` の仕様について、[メーリスの議論](https://externals.io/message/109590#109602)では以下の通り述べていました。

> `return` は関数から戻るという意味を持ち、ある特定の状況でそれを変更するのは適切ではない。別のキーワード（`pass` など）か、キーワードをまったく必要としない別の構文（私が挙げたブロック式のようなもの）が必要だ。

なるほど、確かに `return` というのはプログラムの制御を呼び出し元に戻す作用を持つもので、主に関数で利用されます。そうすると、`match` 式でだけ特別扱いでこの意味を変えるのはおかしい、という主張は頷けますね。

とすると他の案が必要なわけですが、上記の通りどれもスッキリと来ず、お蔵入りとなってしまったようです。

</div></details>

## おわりに

本記事では、PHP 8.0.0 で導入された `match` について、それが導入されるまでの経緯と今後の展望を RFC や内部メーリスに基づいて追ってきました。`match` とそれにまつわる部分は今後の PHP の書き味を良い方向へ変えていくものと思っていますので、今後の進化を期待してやみません。

また、執筆の際には十分な調査を行ったつもりではありますが、もし内容に誤りなどありましたらコメントや編集リクエストなどお気軽にどうぞ。お待ちしています！

[^1]: https://externals.io/message/109590#109590
[^4]: https://externals.io/message/110243#110250
[^6]: https://github.com/php/php-src/compare/master...iluuu1994:pattern-matching
[^return-block]: https://wiki.php.net/rfc/match_expression?rev=1587406178#blocks
[^7]: https://wiki.php.net/rfc/match_expression#pattern_matching
