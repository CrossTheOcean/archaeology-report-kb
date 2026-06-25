#!/usr/bin/env python3
"""
分片处理超大PDF文件 - 使用 mineru-open-api
处理《蒙城尉迟寺（第二部）》131MB
"""

import json
import subprocess
import os
import time
import re
import fitz  # PyMuPDF

BASE = "/Users/crosstheocean/WorkBuddy/20260330184406"
os.chdir(BASE)
os.environ['PATH'] = '/Users/crosstheocean/.npm-global/bin:' + os.environ.get('PATH', '')

# 更小的分片大小（超大文件用50页）
CHUNK_SIZE = 50
MAX_RETRIES = 5
EXTRACT_TIMEOUT = 900

PDF_NAME = "78.丁種第七十八：《蒙城尉迟寺（第二部）》.pdf"
OUTPUT_DIR = "提取结果/《蒙城尉迟寺（第二部）》"

def get_page_chunks(pdf_path):
    """获取PDF页数和分片"""
    doc = fitz.open(pdf_path)
    total = len(doc)
    doc.close()
    
    chunks = []
    s = 1
    while s <= total:
        e = min(s + CHUNK_SIZE - 1, total)
        chunks.append(f'{s}-{e}')
        s = e + 1
    
    return total, chunks

def extract_one_chunk(pdf, chunk_dir, pages_str):
    """提取单个分片"""
    os.makedirs(chunk_dir, exist_ok=True)
    
    cmd = ['mineru-open-api', 'extract', f'考古报告PDF/{pdf}',
           '-o', chunk_dir, '-f', 'md,html', '--ocr', '--pages', pages_str]
    
    for attempt in range(MAX_RETRIES):
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=EXTRACT_TIMEOUT)
        except subprocess.TimeoutExpired:
            print(f'      chunk {pages_str} try {attempt+1}: 超时', flush=True)
            if attempt < MAX_RETRIES - 1:
                time.sleep(30)
            continue
        
        if r.returncode == 0:
            md_files = [f for f in os.listdir(chunk_dir) if f.endswith('.md')]
            if md_files:
                print(f'      chunk {pages_str}: ✓ 成功', flush=True)
                return True
            else:
                print(f'      chunk {pages_str} try {attempt+1}: 无md输出', flush=True)
        else:
            err = (r.stderr or r.stdout or '').strip()[:80]
            print(f'      chunk {pages_str} try {attempt+1}: {err}', flush=True)
        
        if attempt < MAX_RETRIES - 1:
            time.sleep(15)
    
    return False

def merge_and_annotate(out_dir):
    """合并分片并标注"""
    # 收集所有chunk目录
    chunk_dirs = sorted([d for d in os.listdir(out_dir) if d.startswith('_chunk_')])
    
    if not chunk_dirs:
        print('    没有找到分片目录', flush=True)
        return False
    
    # 合并markdown
    all_md = []
    for cd in chunk_dirs:
        cd_path = f'{out_dir}/{cd}'
        md_files = sorted([f for f in os.listdir(cd_path) if f.endswith('.md')])
        for mf in md_files:
            with open(f'{cd_path}/{mf}', 'r', errors='ignore') as f:
                all_md.append(f.read())
    
    if not all_md:
        print('    没有markdown内容', flush=True)
        return False
    
    md_path = f'{out_dir}/蒙城尉迟寺第二部.md'
    with open(md_path, 'w') as f:
        f.write('\n\n---\n\n'.join(all_md))
    
    print(f'    合并 {len(chunk_dirs)} 个分片 → {os.path.getsize(md_path)//1024}KB', flush=True)
    
    # 实体标注
    try:
        r = subprocess.run(
            ['python3', '标注脚本/annotate_entities.py', md_path],
            capture_output=True, text=True, timeout=600
        )
        
        if r.returncode == 0 and os.path.exists(f'{out_dir}/entities.json'):
            with open(f'{out_dir}/entities.json') as f:
                d = json.load(f)
                cnt = sum(len(v) for v in d.values())
            print(f'    标注完成: {cnt} 个实体, {len(d)} 个类别', flush=True)
            return True
        else:
            print(f'    标注失败: {(r.stderr or r.stdout)[:80]}', flush=True)
            return False
    except subprocess.TimeoutExpired:
        print('    标注超时', flush=True)
        return False

def main():
    print("=" * 60)
    print("处理超大PDF文件: 《蒙城尉迟寺（第二部）》")
    print("=" * 60)
    
    pdf_path = f'考古报告PDF/{PDF_NAME}'
    
    # 1. 获取分片信息
    print("\n[1/3] 分析PDF...")
    total_pages, chunks = get_page_chunks(pdf_path)
    print(f"  总页数: {total_pages}")
    print(f"  分片数: {len(chunks)} (每片{CHUNK_SIZE}页)")
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 2. 分片提取
    print("\n[2/3] 分片提取...")
    success_count = 0
    fail_count = 0
    
    for i, chunk in enumerate(chunks):
        chunk_dir = f'{OUTPUT_DIR}/_chunk_{i+1:03d}'
        
        # 检查是否已处理
        if os.path.exists(f'{chunk_dir}/content.md'):
            print(f'  [{i+1}/{len(chunks)}] chunk {chunk}: 已存在，跳过', flush=True)
            success_count += 1
            continue
        
        print(f'  [{i+1}/{len(chunks)}] chunk {chunk}...', flush=True)
        
        if extract_one_chunk(PDF_NAME, chunk_dir, chunk):
            success_count += 1
        else:
            fail_count += 1
        
        # 每处理5个分片休息一下
        if (i + 1) % 5 == 0:
            time.sleep(5)
    
    print(f"\n  提取结果: 成功 {success_count}/{len(chunks)}")
    
    # 3. 合并和标注
    print("\n[3/3] 合并标注...")
    if merge_and_annotate(OUTPUT_DIR):
        print("\n" + "=" * 60)
        print("✓ 处理完成！")
        print("=" * 60)
    else:
        print("\n处理失败，请检查日志")

if __name__ == "__main__":
    main()
