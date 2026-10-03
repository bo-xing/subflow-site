# SubFlow website

SubFlow 上架网站。默认英文，支持简体中文，托管于 GitHub Pages。
开发者：**Bo Xing** · 支持邮箱：**boxing.support@gmail.com**。

完整静态 HTML；无前端框架、在线字体、第三方脚本、Cookie、分析或后端。
Python 3.10+ 标准库即可构建，浏览网页不依赖 Python 或 JavaScript。

## 本地预览

```sh
python3 scripts/build.py --release
python3 scripts/serve.py
```

打开 [英文预览](http://127.0.0.1:4173/subflow-site/) 或
[中文预览](http://127.0.0.1:4173/subflow-site/zh-Hans/)。
修改后重新执行构建并刷新网页。可用 `--port 4174` 更换预览端口。
预览服务仅监听本机；不要把 Python 开发服务器作为公开托管方式。

```sh
python3 -m unittest discover -s tests -v
```

## 发布到 GitHub Pages

1. 将此仓库内容提交并推送到 `bo-xing/subflow-site` 的 `main`。
2. 在 GitHub 仓库 **Settings → Pages → Build and deployment → Source** 选择 **GitHub Actions**。
3. 在 **Actions → Build and deploy SubFlow website → Run workflow** 选择 `main` 手动运行一次。首次推送发生在开启 Pages 之前时，发布步骤可能因 Pages 尚未启用而失败；开启后重跑即可。
4. 部署成功后，在未登录的浏览器中打开下表所有链接，核实内容和联系方式。GitHub Pages 的公开可用性以实际部署为准。

后续推送 `main` 自动构建、检查并发布；Pull Request 与其他分支的手动运行只检查与构建，不发布。
工作流只上传 `dist/` 中的公开站点，不上传配置、测试或内部文档。
没有填写开发者或有效支持邮箱时，发布构建会失败。

参见 [GitHub Pages 自定义工作流文档](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)。

## App Store Connect 填写表

**以下是部署成功后的预期网址，不表示仓库当前已发布。**

| 字段 / 用途 | English (U.S.) | 简体中文 |
| --- | --- | --- |
| Marketing URL（营销网址） | https://bo-xing.github.io/subflow-site/ | https://bo-xing.github.io/subflow-site/zh-Hans/ |
| Support URL（支持网址） | https://bo-xing.github.io/subflow-site/support/ | https://bo-xing.github.io/subflow-site/zh-Hans/support/ |
| Privacy Policy URL（隐私政策网址） | https://bo-xing.github.io/subflow-site/privacy/ | https://bo-xing.github.io/subflow-site/zh-Hans/privacy/ |
| 订阅说明网页 | https://bo-xing.github.io/subflow-site/terms/ | https://bo-xing.github.io/subflow-site/zh-Hans/terms/ |

Apple 标准使用条款（EULA）：
https://www.apple.com/legal/internet-services/itunes/dev/stdeula/

保持 App Store Connect 的 License Agreement 使用 Apple 标准协议；本站条款页是说明页，不是自定义 EULA。
App 的商店描述可附 `Terms of Use (EULA):` 与上述 Apple 链接，并附对应语言的隐私政策链接。

隐私政策 URL 在 **App Privacy** 中配置，支持/营销网址在版本的本地化信息中填写。
支持网址必须能找到实际联系方式；隐私政策也需在 App 内可访问。
本站支持页已包含姓名和邮件入口。主 App 当前显示应用内隐私摘要，公开政策发布后应接入完整网页链接。
参见 [Apple 版本信息字段](https://developer.apple.com/help/app-store-connect/reference/app-information/platform-version-information/)
与 [审核指南 5.1.1](https://developer.apple.com/app-store/review/guidelines/#data-collection-and-storage)。

网页不会代替 App Privacy 问卷、订阅商品设置、商店截图、真实 Sandbox 验收或各发行地区要求。
尤其应分别核实 App 内数据处理、用户主动选择的服务与网站/邮件的数据流，不能仅凭网站文案填写隐私标签。

## 日常维护

- `site.config.json`：公开网址、开发者、邮箱、政策修订日期、可选 App Store 链接。
- `content/en.json` / `content/zh-Hans.json`：两种语言的全部页面文案；支持少量审核过的 HTML 链接。
- `assets/styles.css`：共享样式和响应式布局；品牌色沿用 SubFlow DesignSystem。
- `assets/preview.js`：仅用于首页示意字幕的样式切换；关闭 JavaScript 不影响内容、导航、FAQ 和联系方式。
- `assets/app-icon.png`：来自 SubFlow App 的现有图标。
- `assets/landscape.svg`：本站绘制的风景示意图，不是 App 截图或真实影片素材。
- `scripts/build.py`：生成 8 个双语页面、404、站点地图和 robots.txt。
- `docs/STATUS.md`：本次交付与验证记录。

取得真实商店链接后，填写 `app_store_url`，重新构建：首页按钮自动切为 App Store 链接并移除预发布提示。
当前保留空值，避免假下载按钮或未经确认的商店 ID。
联系方式及政策修订日期由配置统一生成；变更隐私或产品行为时同时维护中英文。

`site_url` 必须与实际部署地址一致。采用自定义域名时先配置 GitHub Pages 的域名/DNS，
再把 `site_url` 更新为 HTTPS 域名并重新构建。所有页面路径和 SEO 链接会自动更新。
仓库项目路径下的 `robots.txt` 不能充当整个 `bo-xing.github.io` 域名根目录的 robots 文件；
`sitemap.xml` 仍可直接提交给搜索引擎。自定义域名根目录部署时 robots.txt 正常适用。

产品声明依据主 App 仓库的当前 PRODUCT、STATUS、DESIGN 和隐私实现。
不宣传暂时隐藏的视频导出、未支持的语言/设备、固定准确率或小窗字幕。
