# 中国考古学专刊·丁种 — 实体标注知识库

> 基于 MinerU OCR + LLM 的考古报告结构化实体标注工程

本项目对中国社会科学院考古研究所编著的**考古学专刊·丁种**系列70种发掘报告进行了批量数字化处理和结构化实体标注。

## 📊 项目概览

| 指标 | 数据 |
|------|------|
| 发掘报告 | 70 份 |
| 总实体数 | 44,526 个 |
| 实体类别 | 26 类 |
| 总页数 | ~30,000+ 页 |
| OCR引擎 | [MinerU](https://mineru.net) |

## 🏷️ 实体类别

本工程自定义了26类考古学实体进行自动标注：

| 类别 | 说明 | 数量 |
|------|------|------|
| 器物编号 | 遗物编号标识 | 15,096 |
| 遗迹编号 | 灰坑、墓葬、房址等编号 | 13,439 |
| 测量数据 | 尺寸、重量、容量等数据 | 8,499 |
| 探方编号 | 发掘探方编号 | 2,822 |
| 陶器 | 陶质器物类型 | 1,006 |
| 铜器 | 铜质器物类型 | 401 |
| 年代 | 年代断代信息 | 368 |
| 地层 | 地层堆积描述 | 304 |
| 石器 | 石质工具类型 | 295 |
| 纹饰 | 器物纹饰 | 251 |
| 骨器 | 骨质器物 | 197 |
| 制作工艺 | 制作技术描述 | 150 |
| 发掘信息 | 发掘经过记录 | 146 |
| 玉器 | 玉质器物 | 141 |
| ... | （更多类别详见可视化页面） | ... |

## 📂 项目结构

```
archaeology-dingzhong-kb/
├── README.md                           # 项目说明
├── LICENSE                             # 开源协议
├── 标注脚本/
│   └── annotate_entities.py            # 26类实体标注脚本
├── scripts/
│   ├── batch_round5.py                 # 最终版批量处理脚本
│   └── build_visualization.py          # 可视化HTML生成脚本
├── data/
│   ├── reports_data.json               # 70份报告的结构化数据
│   └── 考古报告元数据清单.md            # PDF元数据
├── docs/
│   ├── 中国现代考古学重要遗址发掘时间线与报告出版情况.md
│   ├── 中国现代考古学重要遗址——发掘报告电子档获取清单.md
│   └── 考古报告PDF下载指南.md
└── visualization/
    └── 考古报告实体标注知识库.html      # 可视化总览页面
```

## 🛠️ 技术方案

### 处理流程

```
PDF文件 → MinerU OCR → Markdown + HTML → LLM实体标注 → entities.json → 可视化
```

1. **PDF获取**：从 [Internet Archive](https://archive.org/details/archaeology-dingzhong) 批量下载考古学专刊·丁种PDF文件
2. **OCR提取**：使用 [MinerU Open API](https://mineru.net) 进行高质量OCR识别，支持表格和图片区域
3. **大文件策略**：对于 >50MB 的PDF，先用 pymupdf 物理分割为 ≤40MB 的分片，再逐片上传OCR，最后合并
4. **实体标注**：自研 Python 标注脚本，调用 LLM 对提取的 Markdown 文本进行26类实体识别
5. **可视化**：生成包含图表、时间线、气泡图的交互式HTML总览

### 关键依赖

- Python 3.10+
- [MinerU CLI](https://mineru.net) (`mineru-open-api`)
- [PyMuPDF](https://pymupdf.readthedocs.io/) (PDF分割)
- [Chart.js](https://www.chartjs.org/) (可视化图表)

## 📜 时代覆盖

| 时代 | 报告数 | 代表性遗址 |
|------|--------|-----------|
| 新石器时代 | 18 | 半坡、柳湾、屈家岭、雕龙碑 |
| 夏商周 | 23 | 二里头、殷墟、张家坡、曾侯乙墓 |
| 秦汉 | 12 | 满城汉墓、马王堆、未央宫 |
| 魏晋南北朝 | 3 | 北魏永宁寺、鄂城六朝墓 |
| 隋唐 | 4 | 大明宫、永宁寺、王建墓 |
| 宋元明清 | 3 | 定陵、南宋官窑 |
| 边疆考古 | 4 | 吐鲁番、塔里木、北庭 |
| 青铜时代 | 3 | 大甸子、双砣子 |

## 🚀 快速开始

### 安装依赖

```bash
pip install pymupdf
npm install -g mineru-open-api
```

### 运行标注

```bash
# 对单个Markdown文件进行实体标注
python 标注脚本/annotate_entities.py 提取结果/某某报告/某某报告.md

# 批量处理（参考 scripts/batch_round5.py）
python scripts/batch_round5.py
```

### 查看可视化

直接在浏览器中打开 `visualization/考古报告实体标注知识库.html`

## ⚠️ 数据来源说明

- PDF原文来源于 [Internet Archive](https://archive.org/details/archaeology-dingzhong) 公共领域资源
- 所有发掘报告原文版权归**科学出版社**及**中国社会科学院考古研究所**所有
- 本项目仅提供**结构化标注数据**和**处理工具**，不包含原始PDF文件
- 标注数据基于 OCR 自动提取，可能存在识别错误，仅供参考研究使用

## 📄 许可证

- **代码与标注数据**：MIT License
- **原始考古报告**：版权归原出版单位所有

## 🙏 致谢

- [MinerU](https://mineru.net) — 高质量PDF OCR引擎
- [Internet Archive](https://archive.org) — 公共领域考古文献
- [Chart.js](https://www.chartjs.org/) — 数据可视化库
