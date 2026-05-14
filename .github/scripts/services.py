#!/usr/bin/env python3
"""
Read .github/services/*.yaml and run one of two subcommands driven by env vars.

  python3 .github/scripts/services.py menu
    决定要不要给 issue 贴某个服务的菜单（或「需要先打 accepted 标签」提示）。
    需要的 env：EVENT_NAME、EVENT_ACTION、ISSUE、(LABEL_ADDED)、(COMMENT_BODY)、GH_TOKEN

  python3 .github/scripts/services.py forward
    决定要不要把当前评论里的命令通过 repository_dispatch 转发到外仓。
    需要的 env：ISSUE、ISSUE_TITLE、COMMENT_ID、COMMENT_BODY、TRIGGER_USER、
             GH_TOKEN（贴回评用，仓本身 token）、DISPATCH_TOKEN（发 dispatch 用，跨仓 PAT）

YAML schema 见 .github/services/datacenter.yaml（注释最详细）。两个 workflow 文件不直接改本脚本；
加新服务只需要往 .github/services/ 加 YAML。
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import subprocess
import sys

import yaml  # PyYAML — workflow 里会 pip install pyyaml

# 用脚本自身位置定位 services 目录，cwd 在哪里都能跑（workflow 里 cwd=repo root；测试时可能 cwd=任意）
SERVICES_DIR = pathlib.Path(__file__).resolve().parent.parent / "services"


# ───────────────────────── helpers ─────────────────────────

def load_services(services_dir: pathlib.Path | None = None) -> list[dict]:
    """Load all services YAML files. Caller can override services_dir for testing."""
    src = services_dir if services_dir is not None else SERVICES_DIR
    out = []
    for p in sorted(pathlib.Path(src).glob("*.yaml")):
        with open(p, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not data or "service" not in data or "menu" not in data:
            print(f"::warning::{p} 缺少 service / menu 字段，跳过", file=sys.stderr)
            continue
        out.append(data)
    return out


def match_menu_trigger(
    svc: dict,
    event_name: str,
    event_action: str,
    label_added: str,
    comment_body: str,
    comment_history_has: callable,
) -> bool:
    """Pure: 给定事件，本服务的菜单触发该不该命中？"""
    trigger = svc["menu"]["trigger"]
    required_label = svc["menu"].get("required_label") or "accepted"
    if event_name == "issue_comment":
        return trigger in comment_body
    if event_name == "issues" and event_action == "labeled":
        # 加上了所需 label —— 看历史评论里有没有过本服务的 trigger
        return label_added == required_label and comment_history_has(trigger)
    return False


def match_forward_command(services: list[dict], comment_body: str):
    """Pure: 在所有服务的 forward 命令里，找第一个 trigger 跟评论开头匹配的。返回 (svc, cmd, trigger) 或 None。"""
    for svc in services:
        for cmd in svc.get("commands", []):
            if cmd.get("handler") != "forward":
                continue
            for trig in cmd.get("triggers") or []:
                if comment_body.startswith(trig):
                    return svc, cmd, trig
    return None


def gh_json(*args: str) -> dict:
    r = subprocess.run(["gh"] + list(args), check=True, capture_output=True, text=True)
    return json.loads(r.stdout)


def gh(*args: str, env: dict | None = None) -> None:
    subprocess.run(["gh"] + list(args), check=True, env=env or os.environ.copy())


def already_anchored(issue_data: dict, anchor: str) -> bool:
    for c in issue_data.get("comments", []) or []:
        if (c.get("body") or "").startswith(anchor):
            return True
    return False


def render_menu(svc: dict) -> str:
    s, menu = svc["service"], svc["menu"]
    lines = [
        f"<!-- SERVICE_{s['id'].upper()}_MENU -->",
        f"## {menu['header']}",
        "",
        (menu.get("intro") or "").rstrip(),
        "",
        "| 评论 | 干什么 |",
        "|------|--------|",
    ]
    for cmd in svc.get("commands", []):
        title = (cmd.get("title")
                 or (f"`{cmd['triggers'][0]}`" if cmd.get("triggers") else f"（{cmd['id']}）"))
        # 描述里如果有换行，单行化避免破坏 markdown 表格
        desc = " ".join((cmd.get("description") or "").rstrip().split("\n"))
        lines.append(f"| {title} | {desc} |")
    footer = (menu.get("footer") or "").rstrip()
    if footer:
        lines += ["", footer]
    return "\n".join(lines).rstrip() + "\n"


def render_nag(svc: dict) -> str:
    s, menu = svc["service"], svc["menu"]
    label = menu.get("required_label") or "accepted"
    return (
        f"<!-- SERVICE_{s['id'].upper()}_NEEDS_LABEL -->\n"
        f"ℹ️ 收到 `{menu['trigger']}`，但本 issue 还没打 `{label}` 标签。"
        f"请先让 maintainer 给该 issue 打 `{label}` —— 打完标签后我会自动贴出可用命令菜单"
        f"（也可届时再评论一次 `{menu['trigger']}`）。\n"
    )


# ───────────────────────── subcommand: menu ─────────────────────────

def cmd_menu() -> None:
    event_name = os.environ["EVENT_NAME"]
    event_action = os.environ.get("EVENT_ACTION", "")
    issue = os.environ["ISSUE"]
    label_added = os.environ.get("LABEL_ADDED", "")
    comment_body = os.environ.get("COMMENT_BODY", "")

    issue_data = gh_json("issue", "view", issue, "--json", "labels,comments")
    has_label = lambda name: any(
        (l.get("name") == name) for l in (issue_data.get("labels") or [])
    )
    history_has = lambda text: any(
        (text in (c.get("body") or "")) for c in (issue_data.get("comments") or [])
    )

    any_action = False
    for svc in load_services():
        sid = svc["service"]["id"]
        required_label = svc["menu"].get("required_label") or "accepted"

        if not match_menu_trigger(
            svc, event_name, event_action, label_added, comment_body, history_has
        ):
            continue

        anchor_menu = f"<!-- SERVICE_{sid.upper()}_MENU -->"
        anchor_nag = f"<!-- SERVICE_{sid.upper()}_NEEDS_LABEL -->"

        if has_label(required_label):
            if already_anchored(issue_data, anchor_menu):
                print(f"::notice::{sid} 菜单已贴过，跳过")
                continue
            body = render_menu(svc)
            path = "/tmp/menu.md"
            with open(path, "w", encoding="utf-8") as f:
                f.write(body)
            gh("issue", "comment", issue, "--body-file", path)
            print(f"::notice::已贴 {sid} 服务菜单")
            any_action = True
        else:
            # 没 label：只在 issue_comment 事件给提示（label 事件路径根本走不到这里）
            if event_name != "issue_comment":
                continue
            if already_anchored(issue_data, anchor_nag):
                continue
            body = render_nag(svc)
            path = "/tmp/nag.md"
            with open(path, "w", encoding="utf-8") as f:
                f.write(body)
            gh("issue", "comment", issue, "--body-file", path)
            print(f"::notice::{sid} 缺 {required_label} 标签，已贴提示")
            any_action = True

    if not any_action:
        print("::notice::本事件未命中任何服务的菜单触发")


# ───────────────────────── subcommand: forward ─────────────────────────

def cmd_forward() -> None:
    comment_body = os.environ.get("COMMENT_BODY", "")
    matched = match_forward_command(load_services(), comment_body)
    if not matched:
        print("::notice::评论未命中任何 forward 命令的触发词")
        return

    svc, cmd, trig = matched
    fw = cmd["forward"]
    target_repo = fw["repo"]
    event_type = fw["event_type"]

    dispatch_token = os.environ.get("DISPATCH_TOKEN") or ""
    if not dispatch_token:
        print(
            f"::error::转发命令 `{trig}` → `{target_repo}` 失败：未配置 DATACENTER_DISPATCH_TOKEN secret。",
            file=sys.stderr,
        )
        sys.exit(1)

    payload = {
        "event_type": event_type,
        "client_payload": {
            "source_repo": os.environ["GITHUB_REPOSITORY"],
            "issue_number": int(os.environ["ISSUE"]),
            "issue_title": os.environ.get("ISSUE_TITLE", ""),
            "comment_id": int(os.environ.get("COMMENT_ID", "0") or "0"),
            "comment_body": comment_body,
            "trigger_user": os.environ.get("TRIGGER_USER", ""),
        },
    }
    with open("/tmp/dispatch.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)

    # 用 dispatch token 发 dispatch
    dispatch_env = os.environ.copy()
    dispatch_env["GH_TOKEN"] = dispatch_token
    gh(
        "api", "-X", "POST", f"/repos/{target_repo}/dispatches", "--input", "/tmp/dispatch.json",
        env=dispatch_env,
    )
    print(f"::notice::已转发 `{trig}` → `{target_repo}` (event_type=`{event_type}`)")

    # 用仓本身 token 回评 issue（GH_TOKEN 是本仓 token，由 workflow env 注入）
    issue = os.environ["ISSUE"]
    body = (
        f"🚀 已转发到 `{target_repo}` 流水线（event_type=`{event_type}`），进展会回评在本 issue。"
    )
    path = "/tmp/forward_reply.md"
    with open(path, "w", encoding="utf-8") as f:
        f.write(body)
    gh("issue", "comment", issue, "--body-file", path)


# ───────────────────────── main ─────────────────────────

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("cmd", choices=["menu", "forward"])
    args = p.parse_args()
    if args.cmd == "menu":
        cmd_menu()
    elif args.cmd == "forward":
        cmd_forward()
    return 0


if __name__ == "__main__":
    sys.exit(main())
