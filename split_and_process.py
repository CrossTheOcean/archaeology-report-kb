#!/usr/bin/env python3
"""
分片处理超大PDF文件
策略：将大PDF拆分成小文件，分别提取后合并结果
"""

import os
import json
import requests
import time
from pypdf import PdfReader, PdfWriter

# 配置
MINERU_API = "https://mineru.net/api/v4/file/parse"
API_KEY = "Bearer mcp_xh2XrKJgRgOiBnNfFxqSdRpXrMiQlMnN"  # 替换为实际API Key

# 要处理的PDF
PDF_PATH = "/Users/crosstheocean/WorkBuddy/20260330184406/考古报告PDF/78.丁種第七十八：《蒙城尉迟寺（第二部）》.pdf"
OUTPUT_DIR = "/Users/crosstheocean/WorkBuddy/20260330184406/提取结果/《蒙城尉迟寺（第二部）》"
TEMP_DIR = "/Users/crosstheocean/WorkBuddy/20260330184406/temp_split"

# 28类实体标注
ENTITY_TYPES = [
    "遗址", "墓葬", "遗迹", "遗物", "材质", "器型", "纹饰",
    "时代", "年代", "文化层", "地层", "区域", "地点", "位置",
    "人物", "机构", "方法", "技术", "材料", "工具", "单位",
    "尺寸", "数量", "重量", "颜色", "形状", "特征", "其他"
]

def split_pdf(pdf_path, temp_dir, pages_per_split=50):
    """将PDF分割成多个小文件"""
    os.makedirs(temp_dir, exist_ok=True)
    
    reader = PdfReader(pdf_path)
    total_pages = len(reader.pages)
    print(f"PDF总页数: {total_pages}")
    
    split_files = []
    for i in range(0, total_pages, pages_per_split):
        writer = PdfWriter()
        end_page = min(i + pages_per_split, total_pages)
        
        for j in range(i, end_page):
            writer.add_page(reader.pages[j])
        
        split_path = os.path.join(temp_dir, f"split_{i//pages_per_split + 1}.pdf")
        with open(split_path, 'wb') as f:
            writer.write(f)
        
        size_mb = os.path.getsize(split_path) / 1024 / 1024
        print(f"生成分片 {i//pages_per_split + 1}: 页{i+1}-{end_page}, {size_mb:.1f}MB")
        split_files.append((split_path, i, end_page))
    
    return split_files

def extract_with_mineru(pdf_path, max_retries=3):
    """使用MinerU API提取PDF内容"""
    for attempt in range(max_retries):
        try:
            with open(pdf_path, 'rb') as f:
                files = {'file': (os.path.basename(pdf_path), f, 'application/pdf')}
                headers = {'Authorization': API_KEY}
                
                print(f"  上传中... (尝试 {attempt + 1}/{max_retries})")
                response = requests.post(
                    MINERU_API,
                    files=files,
                    headers=headers,
                    timeout=300
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success') and result.get('data', {}).get('markdown'):
                        return result['data']['markdown']
                
                print(f"  响应状态: {response.status_code}")
                time.sleep(2)
        except Exception as e:
            print(f"  错误: {e}")
            time.sleep(5)
    
    return None

def annotate_entities(text):
    """标注实体"""
    # 简化版：使用关键词匹配
    entities = {et: [] for et in ENTITY_TYPES}
    
    # 这里应该用NLP模型，简化处理
    import re
    
    # 一些简单的模式
    patterns = {
        "遗址": r'[\u4e00-\u9fa5]{2,8}(遗址|城址|聚落)',
        "墓葬": r'[\u4e00-\u9fa5]{2,8}(墓|墓葬|M\d+)',
        "时代": r'(新石器|夏|商|周|春秋|战国|汉|唐|宋|元|明|清|龙山|二里头|仰韶|大汶口)文化?',
        "材质": r'(陶|铜|玉|石|骨|蚌|漆|木|金|银|铁)(器|质)?',
    }
    
    for etype, pattern in patterns.items():
        matches = re.findall(pattern, text)
        entities[etype] = list(set(matches))[:50]  # 限制数量
    
    return entities

def main():
    print("=" * 60)
    print("分片处理超大PDF文件")
    print("=" * 60)
    
    # 1. 分割PDF
    print("\n[1/4] 分割PDF...")
    split_files = split_pdf(PDF_PATH, TEMP_DIR, pages_per_split=30)
    print(f"共生成 {len(split_files)} 个分片文件")
    
    # 2. 分别提取
    print("\n[2/4] 提取各分片...")
    all_markdown = []
    successful = 0
    
    for i, (split_path, start_page, end_page) in enumerate(split_files):
        print(f"\n处理分片 {i+1}/{len(split_files)} (页{start_page+1}-{end_page})...")
        
        md_content = extract_with_mineru(split_path)
        if md_content:
            all_markdown.append(f"\n\n---\n\n## 第{start_page+1}-{end_page}页\n\n{md_content}")
            successful += 1
            print(f"  ✓ 成功")
        else:
            all_markdown.append(f"\n\n---\n\n## 第{start_page+1}-{end_page}页\n\n[提取失败]")
            print(f"  ✗ 失败")
    
    print(f"\n提取成功: {successful}/{len(split_files)}")
    
    # 3. 合并结果
    print("\n[3/4] 合并结果...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    full_markdown = "# 《蒙城尉迟寺（第二部）》\n\n" + "".join(all_markdown)
    
    # 保存markdown
    md_path = os.path.join(OUTPUT_DIR, "蒙城尉迟寺第二部.md")
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(full_markdown)
    print(f"已保存: {md_path}")
    
    # 4. 实体标注
    print("\n[4/4] 实体标注...")
    entities = annotate_entities(full_markdown)
    total_entities = sum(len(v) for v in entities.values())
    
    entities_path = os.path.join(OUTPUT_DIR, "entities.json")
    with open(entities_path, 'w', encoding='utf-8') as f:
        json.dump(entities, f, ensure_ascii=False, indent=2)
    print(f"已保存实体: {entities_path}")
    
    # 清理临时文件
    print("\n清理临时文件...")
    import shutil
    shutil.rmtree(TEMP_DIR)
    
    print("\n" + "=" * 60)
    print(f"完成！提取 {successful}/{len(split_files)} 个分片，识别 {total_entities} 个实体")
    print("=" * 60)

if __name__ == "__main__":
    main()
