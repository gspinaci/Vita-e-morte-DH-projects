import importlib
import sys
import types

import pytest

from dhlife import __main__ as cli


@pytest.mark.parametrize("module", sorted(set(cli.COMMANDS.values()) - {
    "dhlife.crawl", "dhlife.proceedings.grobid_parse", "dhlife.proceedings.extract_urls"}))
def test_every_command_has_main(module):
    assert callable(importlib.import_module(module).main)


@pytest.mark.parametrize("argv, code", [(["dhlife"], 2), (["dhlife", "nope"], 2), (["dhlife", "--help"], 0)])
def test_usage(monkeypatch, capsys, argv, code):
    monkeypatch.setattr(sys, "argv", argv)
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == code
    assert "archive-check" in capsys.readouterr().out


def test_dispatch(monkeypatch):
    received = {}
    fake = types.SimpleNamespace(main=lambda argv: received.update(argv=argv, prog=sys.argv[0]))
    monkeypatch.setattr(cli.importlib, "import_module", lambda name: fake)
    monkeypatch.setattr(sys, "argv", ["dhlife", "stats", "--x", "1"])
    cli.main()
    assert received == {"argv": ["--x", "1"], "prog": "dhlife stats"}
