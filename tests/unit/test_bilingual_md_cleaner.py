"""Tests for scripts/utils/bilingual_md_cleaner.py (GitBook EN+CN -> pipeline markdown)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))

from utils.bilingual_md_cleaner import clean_chapter, figure_id, missing_notes  # noqa: E402


def run(text, heading='1. Title'):
    return clean_chapter(text, heading)


def test_drops_chinese_paragraphs_and_replaces_heading():
    out, _ = run('# Chapter 1 Title 第一章\n\nHello world.\n\n你好世界。\n')
    assert out == ['# 1. Title', 'Hello world.']


def test_footnotes_renumbered_and_placed_after_citing_paragraph():
    src = ('See [cognates](#user-content-fn-1)[^1] here.\n\n'
           '看[同源词](#user-content-fn-2)[^2]。\n\n'
           'And [more](#user-content-fn-3)[^3].\n\n'
           '[^1]: Cognates: words.\n\n[^2]: 同源词：词。\n\n[^3]: More: text.\n')
    out, _ = run(src, None)
    assert out == ['See cognates<small>1</small> here.',
                   '<aside class="footnote">1. Cognates: words.</aside>',
                   'And more<small>2</small>.',
                   '<aside class="footnote">2. More: text.</aside>']
    assert missing_notes(out) == []


def test_marker_moved_outside_emphasis():
    out, _ = run('Read *[Rules of Play](#user-content-fn-1)[^1]* now.\n\n[^1]: Book.\n', None)
    assert out[0] == 'Read *Rules of Play*<small>1</small> now.'


def test_image_block_becomes_figure_marker_and_caption_kept():
    src = ('<p align="center">\n  <img src="images/1.2.png"/>\n</p>\n\n'
           '> It is fun.\n> \n> 很有趣。\n> \n> NYAAH!\n> \n> 哎呀！\n')
    out, images = run(src, None)
    assert out == ['<!-- figure id="comic-1-2" -->', '> It is fun.', '> NYAAH!']
    assert images == ['1.2.png'] and figure_id('about-the-author.png') == 'comic-about-the-author'


def test_mixed_list_block_keeps_english_items_only():
    src = ('* First item.\\\n    第一项。\n\n* Second [x](#user-content-fn-1)[^1].\\\n    第二。\n\n'
           '1. Linguistic 语言\n2. Logical-mathematical 逻辑-数学\n\n[^1]: X note.\n')
    out, _ = run(src, None)
    assert out == ['- First item.', '- Second x<small>1</small>.',
                   '<aside class="footnote">1. X note.</aside>',
                   '1. Linguistic', '2. Logical-mathematical']


def test_tables_hints_rules_and_links_removed():
    src = ('> <table>\n>   <tr><td>合作</td></tr>\n> </table>\n\n<hr>\n\n'
           '{% hint style="info" %}\n译者注\n{% endhint %}\n\n'
           'Visit [the site](http://x.com) for \\$5.\n\n> Huckleberry Finn ～ Twain\n')
    out, _ = run(src, None)
    assert out == ['Visit the site for $5.', '> Huckleberry Finn ~ Twain']


def test_styled_paragraph_keeps_english_lines():
    src = ('<p style="text-align: center;">\nTo my kids,<br>\nwith love.<br>\n<br>\n'
           '献给我的孩子们，<br>\n</p>\n')
    out, _ = run(src, None)
    assert out == ['To my kids,', 'with love.']


def test_chinese_attribution_and_repeated_rating_dropped():
    src = ('"Read it."\n\n—Steve Jackson\n\n“读吧。”\n\n——史蒂夫\n\n<hr>\n\n'
           'One of "Five Books"\n\n—1up.com\n\n“五本书”之一\n\n——1up.com\n\n'
           '⭐️⭐️⭐️\n\n—Midwest Book Review\n\n⭐️⭐️⭐️\n')
    out, _ = run(src, None)
    assert out == ['"Read it."', '—Steve Jackson', 'One of "Five Books"', '—1up.com',
                   '⭐️⭐️⭐️', '—Midwest Book Review']
