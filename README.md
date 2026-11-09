# chinese-clause-segmentation

可解释、保留原文的中文 Sentence / Clause 规则切分工具。适用于新闻、评论、口语叙述和中英混合文本的初步处理，提供 general / medical 两种模式。v0.1.0 是开发验证版，尚无独立真实语料验证。

## 安装

要求 Python 3.10+，核心零第三方运行依赖。在仓库根目录执行：

```sh
python -m pip install .
# 可选中文分词（切分核心不需要）
python -m pip install '.[tokenize]'
```

## Python API

```python
from chinese_clause_segmentation import segment, split_sentences, split_clauses

text = "产品非常好，客服很耐心。如果有问题，就联系我们。"
result = segment(text, mode="general")
for sentence in result.sentences:
    print(sentence.text, sentence.start, sentence.end, sentence.sentence_id)
for clause in result.clauses:
    print(clause.text, clause.start, clause.end,
          clause.sentence_id, clause.clause_id, clause.reason)
assert "".join(c.text for c in result.clauses) == text
assert all(text[c.start:c.end] == c.text for c in result.clauses)

sentences = split_sentences(text)
clauses = split_clauses(text, mode="medical")
payload = result.to_dict()
```

偏移是原输入字符串的 Python Unicode 码点下标，0 起点、左闭右开；不是 UTF-8 字节或 UTF-16 偏移。Sentence 编号从1开始，Clause 在所属 Sentence 内从1编号。空串返回空结果；纯空格、标点和短句保留。标点和空白归入相邻 span，拼接能精确重构原文。不提供“去标点后文本”，调用者需要展示时可自行生成副本。

`Rules` 是不可变配置，允许显式传给 `segment(..., rules=...)` 或 `split_clauses(..., rules=...)`，例如调整无标点边界两侧最小长度。配置词命中只是启发式证据，并非真实句法分析或自动语义理解。

## 命令行及批处理

```sh
chinese-clause input.txt --output output.jsonl
chinese-clause input.csv --format csv --text-column text --output output.jsonl
chinese-clause input.jsonl --format jsonl --text-column text --mode medical --output output.jsonl
python -m chinese_clause_segmentation input.txt --output output.jsonl
```

文本文件按整个文件处理；CSV/JSONL逐记录处理，每个输入记录输出一行JSON，包含 `row_id` 和 `segmentation`。输入UTF-8或UTF-8 BOM，输出UTF-8；CSV遵守标准引号/跨行字段。输入记录的其他字段不会复制到输出。输出必须是新路径，已有文件会拒绝覆盖。异常输入返回退出码2；中途出错可能留下部分JSONL，需删除该部分输出再重试，不能视为完成产物。

## 规则

句末标点、连续标点、省略号与换行生成Sentence候选。小数、常见英文缩写、域名和正确嵌套括号/引号受到保护；未闭合括号不会阻塞后续所有句末标点。匹配引号内的整段引语通常保留，避免切碎引述。

Clause考虑逗号、分号、空白和少量明确话语转换词。只有两侧包含谓语/评价线索时才考虑切分；因果、条件、让步、递进等关系对及否定/程度片段优先保留。逗号内数字不当作分界；医疗领域词汇独立放在 `domains.py`。无标点句采用保守策略，不按字数强切。

`general` 为默认模式，使用通用叙述和评价线索；`medical` 在相同算法上增加医生、护士、治疗、复查等通用医疗线索，不加载患者数据或私有停用词。两种模式都属于规则启发式，不是医学诊断或真实句法分析。

## 测试、评估与构建

```sh
python -m pip install -e '.[dev]'
python -m pytest -q
python -m benchmarks.evaluate --output evaluation/results.json
python -m build
python -m twine check dist/*
python -m pip install dist/chinese_clause_segmentation-0.1.0-py3-none-any.whl
```

测试样例全部人工编写，无真实患者评论或记录ID。边界评估按原文位置精确匹配，排除每篇末尾边界；报告micro Precision/Recall/F1、领域分项和基础标点切分对照。开发测试集与算法共同设计，包含保留的困难反例，不是独立测试集。具体结果及兼容性见 [验证报告](docs/VALIDATION.md)。GitHub Actions配置Linux/Windows、Python3.10–3.13矩阵；配置存在不等于远端任务已成功。

## 已知局限

规则不是依存句法模型。省略主语、双关、复杂引用、罕见缩写、URL内复杂符号、隐含话题转换和缺少话语词的无标点长句仍可能欠切或过切。将关系对作为整体是一种保守的语义单元定义，未必符合其他语料的标注规范。默认词汇只能覆盖部分表达，需要独立领域标注评估后再扩展。不得将开发回归通过率当成真实语料泛化准确率。

## 来源、隐私与许可

本项目吸收早期领域研究切分流程的设计思想，采用独立模块重新实现；未复用研究数据、私有回归实例、记录级修补、固定路径、词表或人工标注。与科研封版版本不保证边界一致，不用于替换论文正式输出。迁移审计见 [设计记录](docs/DESIGN.md)。

本项目的公开展示策略为 **All rights reserved（保留全部权利）**，不采用开放源代码许可证。源码公开可见不一般性授予使用、修改或再分发权利；GitHub服务条款允许的查看、Fork等平台行为不受限制，具体见 [LICENSE](LICENSE)。安装和运行示例用于说明技术接口，不单独授予使用许可。代码与合成样例的权属、机构或合作约定仍需权利人确认，选择这一发布策略不代表权属已经获得证明。未打包第三方词典/语料，可选jieba由用户独立安装并遵守其许可。暂不发布PyPI。

**Public source visibility, all rights reserved.** This project is not offered under an open-source license. Source visibility does not grant general rights to use, modify, or redistribute the materials. Viewing and forking permitted by the GitHub Terms of Service remain permitted. Ownership and disclosure authority still require confirmation. The general tool is independent of the research version, and identical segmentation results are not guaranteed. No independent real-world generalization validation has been completed.
