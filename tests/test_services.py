"""
Unit tests for .github/scripts/services.py — the multi-service menu + forward script
driven by .github/services/*.yaml.

Covers:
  - load_services             (file IO, malformed YAML handling)
  - render_menu / render_nag  (markdown shape: anchor / header / table rows / footer)
  - already_anchored          (true/false)
  - match_menu_trigger        (issue_comment / issues.labeled / unknown event)
  - match_forward_command     (forward hit / no hit / handler!=forward 跳过)
  - cmd_menu                  (end-to-end with monkey-patched gh / gh_json: menu / nag / dedupe / no-match)
  - cmd_forward               (end-to-end: success / no DISPATCH_TOKEN / no match)

Run locally: pytest tests/ -v --cov=.github/scripts/services --cov-report=term-missing
"""
from __future__ import annotations

import json
import os
import textwrap
from pathlib import Path
from typing import Any

import pytest

import services  # 由 conftest.py 把 .github/scripts/ 加进 sys.path


# ───────────────────────────── fixtures ─────────────────────────────

@pytest.fixture
def svc_dir(tmp_path: Path) -> Path:
    """Create a temp .github/services/ with one real + one minimal service."""
    d = tmp_path / "services"
    d.mkdir()
    (d / "datacenter.yaml").write_text(textwrap.dedent("""\
        service:
          id: datacenter
          name: 数据中台
          pipeline_repo: opensourceways/om-datacenter
        menu:
          trigger: "[数据中台需求]"
          required_label: accepted
          header: "🤖 数据中台需求 — 可用命令"
          intro: "intro 文字"
          footer: "> footer 文字"
        commands:
          - id: analyze
            triggers: ["[数据中台需求分析]", "[小数需求分析]"]
            handler: in-repo
            title: "`[小数需求分析]`"
            description: "AI 把需求理清楚"
          - id: implement
            triggers: ["[数据中台需求实现]", "[小数需求实现]"]
            handler: forward
            forward:
              repo: opensourceways/om-datacenter
              event_type: backlog_implement
            title: "`[小数需求实现]`"
            description: "需求分析说明书合入后再评"
          - id: release
            triggers: ["[数据中台需求上线]", "[小数需求上线]"]
            handler: forward
            forward:
              repo: opensourceways/om-datacenter
              event_type: backlog_merge
            title: "`[小数需求上线]`"
            description: "白名单 maintainer 才能合"
    """), encoding="utf-8")
    (d / "robot.yaml").write_text(textwrap.dedent("""\
        service:
          id: robot
          name: 机器人
        menu:
          trigger: "[机器人需求]"
          header: "🤖 机器人需求"
          intro: ""
        commands:
          - id: analyze
            triggers: ["[机器人需求分析]"]
            handler: in-repo
            title: "`[机器人需求分析]`"
            description: "robot analyze"
          - id: implement
            handler: disabled
            triggers: []
            title: "`[机器人需求实现]`"
            description: "（暂未接入）"
    """), encoding="utf-8")
    # 一个故意写残的 yaml —— load_services 应该跳过它（保留 .yaml 后缀）
    (d / "broken.yaml").write_text("not_a_valid_service: true\n", encoding="utf-8")
    return d


@pytest.fixture
def loaded(svc_dir: Path) -> list[dict]:
    return services.load_services(svc_dir)


@pytest.fixture
def fake_gh(monkeypatch):
    """Replace gh / gh_json with stubs that record calls and return a configurable issue_data."""
    state: dict[str, Any] = {
        "issue_data": {"labels": [], "comments": []},
        "gh_calls": [],
        "gh_json_calls": [],
        "raise_on_gh": None,
    }

    def _gh_json(*args: str) -> dict:
        state["gh_json_calls"].append(args)
        return state["issue_data"]

    def _gh(*args: str, env: dict | None = None) -> None:
        state["gh_calls"].append({"args": args, "env_keys": sorted((env or {}).keys()) if env else None})
        if state["raise_on_gh"]:
            raise state["raise_on_gh"]

    monkeypatch.setattr(services, "gh_json", _gh_json)
    monkeypatch.setattr(services, "gh", _gh)
    return state


# ───────────────────────────── load_services ─────────────────────────────

def test_load_services_finds_two_valid_skips_broken(svc_dir: Path):
    out = services.load_services(svc_dir)
    ids = [s["service"]["id"] for s in out]
    assert ids == ["datacenter", "robot"]  # sorted alphabetically by filename, broken.yaml skipped


def test_load_services_empty_dir(tmp_path: Path):
    assert services.load_services(tmp_path) == []


def test_load_services_default_path_uses_module_relative():
    # Just ensure SERVICES_DIR points at .github/services next to the script (not cwd-relative).
    assert services.SERVICES_DIR.name == "services"
    assert services.SERVICES_DIR.parent.name == ".github"


# ───────────────────────────── render_menu / render_nag ─────────────────────────────

def test_render_menu_datacenter(loaded: list[dict]):
    dc = next(s for s in loaded if s["service"]["id"] == "datacenter")
    md = services.render_menu(dc)
    # 必含元素
    assert md.startswith("<!-- SERVICE_DATACENTER_MENU -->")
    assert "## 🤖 数据中台需求 — 可用命令" in md
    assert "intro 文字" in md
    assert "| 评论 | 干什么 |" in md
    assert "| `[小数需求分析]` |" in md
    assert "| `[小数需求实现]` |" in md
    assert "| `[小数需求上线]` |" in md
    assert "> footer 文字" in md
    assert md.endswith("\n")


def test_render_menu_disabled_command_kept(loaded: list[dict]):
    """disabled 命令也应该出现在菜单里（只是描述里说『暂未接入』）。"""
    robot = next(s for s in loaded if s["service"]["id"] == "robot")
    md = services.render_menu(robot)
    assert "`[机器人需求实现]`" in md
    assert "暂未接入" in md


def test_render_menu_multiline_description_flattened(svc_dir: Path):
    """description 含换行时应单行化（防止破坏 markdown 表格）。"""
    yaml_path = svc_dir / "x.yaml"
    yaml_path.write_text(textwrap.dedent("""\
        service: {id: x, name: X}
        menu: {trigger: "[X]", header: "X menu", intro: ""}
        commands:
          - id: analyze
            triggers: ["[X]"]
            handler: in-repo
            title: T
            description: "line1\\nline2\\nline3"
    """), encoding="utf-8")
    svc = next(s for s in services.load_services(svc_dir) if s["service"]["id"] == "x")
    md = services.render_menu(svc)
    # 描述出现在一行内（虽然源 YAML 里是多行）
    table_row = [ln for ln in md.split("\n") if "T |" in ln][0]
    assert "line1" in table_row and "line2" in table_row and "line3" in table_row
    # 表格的下一行不能是 description 的尾巴（不能破表）
    assert table_row.count("|") == 3  # | 列1 | 列2 |


def test_render_menu_falls_back_to_first_trigger_when_title_missing(svc_dir: Path):
    """title 缺失时，菜单应该用首个 trigger 字符串作为列名。"""
    yaml_path = svc_dir / "y.yaml"
    yaml_path.write_text(textwrap.dedent("""\
        service: {id: y, name: Y}
        menu: {trigger: "[Y]", header: "Y", intro: ""}
        commands:
          - id: analyze
            triggers: ["[Y分析]"]
            handler: in-repo
            description: d
    """), encoding="utf-8")
    svc = next(s for s in services.load_services(svc_dir) if s["service"]["id"] == "y")
    md = services.render_menu(svc)
    assert "| `[Y分析]` | d |" in md


def test_render_menu_no_triggers_and_no_title_falls_back_to_id(svc_dir: Path):
    """命令既无 title 又无 triggers 时（理论上 disabled 可能这样），列名 fallback 用 id。"""
    yaml_path = svc_dir / "z.yaml"
    yaml_path.write_text(textwrap.dedent("""\
        service: {id: z, name: Z}
        menu: {trigger: "[Z]", header: "Z", intro: ""}
        commands:
          - id: foo
            handler: disabled
            description: d
    """), encoding="utf-8")
    svc = next(s for s in services.load_services(svc_dir) if s["service"]["id"] == "z")
    md = services.render_menu(svc)
    assert "| （foo） | d |" in md


def test_render_nag_uses_custom_label(loaded: list[dict]):
    dc = next(s for s in loaded if s["service"]["id"] == "datacenter")
    nag = services.render_nag(dc)
    assert nag.startswith("<!-- SERVICE_DATACENTER_NEEDS_LABEL -->")
    assert "[数据中台需求]" in nag
    assert "accepted" in nag


def test_render_nag_defaults_label_when_missing(svc_dir: Path):
    yaml_path = svc_dir / "w.yaml"
    yaml_path.write_text(textwrap.dedent("""\
        service: {id: w, name: W}
        menu: {trigger: "[W]", header: "W", intro: ""}
        commands: []
    """), encoding="utf-8")
    svc = next(s for s in services.load_services(svc_dir) if s["service"]["id"] == "w")
    # required_label 缺失，render_nag 应当 fallback 到 'accepted'
    assert "`accepted`" in services.render_nag(svc)


# ───────────────────────────── already_anchored ─────────────────────────────

def test_already_anchored_true():
    data = {"comments": [{"body": "<!-- A -->\nhello"}, {"body": "other"}]}
    assert services.already_anchored(data, "<!-- A -->") is True


def test_already_anchored_false():
    data = {"comments": [{"body": "other"}]}
    assert services.already_anchored(data, "<!-- A -->") is False


def test_already_anchored_empty_and_none_body():
    assert services.already_anchored({"comments": []}, "<!-- X -->") is False
    assert services.already_anchored({"comments": [{"body": None}]}, "<!-- X -->") is False
    assert services.already_anchored({}, "<!-- X -->") is False


# ───────────────────────────── match_menu_trigger ─────────────────────────────

def test_match_menu_trigger_on_comment_hit(loaded: list[dict]):
    dc = next(s for s in loaded if s["service"]["id"] == "datacenter")
    assert services.match_menu_trigger(
        dc, "issue_comment", "", "", "[数据中台需求] 我来一个", lambda t: False
    ) is True


def test_match_menu_trigger_on_comment_no_hit(loaded: list[dict]):
    dc = next(s for s in loaded if s["service"]["id"] == "datacenter")
    assert services.match_menu_trigger(
        dc, "issue_comment", "", "", "随便的评论", lambda t: False
    ) is False


def test_match_menu_trigger_on_labeled_when_history_has(loaded: list[dict]):
    dc = next(s for s in loaded if s["service"]["id"] == "datacenter")
    assert services.match_menu_trigger(
        dc, "issues", "labeled", "accepted", "", lambda t: t == "[数据中台需求]"
    ) is True


def test_match_menu_trigger_on_labeled_when_history_lacks(loaded: list[dict]):
    dc = next(s for s in loaded if s["service"]["id"] == "datacenter")
    assert services.match_menu_trigger(
        dc, "issues", "labeled", "accepted", "", lambda t: False
    ) is False


def test_match_menu_trigger_on_labeled_wrong_label(loaded: list[dict]):
    dc = next(s for s in loaded if s["service"]["id"] == "datacenter")
    # label 不是 required_label —— 不命中（即使历史里有 trigger）
    assert services.match_menu_trigger(
        dc, "issues", "labeled", "needs-info", "", lambda t: True
    ) is False


def test_match_menu_trigger_unknown_event(loaded: list[dict]):
    dc = next(s for s in loaded if s["service"]["id"] == "datacenter")
    assert services.match_menu_trigger(
        dc, "push", "", "", "[数据中台需求]", lambda t: True
    ) is False


def test_match_menu_trigger_default_label_when_missing(svc_dir: Path):
    """svc 没显式 required_label 时按 'accepted' 算。"""
    (svc_dir / "x.yaml").write_text(textwrap.dedent("""\
        service: {id: x, name: X}
        menu: {trigger: "[X]", header: "X", intro: ""}
        commands: []
    """), encoding="utf-8")
    svc = next(s for s in services.load_services(svc_dir) if s["service"]["id"] == "x")
    assert services.match_menu_trigger(
        svc, "issues", "labeled", "accepted", "", lambda t: t == "[X]"
    ) is True
    assert services.match_menu_trigger(
        svc, "issues", "labeled", "other", "", lambda t: t == "[X]"
    ) is False


# ───────────────────────────── match_forward_command ─────────────────────────────

def test_match_forward_command_hit(loaded: list[dict]):
    res = services.match_forward_command(loaded, "[小数需求实现]\n再补一句")
    assert res is not None
    svc, cmd, trig = res
    assert svc["service"]["id"] == "datacenter"
    assert cmd["id"] == "implement"
    assert trig == "[小数需求实现]"


def test_match_forward_command_release_alt_trigger(loaded: list[dict]):
    res = services.match_forward_command(loaded, "[数据中台需求上线]")
    assert res is not None and res[1]["id"] == "release"


def test_match_forward_command_skips_in_repo_handler(loaded: list[dict]):
    """analyze 是 in-repo handler，不应被 forward 匹配。"""
    res = services.match_forward_command(loaded, "[小数需求分析] xxx")
    assert res is None


def test_match_forward_command_no_match(loaded: list[dict]):
    assert services.match_forward_command(loaded, "纯随便的一句话") is None


def test_match_forward_command_skips_disabled(loaded: list[dict]):
    """robot.implement 是 disabled，不应被 forward 匹配，即使 trigger 看起来对。"""
    res = services.match_forward_command(loaded, "[机器人需求实现]")
    assert res is None


# ───────────────────────────── cmd_menu (end-to-end with stubs) ─────────────────────────────

@pytest.fixture
def patch_services_dir(monkeypatch, svc_dir):
    """Make load_services() (no arg) use our temp dir."""
    monkeypatch.setattr(services, "SERVICES_DIR", svc_dir)


def test_cmd_menu_posts_menu_when_label_and_trigger(monkeypatch, patch_services_dir, fake_gh):
    fake_gh["issue_data"] = {"labels": [{"name": "accepted"}], "comments": []}
    monkeypatch.setenv("EVENT_NAME", "issue_comment")
    monkeypatch.setenv("EVENT_ACTION", "")
    monkeypatch.setenv("ISSUE", "42")
    monkeypatch.setenv("COMMENT_BODY", "[数据中台需求] 我要一个")
    monkeypatch.setenv("LABEL_ADDED", "")
    services.cmd_menu()
    # 一次 gh issue comment 调用，body 是菜单
    assert len(fake_gh["gh_calls"]) == 1
    args = fake_gh["gh_calls"][0]["args"]
    assert args[:3] == ("issue", "comment", "42")
    assert args[3] == "--body-file"
    posted = Path(args[4]).read_text(encoding="utf-8")
    assert "<!-- SERVICE_DATACENTER_MENU -->" in posted


def test_cmd_menu_posts_nag_when_trigger_no_label(monkeypatch, patch_services_dir, fake_gh):
    fake_gh["issue_data"] = {"labels": [{"name": "bug"}], "comments": []}
    monkeypatch.setenv("EVENT_NAME", "issue_comment")
    monkeypatch.setenv("EVENT_ACTION", "")
    monkeypatch.setenv("ISSUE", "1")
    monkeypatch.setenv("COMMENT_BODY", "[机器人需求]")
    monkeypatch.setenv("LABEL_ADDED", "")
    services.cmd_menu()
    assert len(fake_gh["gh_calls"]) == 1
    posted = Path(fake_gh["gh_calls"][0]["args"][4]).read_text(encoding="utf-8")
    assert "<!-- SERVICE_ROBOT_NEEDS_LABEL -->" in posted


def test_cmd_menu_dedup_skips_when_already_posted(monkeypatch, patch_services_dir, fake_gh):
    fake_gh["issue_data"] = {
        "labels": [{"name": "accepted"}],
        "comments": [{"body": "<!-- SERVICE_DATACENTER_MENU -->\nold menu"}],
    }
    monkeypatch.setenv("EVENT_NAME", "issue_comment")
    monkeypatch.setenv("EVENT_ACTION", "")
    monkeypatch.setenv("ISSUE", "10")
    monkeypatch.setenv("COMMENT_BODY", "[数据中台需求]")
    monkeypatch.setenv("LABEL_ADDED", "")
    services.cmd_menu()
    assert fake_gh["gh_calls"] == []  # 跳过，不重复贴


def test_cmd_menu_dedup_skips_nag(monkeypatch, patch_services_dir, fake_gh):
    fake_gh["issue_data"] = {
        "labels": [],
        "comments": [{"body": "<!-- SERVICE_ROBOT_NEEDS_LABEL -->\nold nag"}],
    }
    monkeypatch.setenv("EVENT_NAME", "issue_comment")
    monkeypatch.setenv("EVENT_ACTION", "")
    monkeypatch.setenv("ISSUE", "11")
    monkeypatch.setenv("COMMENT_BODY", "[机器人需求]")
    monkeypatch.setenv("LABEL_ADDED", "")
    services.cmd_menu()
    assert fake_gh["gh_calls"] == []


def test_cmd_menu_on_label_event_posts_when_history_has_trigger(monkeypatch, patch_services_dir, fake_gh):
    fake_gh["issue_data"] = {
        "labels": [{"name": "accepted"}],
        "comments": [{"body": "我来个 [机器人需求] 看看"}],
    }
    monkeypatch.setenv("EVENT_NAME", "issues")
    monkeypatch.setenv("EVENT_ACTION", "labeled")
    monkeypatch.setenv("ISSUE", "20")
    monkeypatch.setenv("LABEL_ADDED", "accepted")
    monkeypatch.setenv("COMMENT_BODY", "")
    services.cmd_menu()
    assert len(fake_gh["gh_calls"]) == 1
    posted = Path(fake_gh["gh_calls"][0]["args"][4]).read_text(encoding="utf-8")
    assert "<!-- SERVICE_ROBOT_MENU -->" in posted


def test_cmd_menu_no_match_no_action(monkeypatch, patch_services_dir, fake_gh, capsys):
    fake_gh["issue_data"] = {"labels": [], "comments": []}
    monkeypatch.setenv("EVENT_NAME", "issue_comment")
    monkeypatch.setenv("EVENT_ACTION", "")
    monkeypatch.setenv("ISSUE", "30")
    monkeypatch.setenv("COMMENT_BODY", "无关评论")
    monkeypatch.setenv("LABEL_ADDED", "")
    services.cmd_menu()
    assert fake_gh["gh_calls"] == []
    assert "未命中" in capsys.readouterr().out


# ───────────────────────────── cmd_forward (end-to-end with stubs) ─────────────────────────────

def test_cmd_forward_dispatches_and_replies(monkeypatch, patch_services_dir, fake_gh):
    monkeypatch.setenv("COMMENT_BODY", "[小数需求实现]\n要这样做")
    monkeypatch.setenv("DISPATCH_TOKEN", "fake-token")
    monkeypatch.setenv("ISSUE", "55")
    monkeypatch.setenv("ISSUE_TITLE", "T")
    monkeypatch.setenv("COMMENT_ID", "999")
    monkeypatch.setenv("TRIGGER_USER", "alice")
    monkeypatch.setenv("GITHUB_REPOSITORY", "opensourceways/backlog")
    services.cmd_forward()
    # 2 次 gh：一次 api POST dispatch，一次 issue comment 回评
    assert len(fake_gh["gh_calls"]) == 2
    dispatch_call = fake_gh["gh_calls"][0]
    assert dispatch_call["args"][0] == "api"
    assert "/repos/opensourceways/om-datacenter/dispatches" in dispatch_call["args"]
    # 用 DISPATCH_TOKEN 临时改了 GH_TOKEN，说明走了独立 env
    assert dispatch_call["env_keys"] is not None
    # 回评 issue
    reply_call = fake_gh["gh_calls"][1]
    assert reply_call["args"][:3] == ("issue", "comment", "55")
    reply_body = Path(reply_call["args"][4]).read_text(encoding="utf-8")
    assert "om-datacenter" in reply_body and "backlog_implement" in reply_body
    # dispatch payload 落到 /tmp/dispatch.json
    payload = json.loads(Path("/tmp/dispatch.json").read_text(encoding="utf-8"))
    assert payload["event_type"] == "backlog_implement"
    assert payload["client_payload"]["issue_number"] == 55
    assert payload["client_payload"]["trigger_user"] == "alice"


def test_cmd_forward_no_match(monkeypatch, patch_services_dir, fake_gh, capsys):
    monkeypatch.setenv("COMMENT_BODY", "[小数需求分析] this is in-repo not forward")
    monkeypatch.setenv("DISPATCH_TOKEN", "fake-token")
    services.cmd_forward()
    assert fake_gh["gh_calls"] == []
    assert "未命中" in capsys.readouterr().out


def test_cmd_forward_missing_dispatch_token_exits(monkeypatch, patch_services_dir, fake_gh):
    monkeypatch.setenv("COMMENT_BODY", "[小数需求实现]")
    monkeypatch.setenv("DISPATCH_TOKEN", "")        # 没 token
    monkeypatch.setenv("ISSUE", "1")
    monkeypatch.setenv("GITHUB_REPOSITORY", "x/y")
    with pytest.raises(SystemExit):
        services.cmd_forward()


# ───────────────────────────── main / CLI dispatch ─────────────────────────────

def test_main_dispatches_menu(monkeypatch, patch_services_dir, fake_gh):
    fake_gh["issue_data"] = {"labels": [], "comments": []}
    monkeypatch.setattr("sys.argv", ["services.py", "menu"])
    monkeypatch.setenv("EVENT_NAME", "issue_comment")
    monkeypatch.setenv("EVENT_ACTION", "")
    monkeypatch.setenv("ISSUE", "1")
    monkeypatch.setenv("COMMENT_BODY", "noise")
    monkeypatch.setenv("LABEL_ADDED", "")
    assert services.main() == 0


def test_main_dispatches_forward(monkeypatch, patch_services_dir, fake_gh):
    monkeypatch.setattr("sys.argv", ["services.py", "forward"])
    monkeypatch.setenv("COMMENT_BODY", "无关")
    monkeypatch.setenv("DISPATCH_TOKEN", "x")
    assert services.main() == 0
