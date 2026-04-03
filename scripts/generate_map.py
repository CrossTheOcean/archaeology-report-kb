#!/usr/bin/env python3
"""生成考古遗址分布静态地图图片"""
import json, os, math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
from matplotlib.patches import Circle
from matplotlib.lines import Line2D
import contextily as ctx
from shapely.geometry import Point
import geopandas as gpd

BASE = '/Users/crosstheocean/WorkBuddy/20260330184406'

# ====== 遗址坐标（复用build_visualization.py的数据）======
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
RESULTS_DIR = f'{BASE}/提取结果'
PDF_DIR = f'{BASE}/考古报告PDF'

all_pdfs = sorted([f for f in os.listdir(PDF_DIR) if f.endswith('.pdf')]) if os.path.exists(PDF_DIR) else []

import fitz
reports = []
for r in sorted(os.listdir(RESULTS_DIR)):
    epath = f'{RESULTS_DIR}/{r}/entities.json'
    if not os.path.exists(epath): continue
    with open(epath) as f:
        entities = json.load(f)
    pdf_pages = 0
    for pdf in all_pdfs:
        if r in pdf or pdf.replace('.pdf','') in r:
            try:
                doc = fitz.open(f'{PDF_DIR}/{pdf}')
                pdf_pages = len(doc); doc.close()
            except: pass
            break
    total = sum(len(v) for v in entities.values())
    era = classify(r)
    reports.append({
        "name": r, "display_name": clean_name(r),
        "pdf_pages": pdf_pages,
        "total_entities": total,
        "era_group": era,
    })

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
        r['lat'] = None
        r['lng'] = None
        r['province'] = ''

# 过滤有坐标的报告
sites = [r for r in reports if r.get('province')]
print(f"共 {len(sites)} 个遗址有坐标")

# ====== 生成地图 ======
print("生成地图...")

# 设置中文字体
from matplotlib.font_manager import FontProperties
chinese_font_path = '/System/Library/Fonts/STHeiti Medium.ttc'
if not os.path.exists(chinese_font_path):
    chinese_font_path = '/Library/Fonts/Arial Unicode.ttf'
FONT_PROP = FontProperties(fname=chinese_font_path)
FONT_NAME = FONT_PROP.get_name()
plt.rcParams['font.family'] = FONT_NAME

# ====== 下载中国省级GeoJSON（基于官方测绘数据的标准中国地图）======
china_geojson_path = f'{BASE}/data/china_provinces.json'
if not os.path.exists(china_geojson_path):
    print("下载标准中国地图GeoJSON...")
    import requests as req
    url = 'https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json'
    proxies = {'http': 'http://127.0.0.1:8890', 'https': 'http://127.0.0.1:8890'}
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
    r = req.get(url, headers=headers, proxies=proxies, timeout=15)
    if r.status_code == 200:
        os.makedirs(os.path.dirname(china_geojson_path), exist_ok=True)
        with open(china_geojson_path, 'w', encoding='utf-8') as f:
            f.write(r.text)
        print(f"  下载成功: {len(r.content)//1024}KB")
    else:
        print(f"  下载失败: HTTP {r.status_code}")
        china_geojson_path = None

# 读取中国地图GeoJSON
china_gdf = None
if china_geojson_path and os.path.exists(china_geojson_path):
    china_gdf = gpd.read_file(china_geojson_path, crs='EPSG:4326')
    print(f"  中国地图: {len(china_gdf)} 个省级行政区")

# ====== 准备遗址数据 ======
geometry = [Point(s['lng'], s['lat']) for s in sites]
gdf_sites = gpd.GeoDataFrame(sites, geometry=geometry, crs='EPSG:4326')

# 投影到 Web Mercator (EPSG:3857)
gdf_sites_proj = gdf_sites.to_crs('EPSG:3857')
if china_gdf is not None:
    china_gdf_proj = china_gdf.to_crs('EPSG:3857')

# 计算视图边界：以中国地图边界为主
if china_gdf_proj is not None:
    cxmin, cymin, cxmax, cymax = china_gdf_proj.total_bounds
    # 只保留中国大陆区域（排除南海远端小岛导致的边界膨胀）
    # 用所有遗址的范围作为参考，加上中国地图范围
    sxmin, symin, sxmax, symax = gdf_sites_proj.total_bounds
    # 以中国地图边界为基础
    xmin = cxmin
    xmax = cxmax
    ymin = cymin
    ymax = cymax
else:
    xmin, ymin, xmax, ymax = gdf_sites_proj.total_bounds

# 加padding
pad_x = (xmax - xmin) * 0.05
pad_y = (ymax - ymin) * 0.08
xmin -= pad_x; xmax += pad_x
ymin -= pad_y; ymax += pad_y

# 计算等比例尺寸
data_w = xmax - xmin
data_h = ymax - ymin
aspect = data_w / data_h
fig_h = 14
fig_w = fig_h * aspect

fig, ax = plt.subplots(1, 1, figsize=(fig_w, fig_h), facecolor='#0f1117')
ax.set_facecolor('#0f1117')
ax.set_xlim(xmin, xmax)
ax.set_ylim(ymin, ymax)
ax.set_aspect('equal')

# ====== 绘制中国地图（标准官方边界）======
if china_gdf_proj is not None:
    print("绘制中国地图边界...")
    # 绘制省界填充
    china_gdf_proj.plot(ax=ax, facecolor='#1a1d27', edgecolor='#2a2d3a',
                       linewidth=0.6, alpha=0.9, zorder=1)
    # 绘制省界线（更清晰）
    china_gdf_proj.boundary.plot(ax=ax, color='#3a3d4a', linewidth=0.4, zorder=2)

# ====== 绘制遗址点 ======
max_entities = max(s['total_entities'] for s in sites)
x_coords = gdf_sites_proj.geometry.x.values
y_coords = gdf_sites_proj.geometry.y.values

# 外圈光晕
for i, s in enumerate(sites):
    color = ERA_COLORS.get(s['era_group'], '#666')
    size = max(40, min(260, (s['total_entities'] / max_entities) * 260))
    ax.scatter(x_coords[i], y_coords[i], s=size*2, c=color, alpha=0.15, edgecolors='none', zorder=3)

# 主点
for i, s in enumerate(sites):
    color = ERA_COLORS.get(s['era_group'], '#666')
    size = max(40, min(260, (s['total_entities'] / max_entities) * 260))
    ax.scatter(x_coords[i], y_coords[i], s=size, c=color, alpha=0.85,
              edgecolors='white', linewidths=0.5, zorder=4)

# 标签
top_sites = sorted(sites, key=lambda x: x['total_entities'], reverse=True)[:20]
for i, s in enumerate(sites):
    if s in top_sites:
        ax.annotate(s['site_name'], (x_coords[i], y_coords[i]),
                   textcoords="offset points", xytext=(6, 6),
                   fontsize=8, color='#e4e4e7', alpha=0.9,
                   fontweight='bold', fontproperties=FONT_PROP, zorder=5)
    else:
        ax.annotate(s['site_name'], (x_coords[i], y_coords[i]),
                   textcoords="offset points", xytext=(5, 5),
                   fontsize=6, color='#8b8fa3', alpha=0.6,
                   fontproperties=FONT_PROP, zorder=5)

# 图例
legend_elements = []
for era in ERA_ORDER:
    count = len([s for s in sites if s['era_group'] == era])
    if count > 0:
        legend_elements.append(
            Line2D([0], [0], marker='o', color='none', markerfacecolor=ERA_COLORS[era],
                   markeredgecolor='white', markeredgewidth=0.5, markersize=10,
                   label=f'{era} ({count})')
        )
leg = ax.legend(handles=legend_elements, loc='lower right', fontsize=10,
               facecolor='#1a1d27', edgecolor='#2a2d3a', labelcolor='#e4e4e7',
               framealpha=0.92, ncol=2, prop=FONT_PROP)
leg.get_frame().set_linewidth(1)

# 标题
ax.set_title('中国考古学专刊·丁种 — 遗址分布地图', fontsize=20, fontweight='bold',
            color='#f59e0b', pad=15, fontproperties=FONT_PROP)
subtitle = f'共 {len(sites)} 处遗址 | 底图来源: DataV.GeoAtlas（基于官方测绘数据）'
ax.text(0.5, 1.02, subtitle, transform=ax.transAxes, ha='center', va='bottom',
       fontsize=12, color='#8b8fa3', fontproperties=FONT_PROP)

# 数据来源标注
ax.text(0.01, 0.01, '地图数据: 阿里云DataV GeoAtlas（标准中国地图）',
       transform=ax.transAxes, fontsize=7, color='#555',
       fontproperties=FONT_PROP, va='bottom')

# 隐藏坐标轴
ax.set_xticks([])
ax.set_yticks([])
for spine in ax.spines.values():
    spine.set_visible(False)

plt.tight_layout()

# 保存 — 300dpi 高清
out_path = f'{BASE}/visualization/遗址分布地图.png'
os.makedirs(os.path.dirname(out_path), exist_ok=True)
fig.savefig(out_path, dpi=300, bbox_inches='tight', facecolor='#0f1117',
           edgecolor='none', pad_inches=0.3)
plt.close()

# 检查结果
from PIL import Image
file_size = os.path.getsize(out_path) / (1024*1024)
img = Image.open(out_path)
print(f"地图生成完成: {out_path} ({file_size:.1f}MB, {img.size[0]}x{img.size[1]}px)")
