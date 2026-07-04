"""
文档转微信读书电子书 - Python 后端服务
功能：PDF/TXT/MD → 文字提取(含OCR) → EPUB导出
依赖：flask, pymupdf, tesseract-ocr, chi_sim语言包
用法：python server.py  → 打开 http://localhost:5000
"""

import os, sys, re, uuid, tempfile, subprocess, json
from flask import Flask, request, jsonify, send_file, send_from_directory
import fitz  # pymupdf

app = Flask(__name__, static_folder='.', static_url_path='')

# 配置
TESSERACT_CMD = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
TESSDATA_PREFIX = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)


def ocr_page(image_path, lang='chi_sim+eng'):
    """调用本地 Tesseract OCR 识别图片文字"""
    try:
        result = subprocess.run(
            [TESSERACT_CMD, image_path, 'stdout', '-l', lang, '--psm', '6'],
            capture_output=True, text=True,
            env={**os.environ, 'TESSDATA_PREFIX': TESSDATA_PREFIX},
            timeout=60
        )
        return result.stdout.strip()
    except Exception as e:
        return f'[OCR错误: {e}]'


def extract_pdf_text(pdf_path, use_ocr=True):
    """提取 PDF 文字，自动检测是否需要 OCR"""
    doc = fitz.open(pdf_path)
    num_pages = len(doc)
    results = []
    total_chars = 0
    needs_ocr = False

    # 先尝试直接提取文字（快速判断）
    for i in range(num_pages):
        page = doc[i]
        text = page.get_text().strip()
        char_count = len(text)
        total_chars += char_count
        
        # 如果平均每页文字太少，说明可能是扫描版
        if char_count < 100 and num_pages > 5:
            needs_ocr = True
    
    # 判断是否需要 OCR
    avg_chars = total_chars / max(num_pages, 1)
    
    if use_ocr and (needs_ocr or avg_chars < 200):
        # OCR 模式：渲染为图片再识别
        print(f'[{pdf_path}] 使用OCR模式 ({num_pages}页, 平均{avg_chars:.0f}字符/页)')
        
        tmp_dir = tempfile.mkdtemp(prefix='ocr_')
        all_text = []
        
        for i in range(num_pages):
            page = doc[i]
            # 渲染为高分辨率图片
            pix = page.get_pixmap(dpi=250)
            img_path = os.path.join(tmp_dir, f'page_{i+1}.png')
            pix.save(img_path)
            
            # OCR 识别
            text = ocr_page(img_path)
            
            if text:
                all_text.append(text)
            
            progress = ((i + 1) / num_pages) * 100
            print(f'  OCR进度: {i+1}/{num_pages} ({progress:.0f}%)')
        
        # 清理临时文件
        import shutil
        shutil.rmtree(tmp_dir, ignore_errors=True)
        
        full_text = '\n\n--- 页面分隔 ---\n\n'.join(all_text)
        return full_text, True  # (text, used_ocr)
    else:
        # 直接提取模式
        print(f'[{pdf_path}] 直接提取模式 ({num_pages}页, 平均{avg_chars:.0f}字符/页)')
        texts = []
        for i in range(num_pages):
            page = doc[i]
            text = page.get_text().strip()
            if text:
                texts.append(text)
        return '\n\n'.join(texts), False


@app.route('/')
def index():
    return send_from_directory('.', 'weixin-read-book-maker.html')


@app.route('/api/extract', methods=['POST'])
def api_extract():
    """上传 PDF，返回提取的文字"""
    if 'file' not in request.files:
        return jsonify({'error': '没有上传文件'}), 400
    
    file = request.files['file']
    if not file.filename:
        return jsonify({'error': '没有文件名'}), 400
    
    # 保存文件
    ext = os.path.splitext(file.filename)[1].lower()
    filepath = os.path.join(UPLOAD_DIR, f'{uuid.uuid4().hex}{ext}')
    file.save(filepath)
    
    try:
        if ext == '.pdf':
            text, used_ocr = extract_pdf_text(filepath)
            return jsonify({
                'success': True,
                'text': text,
                'pages': len(fitz.open(filepath)),
                'chars': len(text),
                'used_ocr': used_ocr,
                'filename': file.filename
            })
        else:
            # TXT/MD 文件
            encodings = ['utf-8', 'gbk', 'gb18030', 'big5']
            content = None
            raw = open(filepath, 'rb').read()
            for enc in encodings:
                try:
                    content = raw.decode(enc)
                    if len(re.findall(r'[\u4e00-\u9fff]', content)) > 3:
                        break
                    content = None
                except:
                    pass
            if content is None:
                content = raw.decode('utf-8', errors='ignore')
            
            return jsonify({
                'success': True,
                'text': content,
                'pages': 1,
                'chars': len(content),
                'used_ocr': False,
                'filename': file.filename
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)


@app.route('/api/to-epub', methods=['POST'])
def api_to_epub():
    """将文本转换为 EPUB 并下载"""
    data = request.json
    title = data.get('title', '未命名书籍').strip()
    author = data.get('author', '未知作者').strip()
    content = data.get('content', '').strip()
    
    if not title or len(content) < 10:
        return jsonify({'error': '书名或内容不能为空'}), 400
    
    try:
        from zipfile import ZipFile
        from io import BytesIO
        
        def esc(s):
            return (s.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
                   .replace('"','&quot;').replace("'",'&apos;'))
        
        def gen_uuid():
            import random
            return '%08x-%04x-%04x-%04x-%012x' % (
                random.randint(0,0xffffffff), random.randint(0,0xffff),
                random.randint(0,0xffff), random.randint(0,0xffff),
                random.randint(0,0xffffffffffff))
        
        # 解析章节
        lines = content.split('\n')
        heads = []
        for idx, line in enumerate(lines):
            m = re.match(r'^(#{1,6})\s+(.+)$', line)
            if m:
                heads.append({'level': len(m.group(1)), 'title': m.group(2).strip(), 'idx': idx})
        
        chapters = []
        if heads:
            for i, h in enumerate(heads):
                start = h['idx'] + 1
                end = heads[i+1]['idx'] if i+1 < len(heads) else len(lines)
                chapters.append({
                    'title': h['title'],
                    'content': '\n'.join(lines[start:end])
                })
        elif len(content) <= 30000:
            chapters.append({'title': title, 'content': content})
        else:
            parts = re.split(r'\n\s*\n', content)
            cur_t, cur_c, pn = f'{title}-第1部分', '', 1
            for p in parts:
                if len(cur_c) + len(p) > 30000 and cur_c:
                    chapters.append({'title': cur_t, 'content': cur_c})
                    pn += 1
                    cur_t = f'{title}-第{pn}部分'
                    cur_c = ''
                cur_c += p + '\n\n'
            if cur_c.strip():
                chapters.append({'title': cur_t, 'content': cur_c})
        
        # 构建 EPUB
        buf = BytesIO()
        with ZipFile(buf, 'w') as z:
            z.writestr('mimetype', 'application/epub+zip', compress_type=0)
            
            # container.xml
            z.writestr('META-INF/container.xml',
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                '<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container">\n'
                '  <rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles>\n'
                '</container>')
            
            ids = [f'c{i+1}' for i in range(len(chapters))]
            css = '''@charset "UTF-8";
body{margin:1.5em 1em;font-family:"PingFang SC","Noto Sans CJK SC","Microsoft YaHei",serif;
font-size:1.05em;line-height:1.85;color:#222;text-align:justify;}
header h1{text-align:center;font-size:1.6em;margin:1.5em 0 1em;padding-bottom:.5em;border-bottom:1px solid #ccc;}
main p{margin:.65em 0;text-indent:2em;orphans:3;widows:3;}
main h1,main h2,main h3{margin:1.2em 0 .6em;font-weight:bold;}
main h1{font-size:1.4em;} main h2{font-size:1.22em;} main h3{font-size:1.12em;}'''
            
            oebps_chapters = []
            for i, ch in enumerate(chapters):
                body = md_to_html(ch['content'])
                xhtml = f'''<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="zh-CN">
<head><meta charset="UTF-8"/><title>{esc(ch["title"])}</title><link rel="stylesheet" href="style.css"/></head>
<body><header><h1>{esc(ch["title"])}</h1></header><main>{body}</main></body></html>'''
                fname = f'ch_{str(i+1).zfill(3)}.xhtml'
                z.writestr(f'OEBPS/{fname}', xhtml)
                oebps_chapters.append(fname)
            
            z.writestr('OEBPS/style.css', css)
            
            # content.opf
            manifest_items = '\n'.join(
                f'    <item id="{ids[i]}" href="{oebps_chapters[i]}" media-type="application/xhtml+xml"/>'
                for i in range(len(chapters))
            )
            spine_items = '\n'.join(f'    <itemref idref="{id}"/>' for id in ids)
            
            z.writestr('OEBPS/content.opf', f'''<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="uid" xml:lang="zh-CN">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="uid">urn:uuid:{gen_uuid()}</dc:identifier>
    <dc:title>{esc(title)}</dc:title>
    <dc:creator>{esc(author)}</dc:creator>
    <dc:language>zh-CN</dc:language>
  </metadata>
  <manifest>
    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
    <item id="css" href="style.css" media-type="text/css"/>
{manifest_items}
  </manifest>
  <spine toc="ncx">
{spine_items}
  </spine>
</package>''')
            
            # nav.xhtml
            nav_items = '\n'.join(
                f'      <li><a href="{oebps_chapters[i]}">{esc(chapters[i]["title"])}</a></li>'
                for i in range(len(chapters))
            )
            z.writestr('OEBPS/nav.xhtml', f'''<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="zh-CN">
<head><meta charset="UTF-8"/><title>目录</title><link rel="stylesheet" href="style.css"/></head>
<body><nav epub:type="toc"><ol>
{nav_items}
    </ol></nav></body></html>''')
            
            # toc.ncx
            ncx_points = '\n'.join(
                f'''    <navPoint id="np{i+1}" playOrder="{i+1}">
      <navLabel><text>{esc(chapters[i]["title"])}</text></navLabel>
      <content src="{oebps_chapters[i]}"/>
    </navPoint>'''
                for i in range(len(chapters))
            )
            z.writestr('OEBPS/toc.ncx', f'''<?xml version="1.0" encoding="UTF-8"?>
<ncx version="2005-1" xmlns="http://www.daisy.org/z3986/2005/ncx/" xml:lang="zh-CN">
  <head><meta name="dtb:uid" content="urn:uuid:{gen_uuid()}"/></head>
  <docTitle><text>{esc(title)}</text></docTitle>
  <navMap>
{ncx_points}
  </navMap>
</ncx>''')
        
        buf.seek(0)
        safe_title = re.sub(r'[\\/:*?"<>|]', '_', title)
        output_path = os.path.join(UPLOAD_DIR, f'{safe_title}.epub')
        with open(output_path, 'wb') as f:
            f.write(buf.getvalue())
        
        return send_file(output_path, as_attachment=True, download_name=f'{safe_title}.epub',
                          mimetype='application/epub+zip')
    
    except ImportError:
        return jsonify({'error': '缺少依赖，请确保安装了所有包'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def md_to_html(md):
    """简单 Markdown 转 HTML"""
    if not md:
        return '<p>&nbsp;</p>'
    h = (md.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
         .replace('"','&quot;'))
    h = re.sub(r'^#### (.+)$', r'<h4>\1</h4>', h, flags=re.M)
    h = re.sub(r'^### (.+)$', r'<h3>\1</h3>', h, flags=re.M)
    h = re.sub(r'^## (.+)$', r'<h2>\1</h2>', h, flags=re.M)
    h = re.sub(r'^# (.+)$', r'<h1>\1</h1>', h, flags=re.M)
    h = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', h)
    h = re.sub(r'\*(.+?)\*', r'<em>\1</em>', h)
    h = re.sub(r'```([\s\S]*?)```', lambda m: f'<pre><code>{m.group(1)}</code></pre>', h)
    h = re.sub(r'`(.+?)`', r'<code>\1</code>', h)
    
    parts = h.split('\n')
    out, in_list, in_code = [], False, False
    for line in parts:
        t = line.strip()
        if t.startswith('<pre>') or in_code:
            out.append(line)
            in_code = not t.startswith('</pre>')
            continue
        if t.startswith('<li>'):
            if not in_list: out.append('<ul>'); in_list = True
            out.append(t)
        else:
            if in_list: out.append('</ul>'); in_list = False
            if t: out.append(f'<p>{line}</p>')
    if in_list: out.append('</ul>')
    return '\n'.join(out)


if __name__ == '__main__':
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    print('=' * 50)
    print('文档转微信读书电子书 - 本地服务')
    print('=' * 50)
    print(f'Tesseract: {TESSERACT_CMD}')
    print(f'语言包目录: {TESSDATA_PREFIX}')
    print(f'访问地址: http://localhost:5000')
    print('=' * 50)
    app.run(host='127.0.0.1', port=5000, debug=False)
