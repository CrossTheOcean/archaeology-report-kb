#!/usr/bin/env python3
"""第五轮批量处理 - 坚持用 MinerU API + 分片提取"""
import json, subprocess, os, time, re, sys
import fitz

BASE = "/Users/crosstheocean/WorkBuddy/20260330184406"
os.chdir(BASE)
os.environ['PATH'] = '/Users/crosstheocean/.npm-global/bin:' + os.environ.get('PATH', '')

CHUNK_SIZE = 200
MAX_RETRIES = 5
EXTRACT_TIMEOUT = 1200

def get_short_name(pdf):
    name = pdf.replace('.pdf', '')
    if '：' in name:
        short = name.split('：', 1)[1]
    elif ':' in name:
        short = name.split(':', 1)[1]
    else:
        short = name
    short = short.split('（')[0].split('(')[0].strip()
    short = re.sub(r'^[\d\.\s]+', '', short).strip()
    if not short:
        short = name[:30]
    return short

def get_page_chunks(pdf_path):
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
    os.makedirs(chunk_dir, exist_ok=True)
    cmd = ['mineru-open-api', 'extract', f'考古报告PDF/{pdf}',
           '-o', chunk_dir, '-f', 'md,html', '--ocr', '--pages', pages_str]
    for attempt in range(MAX_RETRIES):
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=EXTRACT_TIMEOUT)
        except subprocess.TimeoutExpired:
            print(f'      chunk {pages_str} try {attempt+1}: TIMEOUT', flush=True)
            if attempt < MAX_RETRIES - 1:
                time.sleep(30)
            continue
        
        if r.returncode == 0:
            md_files = [f for f in os.listdir(chunk_dir) if f.endswith('.md')]
            if md_files:
                print(f'      chunk {pages_str}: OK', flush=True)
                return True
            else:
                print(f'      chunk {pages_str} try {attempt+1}: no_md', flush=True)
        else:
            err = (r.stderr or r.stdout or '').strip()[:60]
            print(f'      chunk {pages_str} try {attempt+1}: {err}', flush=True)
        
        if attempt < MAX_RETRIES - 1:
            time.sleep(20)
    return False

def merge_and_annotate(out_dir, pdf, short):
    base_name = pdf.replace('.pdf', '')
    
    # 收集分片目录
    chunk_dirs = sorted([d for d in os.listdir(out_dir) if d.startswith('_chunk_')])
    if not chunk_dirs:
        # 直接输出的文件
        md_files = sorted([f for f in os.listdir(out_dir) if f.endswith('.md') and not f.startswith('_')])
        if md_files:
            md_path = f'{out_dir}/{md_files[0]}'
        else:
            print(f'    NO_MD', flush=True)
            return False
    else:
        # 合并
        all_md = []
        for cd in chunk_dirs:
            cd_path = f'{out_dir}/{cd}'
            md_files = sorted([f for f in os.listdir(cd_path) if f.endswith('.md')])
            for mf in md_files:
                with open(f'{cd_path}/{mf}', 'r', errors='ignore') as f:
                    all_md.append(f.read())
        
        md_path = f'{out_dir}/{base_name}.md'
        with open(md_path, 'w') as f:
            f.write('\n\n---\n\n'.join(all_md))
        print(f'    合并 {len(chunk_dirs)}片 → {os.path.getsize(md_path)//1024}KB', flush=True)
    
    # 标注
    try:
        r = subprocess.run(
            ['python3', '标注脚本/annotate_entities.py', md_path],
            capture_output=True, text=True, timeout=600
        )
        if r.returncode == 0 and os.path.exists(f'{out_dir}/entities.json'):
            with open(f'{out_dir}/entities.json') as f:
                d = json.load(f)
                cnt = sum(len(v) for v in d.values())
            print(f'    标注完成: {cnt} 实体, {len(d)} 类别', flush=True)
            return True
        else:
            print(f'    标注失败: {(r.stderr or r.stdout)[:80]}', flush=True)
            return False
    except subprocess.TimeoutExpired:
        print(f'    标注超时', flush=True)
        return False

# 扫描已有结果
done_dirs = set()
for r in os.listdir('提取结果'):
    if os.path.exists(f'提取结果/{r}/entities.json'):
        done_dirs.add(r)

# 所有PDF
all_pdfs = sorted([f for f in os.listdir('考古报告PDF') if f.endswith('.pdf')])

remaining = []
for pdf in all_pdfs:
    matched = False
    for d in done_dirs:
        if d in pdf:
            matched = True
            break
    if not matched:
        remaining.append(pdf)

print(f'已有: {len(done_dirs)} 份 | 待处理: {len(remaining)} 份', flush=True)

success = 0
failed = 0
fail_list = []

for i, pdf in enumerate(remaining):
    short = get_short_name(pdf)
    out_dir = f'提取结果/{short}'
    
    if os.path.exists(f'{out_dir}/entities.json'):
        print(f'[{i+1}/{len(remaining)}] SKIP: {short}', flush=True)
        continue
    
    os.makedirs(out_dir, exist_ok=True)
    mb = os.path.getsize(f'考古报告PDF/{pdf}') / (1024*1024)
    
    # 获取页数和分片
    total_pages, chunks = get_page_chunks(f'考古报告PDF/{pdf}')
    print(f'\n[{i+1}/{len(remaining)}] {short} ({mb:.0f}MB, {total_pages}页, {len(chunks)}片)', flush=True)
    
    # 逐片提取
    all_ok = True
    for chunk in chunks:
        chunk_dir = f'{out_dir}/_chunk_{chunk.replace("-", "to")}'
        
        # 如果这个分片已经有了md文件就跳过
        if os.path.exists(chunk_dir):
            md_in_chunk = [f for f in os.listdir(chunk_dir) if f.endswith('.md')]
            if md_in_chunk:
                print(f'      chunk {chunk}: 已有, SKIP', flush=True)
                continue
        
        if not extract_one_chunk(pdf, chunk_dir, chunk):
            all_ok = False
    
    if not all_ok:
        print(f'    部分分片失败，尝试合并已有部分...', flush=True)
        # 即使部分失败也尝试合并标注
        # 但先检查有没有至少一片成功
        has_any = any(
            os.path.exists(f) 
            for cd in os.listdir(out_dir) 
            if cd.startswith('_chunk_')
            for f in [f'{out_dir}/{cd}/{x}' for x in os.listdir(f'{out_dir}/{cd}') if x.endswith('.md')]
        ) if os.path.exists(out_dir) else False
        
        if not has_any:
            failed += 1
            fail_list.append((short, '全部分片失败'))
            continue
    
    # 合并并标注
    if merge_and_annotate(out_dir, pdf, short):
        success += 1
    else:
        failed += 1
        fail_list.append((short, '合并/标注失败'))

# 最终统计
total_reports = 0
total_entities = 0
for r in os.listdir('提取结果'):
    p = f'提取结果/{r}/entities.json'
    if os.path.exists(p):
        total_reports += 1
        with open(p) as f:
            d = json.load(f)
            total_entities += sum(len(v) for v in d.values())

print(f'\n{"="*60}', flush=True)
print(f'本轮: +{success} 成功, {failed} 失败', flush=True)
print(f'总计: {total_reports}/71 份报告, {total_entities} 个实体', flush=True)
if fail_list:
    print(f'失败列表:', flush=True)
    for name, reason in fail_list:
        print(f'  - {name}: {reason}', flush=True)
