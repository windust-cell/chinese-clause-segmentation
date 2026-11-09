# v0.1.0

首次开发验证版。核心零依赖，提供Sentence/Clause原文、偏移、层级编号与边界原因；general / medical规则包；Python API与TXT/CSV/JSONL命令行；可选jieba分词。

Windows本地Python3.10、3.11、3.12、3.13、3.14各63项测试通过。包含44条合成开发评估，Sentence边界F1=0.9630、Clause=0.8846；不代表独立真实语料泛化表现。已知过切/欠切反例与领域详细指标在docs/VALIDATION.md和evaluation/results.json。

提供wheel和sdist附件，不发布PyPI。代码权利未完全确认，当前保留全部权利；仓库可见性及未来许可由权利人决定。无患者数据、原科研私有回归实例或第三方词表。此文档修订不改变既有v0.1.0附件或其许可。

## 后续公开准备（未创建新Release）

拟公开策略为Public源码可见 + All rights reserved，不采用开放源代码许可证，并尊重GitHub服务条款允许的查看与Fork。更新文档和许可表述、增强归档安全检查与测试、设置CI最小权限并固定官方Action版本；不改变切分算法或API。权属及公开权限仍需确认。建议审阅并合并后另行批准v0.1.1；当前包版本仍为0.1.0，候选构建不能替换既有正式附件。
