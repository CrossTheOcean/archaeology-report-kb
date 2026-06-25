#!/usr/bin/env python3
"""
多页面知识库网站构建脚本
从 reports_data.json + 提取结果/ 生成完整的静态网站
"""
import json, os, shutil, re, markdown
from collections import Counter, defaultdict
from pathlib import Path

# ====== 路径配置 ======
BASE = Path(__file__).resolve().parent.parent
DATA_FILE = BASE / 'data' / 'reports_data.json'
RESULTS_DIR = BASE / '提取结果'
OUTPUT_DIR = BASE / '_site'
MAP_IMAGE = BASE / 'visualization' / '遗址分布地图.png'

# 站点配置
SITE_TITLE = '中国考古学专刊·丁种 — 实体标注知识库'
SITE_DESC = '基于70份考古学专刊·丁种发掘报告的实体标注与结构化知识库'
SITE_REPO = 'https://github.com/CrossTheOcean/archaeology-report-kb'
# 本地使用空字符串，GitHub Pages使用 '/archaeology-report-kb'
SITE_BASE = ''  # 本地版本使用相对路径

# ====== 时代分类体系 ======
ERA_MAP = {
    "辉县": "商周", "曾侯乙": "战国", "师赵村": "新石器", "武功": "新石器",
    "三里河": "新石器", "青龙泉": "新石器", "双砣子": "青铜时代",
    "寺洼": "青铜时代", "中州路": "东周", "洛阳发掘": "东周秦汉",
    "二里岗": "商代", "长沙发掘": "战国秦汉", "贝丘": "新石器",
    "定陵": "明代", "满城": "西汉", "未央宫": "西汉", "武库": "西汉",
    "杜陵": "西汉", "礼制": "西汉", "南越王": "西汉", "广州汉墓": "东汉",
    "马王堆": "西汉", "东周汉墓": "东周秦汉", "湾张": "北朝", "鄂城": "六朝",
    "永宁寺": "北魏", "隋唐墓": "隋唐", "大明宫": "唐代", "王建墓": "五代",
    "官窑": "宋代", "灵武": "西夏", "新疆": "边疆考古", "吐鲁番": "边疆考古",
    "塔里木": "边疆考古", "北庭": "边疆考古", "二里头": "夏代", "殷墟": "商代",
    "殷虚": "商代", "妇好": "商代", "张家坡": "西周", "沣西": "西周",
    "澧西": "西周", "虢国": "西周", "碾子坡": "先周", "前掌大": "商代",
    "东下冯": "夏商", "漕运": "秦汉", "程村": "春秋", "雨台山": "战国",
    "屈家岭": "新石器", "元君庙": "新石器", "庙底沟": "新石器", "赵宝沟": "新石器",
    "大甸子": "青铜时代", "卡若": "新石器", "北首岭": "新石器", "雕龙碑": "新石器",
    "王因": "新石器", "柳湾": "新石器", "尉迟寺": "新石器", "哈克": "新石器",
    "半坡": "新石器", "铁生沟": "秦汉", "信阳楚墓": "夏商周", "郊区隋唐": "隋唐",
    "大葆台": "秦汉",
}
ERA_GROUP = {
    "新石器": "新石器时代", "青铜时代": "青铜时代",
    "夏代": "夏商周", "夏商": "夏商周", "商代": "夏商周", "先周": "夏商周",
    "西周": "夏商周", "商周": "夏商周", "东周": "夏商周", "春秋": "夏商周",
    "战国": "夏商周", "战国秦汉": "秦汉",
    "秦汉": "秦汉", "西汉": "秦汉", "东汉": "秦汉",
    "六朝": "魏晋南北朝", "北朝": "魏晋南北朝", "北魏": "魏晋南北朝",
    "隋唐": "隋唐", "唐代": "隋唐", "五代": "隋唐",
    "宋代": "宋元明清", "西夏": "宋元明清", "明代": "宋元明清",
    "边疆考古": "边疆考古",
}
ERA_COLORS = {
    "新石器时代": "#10b981", "青铜时代": "#8b5cf6", "夏商周": "#f59e0b", "秦汉": "#ef4444",
    "魏晋南北朝": "#6366f1", "隋唐": "#ec4899", "宋元明清": "#14b8a6", "边疆考古": "#f97316",
}
ERA_ORDER = ["新石器时代", "青铜时代", "夏商周", "秦汉", "魏晋南北朝", "隋唐", "宋元明清", "边疆考古"]

# 实体大类归类
CAT_SUPER = {
    "器物编号": "编号系统", "遗迹编号": "编号系统", "探方编号": "编号系统", "发掘区": "编号系统",
    "陶器": "器物", "铜器": "器物", "石器": "器物", "骨器": "器物", "玉器": "器物",
    "蚌器": "器物", "纹饰": "器物",
    "测量数据": "测量数据", "方向角度": "测量数据", "土样特征": "测量数据",
    "年代": "考古信息", "地层": "考古信息", "遗存类型": "考古信息", "保存状况": "考古信息",
    "葬具葬式": "考古信息", "制作工艺": "考古信息", "发掘信息": "考古信息", "测年方法": "考古信息",
    "层位关系": "考古信息",
    "地理位置": "空间信息", "建筑结构": "空间信息", "材质": "空间信息",
}
SUPER_COLORS = {
    "编号系统": "#f59e0b", "器物": "#ec4899", "测量数据": "#6366f1",
    "考古信息": "#10b981", "空间信息": "#14b8a6", "未归类": "#8b8fa3",
}
SUPER_ORDER = ["编号系统", "器物", "测量数据", "考古信息", "空间信息", "未归类"]


def load_data():
    """加载主数据文件"""
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        reports = json.load(f)
    return reports


def classify_era(name):
    """根据报告名判断时代分组"""
    for kw, era in ERA_MAP.items():
        if kw in name:
            return ERA_GROUP.get(era, "其他")
    return "其他"


def make_slug(name):
    """生成URL友好的slug"""
    s = re.sub(r'^《', '', name)
    s = re.sub(r'[（(].*$', '', s)
    s = re.sub(r'\s+', '', s)
    s = re.sub(r'[^\w\u4e00-\u9fff]', '-', s)
    return s[:40].strip('-')


def find_md_file(report_dir):
    """在报告目录中找到主MD文件（排除chunk文件）"""
    if not report_dir.is_dir():
        return None
    for f in sorted(report_dir.iterdir()):
        if f.suffix == '.md' and '_chunk' not in f.name:
            return f
    return None


def find_entities_json(report_dir):
    """找entities.json"""
    p = report_dir / 'entities.json'
    return p if p.exists() else None


def md_to_html(md_path):
    """将Markdown转为HTML（带图片占位符处理）"""
    if not md_path or not md_path.exists():
        return None
    with open(md_path, 'r', encoding='utf-8') as f:
        text = f.read()
    # 将本地图片引用替换为占位符
    text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', r'🖼️ \1 <span class="img-placeholder">[本地图片]</span>', text)
    html = markdown.markdown(text, extensions=['tables', 'fenced_code', 'toc'])
    return html


# ====== HTML 模板工具 ======

def page_head(title, extra_css='', extra_js=''):
    """生成页面头部"""
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — {SITE_TITLE}</title>
<meta name="description" content="{SITE_DESC}">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🏺</text></svg>">
<style>
{COMMON_CSS}
{extra_css}
</style>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
</head>
<body>
'''


def nav_bar(active='index', is_report_page=False):
    """生成导航栏
    is_report_page: 是否为报告详情页（需要返回上级目录）
    """
    items = [
        ('index', '总览'),
        ('reports', '报告列表'),
        ('map', '遗址地图'),
        ('download', '数据下载'),
        ('about', '关于'),
    ]
    # 本地版本使用相对路径
    prefix = '../' if is_report_page else './'
    links = ''
    for key, label in items:
        cls = ' class="active"' if key == active else ''
        if key == 'index':
            href = f'{prefix}index.html'
        else:
            href = f'{prefix}{key}.html'
        links += f'<a href="{href}"{cls}>{label}</a>\n'
    logo_href = f'{prefix}index.html'
    return f'''<nav class="topnav">
<div class="nav-inner">
  <a href="{logo_href}" class="logo">🏺 考古知识库</a>
  <div class="nav-links">
{links}  </div>
</div>
</nav>
'''


def page_end(extra_js='', is_report_page=False):
    """页面尾部"""
    prefix = '../' if is_report_page else './'
    return f'''<footer class="site-footer">
<div class="footer-inner">
  <p>中国考古学专刊·丁种 实体标注知识库 &copy; 2026</p>
  <p class="footer-links">
    <a href="{SITE_REPO}" target="_blank">GitHub</a> ·
    <a href="{prefix}about.html">关于本站</a>
  </p>
</div>
</footer>
<script>
{extra_js}
</script>
</body>
</html>
'''


# ====== 公共CSS ======
COMMON_CSS = r''':root {
  --bg: #0f1117;
  --card: #1a1d27;
  --border: #2a2d3a;
  --text: #e4e4e7;
  --muted: #8b8fa3;
  --accent: #f59e0b;
  --accent2: #ec4899;
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  background: var(--bg);
  color: var(--text);
  font-family: 'PingFang SC', 'Microsoft YaHei', 'Noto Sans SC', system-ui, sans-serif;
  line-height: 1.7;
  min-height: 100vh;
}

/* Navigation */
.topnav {
  background: rgba(15, 17, 23, 0.85);
  backdrop-filter: blur(16px);
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 0;
  z-index: 100;
}
.nav-inner {
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 60px;
}
.logo {
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--accent);
  text-decoration: none;
}
.nav-links { display: flex; gap: 4px; }
.nav-links a {
  color: var(--muted);
  text-decoration: none;
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 0.92rem;
  transition: all 0.2s;
}
.nav-links a:hover { color: var(--text); background: rgba(255,255,255,0.04); }
.nav-links a.active { color: var(--accent); background: rgba(245,158,11,0.08); }

/* Layout */
.container { max-width: 1280px; margin: 0 auto; padding: 24px; }
.hero {
  text-align: center;
  padding: 48px 20px 32px;
}
.hero h1 {
  font-size: 2.4rem;
  font-weight: 800;
  background: linear-gradient(135deg, var(--accent), var(--accent2));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin-bottom: 8px;
}
.hero .subtitle { color: var(--muted); font-size: 1.05rem; }

/* Stats */
.stats-row {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  justify-content: center;
  margin: 28px 0 36px;
}
.stat-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px 28px;
  text-align: center;
  min-width: 150px;
  flex: 1;
  max-width: 200px;
}
.stat-card .num {
  font-size: 2rem;
  font-weight: 800;
  color: var(--accent);
}
.stat-card .label { color: var(--muted); font-size: 0.88rem; margin-top: 4px; }

/* Grid */
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
.grid-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; }

/* Cards */
.card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 22px;
}
.card h3 {
  font-size: 1.05rem;
  margin-bottom: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
}

/* Tables */
table { width: 100%; border-collapse: collapse; }
thead th {
  background: var(--card);
  padding: 10px 14px;
  text-align: left;
  font-size: 0.82rem;
  color: var(--muted);
  border-bottom: 2px solid var(--border);
  cursor: pointer;
  user-select: none;
  white-space: nowrap;
}
thead th:hover { color: var(--text); }
tbody td { padding: 10px 14px; font-size: 0.88rem; border-bottom: 1px solid var(--border); }
tbody tr { transition: background 0.15s; }
tbody tr:hover { background: rgba(245, 158, 11, 0.04); }

/* Tags */
.era-tag {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 20px;
  font-size: 0.82rem;
  font-weight: 500;
}
.ebar {
  display: inline-block;
  height: 6px;
  border-radius: 3px;
  margin-right: 8px;
  vertical-align: middle;
}

/* Report detail page */
.report-header {
  margin-bottom: 28px;
}
.report-header h1 {
  font-size: 1.8rem;
  font-weight: 700;
  margin-bottom: 8px;
}
.report-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  color: var(--muted);
  font-size: 0.92rem;
}
.report-meta span {
  background: var(--card);
  border: 1px solid var(--border);
  padding: 4px 12px;
  border-radius: 6px;
}
.report-body h2 { font-size: 1.3rem; margin: 32px 0 16px; color: var(--accent); }
.report-body h3 { font-size: 1.1rem; margin: 24px 0 12px; }
.report-body p { margin-bottom: 12px; }
.report-body ul, .report-body ol { margin: 12px 0 12px 24px; }
.report-body li { margin-bottom: 4px; }
.report-body table { margin: 16px 0; }
.report-body table th { background: var(--card); }
.report-body table td, .report-body table th {
  border: 1px solid var(--border);
  padding: 8px 12px;
}
.report-body pre {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 16px;
  overflow-x: auto;
  margin: 16px 0;
}
.report-body code {
  background: rgba(245,158,11,0.1);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.88em;
}

/* Image placeholder */
.img-placeholder {
  display: inline-block;
  background: var(--card);
  border: 1px dashed var(--border);
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.78rem;
  color: var(--muted);
  vertical-align: middle;
  margin: 0 4px;
}

/* Entity chips */
.entity-section { margin: 20px 0; }
.entity-section h4 { color: var(--muted); font-size: 0.9rem; margin-bottom: 8px; }
.echip {
  display: inline-block;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 5px;
  padding: 2px 8px;
  font-size: 0.8rem;
  margin: 2px 3px;
}

/* Report card (for list page) */
.report-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px;
  transition: all 0.2s;
  text-decoration: none;
  color: inherit;
  display: block;
}
.report-card:hover {
  border-color: var(--accent);
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(0,0,0,0.3);
}
.report-card h3 { font-size: 1.05rem; margin-bottom: 6px; }
.report-card .rc-meta { color: var(--muted); font-size: 0.84rem; }
.report-card .rc-entities { color: var(--accent); font-weight: 600; font-size: 0.92rem; margin-top: 6px; }

/* Search & filter */
.filter-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 24px;
  align-items: center;
}
.search-input {
  background: var(--card);
  border: 1px solid var(--border);
  color: var(--text);
  padding: 8px 14px;
  border-radius: 8px;
  font-size: 0.9rem;
  width: 260px;
  outline: none;
}
.search-input:focus { border-color: var(--accent); }
.filter-btn {
  background: var(--card);
  border: 1px solid var(--border);
  color: var(--text);
  padding: 7px 14px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.88rem;
  transition: all 0.2s;
}
.filter-btn:hover, .filter-btn.active {
  border-color: var(--accent);
  color: var(--accent);
  background: rgba(245,158,11,0.08);
}

/* Footer */
.site-footer {
  border-top: 1px solid var(--border);
  padding: 32px 0;
  margin-top: 60px;
  color: var(--muted);
  font-size: 0.85rem;
}
.footer-inner { text-align: center; max-width: 1280px; margin: 0 auto; padding: 0 24px; }
.footer-links { margin-top: 8px; }
.footer-links a { color: var(--accent); text-decoration: none; }
.footer-links a:hover { text-decoration: underline; }

/* About page */
.about-section { margin: 28px 0; }
.about-section h2 { font-size: 1.3rem; margin-bottom: 12px; color: var(--accent); }
.about-section p { margin-bottom: 12px; color: var(--muted); }
.about-section ul { margin: 8px 0 8px 20px; color: var(--muted); }

/* Download page */
.dl-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 16px;
}
.dl-card h3 { font-size: 1.1rem; margin-bottom: 8px; }
.dl-card p { color: var(--muted); font-size: 0.9rem; margin-bottom: 12px; }
.dl-btn {
  display: inline-block;
  background: var(--accent);
  color: #000;
  padding: 8px 20px;
  border-radius: 8px;
  text-decoration: none;
  font-weight: 600;
  font-size: 0.9rem;
  transition: all 0.2s;
}
.dl-btn:hover { opacity: 0.85; transform: translateY(-1px); }
.dl-btn.secondary {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text);
}
.dl-btn.secondary:hover { border-color: var(--accent); color: var(--accent); }

/* Map page */
.map-container {
  text-align: center;
  margin: 24px 0;
}
.map-container img {
  max-width: 100%;
  border-radius: 12px;
  border: 1px solid var(--border);
}

/* Mobile responsive */
@media (max-width: 768px) {
  .hero h1 { font-size: 1.6rem; }
  .grid-2, .grid-3 { grid-template-columns: 1fr; }
  .stats-row { gap: 10px; }
  .stat-card { min-width: 120px; padding: 14px 16px; }
  .stat-card .num { font-size: 1.5rem; }
  .nav-links a { padding: 6px 10px; font-size: 0.82rem; }
  .search-input { width: 100%; }
  .filter-bar { flex-direction: column; align-items: stretch; }
}
@media (max-width: 480px) {
  .nav-links { gap: 0; }
  .nav-links a { padding: 6px 8px; font-size: 0.78rem; }
  .container { padding: 16px; }
}
'''


# ====== 页面生成函数 ======

def build_index(reports):
    """构建首页 - 总览仪表盘"""
    total_entities = sum(r['total_entities'] for r in reports)
    total_pages = sum(r['pdf_pages'] for r in reports)
    total_pdf_mb = sum(r['pdf_mb'] for r in reports)

    # 时代统计
    era_counts = Counter(r['era_group'] for r in reports)
    era_entities = defaultdict(int)
    for r in reports:
        era_entities[r['era_group']] += r['total_entities']

    # 实体类别统计
    cat_counts = Counter()
    for r in reports:
        for cat, items in r['entities'].items():
            cat_counts[cat] += len(items)

    # 超类统计
    super_counts = Counter()
    for cat, cnt in cat_counts.items():
        sc = CAT_SUPER.get(cat, "未归类")
        super_counts[sc] += cnt

    # 报告列表数据（给JS用）
    reports_js = json.dumps(reports, ensure_ascii=False)

    era_colors_js = json.dumps(ERA_COLORS, ensure_ascii=False)
    era_order_js = json.dumps(ERA_ORDER, ensure_ascii=False)
    super_colors_js = json.dumps(SUPER_COLORS, ensure_ascii=False)
    super_order_js = json.dumps(SUPER_ORDER, ensure_ascii=False)
    super_counts_js = json.dumps(dict(super_counts), ensure_ascii=False)

    html = page_head(SITE_TITLE)
    html += nav_bar('index')
    html += f'''<div class="container">
<div class="hero">
  <h1>🏺 中国考古学专刊·丁种</h1>
  <p class="subtitle">基于70份发掘报告的实体标注与结构化知识库</p>
</div>

<div class="stats-row">
  <div class="stat-card"><div class="num">{len(reports)}</div><div class="label">考古报告</div></div>
  <div class="stat-card"><div class="num">{total_entities:,}</div><div class="label">标注实体</div></div>
  <div class="stat-card"><div class="num">{total_pages:,}</div><div class="label">总页数</div></div>
  <div class="stat-card"><div class="num">{total_pdf_mb:.0f}</div><div class="label">PDF总量(MB)</div></div>
</div>

<div class="grid-2">
  <div class="card">
    <h3>📊 时代分布</h3>
    <canvas id="eraChart" height="260"></canvas>
  </div>
  <div class="card">
    <h3>🏷️ 实体大类分布</h3>
    <canvas id="catChart" height="260"></canvas>
  </div>
</div>

<div class="card" style="margin-top:20px">
  <h3>📋 报告总览</h3>
  <div class="filter-bar">
    <input type="text" class="search-input" id="searchInput" placeholder="搜索报告名称...">
    <button class="filter-btn active" data-era="all" onclick="filterEra('all',this)">全部</button>
'''
    for eg in ERA_ORDER:
        cnt = era_counts.get(eg, 0)
        if cnt > 0:
            html += f'    <button class="filter-btn" data-era="{eg}" onclick="filterEra(\'{eg}\',this)">{eg}({cnt})</button>\n'

    html += '''  </div>
  <div style="overflow-x:auto">
    <table id="reportTable">
      <thead>
        <tr>
          <th onclick="sortTable(0)">报告名称 ▾</th>
          <th onclick="sortTable(1)">时代</th>
          <th onclick="sortTable(2)">页数</th>
          <th onclick="sortTable(3)">PDF大小</th>
          <th onclick="sortTable(4)">实体数 ▾</th>
          <th>密度</th>
        </tr>
      </thead>
      <tbody id="reportBody"></tbody>
    </table>
  </div>
</div>
</div>
'''

    html += page_end(f'''
const reports = {reports_js};
const EC = {era_colors_js};
const EO = {era_order_js};
let currentEra = 'all';
let currentSearch = '';
let sortCol = 4, sortAsc = false;

function filterEra(era, btn) {{
  currentEra = era;
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  renderTable();
}}

document.getElementById('searchInput').addEventListener('input', function(e) {{
  currentSearch = e.target.value.toLowerCase();
  renderTable();
}});

function sortTable(col) {{
  if (sortCol === col) {{ sortAsc = !sortAsc; }} else {{ sortCol = col; sortAsc = col === 4; }}
  renderTable();
}}

function renderTable() {{
  let filtered = reports.filter(r => {{
    if (currentEra !== 'all' && r.era_group !== currentEra) return false;
    if (currentSearch && !r.display_name.toLowerCase().includes(currentSearch) && !r.name.toLowerCase().includes(currentSearch)) return false;
    return true;
  }});
  filtered.sort((a, b) => {{
    let va, vb;
    switch(sortCol) {{
      case 0: va = a.display_name; vb = b.display_name; return sortAsc ? va.localeCompare(vb) : vb.localeCompare(va);
      case 1: va = EO.indexOf(a.era_group); vb = EO.indexOf(b.era_group); break;
      case 2: va = a.pdf_pages; vb = b.pdf_pages; break;
      case 3: va = a.pdf_mb; vb = b.pdf_mb; break;
      case 4: va = a.total_entities; vb = b.total_entities; break;
      case 5: va = a.density; vb = b.density; break;
      default: return 0;
    }}
    return sortAsc ? va - vb : vb - va;
  }});
  const maxE = Math.max(...reports.map(r => r.total_entities));
  const tbody = document.getElementById('reportBody');
  tbody.innerHTML = filtered.map(r => {{
    const color = EC[r.era_group] || '#666';
    const slug = './report/' + r.slug + '.html';
    return '<tr><td><a href="' + slug + '" style="color:var(--text);text-decoration:none">' + r.display_name + '</a></td>' +
      '<td><span class="era-tag" style="background:' + color + '22;color:' + color + '">' + r.era_group + '</span></td>' +
      '<td>' + r.pdf_pages + '</td>' +
      '<td>' + r.pdf_mb + 'MB</td>' +
      '<td><span class="ebar" style="width:' + Math.max(4, r.total_entities/maxE*70) + 'px;background:' + color + '"></span><b>' + r.total_entities.toLocaleString() + '</b></td>' +
      '<td>' + r.density + '</td></tr>';
  }}).join('');
}}

// Charts
new Chart(document.getElementById('eraChart'), {{
  type: 'doughnut',
  data: {{
    labels: EO.filter(e => reports.some(r => r.era_group === e)),
    datasets: [{{
      data: EO.filter(e => reports.some(r => r.era_group === e)).map(e => reports.filter(r => r.era_group === e).length),
      backgroundColor: EO.filter(e => reports.some(r => r.era_group === e)).map(e => (EC[e]||'#666')+'cc'),
      borderColor: '#1a1d27',
      borderWidth: 2,
    }}]
  }},
  options: {{
    responsive: true,
    plugins: {{
      legend: {{ position: 'right', labels: {{ color: '#e4e4e7', font: {{ size: 12 }}, padding: 12 }} }}
    }}
  }}
}});

const SO = {super_order_js};
const SC = {super_colors_js};
const SCO = {super_counts_js};
const catVals = SO.map(function(s) {{ return SCO[s] || 0; }});
new Chart(document.getElementById('catChart'), {{
  type: 'bar',
  data: {{
    labels: SO,
    datasets: [{{
      data: catVals,
      backgroundColor: SO.map(s => (SC[s]||'#666') + '88'),
      borderColor: SO.map(s => SC[s]||'#666'),
      borderWidth: 1,
      borderRadius: 4,
    }}]
  }},
  options: {{
    responsive: true,
    indexAxis: 'y',
    plugins: {{ legend: {{ display: false }} }},
    scales: {{
      x: {{ grid: {{ color: '#2a2d3a' }}, ticks: {{ color: '#8b8fa3' }} }},
      y: {{ grid: {{ display: false }}, ticks: {{ color: '#e4e4e7' }} }}
    }}
  }}
}});

renderTable();
''')

    return html


def build_reports_list(reports):
    """构建报告列表页 - 卡片式布局"""
    html = page_head('报告列表')
    html += nav_bar('reports')
    html += '''<div class="container">
<div class="hero"><h1>📄 报告列表</h1><p class="subtitle">共70份考古学专刊·丁种发掘报告</p></div>
<div class="filter-bar">
  <input type="text" class="search-input" id="searchInput" placeholder="搜索报告名称...">
  <button class="filter-btn active" data-era="all" onclick="filterEra('all',this)">全部</button>
'''
    for eg in ERA_ORDER:
        cnt = len([r for r in reports if r['era_group'] == eg])
        if cnt > 0:
            html += f'  <button class="filter-btn" data-era="{eg}" onclick="filterEra(\'{eg}\',this)">{eg}({cnt})</button>\n'

    html += '</div>\n<div class="grid-3" id="cardGrid"></div>\n</div>'

    cards_js = json.dumps([{
        'name': r['display_name'],
        'slug': r['slug'],
        'era': r['era_group'],
        'entities': r['total_entities'],
        'pages': r['pdf_pages'],
    } for r in reports], ensure_ascii=False)

    html += page_end(f'''
const reports = {cards_js};
const EC = {json.dumps(ERA_COLORS, ensure_ascii=False)};
let currentEra = 'all';

function filterEra(era, btn) {{
  currentEra = era;
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  renderCards();
}}

document.getElementById('searchInput').addEventListener('input', function(e) {{
  renderCards(e.target.value.toLowerCase());
}});

function renderCards(search) {{
  search = search || '';
  const grid = document.getElementById('cardGrid');
  const filtered = reports.filter(r => {{
    if (currentEra !== 'all' && r.era !== currentEra) return false;
    if (search && !r.name.toLowerCase().includes(search)) return false;
    return true;
  }});
  grid.innerHTML = filtered.map(r => {{
    const c = EC[r.era] || '#666';
    return '<a href="./report/' + r.slug + '.html" class="report-card">' +
      '<h3>' + r.name + '</h3>' +
      '<div class="rc-meta"><span class="era-tag" style="background:' + c + '22;color:' + c + '">' + r.era + '</span> · ' + r.pages + '页</div>' +
      '<div class="rc-entities">' + r.entities.toLocaleString() + ' 个实体</div>' +
      '</a>';
  }}).join('');
}}
renderCards();
''')

    return html


def build_report_detail(report, md_html, all_reports):
    """构建单个报告详情页"""
    slug = report['slug']
    name = report['display_name']
    color = ERA_COLORS.get(report['era_group'], '#666')

    entities = report['entities']
    total_ent = report['total_entities']
    cat_counts = {k: len(v) for k, v in entities.items() if v}

    # 实体展示
    entity_html = ''
    for cat in sorted(cat_counts.keys(), key=lambda x: cat_counts[x], reverse=True):
        items = entities[cat][:50]  # 最多显示50个
        more = len(entities[cat]) - 50
        entity_html += f'<div class="entity-section"><h4>{cat} ({cat_counts[cat]})</h4><div>'
        for item in items:
            entity_html += f'<span class="echip">{item}</span>'
        if more > 0:
            entity_html += f'<span class="echip" style="color:var(--muted)">+{more} 更多</span>'
        entity_html += '</div></div>\n'

    # 前后报告导航
    idx = next(i for i, r in enumerate(all_reports) if r['slug'] == slug)
    prev_r = all_reports[idx - 1] if idx > 0 else None
    next_r = all_reports[idx + 1] if idx < len(all_reports) - 1 else None

    nav_html = '<div style="display:flex;justify-content:space-between;margin-top:40px;padding-top:20px;border-top:1px solid var(--border)">'
    if prev_r:
        nav_html += f'<a href="./{prev_r["slug"]}.html" style="color:var(--muted);text-decoration:none">← {prev_r["display_name"]}</a>'
    else:
        nav_html += '<span></span>'
    if next_r:
        nav_html += f'<a href="./{next_r["slug"]}.html" style="color:var(--muted);text-decoration:none">{next_r["display_name"]} →</a>'
    else:
        nav_html += '<span></span>'
    nav_html += '</div>'

    html = page_head(name, extra_css='''
.toc-float {
  position: fixed;
  right: 20px;
  top: 80px;
  max-height: calc(100vh - 100px);
  overflow-y: auto;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 12px 16px;
  font-size: 0.8rem;
  max-width: 220px;
  z-index: 50;
}
.toc-float h4 { color: var(--muted); margin-bottom: 8px; }
.toc-float a { color: var(--muted); text-decoration: none; display: block; padding: 2px 0; }
.toc-float a:hover { color: var(--accent); }
@media (max-width: 1024px) { .toc-float { display: none; } }
''')
    html += nav_bar('reports', is_report_page=True)
    html += f'''<div class="container" style="display:flex;gap:24px">
<div style="flex:1;min-width:0">
<div class="report-header">
  <a href="../reports.html" style="color:var(--muted);font-size:0.88rem;text-decoration:none">← 返回报告列表</a>
  <h1 style="margin-top:8px">{name}</h1>
  <div class="report-meta">
    <span class="era-tag" style="background:{color}22;color:{color}">{report['era_group']}</span>
    <span>{report['pdf_pages']} 页</span>
    <span>{report['pdf_mb']} MB</span>
    <span>{total_ent:,} 个实体</span>
    <span>密度 {report['density']}</span>
  </div>
</div>

<div class="card" style="margin-bottom:24px">
  <h3>🏷️ 实体标注</h3>
  {entity_html}
</div>

<div class="card">
  <h3>📖 报告全文</h3>
  <div class="report-body" id="reportBody">
    {md_html or '<p style="color:var(--muted)">Markdown文件未找到</p>'}
  </div>
</div>

{nav_html}
</div>

<div class="toc-float" id="tocPanel">
  <h4>目录</h4>
  <div id="tocContent">正在生成...</div>
</div>
</div>
'''

    html += page_end('''
// Generate TOC from headings
setTimeout(function() {
  const body = document.getElementById('reportBody');
  const headings = body.querySelectorAll('h1, h2, h3');
  const toc = document.getElementById('tocContent');
  if (headings.length === 0) {
    toc.innerHTML = '<span style="color:var(--muted)">无标题</span>';
    return;
  }
  toc.innerHTML = '';
  headings.forEach((h, i) => {
    h.id = 'heading-' + i;
    const a = document.createElement('a');
    a.href = '#heading-' + i;
    a.textContent = h.textContent;
    a.style.paddingLeft = (h.tagName === 'H3' ? '12px' : '0');
    toc.appendChild(a);
  });
}, 500);
''', is_report_page=True)

    return html


def build_map_page():
    """构建遗址分布地图页"""
    html = page_head('遗址分布地图')
    html += nav_bar('map')
    html += f'''<div class="container">
<div class="hero"><h1>🗺️ 遗址分布地图</h1><p class="subtitle">70处考古遗址的地理分布（按时代分色标注）</p></div>

<div class="card">
  <div class="map-container">
    <img src="./assets/遗址分布地图.png" alt="遗址分布地图" loading="lazy">
  </div>
  <div style="margin-top:16px;display:flex;flex-wrap:wrap;gap:12px;justify-content:center">
'''
    for eg, color in ERA_COLORS.items():
        html += f'    <span class="era-tag" style="background:{color}22;color:{color}">● {eg}</span>\n'

    html += '''  </div>
  <p style="color:var(--muted);font-size:0.85rem;margin-top:12px;text-align:center">
    点大小对应实体数量。地图基于阿里云 DataV GeoAtlas GeoJSON 数据绘制。
  </p>
</div>

<div class="card" style="margin-top:20px">
  <h3>📊 地理分布统计</h3>
  <div id="regionStats" style="margin-top:12px"></div>
</div>
</div>
'''

    # 区域统计 - 从现有数据推断
    region_data = {
        '河南': {'count': 0, 'sites': []},
        '陕西': {'count': 0, 'sites': []},
        '甘肃': {'count': 0, 'sites': []},
        '山东': {'count': 0, 'sites': []},
        '湖北': {'count': 0, 'sites': []},
        '湖南': {'count': 0, 'sites': []},
        '四川': {'count': 0, 'sites': []},
        '新疆': {'count': 0, 'sites': []},
        '青海': {'count': 0, 'sites': []},
        '内蒙古': {'count': 0, 'sites': []},
        '辽宁': {'count': 0, 'sites': []},
        '北京': {'count': 0, 'sites': []},
        '广东': {'count': 0, 'sites': []},
        '浙江': {'count': 0, 'sites': []},
        '宁夏': {'count': 0, 'sites': []},
        '江西': {'count': 0, 'sites': []},
        '河北': {'count': 0, 'sites': []},
        '江苏': {'count': 0, 'sites': []},
        '山西': {'count': 0, 'sites': []},
        '西藏': {'count': 0, 'sites': []},
    }
    region_keywords = {
        '河南': ['辉县', '洛阳', '郑州', '信阳', '三门峡', '满城', '大葆台', '安阳', '殷墟', '妇好', '二里头', '瓦店', '汉魏'],
        '陕西': ['半坡', '宝鸡', '西安', '沣西', '张家坡', '汉中', '杜陵', '大明宫', '前掌大', '永宁寺', '碾子坡', '柳湾'],
        '甘肃': ['寺洼', '东下冯', '师赵村', '马家窑', '大地湾', '秦安'],
        '山东': ['三里河', '大汶口', '两城镇', '尹家城', '程村', '前掌大'],
        '湖北': ['青龙泉', '雕龙碑', '曾侯乙', '雨台山', '盘龙城', '铜绿山'],
        '湖南': ['长沙', '马王堆', '高庙'],
        '四川': ['王建墓', '三星堆', '金沙'],
        '新疆': ['北庭', '塔里木', '尼雅', '吐鲁番'],
        '青海': ['柳湾', '喇家'],
        '内蒙古': ['大甸子', '夏家店', '哈克', '赵宝沟'],
        '辽宁': ['双砣子', '岗上'],
        '北京': ['大葆台', '定陵'],
        '广东': ['广州汉墓', '南越王', '石峡'],
        '浙江': ['良渚', '河姆渡', '庙底沟'],
        '宁夏': ['灵武', '水洞沟'],
        '江西': ['万年', '吴城'],
        '河北': ['磁县', '满城', '定陵', '邺城'],
        '江苏': ['北阴阳营', '赵陵山'],
        '山西': ['南邠州', '陶寺', '曲村'],
        '西藏': ['卡若'],
    }

    html += page_end('')
    return html


def build_download_page():
    """构建数据下载页"""
    html = page_head('数据下载')
    html += nav_bar('download')
    html += f'''<div class="container">
<div class="hero"><h1>📥 数据下载</h1><p class="subtitle">获取完整的实体标注数据和原始提取文本</p></div>

<div class="dl-card">
  <h3>📦 完整数据包 (v1.0)</h3>
  <p>包含全部70份报告的结构化实体数据 (JSON)、提取的Markdown全文、实体标注HTML。不含原始PDF和图片（约4.6GB）。</p>
  <p style="font-size:0.84rem;color:var(--muted)">预计大小: ~120MB | 格式: tar.gz</p>
  <a href="{SITE_REPO}/releases/latest" class="dl-btn" target="_blank">前往 GitHub Releases 下载</a>
</div>

<div class="grid-2">
  <div class="dl-card">
    <h3>🏷️ 实体数据 (JSON)</h3>
    <p>全部70份报告的实体标注数据，按类别组织。可直接用于数据分析、知识图谱构建。</p>
    <a href="{SITE_REPO}/releases" class="dl-btn secondary" target="_blank">下载</a>
  </div>
  <div class="dl-card">
    <h3>📖 Markdown 全文</h3>
    <p>从PDF提取的纯文本Markdown，保留原始章节结构。可用于全文搜索和文本分析。</p>
    <a href="{SITE_REPO}/releases" class="dl-btn secondary" target="_blank">下载</a>
  </div>
  <div class="dl-card">
    <h3>🌐 标注HTML</h3>
    <p>带有实体高亮标注的HTML文件。在本地配合图片文件夹可完整查看标注效果。</p>
    <a href="{SITE_REPO}/releases" class="dl-btn secondary" target="_blank">下载</a>
  </div>
  <div class="dl-card">
    <h3>🛠️ 标注脚本</h3>
    <p>用于实体标注的Python脚本，支持26类实体自动识别与标注。可复用于其他考古报告。</p>
    <a href="{SITE_REPO}/tree/main/标注脚本" class="dl-btn secondary" target="_blank">查看源码</a>
  </div>
</div>

<div class="card" style="margin-top:24px">
  <h3>📋 数据说明</h3>
  <ul style="margin:12px 0 0 20px;color:var(--muted);line-height:2">
    <li><b>实体数据</b>：每份报告的 entities.json 包含26类实体（遗迹编号、器物编号、陶器、铜器、石器、骨器、玉器、蚌器、纹饰、材质、年代、地层、地理位置、建筑结构、遗存类型、保存状况、葬具葬式、制作工艺、发掘信息、测年方法、层位关系、测量数据、方向角度、土样特征、探方编号、发掘区）</li>
    <li><b>Markdown全文</b>：使用 MinerU API 从PDF提取，保留标题层级和表格结构</li>
    <li><b>图片</b>：原始PDF提取的图片（约63,170张，4.6GB）因体积限制不在下载包中，需自行从PDF提取</li>
    <li><b>原始PDF</b>：考古学专刊·丁种的原始PDF可从 Internet Archive 等渠道获取，详见本站 <a href="./about.html" style="color:var(--accent)">关于页</a></li>
  </ul>
</div>
</div>
'''

    html += page_end('')
    return html


def build_about_page():
    """构建关于页"""
    html = page_head('关于')
    html += nav_bar('about')

    html += f'''<div class="container">
<div class="hero"><h1>ℹ️ 关于本站</h1><p class="subtitle">考古报告实体标注知识库的背景与方法说明</p></div>

<div class="about-section card">
  <h2>🎯 项目背景</h2>
  <p>中国考古学专刊·丁种是中国社会科学院考古研究所编辑出版的大型考古报告丛书，自1952年出版第一种（辉县发掘报告）以来，已累计出版八十余种，涵盖了中国考古学史上几乎所有重大遗址的正式发掘报告。</p>
  <p>这些报告内容极为丰富，包含了大量的遗迹编号、器物编号、年代数据、地理位置、地层信息等结构化数据，但目前均以PDF形式存在，难以进行数据化利用。</p>
  <p>本项目旨在对这批重要考古报告进行<strong>全文提取 + 实体自动标注</strong>，构建一个结构化的知识库，便于考古学研究者快速检索和分析报告内容。</p>
</div>

<div class="about-section card">
  <h2>⚙️ 技术方法</h2>
  <p>本项目的处理流程如下：</p>
  <ol style="margin:12px 0 0 20px;color:var(--muted);line-height:2.2">
    <li><b>PDF获取</b>：从 Internet Archive 等渠道获取考古学专刊·丁种的PDF扫描版</li>
    <li><b>文本提取</b>：使用 MinerU API 将PDF转换为Markdown格式文本（保留标题层级、表格结构）</li>
    <li><b>实体标注</b>：使用自研Python脚本进行26类考古实体的自动识别与标注</li>
    <li><b>数据结构化</b>：将标注结果组织为JSON格式，按报告和实体类别索引</li>
    <li><b>可视化展示</b>：生成交互式HTML知识库网站，支持搜索、筛选、统计</li>
  </ol>
</div>

<div class="about-section card">
  <h2>📊 数据规模</h2>
  <div class="stats-row" style="justify-content:flex-start">
    <div class="stat-card"><div class="num">70</div><div class="label">报告数量</div></div>
    <div class="stat-card"><div class="num">44,526</div><div class="label">标注实体</div></div>
    <div class="stat-card"><div class="num">26</div><div class="label">实体类别</div></div>
    <div class="stat-card"><div class="num">~127,000</div><div class="label">总页数</div></div>
  </div>
</div>

<div class="about-section card">
  <h2>📚 原始PDF获取</h2>
  <p>考古学专刊·丁种的原始PDF可通过以下渠道获取：</p>
  <ul style="margin:12px 0 0 20px;color:var(--muted);line-height:2">
    <li><b>Internet Archive</b>：archive.org/details/archaeology-dingzhong （约95册，需代理访问）</li>
    <li><b>全国图书馆参考咨询联盟</b>：ucdrs.superlib.net （可免费文献传递）</li>
    <li><b>各大学术数据库</b>：知网、万方等平台的博硕论文中有部分引用和转载</li>
  </ul>
</div>

<div class="about-section card">
  <h2>🔗 相关资源</h2>
  <ul style="margin:12px 0 0 20px;color:var(--muted);line-height:2">
    <li><a href="{SITE_REPO}" target="_blank" style="color:var(--accent)">GitHub 仓库</a>：源代码与数据</li>
    <li><a href="./download.html" style="color:var(--accent)">数据下载</a>：获取结构化数据</li>
  </ul>
</div>

<div class="about-section card">
  <h2>📜 使用说明</h2>
  <p>本站为静态网站，所有数据已嵌入页面中，无需后端服务。</p>
  <ul style="margin:12px 0 0 20px;color:var(--muted);line-height:2">
    <li>在<b>总览页</b>可查看所有报告的统计图表和筛选表格</li>
    <li>在<b>报告列表</b>页可按时代分类浏览报告卡片</li>
    <li>点击任意报告进入<b>详情页</b>，可查看实体标注和报告全文</li>
    <li>报告全文中的图片标注为「本地图片」，需下载完整数据包后在本地查看</li>
    <li>在<b>数据下载</b>页可获取JSON实体数据、Markdown全文等结构化数据</li>
  </ul>
</div>

<div class="about-section card">
  <h2>⚠️ 免责声明</h2>
  <p style="color:var(--muted)">本知识库中的所有报告内容版权归原出版单位（中国社会科学院考古研究所等）所有。实体标注结果由AI自动生成，可能存在错误，仅供参考。如需引用原始报告，请查阅正式出版物。</p>
</div>
</div>
'''

    html += page_end('')
    return html


# ====== 主构建流程 ======

def prepare_reports(reports):
    """预处理报告数据，添加slug和density"""
    for r in reports:
        r['slug'] = make_slug(r['name'])
        r['density'] = f"{r['total_entities'] / max(1, r['pdf_pages']):.1f}" if r['pdf_pages'] > 0 else "N/A"
        # 确保 era_group 存在
        if 'era_group' not in r:
            r['era_group'] = classify_era(r['name'])
        if 'era' not in r:
            r['era'] = r['era_group']
    # 去重：蒙城尉迟寺有两个条目，合并
    seen = {}
    unique = []
    for r in reports:
        slug = r['slug']
        if slug in seen:
            # 合并实体
            old = seen[slug]
            for cat, items in r['entities'].items():
                old['entities'].setdefault(cat, [])
                old['entities'][cat] = list(set(old['entities'][cat] + items))
            old['total_entities'] = sum(len(v) for v in old['entities'].values())
            old['entity_categories'] = len([v for v in old['entities'].values() if v])
            old['pdf_mb'] = max(old['pdf_mb'], r['pdf_mb'])
            old['pdf_pages'] = max(old['pdf_pages'], r['pdf_pages'])
        else:
            seen[slug] = r
            unique.append(r)
    # 重新计算density
    for r in unique:
        r['density'] = f"{r['total_entities'] / max(1, r['pdf_pages']):.1f}" if r['pdf_pages'] > 0 else "N/A"
    return unique


def main():
    print('=' * 50)
    print('考古报告知识库网站构建')
    print('=' * 50)

    # 清理输出目录
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir()

    # 加载数据
    print('\n[1/6] 加载数据...')
    reports = load_data()
    print(f'  原始数据: {len(reports)} 份报告')

    # 预处理
    print('[2/6] 预处理报告数据...')
    reports = prepare_reports(reports)
    # 按实体数排序
    reports.sort(key=lambda x: x['total_entities'], reverse=True)
    print(f'  去重后: {len(reports)} 份报告')

    # 检查slug唯一性
    slugs = [r['slug'] for r in reports]
    dupes = [s for s in slugs if slugs.count(s) > 1]
    if dupes:
        print(f'  ⚠️ 重复slug: {set(dupes)}')

    # 复制静态资源
    print('[3/6] 复制静态资源...')
    assets_dir = OUTPUT_DIR / 'assets'
    assets_dir.mkdir()
    if MAP_IMAGE.exists():
        shutil.copy2(MAP_IMAGE, assets_dir / '遗址分布地图.png')
        print(f'  ✓ 遗址分布地图.png ({MAP_IMAGE.stat().st_size / 1024:.0f}KB)')

    # 生成各页面
    print('[4/6] 生成首页...')
    with open(OUTPUT_DIR / 'index.html', 'w', encoding='utf-8') as f:
        f.write(build_index(reports))
    print('  ✓ index.html')

    print('[5/6] 生成报告列表页...')
    with open(OUTPUT_DIR / 'reports.html', 'w', encoding='utf-8') as f:
        f.write(build_reports_list(reports))
    print('  ✓ reports.html')

    print('[6/6] 生成报告详情页...')
    report_dir = OUTPUT_DIR / 'report'
    report_dir.mkdir()

    for i, report in enumerate(reports):
        slug = report['slug']
        # 查找对应的提取结果目录
        result_dir = None
        for d in RESULTS_DIR.iterdir():
            if d.is_dir() and slug[:6] in d.name:
                result_dir = d
                break
        # 也尝试用display_name匹配
        if result_dir is None:
            for d in RESULTS_DIR.iterdir():
                if d.is_dir() and report['display_name'][:4] in d.name:
                    result_dir = d
                    break

        md_file = find_md_file(result_dir) if result_dir else None
        md_html = md_to_html(md_file) if md_file else None

        out_path = report_dir / f'{slug}.html'
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(build_report_detail(report, md_html, reports))

        if (i + 1) % 10 == 0 or i == len(reports) - 1:
            print(f'  已生成 {i + 1}/{len(reports)} 份报告页')

    # 生成其他页面
    print('  生成地图页...')
    with open(OUTPUT_DIR / 'map.html', 'w', encoding='utf-8') as f:
        f.write(build_map_page())

    print('  生成下载页...')
    with open(OUTPUT_DIR / 'download.html', 'w', encoding='utf-8') as f:
        f.write(build_download_page())

    print('  生成关于页...')
    with open(OUTPUT_DIR / 'about.html', 'w', encoding='utf-8') as f:
        f.write(build_about_page())

    # 生成 404
    with open(OUTPUT_DIR / '404.html', 'w', encoding='utf-8') as f:
        f.write(page_head('页面未找到') + nav_bar('') +
                '<div class="container"><div class="hero"><h1>404</h1><p class="subtitle">页面未找到</p></div></div>' +
                page_end(''))

    # 统计
    total_size = sum(f.stat().st_size for f in OUTPUT_DIR.rglob('*') if f.is_file())
    html_count = len(list(OUTPUT_DIR.rglob('*.html')))

    print('\n' + '=' * 50)
    print('构建完成!')
    print(f'  输出目录: {OUTPUT_DIR}')
    print(f'  HTML文件: {html_count}')
    print(f'  总大小: {total_size / 1024 / 1024:.1f} MB')
    print(f'  首页: {OUTPUT_DIR / "index.html"}')
    print('=' * 50)
    print('\n预览: open _site/index.html')
    print(f'部署: 将 _site/ 内容推送到 GitHub Pages (base: {SITE_BASE})')


if __name__ == '__main__':
    main()
