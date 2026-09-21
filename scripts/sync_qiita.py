"""Qiita の公開記事を Markdown で保存します（Python の標準ライブラリのみ使用）。

使い方（リポジトリのルートから実行）:
    python3 scripts/sync_qiita.py --user example-user

保存先:
    qiita.com/<記事ID>/README.md

毎回すべての公開記事を未認証で取得し、本文とメタデータを保存します。
画像などのアセットは取得しません。取得済みの記事は削除しません。
取得・データ変換が失敗した場合は既存ファイルを更新せず、エラーで終了します。

テスト:
    python3 -m unittest discover -s tests
"""

import argparse
import json
from pathlib import Path
import re
from typing import TypedDict
from urllib.request import Request, urlopen


class QiitaTag(TypedDict):
    name: str
    versions: list[str]


class QiitaArticle(TypedDict):
    id: str
    title: str
    body: str
    url: str
    created_at: str
    updated_at: str
    tags: list[QiitaTag]
    private: bool


def fetch_articles(user: str) -> list[QiitaArticle]:
    articles: list[QiitaArticle] = []
    for page in range(1, 101):
        request = Request(
            f"https://qiita.com/api/v2/users/{user}/items?page={page}&per_page=100",
            headers={"Accept": "application/json", "User-Agent": "qiita-article-archive"},
        )
        with urlopen(request, timeout=30) as response:
            articles.extend(json.load(response))
            if not re.search(r'rel="next"', response.headers.get("Link", "")):
                return articles
    raise RuntimeError("Qiita pagination limit reached; archive was not updated.")


def render_article(article: QiitaArticle) -> str:
    metadata: dict[str, str | list[str]] = {
        "title": article["title"],
        "url": article["url"],
        "created_at": article["created_at"],
        "updated_at": article["updated_at"],
        "tags": [tag["name"] for tag in article["tags"]],
    }
    # JSON values are valid YAML values, including quotes and multiline titles.
    front_matter = "\n".join(
        f"{key}: {json.dumps(value, ensure_ascii=False)}"
        for key, value in metadata.items()
    )
    return f"---\n{front_matter}\n---\n\n{article['body']}"


def sync_articles(user: str, root: Path = Path("qiita.com")) -> None:
    if not re.fullmatch(r"[A-Za-z0-9_-]+", user):
        raise ValueError("Invalid Qiita user ID.")

    # Fetch and render everything before touching the existing archive.
    files: dict[Path, str] = {}
    for article in fetch_articles(user):
        if article["private"]:
            continue
        if not re.fullmatch(r"[0-9a-f]{20}", article["id"]):
            raise ValueError("Invalid Qiita article ID.")
        files[root / article["id"] / "README.md"] = render_article(article)

    root.mkdir(parents=True, exist_ok=True)
    for path, content in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    print(f"Saved {len(files)} public articles to {root}.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--user", required=True, help="Qiita user ID to archive")
    sync_articles(parser.parse_args().user)
