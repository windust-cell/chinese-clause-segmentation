from chinese_clause_segmentation import segment

text = "产品非常好，客服很耐心。如果有问题，就联系我们。"
result = segment(text)
for clause in result.clauses:
    print(clause.sentence_id, clause.clause_id, clause.start, clause.end, repr(clause.text), clause.reason)
assert "".join(c.text for c in result.clauses) == text
