#!/usr/bin/env python3
"""从entities.json生成可视化HTML总览页面"""
import json, os, fitz

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 时代分类映射
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


def classify(name):
    for kw, era in ERA_MAP.items():
        if kw in name:
            return ERA_GROUP.get(era, "其他")
    return "其他"


def collect_data():
    results_dir = os.path.join(BASE, '提取结果')
    pdfs_dir = os.path.join(BASE, '考古报告PDF')
    all_pdfs = sorted([f for f in os.listdir(pdfs_dir) if f.endswith('.pdf')]) if os.path.exists(pdfs_dir) else []

    reports = []
    for r in sorted(os.listdir(results_dir)):
        epath = os.path.join(results_dir, r, 'entities.json')
        if not os.path.exists(epath):
            continue
        with open(epath) as f:
            entities = json.load(f)

        pdf_mb, pdf_pages = 0, 0
        for pdf in all_pdfs:
            if r in pdf or pdf.replace('.pdf', '') in r:
                pdf_mb = os.path.getsize(os.path.join(pdfs_dir, pdf)) / (1024 * 1024)
                try:
                    doc = fitz.open(os.path.join(pdfs_dir, pdf))
                    pdf_pages = len(doc)
                    doc.close()
                except:
                    pass
                break

        md_size = sum(
            os.path.getsize(os.path.join(results_dir, r, f2))
            for f2 in os.listdir(os.path.join(results_dir, r))
            if f2.endswith('.md') and not f2.startswith('_')
        )

        total = sum(len(v) for v in entities.values())
        era = classify(r)

        reports.append({
            "name": r, "display_name": r.split("  ")[0].split("（")[0].split("(")[0].strip()[:25],
            "pdf_mb": round(pdf_mb, 1), "pdf_pages": pdf_pages,
            "md_size_kb": round(md_size / 1024, 1),
            "total_entities": total, "entity_categories": len(entities),
            "entities": entities, "era_group": era,
        })

    return reports


def build_html(reports):
    # Read template
    template_path = os.path.join(BASE, '知识库网站', 'index_template.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        html = f.read()

    data_json = json.dumps(reports, ensure_ascii=False, indent=2)
    html = html.replace('__DATA_PLACEHOLDER__', data_json)
    # Fix script ordering
    html = html.replace(
        '<script>\n// Load data\nconst DATA = __REPORTS_DATA__;',
        '<script>\n// Data\nconst __REPORTS_DATA__ = __DATA_PLACEHOLDER__;\n// Load data\nconst DATA = __REPORTS_DATA__;'
    )
    html = html.replace(
        '<script>\n// Inject data\nconst __REPORTS_DATA__ = __DATA_PLACEHOLDER__;\n</script>',
        ''
    )

    out_path = os.path.join(BASE, 'visualization', '考古报告实体标注知识库.html')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'HTML生成完成: {out_path} ({len(html) // 1024}KB)')


if __name__ == '__main__':
    reports = collect_data()
    print(f'收集 {len(reports)} 份报告数据')
    build_html(reports)
