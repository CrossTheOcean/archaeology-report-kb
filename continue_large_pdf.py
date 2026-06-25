#!/opt/homebrew/opt/python@3.13/bin/python3.13
"""
继续处理《蒙城尉迟寺（第二部）》131MB超大PDF
chunk_001已完成，从chunk_002开始继续
"""

import json
import subprocess
import os
import time
import fitz

BASE = "/Users/crosstheocean/WorkBuddy/20260330184406"
os.chdir(BASE)
os.environ['PATH'] = '/Users/crosstheocean/.npm-global/bin:' + os.environ.get('PATH', '')

CHUNK_SIZE = 50
MAX_RETRIES = 5
EXTRACT_TIMEOUT = 900

PDF_NAME = "78.丁種第七十八：《蒙城尉迟寺（第二部）》.pdf"
PDF_PATH = f"{BASE}/考古报告PDF/{PDF_NAME}"
OUTPUT_DIR = f"{BASE}/提取结果/《蒙城尉迟寺（第二部）》"

def get_page_chunks():
    """获取PDF页数和分片，跳过已完成的chunk_001"""
    doc = fitz.open(PDF_PATH)
    total = len(doc)
    doc.close()
    
    chunks = []
    s = 1
    chunk_num = 1
    while s <= total:
        e = min(s + CHUNK_SIZE - 1, total)
        chunks.append((chunk_num, s, e))
        s = e + 1
        chunk_num += 1
    
    return total, chunks

def split_one_chunk(chunk_num, start_page, end_page):
    """分割单个chunk为独立PDF"""
    doc = fitz.open(PDF_PATH)
    new_doc = fitz.open()
    
    for i in range(start_page - 1, end_page):
        new_doc.insert_pdf(doc, from_page=i, to_page=i)
    
    chunk_pdf_path = f"{OUTPUT_DIR}/_chunk_{chunk_num:03d}.pdf"
    new_doc.save(chunk_pdf_path)
    new_doc.close()
    doc.close()
    
    size_mb = os.path.getsize(chunk_pdf_path) / (1024 * 1024)
    print(f"  生成分片PDF: {chunk_pdf_path} ({size_mb:.1f}MB, 页{start_page}-{end_page})")
    return chunk_pdf_path

def extract_with_mineru(chunk_pdf_path, chunk_dir):
    """用mineru-open-api提取分片PDF"""
    os.makedirs(chunk_dir, exist_ok=True)
    
    cmd = ['mineru-open-api', 'extract', chunk_pdf_path,
           '-o', chunk_dir, '-f', 'md,html', '--ocr']
    
    for attempt in range(MAX_RETRIES):
        try:
            print(f"    提取中... (尝试 {attempt + 1}/{MAX_RETRIES})")
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=EXTRACT_TIMEOUT)
        except subprocess.TimeoutExpired:
            print(f"    超时")
            if attempt < MAX_RETRIES - 1:
                time.sleep(30)
            continue
        
        if r.returncode == 0:
            md_files = [f for f in os.listdir(chunk_dir) if f.endswith('.md')]
            if md_files:
                print(f"    ✓ 成功")
                return True
            else:
                print(f"    无md输出")
        else:
            err = (r.stderr or r.stdout or '').strip()[:100]
            print(f"    错误: {err}")
        
        if attempt < MAX_RETRIES - 1:
            time.sleep(15)
    
    return False

def merge_and_annotate():
    """合并所有chunk并标注实体"""
    import glob
    
    # 收集所有chunk的md文件
    all_md = []
    chunk_dirs = sorted([d for d in os.listdir(OUTPUT_DIR) if d.startswith('_chunk_') and os.path.isdir(f"{OUTPUT_DIR}/{d}")])
    
    for cd in chunk_dirs:
        cd_path = f"{OUTPUT_DIR}/{cd}"
        md_files = sorted([f for f in os.listdir(cd_path) if f.endswith('.md')])
        for mf in md_files:
            with open(f'{cd_path}/{mf}', 'r', errors='ignore') as f:
                all_md.append(f.read())
    
    if not all_md:
        print("没有markdown内容可合并")
        return False
    
    md_path = f'{OUTPUT_DIR}/蒙城尉迟寺第二部.md'
    with open(md_path, 'w') as f:
        f.write('\n\n---\n\n'.join(all_md))
    
    print(f"合并完成: {len(chunk_dirs)} 个分片 → {os.path.getsize(md_path)//1024}KB")
    
    # 实体标注
    try:
        r = subprocess.run(
            ['python3', '标注脚本/annotate_entities.py', md_path],
            capture_output=True, text=True, timeout=600
        )
        if r.returncode == 0 and os.path.exists(f'{OUTPUT_DIR}/entities.json'):
            with open(f'{OUTPUT_DIR}/entities.json') as f:
                d = json.load(f)
                cnt = sum(len(v) for v in d.values())
            print(f"标注完成: {cnt} 个实体, {len(d)} 个类别")
            return True
        else:
            print(f"标注失败: {(r.stderr or r.stdout)[:80]}")
            return False
    except subprocess.TimeoutExpired:
        print("标注超时")
        return False

def main():
    print("=" * 60)
    print("继续处理《蒙城尉迟寺（第二部）》")
    print("=" * 60)
    
    # 检查chunk_001状态
    chunk1_dir = f"{OUTPUT_DIR}/_chunk_001"
    chunk1_has_md = os.path.exists(chunk1_dir) and any(f.endswith('.md') for f in os.listdir(chunk1_dir))
    
    if not chunk1_has_md:
        print("错误: chunk_001 未完成，需要从头开始")
        return
    
    print(f"✓ chunk_001 已完成")
    
    # 清理失败的chunk_002
    chunk2_dir = f"{OUTPUT_DIR}/_chunk_002"
    if os.path.exists(chunk2_dir) and not any(f.endswith('.md') for f in os.listdir(chunk2_dir)):
        print("清理空的 chunk_002...")
        import shutil
        shutil.rmtree(chunk2_dir)
    
    # 获取分片信息
    total_pages, chunks = get_page_chunks()
    print(f"\nPDF总页数: {total_pages}")
    print(f"总分片数: {len(chunks)}")
    
    # 处理剩余分片
    success_count = 1  # chunk_001已完成
    
    for chunk_num, start_page, end_page in chunks:
        if chunk_num == 1:
            continue  # 跳过已完成的chunk_001
        
        chunk_dir = f"{OUTPUT_DIR}/_chunk_{chunk_num:03d}"
        
        # 检查是否已处理
        if os.path.exists(chunk_dir) and any(f.endswith('.md') for f in os.listdir(chunk_dir)):
            print(f"\n[{chunk_num}/{len(chunks)}] chunk_{chunk_num:03d} (页{start_page}-{end_page}): 已存在，跳过")
            success_count += 1
            continue
        
        print(f"\n[{chunk_num}/{len(chunks)}] 处理 chunk_{chunk_num:03d} (页{start_page}-{end_page})...")
        
        # 1. 分割PDF
        chunk_pdf_path = f"{OUTPUT_DIR}/_chunk_{chunk_num:03d}.pdf"
        if not os.path.exists(chunk_pdf_path):
            print("  分割PDF...")
            split_one_chunk(chunk_num, start_page, end_page)
        
        # 2. 提取
        if extract_with_mineru(chunk_pdf_path, chunk_dir):
            success_count += 1
            # 删除临时PDF
            if os.path.exists(chunk_pdf_path):
                os.remove(chunk_pdf_path)
        else:
            print(f"  ✗ chunk_{chunk_num:03d} 处理失败")
        
        # 休息一下
        if chunk_num < len(chunks):
            time.sleep(5)
    
    print(f"\n提取完成: {success_count}/{len(chunks)} 个分片")
    
    # 3. 合并标注
    if success_count == len(chunks):
        print("\n合并所有分片并标注...")
        merge_and_annotate()
        print("\n" + "=" * 60)
        print("✓ 全部完成！")
        print("=" * 60)
    else:
        print(f"\n⚠ 有 {len(chunks) - success_count} 个分片失败，未进行合并")

if __name__ == "__main__":
    main()
