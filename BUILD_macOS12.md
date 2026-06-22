# 在 macOS 12 上构建 Focus（已改好的版本）

本副本已针对 macOS 12 做了兼容性修改：
- 部署目标 (MACOSX_DEPLOYMENT_TARGET) 从 14.1/15.1 降到 12.0
- 注释掉了 `.windowResizability(.contentSize)`（macOS 13+ API；窗口仍由 .fixedSize 保持内容尺寸）
- 两处 `onChange(of:){ old, new in }`（macOS 14+）改回单参数写法 `{ newValue in }`

这些改动消除了原版在 macOS 12.5 上崩溃的根因（JSONDecoder/JSONEncoder 的派发跳板符号在老系统 Foundation 中不存在）。
以 12.0 为目标重新编译后，编译器不会再引用那些只有 macOS 13/14 才有的符号。

## 构建步骤（需要 Xcode）
1. 双击 `Focus.xcodeproj` 用 Xcode 打开
2. 顶部选择 scheme 为 “Focus”，目标设备选 “My Mac”
3. 菜单 Product → Archive（或直接 Product → Build，⌘B；调试运行用 ⌘R）
4. Archive 完成后在 Organizer 里 “Distribute App” → “Custom” → “Copy App”，得到 Focus.app
5. 首次打开若提示无法验证开发者：系统设置 → 隐私与安全性 → 仍要打开

## 命令行构建（同样需要已安装 Xcode）
```bash
cd Focus-src
xcodebuild -project Focus.xcodeproj -scheme Focus -configuration Release \
  -derivedDataPath build MACOSX_DEPLOYMENT_TARGET=12.0 build
# 产物：build/Build/Products/Release/Focus.app
```

---

## 不想装 Xcode？用 GitHub Actions 在云端编译

本仓库已内置 `.github/workflows/build-macos12.yml`，让 GitHub 的 Mac 服务器替你编译，你只下载成品。

步骤：
1. 在 GitHub 上新建一个仓库（可私有），把本文件夹里的所有内容推上去：
   ```bash
   cd Focus-src
   git init && git add . && git commit -m "Focus build targeting macOS 12"
   git branch -M main
   git remote add origin https://github.com/你的用户名/你的仓库.git
   git push -u origin main
   ```
2. 推送后 Actions 会自动开始；也可在仓库 “Actions” 标签页手动点 “Run workflow”。
3. 等几分钟，构建完成后进入这次运行页面，在底部 “Artifacts” 下载 `Focus-macOS12.zip`。
4. 在你的 Mac 上：
   ```bash
   unzip Focus-macOS12.zip
   xattr -cr Focus.app
   codesign --force --deep --sign - Focus.app   # 保险起见本机再签一次
   open Focus.app
   ```

构建机用的是新系统 + 新 Xcode，但因为指定了 MACOSX_DEPLOYMENT_TARGET=12.0，产物只引用 macOS 12 上存在的符号，可在你的 12.5 上运行。
