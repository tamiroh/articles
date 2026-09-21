from email.message import Message
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError
from urllib.response import addinfourl

from scripts.sync_qiita import QiitaArticle, fetch_articles, sync_articles


def article(
    *,
    id: str = "0123456789abcdef0123",
    title: str = 'テスト: "記事"\nタイトル',
    body: str = "## 本文\n\n```python\nprint('hello')\n```\n",
    private: bool = False,
) -> QiitaArticle:
    return {
        "id": id,
        "title": title,
        "body": body,
        "url": "https://qiita.com/example-user/items/0123456789abcdef0123",
        "created_at": "2026-01-01T00:00:00+09:00",
        "updated_at": "2026-01-02T00:00:00+09:00",
        "tags": [{"name": "Python", "versions": []}],
        "private": private,
    }


def response(items: list[QiitaArticle], link: str = "") -> addinfourl:
    headers = Message()
    headers["Link"] = link
    return addinfourl(io.BytesIO(json.dumps(items).encode()), headers, "https://qiita.com", code=200)


class SyncQiitaTests(unittest.TestCase):
    @patch("scripts.sync_qiita.urlopen")
    def test_pagination_without_authentication(self, urlopen: MagicMock) -> None:
        urlopen.side_effect = [
            response([article()], '<https://qiita.com/api/v2/users/example-user/items?page=2>; rel="next"'),
            response([article(id="a" * 20)], '<https://qiita.com/api/v2/users/example-user/items?page=1>; rel="prev"'),
        ]
        self.assertEqual(len(fetch_articles("example-user")), 2)
        self.assertIn("page=2&per_page=100", urlopen.call_args.args[0].full_url)
        for call in urlopen.call_args_list:
            self.assertIsNone(call.args[0].get_header("Authorization"))

        urlopen.side_effect = [response([])]
        self.assertEqual(fetch_articles("example-user"), [])
        self.assertIsNone(urlopen.call_args.args[0].get_header("Authorization"))

    @patch("scripts.sync_qiita.fetch_articles")
    def test_markdown_updates_are_stable_and_archives_are_retained(self, fetch: MagicMock) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fetch.return_value = [article(), article(id="b" * 20, private=True)]
            sync_articles("example-user", root=root)
            path = root / article()["id"] / "README.md"
            original = path.read_bytes()
            self.assertTrue(original.decode().endswith(article()["body"]))
            self.assertEqual(json.loads(original.decode().splitlines()[1][7:]), article()["title"])
            self.assertEqual(list(root.rglob("*.md")), [path])

            sync_articles("example-user", root=root)
            self.assertEqual(path.read_bytes(), original)
            fetch.return_value = [article(title="新タイトル", body="更新本文")]
            sync_articles("example-user", root=root)
            self.assertTrue(path.read_text().endswith("更新本文"))
            self.assertEqual(list(root.rglob("*.md")), [path])

            fetch.return_value = []
            sync_articles("example-user", root=root)
            self.assertTrue(path.exists())

    @patch("scripts.sync_qiita.urlopen")
    def test_later_page_failure_leaves_archive_untouched(self, urlopen: MagicMock) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            existing = root / article()["id"] / "README.md"
            existing.parent.mkdir()
            existing.write_text("existing content")
            urlopen.side_effect = [
                response([article()], '<https://qiita.com/api/v2/users/example-user/items?page=2>; rel="next"'),
                HTTPError("https://qiita.com", 429, "Too Many Requests", Message(), None),
            ]
            with self.assertRaises(HTTPError):
                sync_articles("example-user", root=root)
            self.assertEqual(existing.read_text(), "existing content")

    @patch("scripts.sync_qiita.fetch_articles")
    def test_invalid_article_does_not_write_partial_archive(self, fetch: MagicMock) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fetch.return_value = [article(), article(id="../../outside")]
            with self.assertRaises(ValueError):
                sync_articles("example-user", root=Path(directory))
            self.assertEqual(list(Path(directory).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
