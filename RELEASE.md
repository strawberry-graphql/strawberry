Release type: patch

TypingUnionType import error check is reraised because TypingGenericAlias is checked at the same time which is checked under 3.9 instead of under 3.10

Fix by separating TypingUnionType and TypingGenericAlias imports in their own try-catch
