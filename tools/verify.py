#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cyber Profile 搭建自检

用法：
    python verify.py <档案库路径>

    例：python verify.py "D:/我的档案"

检查项：
    1. 22 个 .md 文件是否齐全
    2. 16 个子目录是否齐全
    3. AGENTS.md 是否 < 8000 字符
    4. 双链 [[xxx]] 是否有对应文件（断链检查）

退出码：0 = 全部通过，1 = 有问题
"""

import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ---- 标准清单（改这里没用，除非你改了搭建规格）------------------------------

MD_FILES = [
    "AGENTS.md",
    "档案 profile/L4 核心 core.md",
    "档案 profile/me.md",
    "档案 profile/健康 health.md",
    "档案 profile/分身 persona.md",
    "档案 profile/反模式 anti-patterns.md",
    "档案 profile/声音 voice.md",
    "档案 profile/当前 current.md",
    "档案 profile/待确认 conflicts.md",
    "档案 profile/数字档案 identity.md",
    "档案 profile/时间线 timeline.md",
    "档案 profile/框架 frameworks.md",
    "档案 profile/沟通说明书 for-ai.md",
    "档案 profile/纠正日志 correction-log.md",
    "档案 profile/经历 experiences.md",
    "档案 profile/自我评价待核.md",
    "档案 profile/罗盘 compass.md",
    "档案 profile/预测账本 predictions.md",
    "知识库 wiki/分析 analyses/自我认知偏差.md",
    "知识库 wiki/日志 log.md",
    "知识库 wiki/目录 index.md",
    "知识库 wiki/综述 overview.md",
]

DIRS = [
    ".history",
    "原始资料 raw",
    "原始资料 raw/已摄入",
    "原始资料 raw/私密",
    "原始资料 raw/附件 assets",
    "报告 reports",
    "档案 profile",
    "档案 profile/L1 情境 events",
    "档案 profile/L2 行为 behavior",
    "档案 profile/L3 认知 cognition",
    "档案 profile/领域 domains",
    "知识库 wiki",
    "知识库 wiki/分析 analyses",
    "知识库 wiki/实体 entities",
    "知识库 wiki/概念 concepts",
    "知识库 wiki/资料摘要 sources",
]

AGENTS_MAX = 8000
LINK_RE = re.compile(r"\[\[([^\]\|#]+)")

# 模板里的占位符示例，不是真链接，别报断链
PLACEHOLDER_LINKS = {"条目", "标题", "文件名", "链接", "示例", "页面", "页面名", "日期"}
PH_LINK_RE = re.compile(r"^(?:[A-Z][A-Z\-_0-9]*|[\?？xX]+)$|YYYY|MM|DD|XX|xxx|\.\.\.")


def ok(msg):
    print(f"  [✓] {msg}")


def bad(msg):
    print(f"  [✗] {msg}")


def warn(msg):
    print(f"  [!] {msg}")


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    root = os.path.abspath(root)

    if not os.path.isdir(root):
        print(f"路径不存在或不是目录：{root}")
        return 1

    print(f"检查目标：{root}\n")
    problems = 0

    # 1. md 文件
    print(f"[1/4] .md 文件（应有 {len(MD_FILES)} 个）")
    missing = [p for p in MD_FILES if not os.path.isfile(os.path.join(root, p))]
    if missing:
        problems += len(missing)
        for p in missing:
            bad(f"缺 {p}")
    else:
        ok(f"{len(MD_FILES)} 个齐全")

    # 2. 目录
    print(f"\n[2/4] 子目录（应有 {len(DIRS)} 个）")
    missing_dirs = [d for d in DIRS if not os.path.isdir(os.path.join(root, d))]
    if missing_dirs:
        problems += len(missing_dirs)
        for d in missing_dirs:
            bad(f"缺 {d}")
    else:
        ok(f"{len(DIRS)} 个齐全")

    # 3. AGENTS.md 体量
    print(f"\n[3/4] AGENTS.md 体量（上限 {AGENTS_MAX} 字符）")
    ap = os.path.join(root, "AGENTS.md")
    if os.path.isfile(ap):
        text = open(ap, encoding="utf-8", errors="replace").read()
        n = len(text)
        if n > AGENTS_MAX:
            problems += 1
            bad(f"{n} 字符，超出 {n - AGENTS_MAX} 字，需要精简或拆分")
        else:
            ok(f"{n} 字符（余量 {AGENTS_MAX - n}）")
    else:
        problems += 1
        bad("AGENTS.md 不存在，跳过")

    # 4. 断链
    print("\n[4/4] 双链检查")
    stems = set()
    for dirpath, _, files in os.walk(root):
        if any(seg in dirpath for seg in (".history", ".obsidian", ".git")):
            continue
        for f in files:
            if f.endswith(".md"):
                stems.add(os.path.splitext(f)[0].lower())

    broken = []
    for dirpath, _, files in os.walk(root):
        if any(seg in dirpath for seg in (".history", ".obsidian", ".git")):
            continue
        for f in files:
            if not f.endswith(".md"):
                continue
            fp = os.path.join(dirpath, f)
            try:
                body = open(fp, encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            for target in LINK_RE.findall(body):
                t = target.strip()
                low = t.lower()
                if not t or low in stems:
                    continue
                # 跳过占位符示例
                if t in PLACEHOLDER_LINKS or PH_LINK_RE.search(t):
                    continue
                broken.append((os.path.relpath(fp, root), t))

    if broken:
        for src, tgt in broken:
            warn(f"{src} → [[{tgt}]] 找不到对应文件")
        print(f"  共 {len(broken)} 处断链（不是致命错误，但应当修）")
    else:
        ok("没有断链")

    # 汇总
    print("\n" + "=" * 50)
    if problems == 0:
        print("结果：结构通过。可以开始第一次建档了。")
        print("下一步 → 打开 02 第一次对话模板.md，走 A 或 D。")
        print("（填了多少没法自动判断——那得靠你自己看。）")
        return 0
    print(f"结果：{problems} 处硬性问题，先补齐再往下走。")
    return 1


if __name__ == "__main__":
    sys.exit(main())
