---
title: "GitHub の Issues を Markdown 形式で出力する"
url: "https://qiita.com/tamiroh/items/8cc509bc791dcc5048c5"
created_at: "2022-12-24T10:51:26+09:00"
updated_at: "2022-12-24T10:51:26+09:00"
tags: ["JavaScript", "GitHub", "Markdown"]
---

# 背景

私は手元の Markdown ファイルにタスクを書き出すことが多いのですが、その際に GitHub の Issues をタスクとして持ってきたいことがしばしばありました。数が少なければ普通にコピペで十分なのですが、多かったりすると大変です。

ということで楽にできる方法を考えました。

# 手順

1. GitHub の Issues を開く
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/1248726/158f1e21-6e5a-8f7c-d81f-04b57b348153.png)
2. 開発者ツールを開き、コンソールで下記コードを実行する
    ```javascript
    console.log(Array.from(document.getElementsByClassName('h4')).reduce((carry, e) => e.href ? carry + '- [' + e.innerText + '](' + e.href + ')\n' : '', ''));
    ```
3. 出力結果をコピペする
    ```markdown
    - [Out of bounds handling for non-US keyboards](https://github.com/vlang/vinix/issues/104)
    - [Vinix kernel panic on pressing the tab key](https://github.com/vlang/vinix/issues/103)
    - [V panic spam when typing 'vim'](https://github.com/vlang/vinix/issues/100)
    - [Add more than one keyboard layout](https://github.com/vlang/vinix/issues/83)
    - [Vinix halts when pressed keys '(' and ')' in vim or nano](https://github.com/vlang/vinix/issues/79)
    - [question: Can a screen reader be built/ported to this system](https://github.com/vlang/vinix/issues/78)
    - [shell: Number of characters per line limited by screen](https://github.com/vlang/vinix/issues/51)
    - [trying to move cursor in nano inserts capital letters](https://github.com/vlang/vinix/issues/41)
    - [building with v creates weird file](https://github.com/vlang/vinix/issues/39)
    - [OsDev Tutorial ](https://github.com/vlang/vinix/issues/16)
    - [Resources & ideas for inspiration](https://github.com/vlang/vinix/issues/5)
    - [Logo suggestion](https://github.com/vlang/vinix/issues/3)
    ```

# 補足

Pull requests でも使えます。
