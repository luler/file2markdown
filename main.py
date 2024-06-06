import os
import subprocess
import tempfile
from typing import List

import pypandoc
from fastapi import FastAPI, File, UploadFile, HTTPException

app = FastAPI()

pandoc_supports = ['biblatex', 'bibtex', 'commonmark', 'commonmark_x', 'creole', 'csljson', 'csv', 'docbook', 'docx',
                   'dokuwiki', 'epub', 'fb2', 'gfm', 'haddock', 'html', 'ipynb', 'jats', 'jira', 'json', 'latex', 'man',
                   'markdown', 'markdown_github', 'markdown_mmd', 'markdown_phpextra', 'markdown_strict', 'mediawiki',
                   'muse', 'native', 'odt', 'opml', 'org', 'rst', 't2t', 'textile', 'tikiwiki', 'twiki', 'vimwiki']


# 异步函数，用于保存上传的文件到临时目录
async def save_upload_file(upload_file: UploadFile) -> str:
    suffix = os.path.splitext(upload_file.filename)[1]  # 获取文件后缀名
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:  # 创建临时文件
        temp_file.write(await upload_file.read())  # 将上传的文件内容写入临时文件
        return temp_file.name  # 返回临时文件路径


# 将输入文件转换为HTML文件
def convert_to_html(input_file_path: str) -> str:
    output_dir = os.path.dirname(input_file_path)
    base_name, _ = os.path.splitext(input_file_path)  # 分离文件名和原始后缀
    # 使用LibreOffice将文件转换为HTML格式
    subprocess.run(
        ["libreoffice", "--headless", "--convert-to", "html", input_file_path, "--outdir", output_dir],
        check=True
    )
    return f"{base_name}.html"  # 返回生成的HTML文件路径


# 将文件转换为Markdown文件
def convert_to_md(file_path: str):
    return pypandoc.convert_file(file_path, 'commonmark')  # 使用pypandoc进行转换


# 读取文件内容
def read_file_content(file_path: str) -> str:
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()  # 读取并返回文件内容


@app.post("/convert")
async def convert_file(file: List[UploadFile] = File(...)):
    temp_input_file_path, temp_html_path = None, None
    try:
        if not file or any(f.filename == "" for f in file):
            raise Exception("No file was uploaded")
        if len(file) != 1:
            raise Exception("Only one file can be uploaded at a time")
        file = file[0]

        ext_name = os.path.splitext(file.filename)[1].strip('.')
        temp_input_file_path = await save_upload_file(file)  # 保存上传的文件

        if ext_name in pandoc_supports:
            # pandoc直接转markdown
            markdown_content = convert_to_md(temp_input_file_path)  # 将HTML转换为Markdown
        else:
            # 先转html，再转markdown
            temp_html_path = convert_to_html(temp_input_file_path)  # 转换为HTML
            markdown_content = convert_to_md(temp_html_path)  # 将HTML转换为Markdown

        return {"markdown": markdown_content}  # 返回Markdown内容
    except subprocess.CalledProcessError as e:  # 捕获转换过程中的错误
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")
    except Exception as e:  # 捕获其他异常
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # 清理临时文件和目录
        for temp_file in [temp_input_file_path, temp_html_path]:
            if temp_file and os.path.exists(temp_file):  # 检查路径是否存在
                os.remove(temp_file)  # 删除文件


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=6677)  # 运行FastAPI应用
