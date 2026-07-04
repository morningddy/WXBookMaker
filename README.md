<img width="2560" height="1229" alt="image" src="https://github.com/user-attachments/assets/5a065917-fb8a-4c44-ae50-8d77fd92b730" />


# 📚 微信读书电子书制作工具 (WXBookMaker)

[![GitHub stars](https://img.shields.io/github/stars/morningddy/WXBookMaker?style=social)](https://github.com/morningddy/WXBookMaker)
[![GitHub forks](https://img.shields.io/github/forks/morningddy/WXBookMaker?style=social)](https://github.com/morningddy/WXBookMaker)
[![Python](https://img.shields.io/badge/Python-3.8+-green.svg)](https://www.python.org/)

> 将扫描版 PDF、TXT、Markdown 等文档转换为微信读书兼容的 EPUB 电子书

🔗 **GitHub 仓库**: https://github.com/morningddy/WXBookMaker

## ✨ 功能特性

### 🔍 扫描版 PDF 识别
- 支持扫描版/图片型 PDF 文档
- 使用本地 Tesseract OCR 引擎识别中文和英文
- 自动逐页处理，保留完整文本内容

### 📄 多格式输入
- **PDF**（文字版 + 扫描版）
- **TXT**（自动检测编码：UTF-8/GBK/GB18030/Big5）
- **Markdown**（支持标题、加粗、代码块等格式）

### 📚 标准 EPUB 输出
- 生成 EPUB 3.0 格式电子书
- 自动生成目录导航
- 兼容微信读书、iBooks、Kindle 等主流阅读器

## 🚀 快速开始

### 环境要求
- Python 3.8+
- Tesseract OCR 5.0+（用于 PDF 文字识别）

### 安装步骤

1. **克隆仓库**
```bash
git clone https://github.com/morningddy/WXBookMaker.git
cd WXBookMaker
```

2. **安装 Python 依赖**
```bash
pip install -r requirements.txt
```

3. **安装 Tesseract OCR**
- Windows: 下载 [Tesseract installer](https://github.com/UB-Mannheim/tesseract/wiki)
- macOS: `brew install tesseract`
- Ubuntu: `sudo apt install tesseract-ocr tesseract-ocr-chi-sim`

4. **下载中文语言包**（如果 Tesseract 未包含）
   - 下载 `chi_sim.traineddata`
   - 放到 Tesseract 的 `tessdata` 目录

### 启动服务

```bash
python server.py
```

访问 **http://localhost:5000** 即可使用

## 📖 使用指南

1. **打开工具**
   - 启动服务后，浏览器访问 `http://localhost:5000`

2. **填写书籍信息**
   - 输入书名（必填）
   - 输入作者（选填）

3. **上传文档**
   - 点击上传区域选择文件，或拖拽文件到上传区域
   - 支持 PDF/TXT/Markdown 格式

4. **PDF 文字识别**（针对扫描版）
   - 工具自动检测扫描版 PDF
   - 点击「🔍 OCR 识别文字」按钮
   - 等待识别完成（进度条显示实时进度）

5. **编辑内容**
   - OCR 识别结果会显示在文本框中
   - 可手动修正识别错误

6. **生成电子书**
   - 点击「转换为 EPUB」
   - 自动下载 EPUB 文件

7. **导入微信读书**
   - 打开微信读书 App
   - 点击「导入书籍」
   - 选择下载的 EPUB 文件

## 📁 项目结构

```
WX读书/
├── server.py                   # Flask 后端服务
├── weixin-read-book-maker.html # 前端界面
├── requirements.txt            # Python 依赖
├── README.md                   # 项目说明
└── libs/                       # 依赖库（可选）
```

## 🛠️ 技术栈

- **后端**: Python + Flask + PyMuPDF + Tesseract OCR
- **前端**: HTML5 + CSS3 + JavaScript
- **输出**: EPUB 3.0（JSZip + FileSaver.js）

## ⚙️ 配置说明

### Tesseract 路径配置
如果 Tesseract 未添加到系统 PATH，可在 `server.py` 中修改：

```python
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
```

### OCR 语言配置
默认使用中文简体 + 英文，可在 `server.py` 中修改：

```python
LANGUAGES = "chi_sim+eng"  # 中文简体 + 英文
# LANGUAGES = "chi_tra+eng"  # 中文繁体 + 英文
# LANGUAGES = "eng"  # 仅英文
```

## 🐛 常见问题

### Q: OCR 识别速度慢？
A: 识别速度与 PDF 页数和分辨率有关，建议：
- 降低 PDF 分辨率（200 DPI 已足够）
- 使用 SSD 硬盘加速
- 耐心等待，通常 50 页约需 2-5 分钟

### Q: 识别结果有错误？
A: OCR 识别不可能 100% 准确，建议：
- 识别完成后手动检查并修正
- 确保 PDF 图片清晰
- 尝试调整 DPI（150-300 之间）

### Q: 导出的 EPUB 在微信读书中显示乱码？
A: 工具已强制使用 UTF-8 编码，如果仍有问题：
- 确保原文档编码正确
- 尝试重新生成 EPUB
- 检查微信读书是否为最新版本

### Q: 无法启动服务？
A: 检查以下步骤：
1. Python 版本是否 3.8+
2. 依赖是否安装完整（`pip install -r requirements.txt`）
3. 端口 5000 是否被占用

## 📝 开发日志

### v1.0.0 (2026-07-05)
- ✅ 支持 TXT/Markdown 转 EPUB
- ✅ 支持 PDF 文字提取（PyMuPDF）
- ✅ 集成 Tesseract OCR 识别扫描版 PDF
- ✅ 暗色主题 UI
- ✅ 自动生成目录
- ✅ 多编码自动检测

## 📄 许可证

MIT License

## 🙏 致谢

- [PyMuPDF](https://github.com/pymupdf/PyMuPDF) - PDF 处理
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) - 文字识别
- [JSZip](https://github.com/Stuk/jszip) - EPUB 打包
- [Flask](https://flask.palletsprojects.com/) - 后端框架

## 📮 联系方式

- GitHub: [@morningddy](https://github.com/morningddy)
- 项目Issues: [提交问题](https://github.com/morningddy/WX读书/issues)

---

**⭐ 如果这个工具对你有帮助，欢迎 Star！**
