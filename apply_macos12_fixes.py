#!/usr/bin/env python3
# 在 Focus-src 目录下运行：python3 apply_macos12_fixes.py
# 作用：把源码里仅 macOS 13/14 才有的 API 改成 macOS 12 兼容写法。
# 每处修改都做精确匹配校验；若已应用过会自动跳过。

import os
import sys

def patch(path, old, new, label):
    s = open(path, encoding="utf-8").read()
    if new in s and old not in s:
        print(f"  [skip] {label}（看起来已应用过）")
        return s, False
    c = s.count(old)
    if c != 1:
        print(f"  [ERROR] {label}: 预期匹配 1 处，实际 {c} 处。已中止，未改动该文件。")
        sys.exit(1)
    s = s.replace(old, new)
    open(path, "w", encoding="utf-8").write(s)
    print(f"  [ok]   {label}")
    return s, True

if not os.path.exists("Focus/StatisticsView.swift"):
    print("请在 Focus-src 目录（包含 Focus/ 子目录）下运行本脚本。")
    sys.exit(1)

print("StatisticsView.swift:")
# 1) RoundedRectangle 的 fill().stroke() 链（macOS 14+）-> fill + overlay(stroke)
patch("Focus/StatisticsView.swift",
"""                        .fill(Color(.controlBackgroundColor).opacity(0.6))
                        .stroke(Color(.separatorColor).opacity(0.3), lineWidth: 1)""",
"""                        .fill(Color(.controlBackgroundColor).opacity(0.6))
                        .overlay(
                            RoundedRectangle(cornerRadius: 12)
                                .stroke(Color(.separatorColor).opacity(0.3), lineWidth: 1)
                        )""",
"fill/stroke 链 #1 (RoundedRectangle)")

# 2) Capsule 的 fill().stroke() 链（macOS 14+，同时是 1153 行类型推断超时的真因）
patch("Focus/StatisticsView.swift",
"""                        .fill(Color.blue.opacity(0.1))
                        .stroke(Color.blue.opacity(0.2), lineWidth: 1)""",
"""                        .fill(Color.blue.opacity(0.1))
                        .overlay(
                            Capsule()
                                .stroke(Color.blue.opacity(0.2), lineWidth: 1)
                        )""",
"fill/stroke 链 #2 (Capsule)")

# 3) contentTransition(.numericText())（macOS 13+）-> 兼容辅助
patch("Focus/StatisticsView.swift",
"                    .contentTransition(.numericText())",
"                    .compatNumericContentTransition()",
"contentTransition")

print("ContentView.swift:")
# 4) focusEffectDisabled()（macOS 14+，3 处）-> 兼容辅助
# 仅当辅助扩展尚未追加时才替换，避免误改辅助函数内部的 self.focusEffectDisabled()
s = open("Focus/ContentView.swift", encoding="utf-8").read()
if "func compatFocusEffectDisabled" not in s and ".focusEffectDisabled()" in s:
    n = s.count(".focusEffectDisabled()")
    s = s.replace(".focusEffectDisabled()", ".compatFocusEffectDisabled()")
    open("Focus/ContentView.swift", "w", encoding="utf-8").write(s)
    print(f"  [ok]   focusEffectDisabled x{n}")
else:
    print("  [skip] focusEffectDisabled（已应用过）")

# 5) 追加兼容辅助扩展（同一 module 内全局可见）
s = open("Focus/ContentView.swift", encoding="utf-8").read()
if "func compatFocusEffectDisabled" not in s:
    helper = """

// MARK: - macOS 12 兼容性辅助（自动添加）
extension View {
    /// macOS 14+ 使用 focusEffectDisabled()，更低系统为无操作
    @ViewBuilder
    func compatFocusEffectDisabled() -> some View {
        if #available(macOS 14.0, *) {
            self.focusEffectDisabled()
        } else {
            self
        }
    }

    /// macOS 13+ 使用数字内容过渡动画，更低系统为无操作
    @ViewBuilder
    func compatNumericContentTransition() -> some View {
        if #available(macOS 13.0, *) {
            self.contentTransition(.numericText())
        } else {
            self
        }
    }
}
"""
    s = s.rstrip() + "\n" + helper
    open("Focus/ContentView.swift", "w", encoding="utf-8").write(s)
    print("  [ok]   追加兼容辅助扩展")
else:
    print("  [skip] 兼容辅助扩展（已存在）")

print("SettingsView.swift:")
# 6a) focusEffectDisabled()（1 处）
s = open("Focus/SettingsView.swift", encoding="utf-8").read()
if ".focusEffectDisabled()" in s:
    n = s.count(".focusEffectDisabled()")
    s = s.replace(".focusEffectDisabled()", ".compatFocusEffectDisabled()")
    open("Focus/SettingsView.swift", "w", encoding="utf-8").write(s)
    print(f"  [ok]   focusEffectDisabled x{n}")
else:
    print("  [skip] focusEffectDisabled（已应用过）")

# 6b) Color(.tertiarySystemFill)（macOS 14+）-> 12 安全色
s = open("Focus/SettingsView.swift", encoding="utf-8").read()
if "Color(.tertiarySystemFill)" in s:
    n = s.count("Color(.tertiarySystemFill)")
    s = s.replace("Color(.tertiarySystemFill)", "Color.gray.opacity(0.25)")
    open("Focus/SettingsView.swift", "w", encoding="utf-8").write(s)
    print(f"  [ok]   tertiarySystemFill x{n}")
else:
    print("  [skip] tertiarySystemFill（已应用过）")

print("\n全部完成。接下来：")
print("  git add -A && git commit -m 'compat: macOS 12 SwiftUI API fixes' && git push")
