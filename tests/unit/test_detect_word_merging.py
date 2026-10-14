"""Compound-word fixer must not touch proper nouns or real words (P9 A2: 'Quốc hội Hoa Kỳ')."""
from scripts.utils.detect_word_merging import fix_merged_words


def test_fixes_merged_compounds_keeps_proper_nouns_and_real_words():
    text = "hộihọa, vănhóa. Quốc hội Hoa Kỳ. Lễ hội hoa. Lời văn hoa mỹ. Khoa học."
    fixed, n = fix_merged_words(text)
    assert fixed == "hội họa, văn hóa. Quốc hội Hoa Kỳ. Lễ hội hoa. Lời văn hoa mỹ. Khoa học."
    assert n == 2
