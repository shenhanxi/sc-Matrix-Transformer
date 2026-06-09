# sc-Matrix-Transformer
A lightweight Python CLI tool for spatial transcriptomics matrix preprocessing and cell ID alignment.
# sc-Matrix-Transformer

A lightweight, automated Python CLI tool designed for spatial transcriptomics and single-cell matrix preprocessing. 

## 💡 Overview
在处理空间组学（Spatial Omics）数据时，早期的数据清洗、细胞 ID 对齐以及降维矩阵（PCs）的标准化往往伴随着大量机械性的重复劳动。本项目封装了一个支持命令行的自动化预处理流程，可一键完成：
- 基于正则表达的复杂细胞 ID 提取与规范化重命名。
- 动态的主成分（PC）筛选与 `StandardScaler` 标准化。
- 针对特定 PC 的绝对值转换与二次标准化（Z-score）。

## 🚀 Features
- **CLI-Driven**: 易于集成到更大型的 Shell 脚本或自动化工作流（如 Snakemake/Nextflow）中。
- **Robust**: 包含处理表头缺省、防止方差为零等防呆设计，适合处理真实的脏数据。
- **Interactive Mode**: 支持 `--interactive` 模式，方便非生信背景的实验人员手动调整参数。

## 🛠️ Usage

### 基本运行
将您的输入文件放置在同级目录，运行以下命令即可：

```bash
python combined_pipeline.py --input sample_data.csv --output result_matrix.csv --pcs PC1-6 --abs-pcs PC3,PC4
