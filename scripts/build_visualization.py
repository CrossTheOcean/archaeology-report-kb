#!/usr/bin/env python3
"""从提取结果目录读取entities.json，生成完整的可视化HTML"""
import json, os, fitz, math, base64, subprocess
from collections import Counter

BASE = '/Users/crosstheocean/WorkBuddy/20260330184406'
RESULTS_DIR = f'{BASE}/提取结果'
PDF_DIR = f'{BASE}/考古报告PDF'

# ====== 时代分类 ======
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

def classify(name):
    for kw, era in ERA_MAP.items():
        if kw in name:
            return ERA_GROUP.get(era, "其他")
    return "其他"

def clean_name(name):
    n = name
    for s in ["（", "(", "  FB.", "  ON ORDER", "  -"]:
        idx = n.find(s)
        if idx > 0: n = n[:idx]
    if n.startswith("《"): n = n[1:]
    return n.strip()[:30]

# ====== 收集数据 ======
print("收集数据...")
all_pdfs = sorted([f for f in os.listdir(PDF_DIR) if f.endswith('.pdf')]) if os.path.exists(PDF_DIR) else []

reports = []
for r in sorted(os.listdir(RESULTS_DIR)):
    epath = f'{RESULTS_DIR}/{r}/entities.json'
    if not os.path.exists(epath): continue
    with open(epath) as f:
        entities = json.load(f)
    pdf_mb, pdf_pages = 0, 0
    for pdf in all_pdfs:
        if r in pdf or pdf.replace('.pdf','') in r:
            pdf_mb = os.path.getsize(f'{PDF_DIR}/{pdf}') / (1024*1024)
            try:
                doc = fitz.open(f'{PDF_DIR}/{pdf}')
                pdf_pages = len(doc); doc.close()
            except: pass
            break
    md_size = sum(os.path.getsize(f'{RESULTS_DIR}/{r}/{f2}') for f2 in os.listdir(f'{RESULTS_DIR}/{r}') if f2.endswith('.md') and not f2.startswith('_'))
    total = sum(len(v) for v in entities.values())
    era = classify(r)
    reports.append({
        "name": r, "display_name": clean_name(r),
        "pdf_mb": round(pdf_mb,1), "pdf_pages": pdf_pages,
        "md_size_kb": round(md_size/1024,1),
        "total_entities": total, "entities": entities,
        "era_group": era,
    })

print(f"共 {len(reports)} 份报告, {sum(r['total_entities'] for r in reports)} 个实体")

# ====== 清洗数据 ======
print("清洗数据...")
def sanitize(s):
    if not isinstance(s, str): return s
    s = s.replace('\r', ' ').replace('\n', ' ')
    s = ''.join(c if c >= ' ' or c == '\t' else ' ' for c in s)
    if len(s) > 500: s = s[:497] + '...'
    return s

def sanitize_entities(entities):
    cleaned = {}
    for cat, items in entities.items():
        cleaned[cat] = [sanitize(str(item)) for item in items]
    return cleaned

for r in reports:
    r['entities'] = sanitize_entities(r['entities'])
    r['total_entities'] = sum(len(v) for v in r['entities'].values())

# ====== 统计 ======
total_reports = len(reports)
total_entities = sum(r['total_entities'] for r in reports)
total_pages = sum(r['pdf_pages'] for r in reports)
all_cats = set()
for r in reports: all_cats.update(r['entities'].keys())
total_cats = len(all_cats)
total_pdf_gb = sum(r['pdf_mb'] for r in reports) / 1024

# 实体类别汇总
cat_totals = Counter()
for r in reports:
    for k, v in r['entities'].items():
        cat_totals[k] += len(v)

# 大类汇总
super_totals = Counter()
for cat, cnt in cat_totals.items():
    sg = CAT_SUPER.get(cat, "未归类")
    super_totals[sg] += cnt

# ====== 生成HTML ======
print("生成HTML...")

# 内嵌 Chart.js
chartjs_path = '/tmp/chart.umd.min.js'
if not os.path.exists(chartjs_path):
    import urllib.request
    urllib.request.urlretrieve('https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js', chartjs_path)
with open(chartjs_path, 'r') as f:
    chartjs_code = f.read()
print(f"Chart.js: {len(chartjs_code)//1024}KB")

# 遗址坐标
SITE_COORDS = {
    "《蒙城尉迟寺": ("蒙城尉迟寺", 33.17, 116.55, "安徽"),
    "丁種第一_辉县发掘报告": ("辉县", 35.49, 113.78, "河南"),
    "辉县发掘报告": ("辉县", 35.49, 113.78, "河南"),
    "三门峡漕运遗迹": ("三门峡", 34.77, 111.20, "河南"),
    "上村岭虢国墓地": ("三门峡上村岭", 34.77, 111.21, "河南"),
    "临猗程村墓地": ("临猗程村", 35.15, 110.77, "山西"),
    "京山屈家岭": ("京山屈家岭", 30.99, 113.00, "湖北"),
    "偃师二里头": ("偃师二里头", 34.69, 112.87, "河南"),
    "元君庙仰韶墓地": ("华县元君庙", 34.52, 109.77, "陕西"),
    "前蜀王建墓": ("成都王建墓", 30.67, 104.07, "四川"),
    "北京大葆台汉墓": ("北京大葆台", 39.82, 116.33, "北京"),
    "北庭高昌回鹘佛寺遗址": ("吉木萨尔北庭", 44.01, 89.18, "新疆"),
    "北魏洛阳永宁寺": ("洛阳永宁寺", 34.75, 112.47, "河南"),
    "南宋官窑": ("杭州南宋官窑", 30.22, 120.14, "浙江"),
    "南邠州·碾子坡": ("长武碾子坡", 35.21, 107.80, "陕西"),
    "双砣子与岗上": ("大连双砣子", 38.92, 121.60, "辽宁"),
    "吐鲁番考古记": ("吐鲁番", 42.95, 89.18, "新疆"),
    "哈克遗址": ("呼伦贝尔哈克", 49.22, 119.82, "内蒙古"),
    "唐长安城郊隋唐墓": ("西安", 34.26, 108.94, "陕西"),
    "唐长安大明宫": ("西安大明宫", 34.28, 108.95, "陕西"),
    "塔里木盆地考古记": ("塔里木盆地", 39.00, 82.00, "新疆"),
    "夏县东下冯": ("夏县东下冯", 35.19, 111.22, "山西"),
    "大甸子—夏家店下层文化遗址与墓地": ("敖汉大甸子", 42.29, 119.73, "内蒙古"),
    "宁夏灵武窑发掘报告": ("灵武", 38.10, 106.30, "宁夏"),
    "安阳殷墟小屯建筑遗存": ("安阳殷墟", 36.12, 114.35, "河南"),
    "安阳殷墟花园庄东地商代墓葬": ("安阳殷墟", 36.12, 114.35, "河南"),
    "安阳殷墟郭家庄商代墓葬": ("安阳殷墟", 36.12, 114.35, "河南"),
    "定陵": ("昌平定陵", 40.26, 116.23, "北京"),
    "宝鸡北首岭": ("宝鸡北首岭", 34.36, 107.15, "陕西"),
    "山东王因": ("兖州王因", 35.55, 116.83, "山东"),
    "巩县铁生沟": ("巩义铁生沟", 34.77, 112.96, "河南"),
    "师赵村与西山坪": ("天水师赵村", 34.38, 105.72, "甘肃"),
    "广州汉墓": ("广州", 23.13, 113.26, "广东"),
    "庙底沟与三里桥": ("三门峡庙底沟", 34.77, 111.20, "河南"),
    "张家坡西周墓地": ("西安张家坡", 34.28, 108.87, "陕西"),
    "徐家碾寺洼文化墓地": ("庄浪徐家碾", 35.24, 106.04, "甘肃"),
    "敖汉赵宝沟": ("敖汉赵宝沟", 42.29, 119.72, "内蒙古"),
    "新疆考古发掘报告": ("新疆", 43.00, 85.00, "新疆"),
    "昌都卡若": ("昌都卡若", 31.18, 97.17, "西藏"),
    "曾侯乙墓": ("随州曾侯乙墓", 31.72, 113.43, "湖北"),
    "枣阳雕龙碑": ("枣阳雕龙碑", 32.13, 112.77, "湖北"),
    "武功发掘报告": ("武功浒西庄", 34.26, 108.20, "陕西"),
    "殷墟妇好墓": ("安阳殷墟", 36.12, 114.35, "河南"),
    "殷虚妇好墓": ("安阳殷墟", 36.12, 114.35, "河南"),
    "汉杜陵陵园遗址": ("西安杜陵", 34.18, 108.97, "陕西"),
    "汉长安城未央宫": ("西安未央宫", 34.30, 108.88, "陕西"),
    "汉长安城武库": ("西安", 34.30, 108.88, "陕西"),
    "江陵雨台山楚墓": ("荆州雨台山", 30.35, 112.24, "湖北"),
    "沣西发掘报告": ("西安沣西", 34.20, 108.83, "陕西"),
    "河南信阳楚墓出土文物图录": ("信阳", 32.15, 114.09, "河南"),
    "洛阳中州路": ("洛阳", 34.68, 112.45, "河南"),
    "洛阳发掘报告": ("洛阳", 34.68, 112.45, "河南"),
    "滕州前掌大墓地": ("滕州前掌大", 34.95, 117.15, "山东"),
    "满城汉墓": ("满城汉墓", 38.96, 115.38, "河北"),
    "澧西发掘报告": ("西安澧西", 34.20, 108.83, "陕西"),
    "磁县湾张北朝壁画墓": ("磁县湾张", 36.36, 114.37, "河北"),
    "胶东半岛贝丘遗址": ("烟台", 37.46, 121.45, "山东"),
    "胶县三里河": ("胶州三里河", 36.27, 120.00, "山东"),
    "蒙城尉迟寺": ("蒙城尉迟寺", 33.17, 116.55, "安徽"),
    "西安半坡": ("西安半坡", 34.26, 109.11, "陕西"),
    "西安郊区隋唐墓": ("西安", 34.26, 108.94, "陕西"),
    "西汉南越王墓": ("广州南越王墓", 23.13, 113.26, "广东"),
    "西汉礼制建筑遗址": ("西安", 34.30, 108.88, "陕西"),
    "郑州二里岗": ("郑州二里岗", 34.75, 113.70, "河南"),
    "鄂城六朝墓": ("鄂州", 30.39, 114.89, "湖北"),
    "长沙发掘报告": ("长沙", 28.23, 112.94, "湖南"),
    "长沙马王堆一号汉墓发掘报告": ("长沙马王堆", 28.21, 113.03, "湖南"),
    "陕县东周汉墓": ("三门峡陕县", 34.72, 111.20, "河南"),
    "青海柳湾": ("乐都柳湾", 36.48, 102.40, "青海"),
    "青龙泉与大寺": ("郧县青龙泉", 32.83, 110.81, "湖北"),
}

# 给每份报告匹配坐标
for r in reports:
    coord = None
    for kw, val in SITE_COORDS.items():
        if kw in r['name']:
            coord = val
            break
    if coord:
        r['site_name'] = coord[0]
        r['lat'] = coord[1]
        r['lng'] = coord[2]
        r['province'] = coord[3]
    else:
        r['site_name'] = r['display_name']
        r['lat'] = 35.0
        r['lng'] = 110.0
        r['province'] = ''

matched = sum(1 for r in reports if r.get('province'))
print(f"遗址坐标匹配: {matched}/{len(reports)}")

# 数据JSON用Base64编码
data_json = json.dumps(reports, ensure_ascii=False)
data_b64 = base64.b64encode(data_json.encode('utf-8')).decode('ascii')
data_b64_parts = "' +\n  '".join(data_b64[i:i+76] for i in range(0, len(data_b64), 76))

html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>中国考古学专刊·丁种 — 实体标注知识库</title>
<script>__CHARTJS_CODE__</script>
<style>
:root{--bg:#0f1117;--card:#1a1d27;--border:#2a2d3a;--text:#e4e4e7;--muted:#8b8fa3;--accent:#f59e0b}
*{margin:0;padding:0;box-sizing:border-box}
body{background:var(--bg);color:var(--text);font-family:'PingFang SC','Microsoft YaHei','Noto Sans SC',sans-serif;line-height:1.6}
.container{max-width:1400px;margin:0 auto;padding:20px}
.hero{text-align:center;padding:50px 20px 35px;border-bottom:1px solid var(--border);margin-bottom:35px}
.hero h1{font-size:2.6rem;font-weight:800;background:linear-gradient(135deg,var(--accent),#ec4899);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:8px}
.hero .sub{font-size:1.05rem;color:var(--muted);max-width:720px;margin:0 auto 28px}
.stats{display:flex;justify-content:center;gap:24px;flex-wrap:wrap}
.stat{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:18px 28px;text-align:center;min-width:140px}
.stat .n{font-size:2rem;font-weight:800;color:var(--accent)}
.stat .l{font-size:.82rem;color:var(--muted);margin-top:3px}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:22px;margin-bottom:35px}
@media(max-width:900px){.grid2,.grid3{grid-template-columns:1fr}}
.card{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:22px}
.card h3{font-size:1.05rem;margin-bottom:14px}
.chart-box{position:relative;height:300px}
.filter-bar{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:18px;align-items:center}
.fbtn{background:var(--card);border:1px solid var(--border);color:var(--text);padding:7px 14px;border-radius:8px;cursor:pointer;font-size:.88rem;transition:all .2s}
.fbtn:hover,.fbtn.on{border-color:var(--accent);color:var(--accent);background:rgba(245,158,11,.08)}
.sinput{background:var(--card);border:1px solid var(--border);color:var(--text);padding:7px 14px;border-radius:8px;font-size:.88rem;width:220px;outline:none}
.sinput:focus{border-color:var(--accent)}
table{width:100%;border-collapse:collapse}
thead th{background:var(--card);padding:10px 14px;text-align:left;font-size:.82rem;color:var(--muted);border-bottom:2px solid var(--border);cursor:pointer;user-select:none;white-space:nowrap}
thead th:hover{color:var(--accent)}
tbody tr{border-bottom:1px solid var(--border);transition:background .15s}
tbody tr:hover{background:rgba(245,158,11,.04)}
tbody td{padding:10px 14px;font-size:.88rem}
.era-tag{display:inline-block;padding:2px 9px;border-radius:6px;font-size:.78rem;font-weight:600;white-space:nowrap}
.ebar{display:inline-block;height:5px;border-radius:3px;margin-right:6px;vertical-align:middle}
.dtoggle{color:var(--accent);cursor:pointer;font-size:.82rem}
.drow{display:none}
.drow.open{display:table-row}
.dcontent{background:rgba(245,158,11,.03);padding:14px;font-size:.82rem}
.ecat{color:var(--accent);font-weight:600;font-size:.85rem}
.ecat-list{display:flex;flex-wrap:wrap;gap:6px;margin-top:4px;margin-bottom:8px}
.echip{background:var(--bg);border:1px solid var(--border);border-radius:5px;padding:2px 7px;font-size:.78rem}
section{margin-bottom:35px}
section h2{font-size:1.4rem;margin-bottom:18px}
.tl{position:relative;padding-left:36px}
.tl::before{content:'';position:absolute;left:13px;top:0;bottom:0;width:2px;background:var(--border)}
.tli{position:relative;margin-bottom:20px}
.tli::before{content:'';position:absolute;left:-27px;top:5px;width:10px;height:10px;border-radius:50%;background:var(--accent);border:2px solid var(--bg)}
.tl-era{font-size:.95rem;font-weight:700;color:var(--accent)}
.tl-list{color:var(--muted);font-size:.82rem;margin-top:3px;display:flex;flex-wrap:wrap;gap:6px}
footer{text-align:center;padding:35px 20px;border-top:1px solid var(--border);color:var(--muted);font-size:.82rem}
footer a{color:var(--accent);text-decoration:none}
.insight-box{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:18px 22px;margin-bottom:22px}
.insight-box h4{color:var(--accent);font-size:.95rem;margin-bottom:8px}
.insight-box p{font-size:.88rem;color:var(--muted);line-height:1.7}
.insight-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}
@media(max-width:900px){.insight-grid{grid-template-columns:1fr}}
.insight-item{text-align:center;padding:12px}
.insight-item .iv{font-size:1.3rem;font-weight:700;color:var(--text)}
.insight-item .il{font-size:.78rem;color:var(--muted);margin-top:2px}
.map-legend{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:12px}
.map-legend span{display:flex;align-items:center;gap:5px;font-size:.82rem;color:var(--muted)}
.map-legend i{width:12px;height:12px;border-radius:50%;display:inline-block}
</style>
</head>
<body>
<div class="container">

<div class="hero">
  <h1>中国考古学专刊·丁种</h1>
  <div class="sub">基于 MinerU OCR + LLM 实体标注的考古发掘报告知识库，覆盖 __TR__ 种重要报告，自动提取 __TE__ 个结构化实体</div>
  <div class="stats">
    <div class="stat"><div class="n">__TR__</div><div class="l">发掘报告</div></div>
    <div class="stat"><div class="n">__TE__</div><div class="l">结构化实体</div></div>
    <div class="stat"><div class="n">__TC__</div><div class="l">实体类别</div></div>
    <div class="stat"><div class="n">__TP__</div><div class="l">总页数</div></div>
    <div class="stat"><div class="n">__TG__ GB</div><div class="l">PDF总量</div></div>
  </div>
</div>

<div class="grid2">
  <div class="card"><h3>📊 时代分布（报告数量）</h3><div class="chart-box"><canvas id="chart1"></canvas></div></div>
  <div class="card"><h3>📈 时代分布（实体数量）</h3><div class="chart-box"><canvas id="chart2"></canvas></div></div>
</div>

<div class="card" style="max-width:600px;margin:0 auto 35px"><h3>🔍 实体大类分布</h3><div class="chart-box"><canvas id="chart_sup"></canvas></div></div>

<div class="insight-box">
  <h4>💡 数据洞察</h4>
  <div class="insight-grid">
    <div class="insight-item"><div class="iv">编号系统</div><div class="il">占总实体 __PCT_ID__%，含器物/遗迹/探方编号</div></div>
    <div class="insight-item"><div class="iv">器物类型</div><div class="il">陶器最多(__POT__)，次为铜器(__BRZ__)和石器(__STN__)</div></div>
    <div class="insight-item"><div class="iv">时代覆盖</div><div class="il">从旧石器到明清，新石器占比 __PCT_NEO__%</div></div>
  </div>
</div>

<section>
  <h2>🗺️ 遗址分布地图</h2>
  <div style="text-align:center;margin-bottom:35px">
    <img src="data:image/png;base64,__MAP_IMG_B64__" alt="遗址分布地图" style="max-width:100%;border-radius:10px;border:1px solid var(--border)">
  </div>
</section>

<section>
  <h2>📜 考古时代时间线</h2>
  <div class="tl" id="timeline"></div>
</section>

<section>
  <h2>📋 报告详细列表</h2>
  <div class="filter-bar" id="fbar"></div>
  <div style="overflow-x:auto"><table>
    <thead><tr>
      <th data-k="display_name">报告名称 ↕</th>
      <th data-k="era_group">时代 ↕</th>
      <th data-k="pdf_pages">页数 ↕</th>
      <th data-k="pdf_mb">PDF ↕</th>
      <th data-k="total_entities">实体数 ↕</th>
      <th data-k="density">密度 ↕</th>
      <th>操作</th>
    </tr></thead>
    <tbody id="tbody"></tbody>
  </table></div>
</section>

<footer>
  <p>中国考古学专刊·丁种 实体标注知识库 | 数据来源: Internet Archive (archaeology-dingzhong)</p>
  <p>OCR: <a href="https://mineru.net" target="_blank">MinerU</a> | 标注: 自定义26类实体 | 2026年4月</p>
</footer>

</div>
<script>
var D = JSON.parse(decodeURIComponent(escape(atob('__DATA_B64__'))));
var EC = __ERA_COLORS__;
var EO = __ERA_ORDER__;

// 实体大类定义
var CS = __CAT_SUPER__;
var SCO = __SUPER_ORDER__;
var SCC = __SUPER_COLORS__;

// ===== Chart 1: 时代分布（报告数）=====
(function(){
  var labels=[],vals=[],colors=[];
  EO.forEach(function(e){
    var cnt = D.filter(function(r){return r.era_group===e}).length;
    if(cnt>0){labels.push(e);vals.push(cnt);colors.push(EC[e]||'#666');}
  });
  new Chart(document.getElementById('chart1'),{
    type:'doughnut',
    data:{labels:labels,datasets:[{data:vals,backgroundColor:colors,borderColor:'#1a1d27',borderWidth:2,hoverOffset:8}]},
    options:{
      responsive:true,maintainAspectRatio:false,
      cutout:'55%',
      plugins:{
        legend:{position:'bottom',labels:{color:'#8b8fa3',font:{size:10},padding:8,usePointStyle:true,pointStyleWidth:8}},
        tooltip:{callbacks:{label:function(ctx){var t=ctx.dataset.data.reduce(function(a,b){return a+b},0);return ctx.label+': '+ctx.raw+'份 ('+Math.round(ctx.raw/t*100)+'%)';}}}
      }
    }
  });
})();

// ===== Chart 2: 时代分布（实体数）=====
(function(){
  var labels=[],vals=[],colors=[];
  EO.forEach(function(e){
    var cnt=0;D.forEach(function(r){if(r.era_group===e)cnt+=r.total_entities});
    if(cnt>0){labels.push(e);vals.push(cnt);colors.push(EC[e]||'#666');}
  });
  new Chart(document.getElementById('chart2'),{
    type:'bar',
    data:{labels:labels,datasets:[{label:'实体数',data:vals,backgroundColor:colors.map(function(c){return c+'cc'}),borderColor:colors,borderWidth:1,borderRadius:4}]},
    options:{
      responsive:true,maintainAspectRatio:false,indexAxis:'y',
      plugins:{legend:{display:false},tooltip:{callbacks:{label:function(ctx){return ctx.raw.toLocaleString()+' 个实体';}}}},
      scales:{x:{ticks:{color:'#8b8fa3',callback:function(v){return v>=1000?(v/1000)+'k':v;}},grid:{color:'#2a2d3a'}},y:{ticks:{color:'#8b8fa3',font:{size:11}},grid:{display:false}}}
    }
  });
})();

// ===== Chart Super: 实体大类汇总环形图 =====
(function(){
  var cm={};
  D.forEach(function(r){
    Object.keys(r.entities).forEach(function(k){
      var sg=CS[k]||'未归类';
      cm[sg]=(cm[sg]||0)+r.entities[k].length;
    });
  });
  var labels=[],vals=[],colors=[];
  SCO.forEach(function(s){
    if(cm[s]){labels.push(s);vals.push(cm[s]);colors.push(SCC[s]||'#666');}
  });
  new Chart(document.getElementById('chart_sup'),{
    type:'polarArea',
    data:{labels:labels,datasets:[{data:vals,backgroundColor:colors.map(function(c){return c+'88'}),borderColor:colors,borderWidth:2}]},
    options:{
      responsive:true,maintainAspectRatio:false,
      plugins:{
        legend:{position:'bottom',labels:{color:'#8b8fa3',font:{size:10},padding:6,usePointStyle:true}},
        tooltip:{callbacks:{label:function(ctx){var t=ctx.dataset.data.reduce(function(a,b){return a+b},0);return ctx.label+': '+ctx.raw.toLocaleString()+' ('+Math.round(ctx.raw/t*100)+'%)';}}}
      },
      scales:{r:{ticks:{display:false},grid:{color:'#2a2d3a'},beginAtZero:true}}
    }
  });
})();

// ===== Timeline =====
(function(){
  var tl=document.getElementById('timeline');
  EO.forEach(function(e){
    var rs=D.filter(function(r){return r.era_group===e});
    if(!rs.length)return;
    var div=document.createElement('div');
    div.className='tli';
    var ent=rs.reduce(function(s,r){return s+r.total_entities},0);
    div.innerHTML='<div class="tl-era" style="color:'+(EC[e]||'#666')+'">'+e+' ('+rs.length+'份报告, '+ent.toLocaleString()+'实体)</div><div class="tl-list">'+rs.map(function(r){
      return '<span class="era-tag" style="background:'+(EC[e]||'#666')+'22;color:'+(EC[e]||'#666')+'">'+r.display_name+' ('+r.total_entities+')</span>';
    }).join('')+'</div>';
    tl.appendChild(div);
  });
})();

// ===== Table =====
var curFilter='全部',search='',sortK='total_entities',sortD=-1;

// 计算密度
D.forEach(function(r){r.density=r.pdf_pages>0?Math.round(r.total_entities/r.pdf_pages*10)/10:0;});

(function buildFilter(){
  var bar=document.getElementById('fbar');
  bar.innerHTML='<input class="sinput" placeholder="搜索..." id="si">'+
    '<button class="fbtn on" data-f="全部">全部 ('+D.length+')</button>'+
    EO.map(function(e){return '<button class="fbtn" data-f="'+e+'">'+e+' ('+D.filter(function(r){return r.era_group===e}).length+')</button>'}).join('');
  bar.querySelectorAll('.fbtn').forEach(function(b){
    b.onclick=function(){bar.querySelectorAll('.fbtn').forEach(function(x){x.classList.remove('on')});b.classList.add('on');curFilter=b.dataset.f;render();};
  });
  document.getElementById('si').oninput=function(e){search=e.target.value.toLowerCase();render();};
  document.querySelectorAll('thead th[data-k]').forEach(function(th){
    th.onclick=function(){var k=th.dataset.k;if(sortK===k)sortD*=-1;else{sortK=k;sortD=-1;}render();};
  });
})();

function render(){
  var list=D.slice();
  if(curFilter!=='全部')list=list.filter(function(r){return r.era_group===curFilter});
  if(search)list=list.filter(function(r){return r.display_name.toLowerCase().indexOf(search)>=0||r.name.toLowerCase().indexOf(search)>=0});
  list.sort(function(a,b){var va=a[sortK],vb=b[sortK];if(typeof va==='string')return va.localeCompare(vb)*sortD;return(va-vb)*sortD});
  var maxE=Math.max.apply(null,D.map(function(r){return r.total_entities}));
  var maxD=Math.max.apply(null,D.map(function(r){return r.density}));
  var tb=document.getElementById('tbody');
  tb.innerHTML=list.map(function(r){
    var idx=D.indexOf(r);
    var catHtml=Object.keys(r.entities).filter(function(k){return r.entities[k].length>0}).sort(function(a,b){return r.entities[b].length-r.entities[a].length}).map(function(k){
      var v=r.entities[k];
      var sg=CS[k]||'其他';
      return '<div style="margin:5px 0"><span class="ecat">'+k+' ('+v.length+')</span><div class="ecat-list">'+v.slice(0,25).map(function(e){return '<span class="echip">'+e+'</span>'}).join('')+(v.length>25?'<span class="echip" style="color:var(--muted)">...+' + (v.length-25) + '</span>':'')+'</div></div>';
    }).join('');
    return '<tr><td title="'+r.name+'">'+r.display_name+'</td><td><span class="era-tag" style="background:'+(EC[r.era_group]||'#666')+'22;color:'+(EC[r.era_group]||'#666')+'">'+r.era_group+'</span></td><td>'+r.pdf_pages+'</td><td>'+r.pdf_mb+'MB</td><td><span class="ebar" style="width:'+Math.max(4,r.total_entities/maxE*70)+'px;background:'+(EC[r.era_group]||'#666')+'"></span><b>'+r.total_entities.toLocaleString()+'</b></td><td>'+r.density+'</td><td><span class="dtoggle" onclick="tog('+idx+',this)">实体 ▾</span></td></tr><tr class="drow" id="d'+idx+'"><td colspan="7"><div class="dcontent">'+catHtml+'</div></td></tr>';
  }).join('');
}

function tog(idx,el){var row=document.getElementById('d'+idx);row.classList.toggle('open');el.textContent=row.classList.contains('open')?'收起 ▴':'实体 ▾';}
render();
</script>
</body>
</html>"""

# 替换统计占位符
html = html.replace('__CHARTJS_CODE__', chartjs_code)

# 读取地图图片并编码为base64
map_img_path = f'{BASE}/visualization/遗址分布地图.png'
if os.path.exists(map_img_path):
    with open(map_img_path, 'rb') as f:
        map_img_b64 = base64.b64encode(f.read()).decode('ascii')
    html = html.replace('__MAP_IMG_B64__', map_img_b64)
    print(f"地图图片: {len(map_img_b64)//1024}KB (base64)")
else:
    print(f"⚠️ 地图图片不存在: {map_img_path}")

html = html.replace('__TR__', str(total_reports))
html = html.replace('__TE__', f'{total_entities:,}')
html = html.replace('__TC__', str(total_cats))
html = html.replace('__TP__', f'{total_pages:,}')
html = html.replace('__TG__', f'{total_pdf_gb:.1f}')

# 洞察数据
id_pct = round(super_totals.get("编号系统", 0) / total_entities * 100)
html = html.replace('__PCT_ID__', str(id_pct))
html = html.replace('__POT__', str(cat_totals.get("陶器", 0)))
html = html.replace('__BRZ__', str(cat_totals.get("铜器", 0)))
html = html.replace('__STN__', str(cat_totals.get("石器", 0)))
neo_reports = len([r for r in reports if r['era_group'] == "新石器时代"])
html = html.replace('__PCT_NEO__', str(round(neo_reports / total_reports * 100)))

# 替换数据占位符
html = html.replace('__DATA_B64__', data_b64_parts)
html = html.replace('__ERA_COLORS__', json.dumps(ERA_COLORS, ensure_ascii=False))
html = html.replace('__ERA_ORDER__', json.dumps(ERA_ORDER, ensure_ascii=False))
html = html.replace('__CAT_SUPER__', json.dumps(CAT_SUPER, ensure_ascii=False))
html = html.replace('__SUPER_ORDER__', json.dumps(SUPER_ORDER, ensure_ascii=False))
html = html.replace('__SUPER_COLORS__', json.dumps(SUPER_COLORS, ensure_ascii=False))

# ====== 验证 ======
# 验证第二个 <script> 块（主逻辑，跳过 Chart.js）
idx1 = html.find('</script>')
script_start = html.find('<script>', idx1) + 8
script_end = html.find('</script>', idx1 + 1)
js_only = html[script_start:script_end]
for ch, expected in [('(',')'),('{','}'),('[',']')]:
    if js_only.count(ch) != js_only.count(expected):
        print(f"括号不匹配: {ch}={js_only.count(ch)}, {expected}={js_only.count(expected)}")

out_path = f'{BASE}/知识库网站/考古报告实体标注知识库.html'
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(html)
print(f"生成完成: {out_path} ({len(html)//1024}KB)")

# Node.js 语法检查
with open('/tmp/check_html.js', 'w') as f:
    f.write('var Chart=function(){};\n')
    f.write('var document={getElementById:function(){return{appendChild:function(){}}},createElement:function(){return{className:"",innerHTML:""}},querySelectorAll:function(){return{forEach:function(){}}}};\n')
    f.write(js_only)
result = subprocess.run(['node', '--check', '/tmp/check_html.js'], capture_output=True, text=True)
if result.returncode == 0:
    print("✅ Node.js 语法检查通过")
else:
    print(f"❌ Node.js 语法错误: {result.stderr.strip()}")
