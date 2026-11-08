# v0.1.0

首次私人开发交付。核心零依赖，提供Sentence/Clause原文、偏移、层级编号与边界原因；general / medical规则包；Python API与TXT/CSV/JSONL命令行；可选jieba分词。

Windows本地Python3.10、3.11、3.12、3.13、3.14各63项测试通过。包含44条合成开发评估，Sentence边界F1=0.9630、Clause=0.8846；不代表独立真实语料泛化表现。已知过切/欠切反例与领域详细指标在docs/VALIDATION.md和evaluation/results.json。

提供wheel和sdist附件，不发布PyPI。代码权利未完全确认，当前保留全部权利，仓库保持private，不授权公开再分发。无患者数据、原科研私有回归实例或第三方词表。
