#!/usr/bin/env python3
"""
考古发掘报告28类实体自动标注脚本
基于《考古发掘报告28类实体分类标准》
"""

import re
import json
import os
from datetime import datetime

# 28类实体颜色配置（与分类标准一致）
ENTITY_COLORS = {
    "遗址名称": {"bg": "#fce4ec", "color": "#e91e63"},
    "遗迹类型": {"bg": "#e8f5e9", "color": "#16a085"},
    "遗迹编号": {"bg": "#ffebee", "color": "#e74c3c"},
    "器物编号": {"bg": "#fff3e0", "color": "#e65100"},
    "陶器": {"bg": "#fbe9e7", "color": "#d84315"},
    "铜器": {"bg": "#fcf3cf", "color": "#c19d06"},
    "石器": {"bg": "#f4f6f7", "color": "#7f8c8d"},
    "骨器": {"bg": "#fdebd0", "color": "#d35400"},
    "蚌器": {"bg": "#e8daef", "color": "#8e44ad"},
    "玉器": {"bg": "#d1f2eb", "color": "#1abc9c"},
    "材质": {"bg": "#d5f4e6", "color": "#27ae60"},
    "纹饰": {"bg": "#fadbd8", "color": "#e74c3c"},
    "地层": {"bg": "#f3e5f5", "color": "#9b59b6"},
    "层位关系": {"bg": "#e8eaf6", "color": "#3f51b5"},
    "建筑结构": {"bg": "#efebe9", "color": "#795548"},
    "葬具葬式": {"bg": "#fce4ec", "color": "#e91e63"},
    "遗存类型": {"bg": "#fbe9e7", "color": "#ff5722"},
    "保存状况": {"bg": "#e0f7fa", "color": "#00838f"},
    "制作工艺": {"bg": "#f1f8e9", "color": "#7cb342"},
    "测量数据": {"bg": "#fff8e1", "color": "#ffa000"},
    "方向角度": {"bg": "#f3e5f5", "color": "#7b1fa2"},
    "地理位置": {"bg": "#e3f2fd", "color": "#1976d2"},
    "土样特征": {"bg": "#f1f8e9", "color": "#8bc34a"},
    "年代": {"bg": "#e8daef", "color": "#8e44ad"},
    "测年方法": {"bg": "#e0f2f1", "color": "#009688"},
    "发掘区": {"bg": "#fce4ec", "color": "#e91e63"},
    "探方编号": {"bg": "#fbe9e7", "color": "#e74c3c"},
    "发掘信息": {"bg": "#e8eaf6", "color": "#3f51b5"},
}

# 实体匹配规则
ENTITY_PATTERNS = {
    # 遗迹编号: H1, M1, F1, Y1, J1, G1, K1, D1, Z1, L1, Q1, T1
    "遗迹编号": [
        r'\b([A-Z](?:\d+[a-z]?|\d+-\d+|[A-Z]\d*))\b',  # H1, M1, F5-1, A-H1
    ],

    # 器物编号: T1:1, H1:5, M5:8
    "器物编号": [
        r'\b([A-Z]\d+:\d+)\b',  # T1:1, H1:23
        r'\b(\d{4}-[A-Z]\d+:\d+)\b',  # 2024-YX-T1:1
    ],

    # 陶器
    "陶器": [
        r'\b(陶鼎|陶鬲|陶簋|陶豆|陶盘|陶盂|陶钵|陶爵|陶斝|陶觚|陶尊|陶卣|陶壶|陶罐|陶盆|陶瓮|陶缸|陶釜|陶灶|陶埙|陶拍|陶纺轮|陶片|泥质陶|夹砂陶|灰陶|红陶|黑陶|白陶|彩陶)\b',
        r'\b(鼎|鬲|簋|豆|盘|盂|钵|爵|斝|觚|尊|卣|壶|罐|盆|瓮|缸|釜)\b(?![器物])',
    ],

    # 铜器
    "铜器": [
        r'\b(青铜鼎|青铜簋|青铜爵|青铜觚|青铜尊|青铜卣|青铜盘|青铜戈|青铜矛|青铜剑|青铜钺|青铜镞|青铜盔|青铜钟|青铜铙|青铜镈|青铜鼓|青铜编钟|铜鼎|铜爵|铜戈|铜矛|铜剑|铜镜|铜灯|铜炉)\b',
        r'\b(鼎|簋|爵|觚|尊|卣|盘|戈|矛|剑|钺|镞|铙|镈|軎|辖|镳|衔)\b',
    ],

    # 石器
    "石器": [
        r'\b(石斧|石锛|石凿|石铲|石镰|石刀|石镞|石矛|石球|石网坠|石磨盘|石磨棒|石杵|石臼|砍砸器|刮削器|石璧|石琮|石圭|石璋|石璜|石琥)\b',
        r'\b(砺石|燧石|石料)\b',
    ],

    # 骨器
    "骨器": [
        r'\b(骨铲|骨锄|骨耜|骨锥|骨针|骨匕|骨镞|骨鱼镖|骨鱼钩|骨簪|骨梳|骨珠|骨管|骨环|骨笛|骨哨|卜骨)\b',
    ],

    # 蚌器
    "蚌器": [
        r'\b(蚌镰|蚌刀|蚌铲|蚌镞|蚌饰|蚌珠)\b',
    ],

    # 玉器
    "玉器": [
        r'\b(玉璧|玉琮|玉圭|玉璋|玉琥|玉璜|玉环|玉玦|玉珠|玉管|玉坠|玉衣|玉琀|玉握|玉塞|玉戈|玉钺|玉戚|玉斧|玉锛|玉凿|玉刀)\b',
    ],

    # 材质
    "材质": [
        r'\b(青铜|红铜|黄铜|白铜|钢材|铁器|金银器|铅器|锡器|玉石|玛瑙|水晶|绿松石|和田玉|岫岩玉|独山玉)\b',
        r'\b(黏土|高岭土|燧石|大理石)\b',
    ],

    # 纹饰
    "纹饰": [
        r'\b(绳纹|篮纹|方格纹|弦纹|划纹|附加堆纹|乳钉纹|云雷纹|饕餮纹|夔龙纹|回纹|涡纹|兽面纹|龙纹|凤鸟纹|蝉纹|蚕纹|鱼纹|龟纹|虎纹|象纹|蛇纹|窃曲纹|重环纹|垂鳞纹|谷纹|蒲纹|三角纹|水波纹|圆圈纹)\b',
    ],

    # 地层
    "地层": [
        r'\b(文化层|间歇层|扰乱层|生土层|淤积层|风积层|近代层|历史层|表土层|垫土层|红烧土层)\b',
        r'\b([第]?[一二三四五六七八九十百\d]+层)\b',
        r'\b(L\d+)\b',
    ],

    # 层位关系
    "层位关系": [
        r'\b(叠压|打破|平行|依附|堆积)\b',
        r'\b(开口于|叠压于|打破|打破关系|叠压关系)\b',
    ],

    # 建筑结构
    "建筑结构": [
        r'\b(基址|基槽|柱洞|柱础|夯土|墙基|门道|散水|台阶|路面|硬面|居住面|烧土面|姜石面|土墙|石墙|砖墙|木骨墙)\b',
    ],

    # 葬具葬式
    "葬具葬式": [
        r'\b(棺|椁|棺椁|陶棺|瓮棺|石棺|木棺|船棺)\b',
        r'\b(仰身直肢葬|仰身屈肢葬|侧身直肢葬|侧身屈肢葬|俯身葬|屈肢葬|蹲踞葬|二次葬)\b',
    ],

    # 遗存类型
    "遗存类型": [
        r'\b(完整器|复原器|残器|碎片|标本|采集品|征集品|陶片|瓷片|人骨|兽骨|木炭|种子|贝壳)\b',
    ],

    # 保存状况
    "保存状况": [
        r'\b(完整|基本完整|残缺|残破|仅存残片|完好|较好|一般|较差|极差|破碎|变形|腐蚀|风化|污染|锈蚀|霉斑)\b',
        r'\b(已修复|未修复|部分修复|复原)\b',
    ],

    # 制作工艺
    "制作工艺": [
        r'\b(手制|泥条盘筑|泥片贴筑|模制|轮制|慢轮修整|快轮成型)\b',
        r'\b(铸造|锻造|焊接|铆接|错金银|鎏金|镶嵌)\b',
        r'\b(打制|砸击|碰砧|压制|磨制|钻孔|切割|刮削|雕刻)\b',
    ],

    # 测量数据
    "测量数据": [
        r'\b(\d+\.?\d*)\s*(厘米|公分|米|mm|CM|M)\b',
        r'\b(直径|口径|底径|腹径|高|长|宽|深|厚)\s*[:：]?\s*\d+\.?\d*\s*(厘米|米|mm)?\b',
        r'\b\d+\.?\d*\s*(平方米|毫升|升|克|千克|立方米)\b',
    ],

    # 方向角度
    "方向角度": [
        r'\b(正北|正南|正东|正西|东北|东南|西北|西南)\b',
        r'\b(南北向|东西向|东北-西南向|西北-东南向)\b',
        r'\b(坐北朝南|坐南朝北|坐东朝西|坐西朝东)\b',
        r'\b(\d+)\s*°\b',
    ],

    # 地理位置
    "地理位置": [
        r'\b(河南省|河北省|山西省|陕西省|山东省|江苏省|浙江省|安徽省|江西省|福建省|湖北省|湖南省|广东省|广西|四川省|贵州省|云南省|甘肃省|青海省|宁夏|新疆|内蒙古|黑龙江|吉林|辽宁|北京|上海|天津|重庆)\b',
        r'\b(安阳市|西安市|郑州市|洛阳市|北京市|武汉市|长沙市|广州市)\b',
        r'\b(省|市|县|区|乡|镇|村)\b',
    ],

    # 土样特征
    "土样特征": [
        r'\b(黏土|壤土|砂土|粉砂土|砾石土|腐殖土)\b',
        r'\b(灰土|黑土|红土|黄土|褐土|白土|绿土)\b',
        r'\b(疏松|致密|坚硬|分层|纯净|含砂|含砾)\b',
    ],

    # 年代
    "年代": [
        r'\b(旧石器时代|新石器时代|铜石并用时代|青铜时代|铁器时代)\b',
        r'\b(夏代|商代|西周|东周|春秋|战国|秦代|汉代|魏晋|南北朝|隋代|唐代|宋代|元代|明代|清代)\b',
        r'\b(公元前?\d+年|公元\d+年|距今\d+年)\b',
        r'\b(早期|中期|晚期|[一二三四五六七八九十]+期)\b',
    ],

    # 测年方法
    "测年方法": [
        r'\b(碳十四测年|C14测年|钾氩法|铀系法|热释光|光释光|古地磁|树轮校正|类型学断代|地层学断代)\b',
    ],

    # 发掘区
    "发掘区": [
        r'\b([A-Z一二三四])\s*区\b',
        r'\b([IⅣ]+)\s*区\b',
    ],

    # 探方编号
    "探方编号": [
        r'\b(T\d+[A-Z]?\d*[NS]?\d*[EW]?)\b',
    ],

    # 发掘信息
    "发掘信息": [
        r'\b(中国社会科学院考古研究所|.*省文物考古研究院|.*省博物馆|.*大学考古)\b',
        r'\b(文物出版社|科学出版社|中华书局|北京大学出版社)\b',
    ],
}

def create_entity_span(text, category, match):
    """创建带标注的HTML span"""
    colors = ENTITY_COLORS.get(category, {"bg": "#fff", "color": "#000"})
    return f'<span class="entity" data-category="{category}" style="background-color: {colors["bg"]}; color: {colors["color"]}; padding: 1px 3px; border-radius: 2px; cursor: help;" title="{category}">{match}</span>'

def annotate_text(text):
    """对文本进行实体标注"""
    # 按类别优先级处理（编号类先处理，避免重复匹配）
    priority_order = ["遗迹编号", "器物编号", "探方编号", "发掘区"]

    annotated = text
    entity_counts = {}

    # 第一轮：处理高优先级编号类
    for category in priority_order:
        patterns = ENTITY_PATTERNS.get(category, [])
        for pattern in patterns:
            matches = list(re.finditer(pattern, annotated))
            for match in matches:
                original = match.group(0)
                # 避免重复标注
                if f'data-category="{category}"' not in annotated[match.start():match.end()+20]:
                    replacement = create_entity_span(original, category, original)
                    annotated = annotated[:match.start()] + replacement + annotated[match.end():]
                    entity_counts[category] = entity_counts.get(category, 0) + 1

    # 第二轮：处理其他类别
    for category, patterns in ENTITY_PATTERNS.items():
        if category in priority_order:
            continue
        for pattern in patterns:
            matches = list(re.finditer(pattern, annotated))
            for match in matches:
                original = match.group(0)
                # 避免重复标注
                if f'data-category="{category}"' not in annotated[match.start():match.end()+20]:
                    replacement = create_entity_span(original, category, original)
                    annotated = annotated[:match.start()] + replacement + annotated[match.end():]
                    entity_counts[category] = entity_counts.get(category, 0) + 1

    return annotated, entity_counts

def extract_entities_json(text):
    """提取实体并生成JSON"""
    entities = {category: [] for category in ENTITY_PATTERNS.keys()}

    for category, patterns in ENTITY_PATTERNS.items():
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                if match not in entities[category]:
                    entities[category].append(match)

    return entities

def process_report(md_path, output_dir):
    """处理一份报告"""
    print(f"\n📄 处理: {md_path}")

    # 读取Markdown
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 提取实体
    print("  🔍 识别实体...")
    entities = extract_entities_json(content)

    # 统计
    total_entities = sum(len(v) for v in entities.values())
    print(f"  ✅ 共识别 {total_entities} 个实体")

    # 统计非空类别
    active_categories = [k for k, v in entities.items() if v]
    print(f"  📊 涉及 {len(active_categories)} 个类别")

    # 标注文本
    print("  🏷️ 生成标注版本...")
    annotated, entity_counts = annotate_text(content)

    # 生成HTML
    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>曾侯乙墓 - 实体标注版</title>
    <style>
        body {{ font-family: "Source Han Serif SC", "Noto Serif CJK SC", serif; max-width: 900px; margin: 0 auto; padding: 20px; line-height: 1.8; }}
        h1 {{ color: #333; border-bottom: 2px solid #1976d2; padding-bottom: 10px; }}
        h2 {{ color: #555; border-bottom: 1px solid #ddd; padding-bottom: 5px; margin-top: 30px; }}
        .entity {{ padding: 1px 3px; border-radius: 2px; cursor: help; }}
        .legend {{ background: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        .legend-title {{ font-weight: bold; margin-bottom: 10px; }}
        .legend-item {{ display: inline-block; margin: 3px 8px; font-size: 12px; }}
        .content {{ background: white; }}
        .stats {{ background: #e3f2fd; padding: 10px; border-radius: 5px; margin-bottom: 20px; }}
    </style>
</head>
<body>
    <h1>🏛️ 曾侯乙墓发掘报告 - 实体标注版</h1>

    <div class="stats">
        <strong>📊 实体统计</strong><br>
        总计: {total_entities} 个实体 | 类别: {len(active_categories)} 个
    </div>

    <div class="legend">
        <div class="legend-title">🏷️ 图例（点击可筛选）</div>
        {''.join(f'<span class="entity legend-item" style="background-color: {ENTITY_COLORS.get(cat, {}).get("bg", "#fff")}; color: {ENTITY_COLORS.get(cat, {}).get("color", "#000")};" data-category="{cat}">{cat}</span>' for cat in active_categories)}
    </div>

    <div class="content">
        <pre style="white-space: pre-wrap; word-wrap: break-word;">""" + annotated + """
        </pre>
    </div>

    <script>
        // 简单的标注高亮切换
        document.querySelectorAll('.entity').forEach(function(el) {
            el.addEventListener('click', function() {
                var cat = el.dataset.category;
                document.querySelectorAll('.entity').forEach(function(e) {
                    if (e.dataset.category === cat) {
                        e.style.fontWeight = e.style.fontWeight === 'bold' ? 'normal' : 'bold';
                    }
                });
            });
        });
    </script>
</body>
</html>"""

    # 保存标注HTML
    html_path = os.path.join(output_dir, "annotated.html")
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"  💾 已保存: {html_path}")

    # 保存实体JSON
    json_path = os.path.join(output_dir, "entities.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(entities, f, ensure_ascii=False, indent=2)
    print(f"  💾 已保存: {json_path}")

    return entities, entity_counts

if __name__ == "__main__":
    import sys

    md_path = sys.argv[1] if len(sys.argv) > 1 else "提取结果/曾侯乙墓/37.丁种第三十七：曾侯乙墓.md"
    output_dir = os.path.dirname(md_path)

    print("=" * 50)
    print("🏛️ 考古发掘报告实体标注工具 v1.0")
    print("=" * 50)

    if os.path.exists(md_path):
        entities, counts = process_report(md_path, output_dir)

        print("\n" + "=" * 50)
        print("📊 实体统计详情")
        print("=" * 50)
        for cat, items in sorted(entities.items(), key=lambda x: -len(x[1])):
            if items:
                print(f"  {cat}: {len(items)} 个")
                print(f"    示例: {', '.join(items[:5])}")
    else:
        print(f"❌ 文件不存在: {md_path}")
