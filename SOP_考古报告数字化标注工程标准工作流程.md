# 考古报告数字化标注工程标准工作流程（SOP）

## 项目概述

基于中国考古学专刊·丁种（70份报告、44,526个实体、24,866页）标注工程实践经验，总结形成的标准化操作流程。

**适用场景**：考古发掘报告、调查报告、研究文献的数字化提取与实体标注

**预期产出**：结构化实体数据 + 知识库网站 + 标注语料库

---

## 阶段一：项目准备（1-2天）

### 1.1 需求分析

| 检查项 | 说明 | 工具/资源 |
|--------|------|-----------|
| 文献范围 | 明确文献类型、时间跨度、数量 | 文献清单 |
| 标注目标 | 定义实体类别（建议20-30类） | 标注规范文档 |
| 质量标准 | 设定准确率目标（建议≥85%） | 验收标准 |
| 交付形式 | 确定输出格式（JSON/HTML/网站） | 技术方案 |

### 1.2 实体类别设计

**推荐26类实体体系**（可根据项目调整）：

```
├── 编号系统（器物编号、单位编号）
├── 器物（陶片、铜器、玉器、石器等）
├── 测量数据（尺寸、重量、比例）
├── 考古信息（地层、遗迹、墓葬）
├── 空间信息（方位、坐标、关系）
└── 其他（年代、分期、文化类型）
```

### 1.3 环境搭建

**必需工具清单**：

| 工具 | 用途 | 获取方式 |
|------|------|----------|
| Python 3.9+ | 批处理脚本 | python.org |
| MinerU API | PDF文本提取 | mineru.open.ai |
| pymupdf | PDF分割/处理 | pip install pymupdf |
| markdown | MD转HTML | pip install markdown |
| python-docx | 生成Word | pip install python-docx |
| GitHub账号 | 代码托管/部署 | github.com |

**目录结构模板**：

```
项目根目录/
├── 原始PDF/                 # 存放原始PDF文件
├── 提取结果/               # 存放提取后的MD/HTML
│   └── 报告名称/
│       ├── entities.json   # 实体标注结果
│       ├── annotated.html  # 标注可视化
│       └── 报告名称.md     # 提取的Markdown
├── data/                   # 元数据
│   ├── reports_data.json   # 报告元数据
│   └── china_provinces.json # 地图数据
├── scripts/                # 脚本
│   ├── batch_process.py    # 批量处理主脚本
│   ├── annotate_entities.py # 实体标注脚本
│   └── build_site.py       # 网站构建脚本
├── docs/                   # 文档
└── _site/                  # 网站输出（自动生成）
```

---

## 阶段二：数据采集（2-5天）

### 2.1 文献获取

**来源优先级**：
1. **Internet Archive** (archive.org) — 开放获取，批量下载
2. **Anna's Archive** — 学术资源聚合
3. **全国图书馆参考咨询联盟** — 文献传递
4. **机构数字图书馆** — 知网、万方等

**批量下载策略**：

```bash
# 使用aria2c多线程下载
aria2c -x 16 -s 16 -i download_list.txt

# 或使用wget批量下载
wget -i urls.txt -P ./原始PDF/
```

### 2.2 数据清洗

**质量检查清单**：
- [ ] 文件完整性（PDF可正常打开）
- [ ] 页数核对（与目录/前言标注一致）
- [ ] 重复文件去重（MD5校验）
- [ ] 命名规范化（编号_报告名.pdf）

**命名规范示例**：
```
丁種第一_辉县发掘报告.pdf
丁種第二_郑州二里岗.pdf
丁種第三_长沙发掘报告.pdf
```

### 2.3 元数据整理

创建 `reports_data.json`：

```json
[
  {
    "slug": "丁種第一_辉县发掘报告",
    "display_name": "辉县发掘报告",
    "era_group": "夏商周",
    "pdf_pages": 279,
    "pdf_mb": 48.0,
    "coordinates": {"lat": 35.4, "lng": 113.8}
  }
]
```

---

## 阶段三：文本提取（3-7天）

### 3.1 MinerU API提取

**工具原理**：MinerU将PDF转换为结构化Markdown，保留段落、表格、图片位置信息。

**标准提取流程**：

```python
# 1. 小于50MB的文件直接提取
python mineru_extract.py --input 报告.pdf --output 结果目录/

# 2. 大于50MB的文件需要分割
python split_pdf.py --input 大文件.pdf --max-pages 200 --output chunks/

# 3. 分批上传提取
for chunk in chunks/*.pdf:
    python mineru_extract.py --input $chunk --output chunk_results/

# 4. 合并结果
python merge_chunks.py --input chunk_results/ --output final.md
```

### 3.2 大文件处理策略

**触发条件**：PDF > 50MB

**处理步骤**：
1. 使用 `pymupdf` 物理分割为 ≤200页/≤40MB 的片段
2. 逐片上传MinerU API
3. 合并所有片段的Markdown结果
4. 删除临时片段文件

**关键代码**：

```python
import fitz  # pymupdf

def split_pdf(input_path, max_pages=200, max_size_mb=40):
    doc = fitz.open(input_path)
    total_pages = len(doc)
    chunks = []
    
    for start in range(0, total_pages, max_pages):
        end = min(start + max_pages, total_pages)
        chunk_doc = fitz.open()
        chunk_doc.insert_pdf(doc, from_page=start, to_page=end-1)
        
        output_path = f"{input_path.stem}_chunk_{start}_{end}.pdf"
        chunk_doc.save(output_path)
        chunks.append(output_path)
    
    return chunks
```

### 3.3 批量处理脚本

**主处理脚本结构**：

```python
# batch_process.py
import os, json, time
from pathlib import Path

REPORTS_DIR = Path("原始PDF")
OUTPUT_DIR = Path("提取结果")

def process_report(pdf_path):
    """处理单份报告"""
    report_name = pdf_path.stem
    report_dir = OUTPUT_DIR / report_name
    report_dir.mkdir(exist_ok=True)
    
    # 1. 提取文本
    md_content = extract_with_mineru(pdf_path)
    
    # 2. 保存Markdown
    with open(report_dir / f"{report_name}.md", 'w') as f:
        f.write(md_content)
    
    # 3. 实体标注
    entities = annotate_entities(md_content)
    
    # 4. 保存实体
    with open(report_dir / "entities.json", 'w') as f:
        json.dump(entities, f, ensure_ascii=False, indent=2)
    
    return len(entities)

# 批量处理
total = 0
for pdf in REPORTS_DIR.glob("*.pdf"):
    try:
        count = process_report(pdf)
        total += count
        print(f"✓ {pdf.name}: {count} 个实体")
    except Exception as e:
        print(f"✗ {pdf.name}: {e}")
        # 记录失败，稍后重试
```

### 3.4 多轮重试机制

**失败处理策略**：
- 网络错误 → 自动重试3次，指数退避
- 格式错误 → 记录到 `failed_reports.json`，人工检查
- API限制 → 添加延迟，错峰处理

**重试脚本**：

```python
# batch_retry.py
failed = json.load(open('failed_reports.json'))
for report in failed:
    try:
        process_report(Path(report['path']))
        print(f"✓ 重试成功: {report['name']}")
    except Exception as e:
        print(f"✗ 重试失败: {report['name']} - {e}")
```

---

## 阶段四：实体标注（核心阶段，5-10天）

### 4.1 标注规则设计

**命名实体识别（NER）模式**：

```python
ENTITY_PATTERNS = {
    "器物编号": r"([MT]\d{1,4}[a-z]?|[A-Z]\d{1,3}:\d{1,3})",
    "单位编号": r"(T\d{1,3}[A-Z]?|H\d{1,3}|M\d{1,3})",
    "尺寸": r"(\d+\.?\d*)\s*[×xX]\s*(\d+\.?\d*)\s*(?:[×xX]\s*(\d+\.?\d*))?\s*(?:厘米|cm)",
    "年代": r"(?:距今|约|公元前|公元后)\s*\d{1,5}(?:\s*[-～]\s*\d{1,5})?\s*(?:年|代)",
    "地层": r"(?:第?[一二三四五六七八九十]+层|第\s*\d+\s*层)",
}
```

### 4.2 标注脚本核心逻辑

```python
# annotate_entities.py
import re
import json

def annotate_entities(text, patterns):
    """对文本进行实体标注"""
    entities = {}
    
    for entity_type, pattern in patterns.items():
        matches = []
        for match in re.finditer(pattern, text):
            matches.append({
                "text": match.group(),
                "start": match.start(),
                "end": match.end()
            })
        
        if matches:
            entities[entity_type] = matches
    
    return entities

def generate_annotated_html(text, entities):
    """生成带标注高亮的HTML"""
    # 按位置排序，处理重叠
    all_entities = []
    for etype, elist in entities.items():
        for e in elist:
            all_entities.append({**e, "type": etype})
    
    all_entities.sort(key=lambda x: x["start"])
    
    # 构建HTML
    html_parts = []
    last_end = 0
    
    for e in all_entities:
        # 添加普通文本
        html_parts.append(text[last_end:e["start"]])
        
        # 添加标注实体
        color = ENTITY_COLORS.get(e["type"], "#888")
        html_parts.append(
            f'<span class="entity" data-type="{e["type"]}" '
            f'style="background:{color}20;border-bottom:2px solid {color}">'
            f'{text[e["start"]:e["end"]]}'
            f'</span>'
        )
        
        last_end = e["end"]
    
    html_parts.append(text[last_end:])
    return "".join(html_parts)
```

### 4.3 标注质量控制

**自动检查规则**：

```python
QUALITY_CHECKS = {
    "实体密度": lambda r: r["total_entities"] / r["pdf_pages"] > 5,
    "类别覆盖": lambda r: r["entity_categories"] >= 10,
    "无空实体": lambda r: all(len(v) > 0 for v in r["entities"].values()),
}

def validate_report(report_data):
    """验证报告质量"""
    issues = []
    for check_name, check_fn in QUALITY_CHECKS.items():
        if not check_fn(report_data):
            issues.append(check_name)
    return issues
```

### 4.4 人工复核清单

**抽样检查（建议10%）**：
- [ ] 打开 annotated.html，检查标注位置是否正确
- [ ] 检查是否有漏标的明显实体（如"T1"单位编号）
- [ ] 检查是否有误标（如将正文数字标为尺寸）
- [ ] 核对实体数量与预期是否匹配

---

## 阶段五：质量控制（2-3天）

### 5.1 数据完整性检查

```python
# quality_check.py
import json
from pathlib import Path

def check_all_reports():
    results = {"ok": [], "warn": [], "error": []}
    
    for report_dir in Path("提取结果").iterdir():
        if not report_dir.is_dir():
            continue
        
        # 检查必需文件
        required = ["entities.json", f"{report_dir.name}.md"]
        missing = [f for f in required if not (report_dir / f).exists()]
        
        if missing:
            results["error"].append({"name": report_dir.name, "missing": missing})
            continue
        
        # 检查实体数量
        entities = json.load(open(report_dir / "entities.json"))
        total = sum(len(v) for v in entities.values())
        
        if total < 50:
            results["warn"].append({"name": report_dir.name, "entities": total})
        else:
            results["ok"].append({"name": report_dir.name, "entities": total})
    
    return results
```

### 5.2 统计报告生成

**自动生成统计文档**：

```python
def generate_stats_report():
    data = json.load(open("data/reports_data.json"))
    
    # 时代分布
    era_dist = Counter(r["era_group"] for r in data)
    
    # 实体数量分布
    entity_counts = [r["total_entities"] for r in data]
    
    report = f"""
    # 数据质量报告
    
    ## 基本统计
    - 报告总数: {len(data)}
    - 总实体数: {sum(entity_counts):,}
    - 平均每报告: {sum(entity_counts)/len(data):.1f} 个实体
    
    ## 时代分布
    {era_dist}
    
    ## 异常检查
    - 实体数<50的报告: {len([r for r in data if r['total_entities'] < 50])}
    """
    
    return report
```

---

## 阶段六：成果输出（3-5天）

### 6.1 知识库网站构建

**网站架构**：

```
_site/                      # 网站根目录
├── index.html             # 首页（仪表盘）
├── reports.html           # 报告列表
├── map.html               # 遗址地图
├── download.html          # 数据下载
├── about.html             # 关于页面
├── report/                # 报告详情页
│   ├── 丁種第一_辉县发掘报告.html
│   ├── 丁種第二_郑州二里岗.html
│   └── ...
└── assets/                # 静态资源
    ├── style.css
    └── chart.js
```

**构建脚本执行**：

```bash
# 1. 构建网站
python3 scripts/build_site.py

# 2. 本地预览
open _site/index.html

# 3. 部署到GitHub Pages
cd _site
git init
git checkout -b gh-pages
git add .
git commit -m "deploy: 知识库 v1.0"
git remote add origin https://github.com/用户名/仓库名.git
git push origin gh-pages --force
```

### 6.2 数据发布

**推荐发布渠道**：

| 渠道 | 用途 | 格式 |
|------|------|------|
| GitHub Releases | 数据包下载 | tar.gz / zip |
| Zenodo | 学术引用 | 完整数据集 |
| Figshare | 可视化数据 | CSV/JSON |
| 个人网站 | 展示与导航 | HTML |

**发布清单**：
- [ ] entities.json（所有报告的实体数据）
- [ ] reports_metadata.json（报告元数据）
- [ ] annotated_html.zip（标注可视化文件）
- [ ] full_text_md.zip（全文Markdown）
- [ ] README.md（使用说明）

### 6.3 文档撰写

**推荐产出文档**：

1. **研究报告** — 学术论文格式，包含方法、结果、讨论
2. **技术白皮书** — 详细的技术实现说明
3. **使用手册** — 面向用户的数据使用指南
4. **统计报表** — 报告清单与实体统计表

---

## 资源清单

### 人力资源估算

| 角色 | 人数 | 工作内容 | 时间 |
|------|------|----------|------|
| 项目负责人 | 1 | 规划、协调、质量把关 | 全程 |
| 数据处理员 | 1-2 | 文本提取、批量处理 | 阶段三、四 |
| 标注审核员 | 1 | 实体标注规则制定与审核 | 阶段四、五 |
| 开发人员 | 1 | 脚本编写、网站构建 | 阶段六 |

**总工期估算**：4-6周（单人）/ 2-3周（团队）

### 计算资源估算

| 资源 | 规格 | 用途 | 成本 |
|------|------|------|------|
| MinerU API | 按需付费 | PDF提取 | ¥0.1-0.3/页 |
| 云服务器 | 4核8G | 批量处理（可选） | ¥0.5/小时 |
| GitHub Pages | 免费 | 网站托管 | ¥0 |
| 本地存储 | 50GB+ | 数据存储 | - |

### 软件许可

- Python：免费开源
- MinerU API：按量付费
- pymupdf：AGPL（商用需授权）
- GitHub：免费公开仓库

---

## 常见问题与解决方案

### Q1: PDF提取失败怎么办？

**可能原因及解决**：
- 扫描版PDF → 使用OCR预处理（如Adobe Acrobat）
- 文件过大 → 分割后分批处理
- 加密PDF → 先解密再处理
- 格式特殊 → 尝试PDF转图片再提取

### Q2: 实体标注准确率不高？

**优化策略**：
- 调整正则表达式，增加边界限制（如`\b`）
- 增加上下文规则（如"第X层"才是地层）
- 人工标注样本，训练机器学习模型
- 设置黑名单过滤常见误标词

### Q3: 如何处理图片中的文字？

**方案选择**：
- 少量图片 → 人工转录
- 大量图片 → 使用OCR工具（PaddleOCR、Tesseract）
- 图文混排 → MinerU已集成OCR，自动提取

### Q4: 项目数据量很大如何处理？

**扩展方案**：
- 使用消息队列（Redis/RabbitMQ）管理任务
- 多机并行处理
- 数据库（SQLite/PostgreSQL）存储实体
- 增量更新机制

---

## 模板文件

### 项目启动模板

```markdown
# 项目启动文档

## 基本信息
- 项目名称：
- 文献来源：
- 预期数量：
- 标注类别：

## 时间计划
| 阶段 | 开始日期 | 结束日期 | 负责人 |
|------|----------|----------|--------|
| 准备 | | | |
| 采集 | | | |
| 提取 | | | |
| 标注 | | | |
| 质控 | | | |
| 输出 | | | |

## 验收标准
- [ ] 提取成功率 ≥ 95%
- [ ] 实体标注准确率 ≥ 85%
- [ ] 网站正常访问
- [ ] 数据完整发布
```

### 日报模板

```markdown
# 工作日报 — YYYY-MM-DD

## 今日完成
- [ ] 处理报告 X 份
- [ ] 提取实体 X 个
- [ ] 修复问题 X 个

## 遇到的问题
- 

## 明日计划
- 

## 阻塞事项
- 
```

---

## 附录

### A. 推荐实体类别参考

| 大类 | 子类 | 示例 | 正则参考 |
|------|------|------|----------|
| 编号系统 | 器物编号 | M1001, T3:15 | `[MT]\d+[a-z]?` |
| 编号系统 | 单位编号 | T1, H5, M20 | `[THM]\d+[A-Z]?` |
| 器物 | 陶片 | 陶片、陶器、陶罐 | `陶器?|陶片|陶罐` |
| 器物 | 铜器 | 铜器、铜鼎、铜镜 | `铜[器鼎镜剑]` |
| 器物 | 玉器 | 玉器、玉璧、玉琮 | `玉[器璧琮璜]` |
| 测量数据 | 尺寸 | 10×5×3厘米 | `\d+\.?\d*\s*[×xX]` |
| 测量数据 | 重量 | 50克、1.5千克 | `\d+\.?\d*\s*克` |
| 考古信息 | 地层 | 第3层、第三层 | `第[一二三四五六七八九十\d]+层` |
| 考古信息 | 遗迹 | F1, H2, M3 | `[FHM]\d+` |
| 空间信息 | 方位 | 东南、西北偏北 | `东|南|西|北|东南|西北|东北|西南` |
| 年代 | 绝对年代 | 距今5000年 | `距今\s*\d+\s*年` |
| 年代 | 相对年代 | 商代晚期 | `[夏商周秦汉]代` |

### B. 代码仓库模板

```
project-template/
├── .gitignore
├── README.md
├── requirements.txt
├── data/
│   └── .gitkeep
├── 原始PDF/
│   └── .gitkeep
├── 提取结果/
│   └── .gitkeep
├── scripts/
│   ├── __init__.py
│   ├── config.py
│   ├── batch_process.py
│   ├── annotate_entities.py
│   ├── quality_check.py
│   └── build_site.py
├── docs/
│   └── SOP.md
└── tests/
    └── test_annotate.py
```

### C. 参考文献格式

采用 GB/T 7714-2015 标准：

```
[1] 中国科学院考古研究所. 辉县发掘报告[M]. 北京: 科学出版社, 1956.
[2] 中国社会科学院考古研究所. 偃师二里头：1959—1978年考古发掘报告[M]. 北京: 中国大百科全书出版社, 1999.
```

---

## 版本历史

| 版本 | 日期 | 更新内容 | 作者 |
|------|------|----------|------|
| v1.0 | 2026-04 | 基于丁种丛书项目经验整理 | - |

---

*本文档基于中国考古学专刊·丁种（70份报告、44,526个实体）标注工程实践经验总结而成。*
