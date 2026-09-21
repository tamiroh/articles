---
title: "【Laravel】コマンドのオプション指定を対話形式で行えるようになる"
url: "https://qiita.com/tamiroh/items/ddfd4a5d618de1573288"
created_at: "2023-02-02T09:28:02+09:00"
updated_at: "2024-08-18T00:31:28+09:00"
tags: ["PHP", "Laravel", "Laravel9"]
---

## 何が実現するのか？

2023 年 1 月 23 日に以下の PR がマージされました。

https://github.com/laravel/framework/pull/45629

そして 2023 年 2 月 1 日の v9.49.0 で上記変更分がリリースされました。

これにより、以下が実現します。

- **`make:*` コマンドのオプション指定を対話形式で行えるようになる**
- **既存コマンドを対話形式のオプション指定に容易に対応できるようになる**

一つずつ見ていきましょう。

## `make:*` コマンドのオプション指定を対話形式で行えるようになる

多くの Laravel ユーザーにとって真っ先に恩恵があるのはこれでしょう。今回の PR により、`make:*` コマンドが対話形式でのオプション指定に対応しました。

例えば `make:model` だと、これまでは引数が足りない場合以下の通りにエラーが発生しました。

![](https://user-images.githubusercontent.com/4977161/212221423-c6b62de6-cf87-47fc-b55f-752c38d801bc.png)

が、今回の PR により、必要な引数を省略した場合は以下の通りに対話形式で項目を埋めていくことが出来るようになりました。

![](https://user-images.githubusercontent.com/4977161/212221750-dd25cceb-2f7d-42f7-90c5-37058edc6396.png)

これまででも `php artisan make:model --help` というふうに `--help` オプションを付ければ引数の形式を確認出来たのですが、より一層分かりやすくなりましたね。

## 既存コマンドを対話形式のオプション指定に容易に対応できるようになる

以下の通り、`PromptsForMissingInput` インターフェースを実装することで対応ができます。

```php
use Illuminate\Console\Command;
use Illuminate\Contracts\Console\PromptsForMissingInput;

class MyCommand extends Command implements PromptsForMissingInput
{
    // ...
}
```

`PromptsForMissingInput` 自体は空っぽなので何かのメソッドの実装を強要されるわけではありませんが、以下のメソッドをオーバーライドすることでプロンプトの表示や挙動をカスタムすることが可能です。

### 1. `promptForMissingArgumentsUsing`

ある特定のオプションについての質問文を指定します。`make:*` コマンドは一律で以下の通りになっています。

```src/Illuminate/Console/GeneratorCommand.php
    ...
    /**
     * Prompt for missing input arguments using the returned questions.
     *
     * @return array
     */
    protected function promptForMissingArgumentsUsing()
    {
        return [
            'name' => 'What should the '.strtolower($this->type).' be named?',
        ];
    }
    ...
```

### 2. `afterPromptingForMissingArguments`

対話形式で必須引数を埋めた後の処理をフックとして追加できます。デフォルトでは空です。

`make:model` の場合は下記の通り実装されてます。ファクトリーやマイグレーションなどを追加で作成するかどうか尋ねてますね。

```src/Illuminate/Foundation/Console/ModelMakeCommand.php
    ...
    /**
     * Interact further with the user if they were prompted for missing arguments.
     *
     * @param  \Symfony\Component\Console\Input\InputInterface  $input
     * @param  \Symfony\Component\Console\Output\OutputInterface  $output
     * @return void
     */
    protected function afterPromptingForMissingArguments(InputInterface $input, OutputInterface $output)
    {
        if ($this->didReceiveOptions($input)) {
            return;
        }

        collect($this->components->choice('Would you like any of the following?', [
            'none',
            'all',
            'factory',
            'form requests',
            'migration',
            'policy',
            'resource controller',
            'seed',
        ], default: 0, multiple: true))
        ->reject('none')
        ->map(fn ($option) => match ($option) {
            'resource controller' => 'resource',
            'form requests' => 'requests',
            default => $option,
        })
        ->each(fn ($option) => $input->setOption($option, true));
    }
    ...
```

## まとめ

Laravel を使っていると artisan コマンドを使うことはよくありますが、引数などの細かい仕様は忘れがちです。これによりスムーズに使えるようになったり、これまで気付かなかったオプションに気付けたりなどあると思うとささやかながらも便利になったなあと思います。

こういう細かいけど質の向上に寄与するコントリビューションはいいですね。
