# 迁移审计与设计边界

## 只读审计

审计对象为领域研究的正式 `segment_sentence_clauses.py`，其SHA-256为
`f394e040c1f8bc7a092b1288ce5f7088212c9fbdef649a3ded5336ac7ca20a6a`。
只读查阅了阶段记录、质量报告、内嵌回归、字段字典及依赖说明。未执行该脚本、未读取患者CSV正文、未修改科研正式产物。源位置只记在本地私有审计，不带入可提交文件。

原流程：`main → run → validate_preflight → sentence_spans → clause_spans → tokenize_clause → 输出与核验`。
Sentence内部为 `terminal_sentence_spans → recover_sentence_boundaries_from_unclosed_brackets → merge_hard_sentence_fragments`。
Clause内部为 `split_whitespace_units → delimiter_clause_spans → merge_fragment_spans → merge_unbalanced_bracket_relation_pairs → recover_clause_boundaries_from_unclosed_brackets → refine_long_clause_span`。

通用思想包括连续标点处理、括号保护、异常括号恢复、因果/条件依存保护、短片段保护、主语/时间/话题变化提示以及基于原文偏移的追溯。原有谓语词命中只是启发式，不能解释为句法分析。

领域专用内容包括医疗角色/治疗阶段/症状词汇、医疗时间背景及长句阶段关键词、Topic分词保护词。不可迁移内容包括固定研究输入输出路径、输入哈希锁定、四组样本规模、按记录查找的回归与特定原句精确修补、患者片段、词表、报告与UID构造。

原脚本的75项回归与真实记录绑定，不导入新仓库，也不在新工程中运行。新样例均独立编写；原测试数量不计入本工具测试数量。

## 重构

`models.py`定义不可变Span结果；`rules.py`定义通用启发式配置；`domains.py`提供显式领域适配；`core.py`负责无损切分；`cli.py`负责流式记录输入输出；`tokenization.py`提供可选分词。无哈希/记录ID驱动的算法分支，无研究词表运行依赖。

与原实现的主要差异：不裁剪空白、不删除符号，span连续覆盖全文；采用匹配类型的括号/引号保护，未匹配开括号不遮蔽全文；保护常见英文缩写、小数和数字分隔符；中文省略号和英文连续点合组；保留合法短句；领域词汇不进入默认核心；语义边界带reason供解释。医用规则包仅含手写通用术语，不含姓名或私有例外。

语义策略保守：因果、条件、让步、递进显式关系对不拆；独立目标/主语/时间变化结合谓语线索才拆；无标点时只在明确话语词和两侧命题证据下提出边界。没有神经解析器，不保证复杂中文全覆盖。

## 权利与发布

只迁移算法思想，代码独立重写。无法单靠本地文件确认原研究所有权/雇佣约定，故不擅自选择MIT或Apache许可，当前保留全部权利并仅私人交付。Git提交前审查文件允许清单、绝对路径、长数字ID、密钥模式和构建包内容；工具、环境与本地原文件审计在ignore目录内。
