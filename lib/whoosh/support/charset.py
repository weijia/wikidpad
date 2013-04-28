# coding=utf-8

"""This module contains tools for working with Sphinx charset table files. These files
are useful for doing case and accent folding.
See :class:`whoosh.analysis.CharsetTokenizer` and :class:`whoosh.analysis.CharsetFilter`.
"""

from collections import defaultdict
from itertools import izip
import re

# This is a straightforward accent-folding charset taken from Carlos Bueno's
# article "Accent Folding for Auto-Complete", for use with CharsetFilter.
# 
# http://www.alistapart.com/articles/accent-folding-for-auto-complete/
#
# See the article for information and caveats. The code is lifted directly
# from here:
# 
# http://github.com/aristus/accent-folding/blob/master/accent_fold.py

accent_map = {u'ẚ':u'a',u'Á':u'a',u'á':u'a',u'À':u'a',u'à':u'a',u'Ă':u'a',
              u'ă':u'a',u'Ắ':u'a',u'ắ':u'a',u'Ằ':u'a',u'ằ':u'a',u'Ẵ':u'a',
              u'ẵ':u'a',u'Ẳ':u'a',u'ẳ':u'a',u'Â':u'a',u'â':u'a',u'Ấ':u'a',
              u'ấ':u'a',u'Ầ':u'a',u'ầ':u'a',u'Ẫ':u'a',u'ẫ':u'a',u'Ẩ':u'a',
              u'ẩ':u'a',u'Ǎ':u'a',u'ǎ':u'a',u'Å':u'a',u'å':u'a',u'Ǻ':u'a',
              u'ǻ':u'a',u'Ä':u'a',u'ä':u'a',u'Ǟ':u'a',u'ǟ':u'a',u'Ã':u'a',
              u'ã':u'a',u'Ȧ':u'a',u'ȧ':u'a',u'Ǡ':u'a',u'ǡ':u'a',u'Ą':u'a',
              u'ą':u'a',u'Ā':u'a',u'ā':u'a',u'Ả':u'a',u'ả':u'a',u'Ȁ':u'a',
              u'ȁ':u'a',u'Ȃ':u'a',u'ȃ':u'a',u'Ạ':u'a',u'ạ':u'a',u'Ặ':u'a',
              u'ặ':u'a',u'Ậ':u'a',u'ậ':u'a',u'Ḁ':u'a',u'ḁ':u'a',u'Ⱥ':u'a',
              u'ⱥ':u'a',u'Ǽ':u'a',u'ǽ':u'a',u'Ǣ':u'a',u'ǣ':u'a',u'Ḃ':u'b',
              u'ḃ':u'b',u'Ḅ':u'b',u'ḅ':u'b',u'Ḇ':u'b',u'ḇ':u'b',u'Ƀ':u'b',
              u'ƀ':u'b',u'ᵬ':u'b',u'Ɓ':u'b',u'ɓ':u'b',u'Ƃ':u'b',u'ƃ':u'b',
              u'Ć':u'c',u'ć':u'c',u'Ĉ':u'c',u'ĉ':u'c',u'Č':u'c',u'č':u'c',
              u'Ċ':u'c',u'ċ':u'c',u'Ç':u'c',u'ç':u'c',u'Ḉ':u'c',u'ḉ':u'c',
              u'Ȼ':u'c',u'ȼ':u'c',u'Ƈ':u'c',u'ƈ':u'c',u'ɕ':u'c',u'Ď':u'd',
              u'ď':u'd',u'Ḋ':u'd',u'ḋ':u'd',u'Ḑ':u'd',u'ḑ':u'd',u'Ḍ':u'd',
              u'ḍ':u'd',u'Ḓ':u'd',u'ḓ':u'd',u'Ḏ':u'd',u'ḏ':u'd',u'Đ':u'd',
              u'đ':u'd',u'ᵭ':u'd',u'Ɖ':u'd',u'ɖ':u'd',u'Ɗ':u'd',u'ɗ':u'd',
              u'Ƌ':u'd',u'ƌ':u'd',u'ȡ':u'd',u'ð':u'd',u'É':u'e',u'Ə':u'e',
              u'Ǝ':u'e',u'ǝ':u'e',u'é':u'e',u'È':u'e',u'è':u'e',u'Ĕ':u'e',
              u'ĕ':u'e',u'Ê':u'e',u'ê':u'e',u'Ế':u'e',u'ế':u'e',u'Ề':u'e',
              u'ề':u'e',u'Ễ':u'e',u'ễ':u'e',u'Ể':u'e',u'ể':u'e',u'Ě':u'e',
              u'ě':u'e',u'Ë':u'e',u'ë':u'e',u'Ẽ':u'e',u'ẽ':u'e',u'Ė':u'e',
              u'ė':u'e',u'Ȩ':u'e',u'ȩ':u'e',u'Ḝ':u'e',u'ḝ':u'e',u'Ę':u'e',
              u'ę':u'e',u'Ē':u'e',u'ē':u'e',u'Ḗ':u'e',u'ḗ':u'e',u'Ḕ':u'e',
              u'ḕ':u'e',u'Ẻ':u'e',u'ẻ':u'e',u'Ȅ':u'e',u'ȅ':u'e',u'Ȇ':u'e',
              u'ȇ':u'e',u'Ẹ':u'e',u'ẹ':u'e',u'Ệ':u'e',u'ệ':u'e',u'Ḙ':u'e',
              u'ḙ':u'e',u'Ḛ':u'e',u'ḛ':u'e',u'Ɇ':u'e',u'ɇ':u'e',u'ɚ':u'e',
              u'ɝ':u'e',u'Ḟ':u'f',u'ḟ':u'f',u'ᵮ':u'f',u'Ƒ':u'f',u'ƒ':u'f',
              u'Ǵ':u'g',u'ǵ':u'g',u'Ğ':u'g',u'ğ':u'g',u'Ĝ':u'g',u'ĝ':u'g',
              u'Ǧ':u'g',u'ǧ':u'g',u'Ġ':u'g',u'ġ':u'g',u'Ģ':u'g',u'ģ':u'g',
              u'Ḡ':u'g',u'ḡ':u'g',u'Ǥ':u'g',u'ǥ':u'g',u'Ɠ':u'g',u'ɠ':u'g',
              u'Ĥ':u'h',u'ĥ':u'h',u'Ȟ':u'h',u'ȟ':u'h',u'Ḧ':u'h',u'ḧ':u'h',
              u'Ḣ':u'h',u'ḣ':u'h',u'Ḩ':u'h',u'ḩ':u'h',u'Ḥ':u'h',u'ḥ':u'h',
              u'Ḫ':u'h',u'ḫ':u'h',u'H':u'h',u'̱':u'h',u'ẖ':u'h',u'Ħ':u'h',
              u'ħ':u'h',u'Ⱨ':u'h',u'ⱨ':u'h',u'Í':u'i',u'í':u'i',u'Ì':u'i',
              u'ì':u'i',u'Ĭ':u'i',u'ĭ':u'i',u'Î':u'i',u'î':u'i',u'Ǐ':u'i',
              u'ǐ':u'i',u'Ï':u'i',u'ï':u'i',u'Ḯ':u'i',u'ḯ':u'i',u'Ĩ':u'i',
              u'ĩ':u'i',u'İ':u'i',u'i':u'i',u'Į':u'i',u'į':u'i',u'Ī':u'i',
              u'ī':u'i',u'Ỉ':u'i',u'ỉ':u'i',u'Ȉ':u'i',u'ȉ':u'i',u'Ȋ':u'i',
              u'ȋ':u'i',u'Ị':u'i',u'ị':u'i',u'Ḭ':u'i',u'ḭ':u'i',u'I':u'i',
              u'ı':u'i',u'Ɨ':u'i',u'ɨ':u'i',u'Ĵ':u'j',u'ĵ':u'j',u'J':u'j',
              u'̌':u'j',u'ǰ':u'j',u'ȷ':u'j',u'Ɉ':u'j',u'ɉ':u'j',u'ʝ':u'j',
              u'ɟ':u'j',u'ʄ':u'j',u'Ḱ':u'k',u'ḱ':u'k',u'Ǩ':u'k',u'ǩ':u'k',
              u'Ķ':u'k',u'ķ':u'k',u'Ḳ':u'k',u'ḳ':u'k',u'Ḵ':u'k',u'ḵ':u'k',
              u'Ƙ':u'k',u'ƙ':u'k',u'Ⱪ':u'k',u'ⱪ':u'k',u'Ĺ':u'a',u'ĺ':u'l',
              u'Ľ':u'l',u'ľ':u'l',u'Ļ':u'l',u'ļ':u'l',u'Ḷ':u'l',u'ḷ':u'l',
              u'Ḹ':u'l',u'ḹ':u'l',u'Ḽ':u'l',u'ḽ':u'l',u'Ḻ':u'l',u'ḻ':u'l',
              u'Ł':u'l',u'ł':u'l',u'Ł':u'l',u'̣':u'l',u'ł':u'l',u'̣':u'l',
              u'Ŀ':u'l',u'ŀ':u'l',u'Ƚ':u'l',u'ƚ':u'l',u'Ⱡ':u'l',u'ⱡ':u'l',
              u'Ɫ':u'l',u'ɫ':u'l',u'ɬ':u'l',u'ɭ':u'l',u'ȴ':u'l',u'Ḿ':u'm',
              u'ḿ':u'm',u'Ṁ':u'm',u'ṁ':u'm',u'Ṃ':u'm',u'ṃ':u'm',u'ɱ':u'm',
              u'Ń':u'n',u'ń':u'n',u'Ǹ':u'n',u'ǹ':u'n',u'Ň':u'n',u'ň':u'n',
              u'Ñ':u'n',u'ñ':u'n',u'Ṅ':u'n',u'ṅ':u'n',u'Ņ':u'n',u'ņ':u'n',
              u'Ṇ':u'n',u'ṇ':u'n',u'Ṋ':u'n',u'ṋ':u'n',u'Ṉ':u'n',u'ṉ':u'n',
              u'Ɲ':u'n',u'ɲ':u'n',u'Ƞ':u'n',u'ƞ':u'n',u'ɳ':u'n',u'ȵ':u'n',
              u'N':u'n',u'̈':u'n',u'n':u'n',u'̈':u'n',u'Ó':u'o',u'ó':u'o',
              u'Ò':u'o',u'ò':u'o',u'Ŏ':u'o',u'ŏ':u'o',u'Ô':u'o',u'ô':u'o',
              u'Ố':u'o',u'ố':u'o',u'Ồ':u'o',u'ồ':u'o',u'Ỗ':u'o',u'ỗ':u'o',
              u'Ổ':u'o',u'ổ':u'o',u'Ǒ':u'o',u'ǒ':u'o',u'Ö':u'o',u'ö':u'o',
              u'Ȫ':u'o',u'ȫ':u'o',u'Ő':u'o',u'ő':u'o',u'Õ':u'o',u'õ':u'o',
              u'Ṍ':u'o',u'ṍ':u'o',u'Ṏ':u'o',u'ṏ':u'o',u'Ȭ':u'o',u'ȭ':u'o',
              u'Ȯ':u'o',u'ȯ':u'o',u'Ȱ':u'o',u'ȱ':u'o',u'Ø':u'o',u'ø':u'o',
              u'Ǿ':u'o',u'ǿ':u'o',u'Ǫ':u'o',u'ǫ':u'o',u'Ǭ':u'o',u'ǭ':u'o',
              u'Ō':u'o',u'ō':u'o',u'Ṓ':u'o',u'ṓ':u'o',u'Ṑ':u'o',u'ṑ':u'o',
              u'Ỏ':u'o',u'ỏ':u'o',u'Ȍ':u'o',u'ȍ':u'o',u'Ȏ':u'o',u'ȏ':u'o',
              u'Ơ':u'o',u'ơ':u'o',u'Ớ':u'o',u'ớ':u'o',u'Ờ':u'o',u'ờ':u'o',
              u'Ỡ':u'o',u'ỡ':u'o',u'Ở':u'o',u'ở':u'o',u'Ợ':u'o',u'ợ':u'o',
              u'Ọ':u'o',u'ọ':u'o',u'Ộ':u'o',u'ộ':u'o',u'Ɵ':u'o',u'ɵ':u'o',
              u'Ṕ':u'p',u'ṕ':u'p',u'Ṗ':u'p',u'ṗ':u'p',u'Ᵽ':u'p',u'Ƥ':u'p',
              u'ƥ':u'p',u'P':u'p',u'̃':u'p',u'p':u'p',u'̃':u'p',u'ʠ':u'q',
              u'Ɋ':u'q',u'ɋ':u'q',u'Ŕ':u'r',u'ŕ':u'r',u'Ř':u'r',u'ř':u'r',
              u'Ṙ':u'r',u'ṙ':u'r',u'Ŗ':u'r',u'ŗ':u'r',u'Ȑ':u'r',u'ȑ':u'r',
              u'Ȓ':u'r',u'ȓ':u'r',u'Ṛ':u'r',u'ṛ':u'r',u'Ṝ':u'r',u'ṝ':u'r',
              u'Ṟ':u'r',u'ṟ':u'r',u'Ɍ':u'r',u'ɍ':u'r',u'ᵲ':u'r',u'ɼ':u'r',
              u'Ɽ':u'r',u'ɽ':u'r',u'ɾ':u'r',u'ᵳ':u'r',u'ß':u's',u'Ś':u's',
              u'ś':u's',u'Ṥ':u's',u'ṥ':u's',u'Ŝ':u's',u'ŝ':u's',u'Š':u's',
              u'š':u's',u'Ṧ':u's',u'ṧ':u's',u'Ṡ':u's',u'ṡ':u's',u'ẛ':u's',
              u'Ş':u's',u'ş':u's',u'Ṣ':u's',u'ṣ':u's',u'Ṩ':u's',u'ṩ':u's',
              u'Ș':u's',u'ș':u's',u'ʂ':u's',u'S':u's',u'̩':u's',u's':u's',
              u'̩':u's',u'Þ':u't',u'þ':u't',u'Ť':u't',u'ť':u't',u'T':u't',
              u'̈':u't',u'ẗ':u't',u'Ṫ':u't',u'ṫ':u't',u'Ţ':u't',u'ţ':u't',
              u'Ṭ':u't',u'ṭ':u't',u'Ț':u't',u'ț':u't',u'Ṱ':u't',u'ṱ':u't',
              u'Ṯ':u't',u'ṯ':u't',u'Ŧ':u't',u'ŧ':u't',u'Ⱦ':u't',u'ⱦ':u't',
              u'ᵵ':u't',u'ƫ':u't',u'Ƭ':u't',u'ƭ':u't',u'Ʈ':u't',u'ʈ':u't',
              u'ȶ':u't',u'Ú':u'u',u'ú':u'u',u'Ù':u'u',u'ù':u'u',u'Ŭ':u'u',
              u'ŭ':u'u',u'Û':u'u',u'û':u'u',u'Ǔ':u'u',u'ǔ':u'u',u'Ů':u'u',
              u'ů':u'u',u'Ü':u'u',u'ü':u'u',u'Ǘ':u'u',u'ǘ':u'u',u'Ǜ':u'u',
              u'ǜ':u'u',u'Ǚ':u'u',u'ǚ':u'u',u'Ǖ':u'u',u'ǖ':u'u',u'Ű':u'u',
              u'ű':u'u',u'Ũ':u'u',u'ũ':u'u',u'Ṹ':u'u',u'ṹ':u'u',u'Ų':u'u',
              u'ų':u'u',u'Ū':u'u',u'ū':u'u',u'Ṻ':u'u',u'ṻ':u'u',u'Ủ':u'u',
              u'ủ':u'u',u'Ȕ':u'u',u'ȕ':u'u',u'Ȗ':u'u',u'ȗ':u'u',u'Ư':u'u',
              u'ư':u'u',u'Ứ':u'u',u'ứ':u'u',u'Ừ':u'u',u'ừ':u'u',u'Ữ':u'u',
              u'ữ':u'u',u'Ử':u'u',u'ử':u'u',u'Ự':u'u',u'ự':u'u',u'Ụ':u'u',
              u'ụ':u'u',u'Ṳ':u'u',u'ṳ':u'u',u'Ṷ':u'u',u'ṷ':u'u',u'Ṵ':u'u',
              u'ṵ':u'u',u'Ʉ':u'u',u'ʉ':u'u',u'Ṽ':u'v',u'ṽ':u'v',u'Ṿ':u'v',
              u'ṿ':u'v',u'Ʋ':u'v',u'ʋ':u'v',u'Ẃ':u'w',u'ẃ':u'w',u'Ẁ':u'w',
              u'ẁ':u'w',u'Ŵ':u'w',u'ŵ':u'w',u'W':u'w',u'̊':u'w',u'ẘ':u'w',
              u'Ẅ':u'w',u'ẅ':u'w',u'Ẇ':u'w',u'ẇ':u'w',u'Ẉ':u'w',u'ẉ':u'w',
              u'Ẍ':u'x',u'ẍ':u'x',u'Ẋ':u'x',u'ẋ':u'x',u'Ý':u'y',u'ý':u'y',
              u'Ỳ':u'y',u'ỳ':u'y',u'Ŷ':u'y',u'ŷ':u'y',u'Y':u'y',u'̊':u'y',
              u'ẙ':u'y',u'Ÿ':u'y',u'ÿ':u'y',u'Ỹ':u'y',u'ỹ':u'y',u'Ẏ':u'y',
              u'ẏ':u'y',u'Ȳ':u'y',u'ȳ':u'y',u'Ỷ':u'y',u'ỷ':u'y',u'Ỵ':u'y',
              u'ỵ':u'y',u'ʏ':u'y',u'Ɏ':u'y',u'ɏ':u'y',u'Ƴ':u'y',u'ƴ':u'y',
              u'Ź':u'z',u'ź':u'z',u'Ẑ':u'z',u'ẑ':u'z',u'Ž':u'z',u'ž':u'z',
              u'Ż':u'z',u'ż':u'z',u'Ẓ':u'z',u'ẓ':u'z',u'Ẕ':u'z',u'ẕ':u'z',
              u'Ƶ':u'z',u'ƶ':u'z',u'Ȥ':u'z',u'ȥ':u'z',u'ʐ':u'z',u'ʑ':u'z',
              u'Ⱬ':u'z',u'ⱬ':u'z',u'Ǯ':u'z',u'ǯ':u'z',u'ƺ':u'z',u'２':u'2',
              u'６':u'6',u'Ｂ':u'B',u'Ｆ':u'F',u'Ｊ':u'J',u'Ｎ':u'N',u'Ｒ':u'R',
              u'Ｖ':u'V',u'Ｚ':u'Z',u'ｂ':u'b',u'ｆ':u'f',u'ｊ':u'j',u'ｎ':u'n',
              u'ｒ':u'r',u'ｖ':u'v',u'ｚ':u'z',u'１':u'1',u'５':u'5',u'９':u'9',
              u'Ａ':u'A',u'Ｅ':u'E',u'Ｉ':u'I',u'Ｍ':u'M',u'Ｑ':u'Q',u'Ｕ':u'U',
              u'Ｙ':u'Y',u'ａ':u'a',u'ｅ':u'e',u'ｉ':u'i',u'ｍ':u'm',u'ｑ':u'q',
              u'ｕ':u'u',u'ｙ':u'y',u'０':u'0',u'４':u'4',u'８':u'8',u'Ｄ':u'D',
              u'Ｈ':u'H',u'Ｌ':u'L',u'Ｐ':u'P',u'Ｔ':u'T',u'Ｘ':u'X',u'ｄ':u'd',
              u'ｈ':u'h',u'ｌ':u'l',u'ｐ':u'p',u'ｔ':u't',u'ｘ':u'x',u'３':u'3',
              u'７':u'7',u'Ｃ':u'C',u'Ｇ':u'G',u'Ｋ':u'K',u'Ｏ':u'O',u'Ｓ':u'S',
              u'Ｗ':u'W',u'ｃ':u'c',u'ｇ':u'g',u'ｋ':u'k',u'ｏ':u'o',u'ｓ':u's',
              u'ｗ':u'w'};
# The unicode.translate() method actually requires a dictionary mapping
# character *numbers* to characters, for some reason.
accent_map = dict((ord(k), v) for k, v in accent_map.iteritems())


# This Sphinx charset table taken from http://speeple.com/unicode-maps.txt

default_charset = """
##################################################
# Latin
# A
U+00C0->a, U+00C1->a, U+00C2->a, U+00C3->a, U+00C4->a, U+00C5->a, U+00E0->a, U+00E1->a, U+00E2->a, U+00E3->a, U+00E4->a, U+00E5->a,
U+0100->a, U+0101->a, U+0102->a, U+0103->a, U+010300->a, U+0104->a, U+0105->a, U+01CD->a, U+01CE->a, U+01DE->a, U+01DF->a, U+01E0->a,
U+01E1->a, U+01FA->a, U+01FB->a, U+0200->a, U+0201->a, U+0202->a, U+0203->a, U+0226->a, U+0227->a, U+023A->a, U+0250->a, U+04D0->a,
U+04D1->a, U+1D2C->a, U+1D43->a, U+1D44->a, U+1D8F->a, U+1E00->a, U+1E01->a, U+1E9A->a, U+1EA0->a, U+1EA1->a, U+1EA2->a, U+1EA3->a,
U+1EA4->a, U+1EA5->a, U+1EA6->a, U+1EA7->a, U+1EA8->a, U+1EA9->a, U+1EAA->a, U+1EAB->a, U+1EAC->a, U+1EAD->a, U+1EAE->a, U+1EAF->a,
U+1EB0->a, U+1EB1->a, U+1EB2->a, U+1EB3->a, U+1EB4->a, U+1EB5->a, U+1EB6->a, U+1EB7->a, U+2090->a, U+2C65->a

# B
U+0180->b, U+0181->b, U+0182->b, U+0183->b, U+0243->b, U+0253->b, U+0299->b, U+16D2->b, U+1D03->b, U+1D2E->b, U+1D2F->b, U+1D47->b,
U+1D6C->b, U+1D80->b, U+1E02->b, U+1E03->b, U+1E04->b, U+1E05->b, U+1E06->b, U+1E07->b

# C
U+00C7->c, U+00E7->c, U+0106->c, U+0107->c, U+0108->c, U+0109->c, U+010A->c, U+010B->c, U+010C->c, U+010D->c, U+0187->c, U+0188->c,
U+023B->c, U+023C->c, U+0255->c, U+0297->c, U+1D9C->c, U+1D9D->c, U+1E08->c, U+1E09->c, U+212D->c, U+2184->c

# D
U+010E->d, U+010F->d, U+0110->d, U+0111->d, U+0189->d, U+018A->d, U+018B->d, U+018C->d, U+01C5->d, U+01F2->d, U+0221->d, U+0256->d,
U+0257->d, U+1D05->d, U+1D30->d, U+1D48->d, U+1D6D->d, U+1D81->d, U+1D91->d, U+1E0A->d, U+1E0B->d, U+1E0C->d, U+1E0D->d, U+1E0E->d,
U+1E0F->d, U+1E10->d, U+1E11->d, U+1E12->d, U+1E13->d

# E
U+00C8->e, U+00C9->e, U+00CA->e, U+00CB->e, U+00E8->e, U+00E9->e, U+00EA->e, U+00EB->e, U+0112->e, U+0113->e, U+0114->e, U+0115->e,
U+0116->e, U+0117->e, U+0118->e, U+0119->e, U+011A->e, U+011B->e, U+018E->e, U+0190->e, U+01DD->e, U+0204->e, U+0205->e, U+0206->e,
U+0207->e, U+0228->e, U+0229->e, U+0246->e, U+0247->e, U+0258->e, U+025B->e, U+025C->e, U+025D->e, U+025E->e, U+029A->e, U+1D07->e,
U+1D08->e, U+1D31->e, U+1D32->e, U+1D49->e, U+1D4B->e, U+1D4C->e, U+1D92->e, U+1D93->e, U+1D94->e, U+1D9F->e, U+1E14->e, U+1E15->e,
U+1E16->e, U+1E17->e, U+1E18->e, U+1E19->e, U+1E1A->e, U+1E1B->e, U+1E1C->e, U+1E1D->e, U+1EB8->e, U+1EB9->e, U+1EBA->e, U+1EBB->e,
U+1EBC->e, U+1EBD->e, U+1EBE->e, U+1EBF->e, U+1EC0->e, U+1EC1->e, U+1EC2->e, U+1EC3->e, U+1EC4->e, U+1EC5->e, U+1EC6->e, U+1EC7->e,
U+2091->e

# F
U+0191->f, U+0192->f, U+1D6E->f, U+1D82->f, U+1DA0->f, U+1E1E->f, U+1E1F->f

# G
U+011C->g, U+011D->g, U+011E->g, U+011F->g, U+0120->g, U+0121->g, U+0122->g, U+0123->g, U+0193->g, U+01E4->g, U+01E5->g, U+01E6->g,
U+01E7->g, U+01F4->g, U+01F5->g, U+0260->g, U+0261->g, U+0262->g, U+029B->g, U+1D33->g, U+1D4D->g, U+1D77->g, U+1D79->g, U+1D83->g,
U+1DA2->g, U+1E20->g, U+1E21->g

# H
U+0124->h, U+0125->h, U+0126->h, U+0127->h, U+021E->h, U+021F->h, U+0265->h, U+0266->h, U+029C->h, U+02AE->h, U+02AF->h, U+02B0->h,
U+02B1->h, U+1D34->h, U+1DA3->h, U+1E22->h, U+1E23->h, U+1E24->h, U+1E25->h, U+1E26->h, U+1E27->h, U+1E28->h, U+1E29->h, U+1E2A->h,
U+1E2B->h, U+1E96->h, U+210C->h, U+2C67->h, U+2C68->h, U+2C75->h, U+2C76->h

# I
U+00CC->i, U+00CD->i, U+00CE->i, U+00CF->i, U+00EC->i, U+00ED->i, U+00EE->i, U+00EF->i, U+010309->i, U+0128->i, U+0129->i, U+012A->i,
U+012B->i, U+012C->i, U+012D->i, U+012E->i, U+012F->i, U+0130->i, U+0131->i, U+0197->i, U+01CF->i, U+01D0->i, U+0208->i, U+0209->i,
U+020A->i, U+020B->i, U+0268->i, U+026A->i, U+040D->i, U+0418->i, U+0419->i, U+0438->i, U+0439->i, U+0456->i, U+1D09->i, U+1D35->i,
U+1D4E->i, U+1D62->i, U+1D7B->i, U+1D96->i, U+1DA4->i, U+1DA6->i, U+1DA7->i, U+1E2C->i, U+1E2D->i, U+1E2E->i, U+1E2F->i, U+1EC8->i,
U+1EC9->i, U+1ECA->i, U+1ECB->i, U+2071->i, U+2111->i

# J
U+0134->j, U+0135->j, U+01C8->j, U+01CB->j, U+01F0->j, U+0237->j, U+0248->j, U+0249->j, U+025F->j, U+0284->j, U+029D->j, U+02B2->j,
U+1D0A->j, U+1D36->j, U+1DA1->j, U+1DA8->j

# K
U+0136->k, U+0137->k, U+0198->k, U+0199->k, U+01E8->k, U+01E9->k, U+029E->k, U+1D0B->k, U+1D37->k, U+1D4F->k, U+1D84->k, U+1E30->k,
U+1E31->k, U+1E32->k, U+1E33->k, U+1E34->k, U+1E35->k, U+2C69->k, U+2C6A->k

# L
U+0139->l, U+013A->l, U+013B->l, U+013C->l, U+013D->l, U+013E->l, U+013F->l, U+0140->l, U+0141->l, U+0142->l, U+019A->l, U+01C8->l,
U+0234->l, U+023D->l, U+026B->l, U+026C->l, U+026D->l, U+029F->l, U+02E1->l, U+1D0C->l, U+1D38->l, U+1D85->l, U+1DA9->l, U+1DAA->l,
U+1DAB->l, U+1E36->l, U+1E37->l, U+1E38->l, U+1E39->l, U+1E3A->l, U+1E3B->l, U+1E3C->l, U+1E3D->l, U+2C60->l, U+2C61->l, U+2C62->l

# M
U+019C->m, U+026F->m, U+0270->m, U+0271->m, U+1D0D->m, U+1D1F->m, U+1D39->m, U+1D50->m, U+1D5A->m, U+1D6F->m, U+1D86->m, U+1DAC->m,
U+1DAD->m, U+1E3E->m, U+1E3F->m, U+1E40->m, U+1E41->m, U+1E42->m, U+1E43->m

# N
U+00D1->n, U+00F1->n, U+0143->n, U+0144->n, U+0145->n, U+0146->n, U+0147->n, U+0148->n, U+0149->n, U+019D->n, U+019E->n, U+01CB->n,
U+01F8->n, U+01F9->n, U+0220->n, U+0235->n, U+0272->n, U+0273->n, U+0274->n, U+1D0E->n, U+1D3A->n, U+1D3B->n, U+1D70->n, U+1D87->n,
U+1DAE->n, U+1DAF->n, U+1DB0->n, U+1E44->n, U+1E45->n, U+1E46->n, U+1E47->n, U+1E48->n, U+1E49->n, U+1E4A->n, U+1E4B->n, U+207F->n

# O
U+00D2->o, U+00D3->o, U+00D4->o, U+00D5->o, U+00D6->o, U+00D8->o, U+00F2->o, U+00F3->o, U+00F4->o, U+00F5->o, U+00F6->o, U+00F8->o,
U+01030F->o, U+014C->o, U+014D->o, U+014E->o, U+014F->o, U+0150->o, U+0151->o, U+0186->o, U+019F->o, U+01A0->o, U+01A1->o, U+01D1->o,
U+01D2->o, U+01EA->o, U+01EB->o, U+01EC->o, U+01ED->o, U+01FE->o, U+01FF->o, U+020C->o, U+020D->o, U+020E->o, U+020F->o, U+022A->o,
U+022B->o, U+022C->o, U+022D->o, U+022E->o, U+022F->o, U+0230->o, U+0231->o, U+0254->o, U+0275->o, U+043E->o, U+04E6->o, U+04E7->o,
U+04E8->o, U+04E9->o, U+04EA->o, U+04EB->o, U+1D0F->o, U+1D10->o, U+1D11->o, U+1D12->o, U+1D13->o, U+1D16->o, U+1D17->o, U+1D3C->o,
U+1D52->o, U+1D53->o, U+1D54->o, U+1D55->o, U+1D97->o, U+1DB1->o, U+1E4C->o, U+1E4D->o, U+1E4E->o, U+1E4F->o, U+1E50->o, U+1E51->o,
U+1E52->o, U+1E53->o, U+1ECC->o, U+1ECD->o, U+1ECE->o, U+1ECF->o, U+1ED0->o, U+1ED1->o, U+1ED2->o, U+1ED3->o, U+1ED4->o, U+1ED5->o,
U+1ED6->o, U+1ED7->o, U+1ED8->o, U+1ED9->o, U+1EDA->o, U+1EDB->o, U+1EDC->o, U+1EDD->o, U+1EDE->o, U+1EDF->o, U+1EE0->o, U+1EE1->o,
U+1EE2->o, U+1EE3->o, U+2092->o, U+2C9E->o, U+2C9F->o

# P
U+01A4->p, U+01A5->p, U+1D18->p, U+1D3E->p, U+1D56->p, U+1D71->p, U+1D7D->p, U+1D88->p, U+1E54->p, U+1E55->p, U+1E56->p, U+1E57->p,
U+2C63->p

# Q
U+024A->q, U+024B->q, U+02A0->q

# R
U+0154->r, U+0155->r, U+0156->r, U+0157->r, U+0158->r, U+0159->r, U+0210->r, U+0211->r, U+0212->r, U+0213->r, U+024C->r, U+024D->r,
U+0279->r, U+027A->r, U+027B->r, U+027C->r, U+027D->r, U+027E->r, U+027F->r, U+0280->r, U+0281->r, U+02B3->r, U+02B4->r, U+02B5->r,
U+02B6->r, U+1D19->r, U+1D1A->r, U+1D3F->r, U+1D63->r, U+1D72->r, U+1D73->r, U+1D89->r, U+1DCA->r, U+1E58->r, U+1E59->r, U+1E5A->r,
U+1E5B->r, U+1E5C->r, U+1E5D->r, U+1E5E->r, U+1E5F->r, U+211C->r, U+2C64->r

# S
U+00DF->s, U+015A->s, U+015B->s, U+015C->s, U+015D->s, U+015E->s, U+015F->s, U+0160->s, U+0161->s, U+017F->s, U+0218->s, U+0219->s,
U+023F->s, U+0282->s, U+02E2->s, U+1D74->s, U+1D8A->s, U+1DB3->s, U+1E60->s, U+1E61->s, U+1E62->s, U+1E63->s, U+1E64->s, U+1E65->s,
U+1E66->s, U+1E67->s, U+1E68->s, U+1E69->s, U+1E9B->s

# T
U+0162->t, U+0163->t, U+0164->t, U+0165->t, U+0166->t, U+0167->t, U+01AB->t, U+01AC->t, U+01AD->t, U+01AE->t, U+021A->t, U+021B->t,
U+0236->t, U+023E->t, U+0287->t, U+0288->t, U+1D1B->t, U+1D40->t, U+1D57->t, U+1D75->t, U+1DB5->t, U+1E6A->t, U+1E6B->t, U+1E6C->t,
U+1E6D->t, U+1E6E->t, U+1E6F->t, U+1E70->t, U+1E71->t, U+1E97->t, U+2C66->t

# U
U+00D9->u, U+00DA->u, U+00DB->u, U+00DC->u, U+00F9->u, U+00FA->u, U+00FB->u, U+00FC->u, U+010316->u, U+0168->u, U+0169->u, U+016A->u,
U+016B->u, U+016C->u, U+016D->u, U+016E->u, U+016F->u, U+0170->u, U+0171->u, U+0172->u, U+0173->u, U+01AF->u, U+01B0->u, U+01D3->u,
U+01D4->u, U+01D5->u, U+01D6->u, U+01D7->u, U+01D8->u, U+01D9->u, U+01DA->u, U+01DB->u, U+01DC->u, U+0214->u, U+0215->u, U+0216->u,
U+0217->u, U+0244->u, U+0289->u, U+1D1C->u, U+1D1D->u, U+1D1E->u, U+1D41->u, U+1D58->u, U+1D59->u, U+1D64->u, U+1D7E->u, U+1D99->u,
U+1DB6->u, U+1DB8->u, U+1E72->u, U+1E73->u, U+1E74->u, U+1E75->u, U+1E76->u, U+1E77->u, U+1E78->u, U+1E79->u, U+1E7A->u, U+1E7B->u,
U+1EE4->u, U+1EE5->u, U+1EE6->u, U+1EE7->u, U+1EE8->u, U+1EE9->u, U+1EEA->u, U+1EEB->u, U+1EEC->u, U+1EED->u, U+1EEE->u, U+1EEF->u,
U+1EF0->u, U+1EF1->u

# V
U+01B2->v, U+0245->v, U+028B->v, U+028C->v, U+1D20->v, U+1D5B->v, U+1D65->v, U+1D8C->v, U+1DB9->v, U+1DBA->v, U+1E7C->v, U+1E7D->v,
U+1E7E->v, U+1E7F->v, U+2C74->v

# W
U+0174->w, U+0175->w, U+028D->w, U+02B7->w, U+1D21->w, U+1D42->w, U+1E80->w, U+1E81->w, U+1E82->w, U+1E83->w, U+1E84->w, U+1E85->w,
U+1E86->w, U+1E87->w, U+1E88->w, U+1E89->w, U+1E98->w

# X
U+02E3->x, U+1D8D->x, U+1E8A->x, U+1E8B->x, U+1E8C->x, U+1E8D->x, U+2093->x

# Y
U+00DD->y, U+00FD->y, U+00FF->y, U+0176->y, U+0177->y, U+0178->y, U+01B3->y, U+01B4->y, U+0232->y, U+0233->y, U+024E->y, U+024F->y,
U+028E->y, U+028F->y, U+02B8->y, U+1E8E->y, U+1E8F->y, U+1E99->y, U+1EF2->y, U+1EF3->y, U+1EF4->y, U+1EF5->y, U+1EF6->y, U+1EF7->y,
U+1EF8->y, U+1EF9->y

# Z
U+0179->z, U+017A->z, U+017B->z, U+017C->z, U+017D->z, U+017E->z, U+01B5->z, U+01B6->z, U+0224->z, U+0225->z, U+0240->z, U+0290->z,
U+0291->z, U+1D22->z, U+1D76->z, U+1D8E->z, U+1DBB->z, U+1DBC->z, U+1DBD->z, U+1E90->z, U+1E91->z, U+1E92->z, U+1E93->z, U+1E94->z,
U+1E95->z, U+2128->z, U+2C6B->z, U+2C6C->z

# Latin Extras:
U+00C6->U+00E6, U+01E2->U+00E6, U+01E3->U+00E6, U+01FC->U+00E6, U+01FD->U+00E6, U+1D01->U+00E6, U+1D02->U+00E6, U+1D2D->U+00E6,
U+1D46->U+00E6, U+00E6

##################################################
# Arabic
U+0622->U+0627, U+0623->U+0627, U+0624->U+0648, U+0625->U+0627, U+0626->U+064A, U+06C0->U+06D5, U+06C2->U+06C1, U+06D3->U+06D2,
U+FB50->U+0671, U+FB51->U+0671, U+FB52->U+067B, U+FB53->U+067B, U+FB54->U+067B, U+FB56->U+067E, U+FB57->U+067E, U+FB58->U+067E,
U+FB5A->U+0680, U+FB5B->U+0680, U+FB5C->U+0680, U+FB5E->U+067A, U+FB5F->U+067A, U+FB60->U+067A, U+FB62->U+067F, U+FB63->U+067F,
U+FB64->U+067F, U+FB66->U+0679, U+FB67->U+0679, U+FB68->U+0679, U+FB6A->U+06A4, U+FB6B->U+06A4, U+FB6C->U+06A4, U+FB6E->U+06A6,
U+FB6F->U+06A6, U+FB70->U+06A6, U+FB72->U+0684, U+FB73->U+0684, U+FB74->U+0684, U+FB76->U+0683, U+FB77->U+0683, U+FB78->U+0683,
U+FB7A->U+0686, U+FB7B->U+0686, U+FB7C->U+0686, U+FB7E->U+0687, U+FB7F->U+0687, U+FB80->U+0687, U+FB82->U+068D, U+FB83->U+068D,
U+FB84->U+068C, U+FB85->U+068C, U+FB86->U+068E, U+FB87->U+068E, U+FB88->U+0688, U+FB89->U+0688, U+FB8A->U+0698, U+FB8B->U+0698,
U+FB8C->U+0691, U+FB8D->U+0691, U+FB8E->U+06A9, U+FB8F->U+06A9, U+FB90->U+06A9, U+FB92->U+06AF, U+FB93->U+06AF, U+FB94->U+06AF,
U+FB96->U+06B3, U+FB97->U+06B3, U+FB98->U+06B3, U+FB9A->U+06B1, U+FB9B->U+06B1, U+FB9C->U+06B1, U+FB9E->U+06BA, U+FB9F->U+06BA,
U+FBA0->U+06BB, U+FBA1->U+06BB, U+FBA2->U+06BB, U+FBA4->U+06C0, U+FBA5->U+06C0, U+FBA6->U+06C1, U+FBA7->U+06C1, U+FBA8->U+06C1,
U+FBAA->U+06BE, U+FBAB->U+06BE, U+FBAC->U+06BE, U+FBAE->U+06D2, U+FBAF->U+06D2, U+FBB0->U+06D3, U+FBB1->U+06D3, U+FBD3->U+06AD,
U+FBD4->U+06AD, U+FBD5->U+06AD, U+FBD7->U+06C7, U+FBD8->U+06C7, U+FBD9->U+06C6, U+FBDA->U+06C6, U+FBDB->U+06C8, U+FBDC->U+06C8,
U+FBDD->U+0677, U+FBDE->U+06CB, U+FBDF->U+06CB, U+FBE0->U+06C5, U+FBE1->U+06C5, U+FBE2->U+06C9, U+FBE3->U+06C9, U+FBE4->U+06D0,
U+FBE5->U+06D0, U+FBE6->U+06D0, U+FBE8->U+0649, U+FBFC->U+06CC, U+FBFD->U+06CC, U+FBFE->U+06CC, U+0621, U+0627..U+063A, U+0641..U+064A,
U+0660..U+0669, U+066E, U+066F, U+0671..U+06BF, U+06C1, U+06C3..U+06D2, U+06D5, U+06EE..U+06FC, U+06FF, U+0750..U+076D, U+FB55, U+FB59,
U+FB5D, U+FB61, U+FB65, U+FB69, U+FB6D, U+FB71, U+FB75, U+FB79, U+FB7D, U+FB81, U+FB91, U+FB95, U+FB99, U+FB9D, U+FBA3, U+FBA9, U+FBAD,
U+FBD6, U+FBE7, U+FBE9, U+FBFF

##################################################
# Armenian
U+0531..U+0556->U+0561..U+0586, U+0561..U+0586, U+0587

#################################################
# Bengali
U+09DC->U+09A1, U+09DD->U+09A2, U+09DF->U+09AF, U+09F0->U+09AC, U+09F1->U+09AC, U+0985..U+0990, U+0993..U+09B0, U+09B2, U+09B6..U+09B9,
U+09CE, U+09E0, U+09E1, U+09E6..U+09EF

#################################################
# CJK*
U+F900->U+8C48, U+F901->U+66F4, U+F902->U+8ECA, U+F903->U+8CC8, U+F904->U+6ED1, U+F905->U+4E32, U+F906->U+53E5, U+F907->U+9F9C,
U+F908->U+9F9C, U+F909->U+5951, U+F90A->U+91D1, U+F90B->U+5587, U+F90C->U+5948, U+F90D->U+61F6, U+F90E->U+7669, U+F90F->U+7F85,
U+F910->U+863F, U+F911->U+87BA, U+F912->U+88F8, U+F913->U+908F, U+F914->U+6A02, U+F915->U+6D1B, U+F916->U+70D9, U+F917->U+73DE,
U+F918->U+843D, U+F919->U+916A, U+F91A->U+99F1, U+F91B->U+4E82, U+F91C->U+5375, U+F91D->U+6B04, U+F91E->U+721B, U+F91F->U+862D,
U+F920->U+9E1E, U+F921->U+5D50, U+F922->U+6FEB, U+F923->U+85CD, U+F924->U+8964, U+F925->U+62C9, U+F926->U+81D8, U+F927->U+881F,
U+F928->U+5ECA, U+F929->U+6717, U+F92A->U+6D6A, U+F92B->U+72FC, U+F92C->U+90CE, U+F92D->U+4F86, U+F92E->U+51B7, U+F92F->U+52DE,
U+F930->U+64C4, U+F931->U+6AD3, U+F932->U+7210, U+F933->U+76E7, U+F934->U+8001, U+F935->U+8606, U+F936->U+865C, U+F937->U+8DEF,
U+F938->U+9732, U+F939->U+9B6F, U+F93A->U+9DFA, U+F93B->U+788C, U+F93C->U+797F, U+F93D->U+7DA0, U+F93E->U+83C9, U+F93F->U+9304,
U+F940->U+9E7F, U+F941->U+8AD6, U+F942->U+58DF, U+F943->U+5F04, U+F944->U+7C60, U+F945->U+807E, U+F946->U+7262, U+F947->U+78CA,
U+F948->U+8CC2, U+F949->U+96F7, U+F94A->U+58D8, U+F94B->U+5C62, U+F94C->U+6A13, U+F94D->U+6DDA, U+F94E->U+6F0F, U+F94F->U+7D2F,
U+F950->U+7E37, U+F951->U+964B, U+F952->U+52D2, U+F953->U+808B, U+F954->U+51DC, U+F955->U+51CC, U+F956->U+7A1C, U+F957->U+7DBE,
U+F958->U+83F1, U+F959->U+9675, U+F95A->U+8B80, U+F95B->U+62CF, U+F95C->U+6A02, U+F95D->U+8AFE, U+F95E->U+4E39, U+F95F->U+5BE7,
U+F960->U+6012, U+F961->U+7387, U+F962->U+7570, U+F963->U+5317, U+F964->U+78FB, U+F965->U+4FBF, U+F966->U+5FA9, U+F967->U+4E0D,
U+F968->U+6CCC, U+F969->U+6578, U+F96A->U+7D22, U+F96B->U+53C3, U+F96C->U+585E, U+F96D->U+7701, U+F96E->U+8449, U+F96F->U+8AAA,
U+F970->U+6BBA, U+F971->U+8FB0, U+F972->U+6C88, U+F973->U+62FE, U+F974->U+82E5, U+F975->U+63A0, U+F976->U+7565, U+F977->U+4EAE,
U+F978->U+5169, U+F979->U+51C9, U+F97A->U+6881, U+F97B->U+7CE7, U+F97C->U+826F, U+F97D->U+8AD2, U+F97E->U+91CF, U+F97F->U+52F5,
U+F980->U+5442, U+F981->U+5973, U+F982->U+5EEC, U+F983->U+65C5, U+F984->U+6FFE, U+F985->U+792A, U+F986->U+95AD, U+F987->U+9A6A,
U+F988->U+9E97, U+F989->U+9ECE, U+F98A->U+529B, U+F98B->U+66C6, U+F98C->U+6B77, U+F98D->U+8F62, U+F98E->U+5E74, U+F98F->U+6190,
U+F990->U+6200, U+F991->U+649A, U+F992->U+6F23, U+F993->U+7149, U+F994->U+7489, U+F995->U+79CA, U+F996->U+7DF4, U+F997->U+806F,
U+F998->U+8F26, U+F999->U+84EE, U+F99A->U+9023, U+F99B->U+934A, U+F99C->U+5217, U+F99D->U+52A3, U+F99E->U+54BD, U+F99F->U+70C8,
U+F9A0->U+88C2, U+F9A1->U+8AAA, U+F9A2->U+5EC9, U+F9A3->U+5FF5, U+F9A4->U+637B, U+F9A5->U+6BAE, U+F9A6->U+7C3E, U+F9A7->U+7375,
U+F9A8->U+4EE4, U+F9A9->U+56F9, U+F9AA->U+5BE7, U+F9AB->U+5DBA, U+F9AC->U+601C, U+F9AD->U+73B2, U+F9AE->U+7469, U+F9AF->U+7F9A,
U+F9B0->U+8046, U+F9B1->U+9234, U+F9B2->U+96F6, U+F9B3->U+9748, U+F9B4->U+9818, U+F9B5->U+4F8B, U+F9B6->U+79AE, U+F9B7->U+91B4,
U+F9B8->U+96B8, U+F9B9->U+60E1, U+F9BA->U+4E86, U+F9BB->U+50DA, U+F9BC->U+5BEE, U+F9BD->U+5C3F, U+F9BE->U+6599, U+F9BF->U+6A02,
U+F9C0->U+71CE, U+F9C1->U+7642, U+F9C2->U+84FC, U+F9C3->U+907C, U+F9C4->U+9F8D, U+F9C5->U+6688, U+F9C6->U+962E, U+F9C7->U+5289,
U+F9C8->U+677B, U+F9C9->U+67F3, U+F9CA->U+6D41, U+F9CB->U+6E9C, U+F9CC->U+7409, U+F9CD->U+7559, U+F9CE->U+786B, U+F9CF->U+7D10,
U+F9D0->U+985E, U+F9D1->U+516D, U+F9D2->U+622E, U+F9D3->U+9678, U+F9D4->U+502B, U+F9D5->U+5D19, U+F9D6->U+6DEA, U+F9D7->U+8F2A,
U+F9D8->U+5F8B, U+F9D9->U+6144, U+F9DA->U+6817, U+F9DB->U+7387, U+F9DC->U+9686, U+F9DD->U+5229, U+F9DE->U+540F, U+F9DF->U+5C65,
U+F9E0->U+6613, U+F9E1->U+674E, U+F9E2->U+68A8, U+F9E3->U+6CE5, U+F9E4->U+7406, U+F9E5->U+75E2, U+F9E6->U+7F79, U+F9E7->U+88CF,
U+F9E8->U+88E1, U+F9E9->U+91CC, U+F9EA->U+96E2, U+F9EB->U+533F, U+F9EC->U+6EBA, U+F9ED->U+541D, U+F9EE->U+71D0, U+F9EF->U+7498,
U+F9F0->U+85FA, U+F9F1->U+96A3, U+F9F2->U+9C57, U+F9F3->U+9E9F, U+F9F4->U+6797, U+F9F5->U+6DCB, U+F9F6->U+81E8, U+F9F7->U+7ACB,
U+F9F8->U+7B20, U+F9F9->U+7C92, U+F9FA->U+72C0, U+F9FB->U+7099, U+F9FC->U+8B58, U+F9FD->U+4EC0, U+F9FE->U+8336, U+F9FF->U+523A,
U+FA00->U+5207, U+FA01->U+5EA6, U+FA02->U+62D3, U+FA03->U+7CD6, U+FA04->U+5B85, U+FA05->U+6D1E, U+FA06->U+66B4, U+FA07->U+8F3B,
U+FA08->U+884C, U+FA09->U+964D, U+FA0A->U+898B, U+FA0B->U+5ED3, U+FA0C->U+5140, U+FA0D->U+55C0, U+FA10->U+585A, U+FA12->U+6674,
U+FA15->U+51DE, U+FA16->U+732A, U+FA17->U+76CA, U+FA18->U+793C, U+FA19->U+795E, U+FA1A->U+7965, U+FA1B->U+798F, U+FA1C->U+9756,
U+FA1D->U+7CBE, U+FA1E->U+7FBD, U+FA20->U+8612, U+FA22->U+8AF8, U+FA25->U+9038, U+FA26->U+90FD, U+FA2A->U+98EF, U+FA2B->U+98FC,
U+FA2C->U+9928, U+FA2D->U+9DB4, U+FA30->U+4FAE, U+FA31->U+50E7, U+FA32->U+514D, U+FA33->U+52C9, U+FA34->U+52E4, U+FA35->U+5351,
U+FA36->U+559D, U+FA37->U+5606, U+FA38->U+5668, U+FA39->U+5840, U+FA3A->U+58A8, U+FA3B->U+5C64, U+FA3C->U+5C6E, U+FA3D->U+6094,
U+FA3E->U+6168, U+FA3F->U+618E, U+FA40->U+61F2, U+FA41->U+654F, U+FA42->U+65E2, U+FA43->U+6691, U+FA44->U+6885, U+FA45->U+6D77,
U+FA46->U+6E1A, U+FA47->U+6F22, U+FA48->U+716E, U+FA49->U+722B, U+FA4A->U+7422, U+FA4B->U+7891, U+FA4C->U+793E, U+FA4D->U+7949,
U+FA4E->U+7948, U+FA4F->U+7950, U+FA50->U+7956, U+FA51->U+795D, U+FA52->U+798D, U+FA53->U+798E, U+FA54->U+7A40, U+FA55->U+7A81,
U+FA56->U+7BC0, U+FA57->U+7DF4, U+FA58->U+7E09, U+FA59->U+7E41, U+FA5A->U+7F72, U+FA5B->U+8005, U+FA5C->U+81ED, U+FA5D->U+8279,
U+FA5E->U+8279, U+FA5F->U+8457, U+FA60->U+8910, U+FA61->U+8996, U+FA62->U+8B01, U+FA63->U+8B39, U+FA64->U+8CD3, U+FA65->U+8D08,
U+FA66->U+8FB6, U+FA67->U+9038, U+FA68->U+96E3, U+FA69->U+97FF, U+FA6A->U+983B, U+FA70->U+4E26, U+FA71->U+51B5, U+FA72->U+5168,
U+FA73->U+4F80, U+FA74->U+5145, U+FA75->U+5180, U+FA76->U+52C7, U+FA77->U+52FA, U+FA78->U+559D, U+FA79->U+5555, U+FA7A->U+5599,
U+FA7B->U+55E2, U+FA7C->U+585A, U+FA7D->U+58B3, U+FA7E->U+5944, U+FA7F->U+5954, U+FA80->U+5A62, U+FA81->U+5B28, U+FA82->U+5ED2,
U+FA83->U+5ED9, U+FA84->U+5F69, U+FA85->U+5FAD, U+FA86->U+60D8, U+FA87->U+614E, U+FA88->U+6108, U+FA89->U+618E, U+FA8A->U+6160,
U+FA8B->U+61F2, U+FA8C->U+6234, U+FA8D->U+63C4, U+FA8E->U+641C, U+FA8F->U+6452, U+FA90->U+6556, U+FA91->U+6674, U+FA92->U+6717,
U+FA93->U+671B, U+FA94->U+6756, U+FA95->U+6B79, U+FA96->U+6BBA, U+FA97->U+6D41, U+FA98->U+6EDB, U+FA99->U+6ECB, U+FA9A->U+6F22,
U+FA9B->U+701E, U+FA9C->U+716E, U+FA9D->U+77A7, U+FA9E->U+7235, U+FA9F->U+72AF, U+FAA0->U+732A, U+FAA1->U+7471, U+FAA2->U+7506,
U+FAA3->U+753B, U+FAA4->U+761D, U+FAA5->U+761F, U+FAA6->U+76CA, U+FAA7->U+76DB, U+FAA8->U+76F4, U+FAA9->U+774A, U+FAAA->U+7740,
U+FAAB->U+78CC, U+FAAC->U+7AB1, U+FAAD->U+7BC0, U+FAAE->U+7C7B, U+FAAF->U+7D5B, U+FAB0->U+7DF4, U+FAB1->U+7F3E, U+FAB2->U+8005,
U+FAB3->U+8352, U+FAB4->U+83EF, U+FAB5->U+8779, U+FAB6->U+8941, U+FAB7->U+8986, U+FAB8->U+8996, U+FAB9->U+8ABF, U+FABA->U+8AF8,
U+FABB->U+8ACB, U+FABC->U+8B01, U+FABD->U+8AFE, U+FABE->U+8AED, U+FABF->U+8B39, U+FAC0->U+8B8A, U+FAC1->U+8D08, U+FAC2->U+8F38,
U+FAC3->U+9072, U+FAC4->U+9199, U+FAC5->U+9276, U+FAC6->U+967C, U+FAC7->U+96E3, U+FAC8->U+9756, U+FAC9->U+97DB, U+FACA->U+97FF,
U+FACB->U+980B, U+FACC->U+983B, U+FACD->U+9B12, U+FACE->U+9F9C, U+FACF->U+2284A, U+FAD0->U+22844, U+FAD1->U+233D5, U+FAD2->U+3B9D,
U+FAD3->U+4018, U+FAD4->U+4039, U+FAD5->U+25249, U+FAD6->U+25CD0, U+FAD7->U+27ED3, U+FAD8->U+9F43, U+FAD9->U+9F8E, U+2F800->U+4E3D,
U+2F801->U+4E38, U+2F802->U+4E41, U+2F803->U+20122, U+2F804->U+4F60, U+2F805->U+4FAE, U+2F806->U+4FBB, U+2F807->U+5002, U+2F808->U+507A,
U+2F809->U+5099, U+2F80A->U+50E7, U+2F80B->U+50CF, U+2F80C->U+349E, U+2F80D->U+2063A, U+2F80E->U+514D, U+2F80F->U+5154, U+2F810->U+5164,
U+2F811->U+5177, U+2F812->U+2051C, U+2F813->U+34B9, U+2F814->U+5167, U+2F815->U+518D, U+2F816->U+2054B, U+2F817->U+5197,
U+2F818->U+51A4, U+2F819->U+4ECC, U+2F81A->U+51AC, U+2F81B->U+51B5, U+2F81C->U+291DF, U+2F81D->U+51F5, U+2F81E->U+5203,
U+2F81F->U+34DF, U+2F820->U+523B, U+2F821->U+5246, U+2F822->U+5272, U+2F823->U+5277, U+2F824->U+3515, U+2F825->U+52C7,
U+2F826->U+52C9, U+2F827->U+52E4, U+2F828->U+52FA, U+2F829->U+5305, U+2F82A->U+5306, U+2F82B->U+5317, U+2F82C->U+5349,
U+2F82D->U+5351, U+2F82E->U+535A, U+2F82F->U+5373, U+2F830->U+537D, U+2F831->U+537F, U+2F832->U+537F, U+2F833->U+537F,
U+2F834->U+20A2C, U+2F835->U+7070, U+2F836->U+53CA, U+2F837->U+53DF, U+2F838->U+20B63, U+2F839->U+53EB, U+2F83A->U+53F1,
U+2F83B->U+5406, U+2F83C->U+549E, U+2F83D->U+5438, U+2F83E->U+5448, U+2F83F->U+5468, U+2F840->U+54A2, U+2F841->U+54F6,
U+2F842->U+5510, U+2F843->U+5553, U+2F844->U+5563, U+2F845->U+5584, U+2F846->U+5584, U+2F847->U+5599, U+2F848->U+55AB,
U+2F849->U+55B3, U+2F84A->U+55C2, U+2F84B->U+5716, U+2F84C->U+5606, U+2F84D->U+5717, U+2F84E->U+5651, U+2F84F->U+5674,
U+2F850->U+5207, U+2F851->U+58EE, U+2F852->U+57CE, U+2F853->U+57F4, U+2F854->U+580D, U+2F855->U+578B, U+2F856->U+5832,
U+2F857->U+5831, U+2F858->U+58AC, U+2F859->U+214E4, U+2F85A->U+58F2, U+2F85B->U+58F7, U+2F85C->U+5906, U+2F85D->U+591A,
U+2F85E->U+5922, U+2F85F->U+5962, U+2F860->U+216A8, U+2F861->U+216EA, U+2F862->U+59EC, U+2F863->U+5A1B, U+2F864->U+5A27,
U+2F865->U+59D8, U+2F866->U+5A66, U+2F867->U+36EE, U+2F868->U+36FC, U+2F869->U+5B08, U+2F86A->U+5B3E, U+2F86B->U+5B3E,
U+2F86C->U+219C8, U+2F86D->U+5BC3, U+2F86E->U+5BD8, U+2F86F->U+5BE7, U+2F870->U+5BF3, U+2F871->U+21B18, U+2F872->U+5BFF,
U+2F873->U+5C06, U+2F874->U+5F53, U+2F875->U+5C22, U+2F876->U+3781, U+2F877->U+5C60, U+2F878->U+5C6E, U+2F879->U+5CC0,
U+2F87A->U+5C8D, U+2F87B->U+21DE4, U+2F87C->U+5D43, U+2F87D->U+21DE6, U+2F87E->U+5D6E, U+2F87F->U+5D6B, U+2F880->U+5D7C,
U+2F881->U+5DE1, U+2F882->U+5DE2, U+2F883->U+382F, U+2F884->U+5DFD, U+2F885->U+5E28, U+2F886->U+5E3D, U+2F887->U+5E69,
U+2F888->U+3862, U+2F889->U+22183, U+2F88A->U+387C, U+2F88B->U+5EB0, U+2F88C->U+5EB3, U+2F88D->U+5EB6, U+2F88E->U+5ECA,
U+2F88F->U+2A392, U+2F890->U+5EFE, U+2F891->U+22331, U+2F892->U+22331, U+2F893->U+8201, U+2F894->U+5F22, U+2F895->U+5F22,
U+2F896->U+38C7, U+2F897->U+232B8, U+2F898->U+261DA, U+2F899->U+5F62, U+2F89A->U+5F6B, U+2F89B->U+38E3, U+2F89C->U+5F9A,
U+2F89D->U+5FCD, U+2F89E->U+5FD7, U+2F89F->U+5FF9, U+2F8A0->U+6081, U+2F8A1->U+393A, U+2F8A2->U+391C, U+2F8A3->U+6094,
U+2F8A4->U+226D4, U+2F8A5->U+60C7, U+2F8A6->U+6148, U+2F8A7->U+614C, U+2F8A8->U+614E, U+2F8A9->U+614C, U+2F8AA->U+617A,
U+2F8AB->U+618E, U+2F8AC->U+61B2, U+2F8AD->U+61A4, U+2F8AE->U+61AF, U+2F8AF->U+61DE, U+2F8B0->U+61F2, U+2F8B1->U+61F6,
U+2F8B2->U+6210, U+2F8B3->U+621B, U+2F8B4->U+625D, U+2F8B5->U+62B1, U+2F8B6->U+62D4, U+2F8B7->U+6350, U+2F8B8->U+22B0C,
U+2F8B9->U+633D, U+2F8BA->U+62FC, U+2F8BB->U+6368, U+2F8BC->U+6383, U+2F8BD->U+63E4, U+2F8BE->U+22BF1, U+2F8BF->U+6422,
U+2F8C0->U+63C5, U+2F8C1->U+63A9, U+2F8C2->U+3A2E, U+2F8C3->U+6469, U+2F8C4->U+647E, U+2F8C5->U+649D, U+2F8C6->U+6477,
U+2F8C7->U+3A6C, U+2F8C8->U+654F, U+2F8C9->U+656C, U+2F8CA->U+2300A, U+2F8CB->U+65E3, U+2F8CC->U+66F8, U+2F8CD->U+6649,
U+2F8CE->U+3B19, U+2F8CF->U+6691, U+2F8D0->U+3B08, U+2F8D1->U+3AE4, U+2F8D2->U+5192, U+2F8D3->U+5195, U+2F8D4->U+6700,
U+2F8D5->U+669C, U+2F8D6->U+80AD, U+2F8D7->U+43D9, U+2F8D8->U+6717, U+2F8D9->U+671B, U+2F8DA->U+6721, U+2F8DB->U+675E,
U+2F8DC->U+6753, U+2F8DD->U+233C3, U+2F8DE->U+3B49, U+2F8DF->U+67FA, U+2F8E0->U+6785, U+2F8E1->U+6852, U+2F8E2->U+6885,
U+2F8E3->U+2346D, U+2F8E4->U+688E, U+2F8E5->U+681F, U+2F8E6->U+6914, U+2F8E7->U+3B9D, U+2F8E8->U+6942, U+2F8E9->U+69A3,
U+2F8EA->U+69EA, U+2F8EB->U+6AA8, U+2F8EC->U+236A3, U+2F8ED->U+6ADB, U+2F8EE->U+3C18, U+2F8EF->U+6B21, U+2F8F0->U+238A7,
U+2F8F1->U+6B54, U+2F8F2->U+3C4E, U+2F8F3->U+6B72, U+2F8F4->U+6B9F, U+2F8F5->U+6BBA, U+2F8F6->U+6BBB, U+2F8F7->U+23A8D,
U+2F8F8->U+21D0B, U+2F8F9->U+23AFA, U+2F8FA->U+6C4E, U+2F8FB->U+23CBC, U+2F8FC->U+6CBF, U+2F8FD->U+6CCD, U+2F8FE->U+6C67,
U+2F8FF->U+6D16, U+2F900->U+6D3E, U+2F901->U+6D77, U+2F902->U+6D41, U+2F903->U+6D69, U+2F904->U+6D78, U+2F905->U+6D85,
U+2F906->U+23D1E, U+2F907->U+6D34, U+2F908->U+6E2F, U+2F909->U+6E6E, U+2F90A->U+3D33, U+2F90B->U+6ECB, U+2F90C->U+6EC7,
U+2F90D->U+23ED1, U+2F90E->U+6DF9, U+2F90F->U+6F6E, U+2F910->U+23F5E, U+2F911->U+23F8E, U+2F912->U+6FC6, U+2F913->U+7039,
U+2F914->U+701E, U+2F915->U+701B, U+2F916->U+3D96, U+2F917->U+704A, U+2F918->U+707D, U+2F919->U+7077, U+2F91A->U+70AD,
U+2F91B->U+20525, U+2F91C->U+7145, U+2F91D->U+24263, U+2F91E->U+719C, U+2F91F->U+243AB, U+2F920->U+7228, U+2F921->U+7235,
U+2F922->U+7250, U+2F923->U+24608, U+2F924->U+7280, U+2F925->U+7295, U+2F926->U+24735, U+2F927->U+24814, U+2F928->U+737A,
U+2F929->U+738B, U+2F92A->U+3EAC, U+2F92B->U+73A5, U+2F92C->U+3EB8, U+2F92D->U+3EB8, U+2F92E->U+7447, U+2F92F->U+745C,
U+2F930->U+7471, U+2F931->U+7485, U+2F932->U+74CA, U+2F933->U+3F1B, U+2F934->U+7524, U+2F935->U+24C36, U+2F936->U+753E,
U+2F937->U+24C92, U+2F938->U+7570, U+2F939->U+2219F, U+2F93A->U+7610, U+2F93B->U+24FA1, U+2F93C->U+24FB8, U+2F93D->U+25044,
U+2F93E->U+3FFC, U+2F93F->U+4008, U+2F940->U+76F4, U+2F941->U+250F3, U+2F942->U+250F2, U+2F943->U+25119, U+2F944->U+25133,
U+2F945->U+771E, U+2F946->U+771F, U+2F947->U+771F, U+2F948->U+774A, U+2F949->U+4039, U+2F94A->U+778B, U+2F94B->U+4046,
U+2F94C->U+4096, U+2F94D->U+2541D, U+2F94E->U+784E, U+2F94F->U+788C, U+2F950->U+78CC, U+2F951->U+40E3, U+2F952->U+25626,
U+2F953->U+7956, U+2F954->U+2569A, U+2F955->U+256C5, U+2F956->U+798F, U+2F957->U+79EB, U+2F958->U+412F, U+2F959->U+7A40,
U+2F95A->U+7A4A, U+2F95B->U+7A4F, U+2F95C->U+2597C, U+2F95D->U+25AA7, U+2F95E->U+25AA7, U+2F95F->U+7AEE, U+2F960->U+4202,
U+2F961->U+25BAB, U+2F962->U+7BC6, U+2F963->U+7BC9, U+2F964->U+4227, U+2F965->U+25C80, U+2F966->U+7CD2, U+2F967->U+42A0,
U+2F968->U+7CE8, U+2F969->U+7CE3, U+2F96A->U+7D00, U+2F96B->U+25F86, U+2F96C->U+7D63, U+2F96D->U+4301, U+2F96E->U+7DC7,
U+2F96F->U+7E02, U+2F970->U+7E45, U+2F971->U+4334, U+2F972->U+26228, U+2F973->U+26247, U+2F974->U+4359, U+2F975->U+262D9,
U+2F976->U+7F7A, U+2F977->U+2633E, U+2F978->U+7F95, U+2F979->U+7FFA, U+2F97A->U+8005, U+2F97B->U+264DA, U+2F97C->U+26523,
U+2F97D->U+8060, U+2F97E->U+265A8, U+2F97F->U+8070, U+2F980->U+2335F, U+2F981->U+43D5, U+2F982->U+80B2, U+2F983->U+8103,
U+2F984->U+440B, U+2F985->U+813E, U+2F986->U+5AB5, U+2F987->U+267A7, U+2F988->U+267B5, U+2F989->U+23393, U+2F98A->U+2339C,
U+2F98B->U+8201, U+2F98C->U+8204, U+2F98D->U+8F9E, U+2F98E->U+446B, U+2F98F->U+8291, U+2F990->U+828B, U+2F991->U+829D,
U+2F992->U+52B3, U+2F993->U+82B1, U+2F994->U+82B3, U+2F995->U+82BD, U+2F996->U+82E6, U+2F997->U+26B3C, U+2F998->U+82E5,
U+2F999->U+831D, U+2F99A->U+8363, U+2F99B->U+83AD, U+2F99C->U+8323, U+2F99D->U+83BD, U+2F99E->U+83E7, U+2F99F->U+8457,
U+2F9A0->U+8353, U+2F9A1->U+83CA, U+2F9A2->U+83CC, U+2F9A3->U+83DC, U+2F9A4->U+26C36, U+2F9A5->U+26D6B, U+2F9A6->U+26CD5,
U+2F9A7->U+452B, U+2F9A8->U+84F1, U+2F9A9->U+84F3, U+2F9AA->U+8516, U+2F9AB->U+273CA, U+2F9AC->U+8564, U+2F9AD->U+26F2C,
U+2F9AE->U+455D, U+2F9AF->U+4561, U+2F9B0->U+26FB1, U+2F9B1->U+270D2, U+2F9B2->U+456B, U+2F9B3->U+8650, U+2F9B4->U+865C,
U+2F9B5->U+8667, U+2F9B6->U+8669, U+2F9B7->U+86A9, U+2F9B8->U+8688, U+2F9B9->U+870E, U+2F9BA->U+86E2, U+2F9BB->U+8779,
U+2F9BC->U+8728, U+2F9BD->U+876B, U+2F9BE->U+8786, U+2F9BF->U+45D7, U+2F9C0->U+87E1, U+2F9C1->U+8801, U+2F9C2->U+45F9,
U+2F9C3->U+8860, U+2F9C4->U+8863, U+2F9C5->U+27667, U+2F9C6->U+88D7, U+2F9C7->U+88DE, U+2F9C8->U+4635, U+2F9C9->U+88FA,
U+2F9CA->U+34BB, U+2F9CB->U+278AE, U+2F9CC->U+27966, U+2F9CD->U+46BE, U+2F9CE->U+46C7, U+2F9CF->U+8AA0, U+2F9D0->U+8AED,
U+2F9D1->U+8B8A, U+2F9D2->U+8C55, U+2F9D3->U+27CA8, U+2F9D4->U+8CAB, U+2F9D5->U+8CC1, U+2F9D6->U+8D1B, U+2F9D7->U+8D77,
U+2F9D8->U+27F2F, U+2F9D9->U+20804, U+2F9DA->U+8DCB, U+2F9DB->U+8DBC, U+2F9DC->U+8DF0, U+2F9DD->U+208DE, U+2F9DE->U+8ED4,
U+2F9DF->U+8F38, U+2F9E0->U+285D2, U+2F9E1->U+285ED, U+2F9E2->U+9094, U+2F9E3->U+90F1, U+2F9E4->U+9111, U+2F9E5->U+2872E,
U+2F9E6->U+911B, U+2F9E7->U+9238, U+2F9E8->U+92D7, U+2F9E9->U+92D8, U+2F9EA->U+927C, U+2F9EB->U+93F9, U+2F9EC->U+9415,
U+2F9ED->U+28BFA, U+2F9EE->U+958B, U+2F9EF->U+4995, U+2F9F0->U+95B7, U+2F9F1->U+28D77, U+2F9F2->U+49E6, U+2F9F3->U+96C3,
U+2F9F4->U+5DB2, U+2F9F5->U+9723, U+2F9F6->U+29145, U+2F9F7->U+2921A, U+2F9F8->U+4A6E, U+2F9F9->U+4A76, U+2F9FA->U+97E0,
U+2F9FB->U+2940A, U+2F9FC->U+4AB2, U+2F9FD->U+29496, U+2F9FE->U+980B, U+2F9FF->U+980B, U+2FA00->U+9829, U+2FA01->U+295B6,
U+2FA02->U+98E2, U+2FA03->U+4B33, U+2FA04->U+9929, U+2FA05->U+99A7, U+2FA06->U+99C2, U+2FA07->U+99FE, U+2FA08->U+4BCE,
U+2FA09->U+29B30, U+2FA0A->U+9B12, U+2FA0B->U+9C40, U+2FA0C->U+9CFD, U+2FA0D->U+4CCE, U+2FA0E->U+4CED, U+2FA0F->U+9D67,
U+2FA10->U+2A0CE, U+2FA11->U+4CF8, U+2FA12->U+2A105, U+2FA13->U+2A20E, U+2FA14->U+2A291, U+2FA15->U+9EBB, U+2FA16->U+4D56,
U+2FA17->U+9EF9, U+2FA18->U+9EFE, U+2FA19->U+9F05, U+2FA1A->U+9F0F, U+2FA1B->U+9F16, U+2FA1C->U+9F3B, U+2FA1D->U+2A600,
U+2F00->U+4E00, U+2F01->U+4E28, U+2F02->U+4E36, U+2F03->U+4E3F, U+2F04->U+4E59, U+2F05->U+4E85, U+2F06->U+4E8C, U+2F07->U+4EA0,
U+2F08->U+4EBA, U+2F09->U+513F, U+2F0A->U+5165, U+2F0B->U+516B, U+2F0C->U+5182, U+2F0D->U+5196, U+2F0E->U+51AB, U+2F0F->U+51E0,
U+2F10->U+51F5, U+2F11->U+5200, U+2F12->U+529B, U+2F13->U+52F9, U+2F14->U+5315, U+2F15->U+531A, U+2F16->U+5338, U+2F17->U+5341,
U+2F18->U+535C, U+2F19->U+5369, U+2F1A->U+5382, U+2F1B->U+53B6, U+2F1C->U+53C8, U+2F1D->U+53E3, U+2F1E->U+56D7, U+2F1F->U+571F,
U+2F20->U+58EB, U+2F21->U+5902, U+2F22->U+590A, U+2F23->U+5915, U+2F24->U+5927, U+2F25->U+5973, U+2F26->U+5B50, U+2F27->U+5B80,
U+2F28->U+5BF8, U+2F29->U+5C0F, U+2F2A->U+5C22, U+2F2B->U+5C38, U+2F2C->U+5C6E, U+2F2D->U+5C71, U+2F2E->U+5DDB, U+2F2F->U+5DE5,
U+2F30->U+5DF1, U+2F31->U+5DFE, U+2F32->U+5E72, U+2F33->U+5E7A, U+2F34->U+5E7F, U+2F35->U+5EF4, U+2F36->U+5EFE, U+2F37->U+5F0B,
U+2F38->U+5F13, U+2F39->U+5F50, U+2F3A->U+5F61, U+2F3B->U+5F73, U+2F3C->U+5FC3, U+2F3D->U+6208, U+2F3E->U+6236, U+2F3F->U+624B,
U+2F40->U+652F, U+2F41->U+6534, U+2F42->U+6587, U+2F43->U+6597, U+2F44->U+65A4, U+2F45->U+65B9, U+2F46->U+65E0, U+2F47->U+65E5,
U+2F48->U+66F0, U+2F49->U+6708, U+2F4A->U+6728, U+2F4B->U+6B20, U+2F4C->U+6B62, U+2F4D->U+6B79, U+2F4E->U+6BB3, U+2F4F->U+6BCB,
U+2F50->U+6BD4, U+2F51->U+6BDB, U+2F52->U+6C0F, U+2F53->U+6C14, U+2F54->U+6C34, U+2F55->U+706B, U+2F56->U+722A, U+2F57->U+7236,
U+2F58->U+723B, U+2F59->U+723F, U+2F5A->U+7247, U+2F5B->U+7259, U+2F5C->U+725B, U+2F5D->U+72AC, U+2F5E->U+7384, U+2F5F->U+7389,
U+2F60->U+74DC, U+2F61->U+74E6, U+2F62->U+7518, U+2F63->U+751F, U+2F64->U+7528, U+2F65->U+7530, U+2F66->U+758B, U+2F67->U+7592,
U+2F68->U+7676, U+2F69->U+767D, U+2F6A->U+76AE, U+2F6B->U+76BF, U+2F6C->U+76EE, U+2F6D->U+77DB, U+2F6E->U+77E2, U+2F6F->U+77F3,
U+2F70->U+793A, U+2F71->U+79B8, U+2F72->U+79BE, U+2F73->U+7A74, U+2F74->U+7ACB, U+2F75->U+7AF9, U+2F76->U+7C73, U+2F77->U+7CF8,
U+2F78->U+7F36, U+2F79->U+7F51, U+2F7A->U+7F8A, U+2F7B->U+7FBD, U+2F7C->U+8001, U+2F7D->U+800C, U+2F7E->U+8012, U+2F7F->U+8033,
U+2F80->U+807F, U+2F81->U+8089, U+2F82->U+81E3, U+2F83->U+81EA, U+2F84->U+81F3, U+2F85->U+81FC, U+2F86->U+820C, U+2F87->U+821B,
U+2F88->U+821F, U+2F89->U+826E, U+2F8A->U+8272, U+2F8B->U+8278, U+2F8C->U+864D, U+2F8D->U+866B, U+2F8E->U+8840, U+2F8F->U+884C,
U+2F90->U+8863, U+2F91->U+897E, U+2F92->U+898B, U+2F93->U+89D2, U+2F94->U+8A00, U+2F95->U+8C37, U+2F96->U+8C46, U+2F97->U+8C55,
U+2F98->U+8C78, U+2F99->U+8C9D, U+2F9A->U+8D64, U+2F9B->U+8D70, U+2F9C->U+8DB3, U+2F9D->U+8EAB, U+2F9E->U+8ECA, U+2F9F->U+8F9B,
U+2FA0->U+8FB0, U+2FA1->U+8FB5, U+2FA2->U+9091, U+2FA3->U+9149, U+2FA4->U+91C6, U+2FA5->U+91CC, U+2FA6->U+91D1, U+2FA7->U+9577,
U+2FA8->U+9580, U+2FA9->U+961C, U+2FAA->U+96B6, U+2FAB->U+96B9, U+2FAC->U+96E8, U+2FAD->U+9751, U+2FAE->U+975E, U+2FAF->U+9762,
U+2FB0->U+9769, U+2FB1->U+97CB, U+2FB2->U+97ED, U+2FB3->U+97F3, U+2FB4->U+9801, U+2FB5->U+98A8, U+2FB6->U+98DB, U+2FB7->U+98DF,
U+2FB8->U+9996, U+2FB9->U+9999, U+2FBA->U+99AC, U+2FBB->U+9AA8, U+2FBC->U+9AD8, U+2FBD->U+9ADF, U+2FBE->U+9B25, U+2FBF->U+9B2F,
U+2FC0->U+9B32, U+2FC1->U+9B3C, U+2FC2->U+9B5A, U+2FC3->U+9CE5, U+2FC4->U+9E75, U+2FC5->U+9E7F, U+2FC6->U+9EA5, U+2FC7->U+9EBB,
U+2FC8->U+9EC3, U+2FC9->U+9ECD, U+2FCA->U+9ED1, U+2FCB->U+9EF9, U+2FCC->U+9EFD, U+2FCD->U+9F0E, U+2FCE->U+9F13, U+2FCF->U+9F20,
U+2FD0->U+9F3B, U+2FD1->U+9F4A, U+2FD2->U+9F52, U+2FD3->U+9F8D, U+2FD4->U+9F9C, U+2FD5->U+9FA0, U+3042->U+3041, U+3044->U+3043,
U+3046->U+3045, U+3048->U+3047, U+304A->U+3049, U+304C->U+304B, U+304E->U+304D, U+3050->U+304F, U+3052->U+3051, U+3054->U+3053,
U+3056->U+3055, U+3058->U+3057, U+305A->U+3059, U+305C->U+305B, U+305E->U+305D, U+3060->U+305F, U+3062->U+3061, U+3064->U+3063,
U+3065->U+3063, U+3067->U+3066, U+3069->U+3068, U+3070->U+306F, U+3071->U+306F, U+3073->U+3072, U+3074->U+3072, U+3076->U+3075,
U+3077->U+3075, U+3079->U+3078, U+307A->U+3078, U+307C->U+307B, U+307D->U+307B, U+3084->U+3083, U+3086->U+3085, U+3088->U+3087,
U+308F->U+308E, U+3094->U+3046, U+3095->U+304B, U+3096->U+3051, U+30A2->U+30A1, U+30A4->U+30A3, U+30A6->U+30A5, U+30A8->U+30A7,
U+30AA->U+30A9, U+30AC->U+30AB, U+30AE->U+30AD, U+30B0->U+30AF, U+30B2->U+30B1, U+30B4->U+30B3, U+30B6->U+30B5, U+30B8->U+30B7,
U+30BA->U+30B9, U+30BC->U+30BB, U+30BE->U+30BD, U+30C0->U+30BF, U+30C2->U+30C1, U+30C5->U+30C4, U+30C7->U+30C6, U+30C9->U+30C8,
U+30D0->U+30CF, U+30D1->U+30CF, U+30D3->U+30D2, U+30D4->U+30D2, U+30D6->U+30D5, U+30D7->U+30D5, U+30D9->U+30D8, U+30DA->U+30D8,
U+30DC->U+30DB, U+30DD->U+30DB, U+30E4->U+30E3, U+30E6->U+30E5, U+30E8->U+30E7, U+30EF->U+30EE, U+30F4->U+30A6, U+30AB->U+30F5,
U+30B1->U+30F6, U+30F7->U+30EF, U+30F8->U+30F0, U+30F9->U+30F1, U+30FA->U+30F2, U+30AF->U+31F0, U+30B7->U+31F1, U+30B9->U+31F2,
U+30C8->U+31F3, U+30CC->U+31F4, U+30CF->U+31F5, U+30D2->U+31F6, U+30D5->U+31F7, U+30D8->U+31F8, U+30DB->U+31F9, U+30E0->U+31FA,
U+30E9->U+31FB, U+30EA->U+31FC, U+30EB->U+31FD, U+30EC->U+31FE, U+30ED->U+31FF, U+FF66->U+30F2, U+FF67->U+30A1, U+FF68->U+30A3,
U+FF69->U+30A5, U+FF6A->U+30A7, U+FF6B->U+30A9, U+FF6C->U+30E3, U+FF6D->U+30E5, U+FF6E->U+30E7, U+FF6F->U+30C3, U+FF71->U+30A1,
U+FF72->U+30A3, U+FF73->U+30A5, U+FF74->U+30A7, U+FF75->U+30A9, U+FF76->U+30AB, U+FF77->U+30AD, U+FF78->U+30AF, U+FF79->U+30B1,
U+FF7A->U+30B3, U+FF7B->U+30B5, U+FF7C->U+30B7, U+FF7D->U+30B9, U+FF7E->U+30BB, U+FF7F->U+30BD, U+FF80->U+30BF, U+FF81->U+30C1,
U+FF82->U+30C3, U+FF83->U+30C6, U+FF84->U+30C8, U+FF85->U+30CA, U+FF86->U+30CB, U+FF87->U+30CC, U+FF88->U+30CD, U+FF89->U+30CE,
U+FF8A->U+30CF, U+FF8B->U+30D2, U+FF8C->U+30D5, U+FF8D->U+30D8, U+FF8E->U+30DB, U+FF8F->U+30DE, U+FF90->U+30DF, U+FF91->U+30E0,
U+FF92->U+30E1, U+FF93->U+30E2, U+FF94->U+30E3, U+FF95->U+30E5, U+FF96->U+30E7, U+FF97->U+30E9, U+FF98->U+30EA, U+FF99->U+30EB,
U+FF9A->U+30EC, U+FF9B->U+30ED, U+FF9C->U+30EF, U+FF9D->U+30F3, U+FFA0->U+3164, U+FFA1->U+3131, U+FFA2->U+3132, U+FFA3->U+3133,
U+FFA4->U+3134, U+FFA5->U+3135, U+FFA6->U+3136, U+FFA7->U+3137, U+FFA8->U+3138, U+FFA9->U+3139, U+FFAA->U+313A, U+FFAB->U+313B,
U+FFAC->U+313C, U+FFAD->U+313D, U+FFAE->U+313E, U+FFAF->U+313F, U+FFB0->U+3140, U+FFB1->U+3141, U+FFB2->U+3142, U+FFB3->U+3143,
U+FFB4->U+3144, U+FFB5->U+3145, U+FFB6->U+3146, U+FFB7->U+3147, U+FFB8->U+3148, U+FFB9->U+3149, U+FFBA->U+314A, U+FFBB->U+314B,
U+FFBC->U+314C, U+FFBD->U+314D, U+FFBE->U+314E, U+FFC2->U+314F, U+FFC3->U+3150, U+FFC4->U+3151, U+FFC5->U+3152, U+FFC6->U+3153,
U+FFC7->U+3154, U+FFCA->U+3155, U+FFCB->U+3156, U+FFCC->U+3157, U+FFCD->U+3158, U+FFCE->U+3159, U+FFCF->U+315A, U+FFD2->U+315B,
U+FFD3->U+315C, U+FFD4->U+315D, U+FFD5->U+315E, U+FFD6->U+315F, U+FFD7->U+3160, U+FFDA->U+3161, U+FFDB->U+3162, U+FFDC->U+3163,
U+3131->U+1100, U+3132->U+1101, U+3133->U+11AA, U+3134->U+1102, U+3135->U+11AC, U+3136->U+11AD, U+3137->U+1103, U+3138->U+1104,
U+3139->U+1105, U+313A->U+11B0, U+313B->U+11B1, U+313C->U+11B2, U+313D->U+11B3, U+313E->U+11B4, U+313F->U+11B5, U+3140->U+111A,
U+3141->U+1106, U+3142->U+1107, U+3143->U+1108, U+3144->U+1121, U+3145->U+1109, U+3146->U+110A, U+3147->U+110B, U+3148->U+110C,
U+3149->U+110D, U+314A->U+110E, U+314B->U+110F, U+314C->U+1110, U+314D->U+1111, U+314E->U+1112, U+314F->U+1161, U+3150->U+1162,
U+3151->U+1163, U+3152->U+1164, U+3153->U+1165, U+3154->U+1166, U+3155->U+1167, U+3156->U+1168, U+3157->U+1169, U+3158->U+116A,
U+3159->U+116B, U+315A->U+116C, U+315B->U+116D, U+315C->U+116E, U+315D->U+116F, U+315E->U+1170, U+315F->U+1171, U+3160->U+1172,
U+3161->U+1173, U+3162->U+1174, U+3163->U+1175, U+3165->U+1114, U+3166->U+1115, U+3167->U+11C7, U+3168->U+11C8, U+3169->U+11CC,
U+316A->U+11CE, U+316B->U+11D3, U+316C->U+11D7, U+316D->U+11D9, U+316E->U+111C, U+316F->U+11DD, U+3170->U+11DF, U+3171->U+111D,
U+3172->U+111E, U+3173->U+1120, U+3174->U+1122, U+3175->U+1123, U+3176->U+1127, U+3177->U+1129, U+3178->U+112B, U+3179->U+112C,
U+317A->U+112D, U+317B->U+112E, U+317C->U+112F, U+317D->U+1132, U+317E->U+1136, U+317F->U+1140, U+3180->U+1147, U+3181->U+114C,
U+3182->U+11F1, U+3183->U+11F2, U+3184->U+1157, U+3185->U+1158, U+3186->U+1159, U+3187->U+1184, U+3188->U+1185, U+3189->U+1188,
U+318A->U+1191, U+318B->U+1192, U+318C->U+1194, U+318D->U+119E, U+318E->U+11A1, U+A490->U+A408, U+A491->U+A1B9, U+4E00..U+9FBB,
U+3400..U+4DB5, U+20000..U+2A6D6, U+FA0E, U+FA0F, U+FA11, U+FA13, U+FA14, U+FA1F, U+FA21, U+FA23, U+FA24, U+FA27, U+FA28, U+FA29,
U+3105..U+312C, U+31A0..U+31B7, U+3041, U+3043, U+3045, U+3047, U+3049, U+304B, U+304D, U+304F, U+3051, U+3053, U+3055, U+3057,
U+3059, U+305B, U+305D, U+305F, U+3061, U+3063, U+3066, U+3068, U+306A..U+306F, U+3072, U+3075, U+3078, U+307B, U+307E..U+3083,
U+3085, U+3087, U+3089..U+308E, U+3090..U+3093, U+30A1, U+30A3, U+30A5, U+30A7, U+30A9, U+30AD, U+30AF, U+30B3, U+30B5, U+30BB,
U+30BD, U+30BF, U+30C1, U+30C3, U+30C4, U+30C6, U+30CA, U+30CB, U+30CD, U+30CE, U+30DE, U+30DF, U+30E1, U+30E2, U+30E3, U+30E5,
U+30E7, U+30EE, U+30F0..U+30F3, U+30F5, U+30F6, U+31F0, U+31F1, U+31F2, U+31F3, U+31F4, U+31F5, U+31F6, U+31F7, U+31F8, U+31F9,
U+31FA, U+31FB, U+31FC, U+31FD, U+31FE, U+31FF, U+AC00..U+D7A3, U+1100..U+1159, U+1161..U+11A2, U+11A8..U+11F9, U+A000..U+A48C,
U+A492..U+A4C6

##################################################
# Coptic
# Notes: Some shared Greek characters, may require amendments.
U+2C80->U+2C81, U+2C81, U+2C82->U+2C83, U+2C83, U+2C84->U+2C85, U+2C85, U+2C86->U+2C87, U+2C87, U+2C88->U+2C89, U+2C89, U+2C8A->U+2C8B,
U+2C8B, U+2C8C->U+2C8D, U+2C8D, U+2C8E->U+2C8F, U+2C8F, U+2C90->U+2C91, U+2C91, U+2C92->U+2C93, U+2C93, U+2C94->U+2C95, U+2C95,
U+2C96->U+2C97, U+2C97, U+2C98->U+2C99, U+2C99, U+2C9A->U+2C9B, U+2C9B, U+2C9C->U+2C9D, U+2C9D, U+2C9E->U+2C9F, U+2C9F, U+2CA0->U+2CA1,
U+2CA1, U+2CA2->U+2CA3, U+2CA3, U+2CA4->U+2CA5, U+2CA5, U+2CA6->U+2CA7, U+2CA7, U+2CA8->U+2CA9, U+2CA9, U+2CAA->U+2CAB, U+2CAB,
U+2CAC->U+2CAD, U+2CAD, U+2CAE->U+2CAF, U+2CAF, U+2CB0->U+2CB1, U+2CB1, U+2CB2->U+2CB3, U+2CB3, U+2CB4->U+2CB5, U+2CB5,
U+2CB6->U+2CB7, U+2CB7, U+2CB8->U+2CB9, U+2CB9, U+2CBA->U+2CBB, U+2CBB, U+2CBC->U+2CBD, U+2CBD, U+2CBE->U+2CBF, U+2CBF,
U+2CC0->U+2CC1, U+2CC1, U+2CC2->U+2CC3, U+2CC3, U+2CC4->U+2CC5, U+2CC5, U+2CC6->U+2CC7, U+2CC7, U+2CC8->U+2CC9, U+2CC9,
U+2CCA->U+2CCB, U+2CCB, U+2CCC->U+2CCD, U+2CCD, U+2CCE->U+2CCF, U+2CCF, U+2CD0->U+2CD1, U+2CD1, U+2CD2->U+2CD3, U+2CD3,
U+2CD4->U+2CD5, U+2CD5, U+2CD6->U+2CD7, U+2CD7, U+2CD8->U+2CD9, U+2CD9, U+2CDA->U+2CDB, U+2CDB, U+2CDC->U+2CDD, U+2CDD,
U+2CDE->U+2CDF, U+2CDF, U+2CE0->U+2CE1, U+2CE1, U+2CE2->U+2CE3, U+2CE3

##################################################
# Cryllic*
U+0400->U+0435, U+0401->U+0435, U+0402->U+0452, U+0452, U+0403->U+0433, U+0404->U+0454, U+0454, U+0405->U+0455, U+0455,
U+0406->U+0456, U+0407->U+0456, U+0457->U+0456, U+0456, U+0408..U+040B->U+0458..U+045B, U+0458..U+045B, U+040C->U+043A,
U+040D->U+0438, U+040E->U+0443, U+040F->U+045F, U+045F, U+0450->U+0435, U+0451->U+0435, U+0453->U+0433, U+045C->U+043A,
U+045D->U+0438, U+045E->U+0443, U+0460->U+0461, U+0461, U+0462->U+0463, U+0463, U+0464->U+0465, U+0465, U+0466->U+0467,
U+0467, U+0468->U+0469, U+0469, U+046A->U+046B, U+046B, U+046C->U+046D, U+046D, U+046E->U+046F, U+046F, U+0470->U+0471,
U+0471, U+0472->U+0473, U+0473, U+0474->U+0475, U+0476->U+0475, U+0477->U+0475, U+0475, U+0478->U+0479, U+0479, U+047A->U+047B,
U+047B, U+047C->U+047D, U+047D, U+047E->U+047F, U+047F, U+0480->U+0481, U+0481, U+048A->U+0438, U+048B->U+0438, U+048C->U+044C,
U+048D->U+044C, U+048E->U+0440, U+048F->U+0440, U+0490->U+0433, U+0491->U+0433, U+0490->U+0433, U+0491->U+0433, U+0492->U+0433,
U+0493->U+0433, U+0494->U+0433, U+0495->U+0433, U+0496->U+0436, U+0497->U+0436, U+0498->U+0437, U+0499->U+0437, U+049A->U+043A,
U+049B->U+043A, U+049C->U+043A, U+049D->U+043A, U+049E->U+043A, U+049F->U+043A, U+04A0->U+043A, U+04A1->U+043A, U+04A2->U+043D,
U+04A3->U+043D, U+04A4->U+043D, U+04A5->U+043D, U+04A6->U+043F, U+04A7->U+043F, U+04A8->U+04A9, U+04A9, U+04AA->U+0441,
U+04AB->U+0441, U+04AC->U+0442, U+04AD->U+0442, U+04AE->U+0443, U+04AF->U+0443, U+04B0->U+0443, U+04B1->U+0443, U+04B2->U+0445,
U+04B3->U+0445, U+04B4->U+04B5, U+04B5, U+04B6->U+0447, U+04B7->U+0447, U+04B8->U+0447, U+04B9->U+0447, U+04BA->U+04BB, U+04BB,
U+04BC->U+04BD, U+04BE->U+04BD, U+04BF->U+04BD, U+04BD, U+04C0->U+04CF, U+04CF, U+04C1->U+0436, U+04C2->U+0436, U+04C3->U+043A,
U+04C4->U+043A, U+04C5->U+043B, U+04C6->U+043B, U+04C7->U+043D, U+04C8->U+043D, U+04C9->U+043D, U+04CA->U+043D, U+04CB->U+0447,
U+04CC->U+0447, U+04CD->U+043C, U+04CE->U+043C, U+04D0->U+0430, U+04D1->U+0430, U+04D2->U+0430, U+04D3->U+0430, U+04D4->U+00E6,
U+04D5->U+00E6, U+04D6->U+0435, U+04D7->U+0435, U+04D8->U+04D9, U+04DA->U+04D9, U+04DB->U+04D9, U+04D9, U+04DC->U+0436,
U+04DD->U+0436, U+04DE->U+0437, U+04DF->U+0437, U+04E0->U+04E1, U+04E1, U+04E2->U+0438, U+04E3->U+0438, U+04E4->U+0438,
U+04E5->U+0438, U+04E6->U+043E, U+04E7->U+043E, U+04E8->U+043E, U+04E9->U+043E, U+04EA->U+043E, U+04EB->U+043E, U+04EC->U+044D,
U+04ED->U+044D, U+04EE->U+0443, U+04EF->U+0443, U+04F0->U+0443, U+04F1->U+0443, U+04F2->U+0443, U+04F3->U+0443, U+04F4->U+0447,
U+04F5->U+0447, U+04F6->U+0433, U+04F7->U+0433, U+04F8->U+044B, U+04F9->U+044B, U+04FA->U+0433, U+04FB->U+0433, U+04FC->U+0445,
U+04FD->U+0445, U+04FE->U+0445, U+04FF->U+0445, U+0410..U+0418->U+0430..U+0438, U+0419->U+0438, U+0430..U+0438,
U+041A..U+042F->U+043A..U+044F, U+043A..U+044F

##################################################
# Devanagari
U+0929->U+0928, U+0931->U+0930, U+0934->U+0933, U+0958->U+0915, U+0959->U+0916, U+095A->U+0917, U+095B->U+091C, U+095C->U+0921,
U+095D->U+0922, U+095E->U+092B, U+095F->U+092F, U+0904..U+0928, U+092A..U+0930, U+0932, U+0933, U+0935..U+0939, U+0960, U+0961,
U+0966..U+096F, U+097B..U+097F

##################################################
# Georgian
U+10FC->U+10DC, U+10D0..U+10FA, U+10A0..U+10C5->U+2D00..U+2D25, U+2D00..U+2D25

##################################################
# Greek
U+0386->U+03B1, U+0388->U+03B5, U+0389->U+03B7, U+038A->U+03B9, U+038C->U+03BF, U+038E->U+03C5, U+038F->U+03C9, U+0390->U+03B9,
U+03AA->U+03B9, U+03AB->U+03C5, U+03AC->U+03B1, U+03AD->U+03B5, U+03AE->U+03B7, U+03AF->U+03B9, U+03B0->U+03C5, U+03CA->U+03B9,
U+03CB->U+03C5, U+03CC->U+03BF, U+03CD->U+03C5, U+03CE->U+03C9, U+03D0->U+03B2, U+03D1->U+03B8, U+03D2->U+03C5, U+03D3->U+03C5,
U+03D4->U+03C5, U+03D5->U+03C6, U+03D6->U+03C0, U+03D8->U+03D9, U+03DA->U+03DB, U+03DC->U+03DD, U+03DE->U+03DF, U+03E0->U+03E1,
U+03E2->U+03E3, U+03E4->U+03E5, U+03E6->U+03E7, U+03E8->U+03E9, U+03EA->U+03EB, U+03EC->U+03ED, U+03EE->U+03EF, U+03F0->U+03BA,
U+03F1->U+03C1, U+03F2->U+03C3, U+03F4->U+03B8, U+03F5->U+03B5, U+03F6->U+03B5, U+03F7->U+03F8, U+03F9->U+03C3, U+03FA->U+03FB,
U+1F00->U+03B1, U+1F01->U+03B1, U+1F02->U+03B1, U+1F03->U+03B1, U+1F04->U+03B1, U+1F05->U+03B1, U+1F06->U+03B1, U+1F07->U+03B1,
U+1F08->U+03B1, U+1F09->U+03B1, U+1F0A->U+03B1, U+1F0B->U+03B1, U+1F0C->U+03B1, U+1F0D->U+03B1, U+1F0E->U+03B1, U+1F0F->U+03B1,
U+1F10->U+03B5, U+1F11->U+03B5, U+1F12->U+03B5, U+1F13->U+03B5, U+1F14->U+03B5, U+1F15->U+03B5, U+1F18->U+03B5, U+1F19->U+03B5,
U+1F1A->U+03B5, U+1F1B->U+03B5, U+1F1C->U+03B5, U+1F1D->U+03B5, U+1F20->U+03B7, U+1F21->U+03B7, U+1F22->U+03B7, U+1F23->U+03B7,
U+1F24->U+03B7, U+1F25->U+03B7, U+1F26->U+03B7, U+1F27->U+03B7, U+1F28->U+03B7, U+1F29->U+03B7, U+1F2A->U+03B7, U+1F2B->U+03B7,
U+1F2C->U+03B7, U+1F2D->U+03B7, U+1F2E->U+03B7, U+1F2F->U+03B7, U+1F30->U+03B9, U+1F31->U+03B9, U+1F32->U+03B9, U+1F33->U+03B9,
U+1F34->U+03B9, U+1F35->U+03B9, U+1F36->U+03B9, U+1F37->U+03B9, U+1F38->U+03B9, U+1F39->U+03B9, U+1F3A->U+03B9, U+1F3B->U+03B9,
U+1F3C->U+03B9, U+1F3D->U+03B9, U+1F3E->U+03B9, U+1F3F->U+03B9, U+1F40->U+03BF, U+1F41->U+03BF, U+1F42->U+03BF, U+1F43->U+03BF,
U+1F44->U+03BF, U+1F45->U+03BF, U+1F48->U+03BF, U+1F49->U+03BF, U+1F4A->U+03BF, U+1F4B->U+03BF, U+1F4C->U+03BF, U+1F4D->U+03BF,
U+1F50->U+03C5, U+1F51->U+03C5, U+1F52->U+03C5, U+1F53->U+03C5, U+1F54->U+03C5, U+1F55->U+03C5, U+1F56->U+03C5, U+1F57->U+03C5,
U+1F59->U+03C5, U+1F5B->U+03C5, U+1F5D->U+03C5, U+1F5F->U+03C5, U+1F60->U+03C9, U+1F61->U+03C9, U+1F62->U+03C9, U+1F63->U+03C9,
U+1F64->U+03C9, U+1F65->U+03C9, U+1F66->U+03C9, U+1F67->U+03C9, U+1F68->U+03C9, U+1F69->U+03C9, U+1F6A->U+03C9, U+1F6B->U+03C9,
U+1F6C->U+03C9, U+1F6D->U+03C9, U+1F6E->U+03C9, U+1F6F->U+03C9, U+1F70->U+03B1, U+1F71->U+03B1, U+1F72->U+03B5, U+1F73->U+03B5,
U+1F74->U+03B7, U+1F75->U+03B7, U+1F76->U+03B9, U+1F77->U+03B9, U+1F78->U+03BF, U+1F79->U+03BF, U+1F7A->U+03C5, U+1F7B->U+03C5,
U+1F7C->U+03C9, U+1F7D->U+03C9, U+1F80->U+03B1, U+1F81->U+03B1, U+1F82->U+03B1, U+1F83->U+03B1, U+1F84->U+03B1, U+1F85->U+03B1,
U+1F86->U+03B1, U+1F87->U+03B1, U+1F88->U+03B1, U+1F89->U+03B1, U+1F8A->U+03B1, U+1F8B->U+03B1, U+1F8C->U+03B1, U+1F8D->U+03B1,
U+1F8E->U+03B1, U+1F8F->U+03B1, U+1F90->U+03B7, U+1F91->U+03B7, U+1F92->U+03B7, U+1F93->U+03B7, U+1F94->U+03B7, U+1F95->U+03B7,
U+1F96->U+03B7, U+1F97->U+03B7, U+1F98->U+03B7, U+1F99->U+03B7, U+1F9A->U+03B7, U+1F9B->U+03B7, U+1F9C->U+03B7, U+1F9D->U+03B7,
U+1F9E->U+03B7, U+1F9F->U+03B7, U+1FA0->U+03C9, U+1FA1->U+03C9, U+1FA2->U+03C9, U+1FA3->U+03C9, U+1FA4->U+03C9, U+1FA5->U+03C9,
U+1FA6->U+03C9, U+1FA7->U+03C9, U+1FA8->U+03C9, U+1FA9->U+03C9, U+1FAA->U+03C9, U+1FAB->U+03C9, U+1FAC->U+03C9, U+1FAD->U+03C9,
U+1FAE->U+03C9, U+1FAF->U+03C9, U+1FB0->U+03B1, U+1FB1->U+03B1, U+1FB2->U+03B1, U+1FB3->U+03B1, U+1FB4->U+03B1, U+1FB6->U+03B1,
U+1FB7->U+03B1, U+1FB8->U+03B1, U+1FB9->U+03B1, U+1FBA->U+03B1, U+1FBB->U+03B1, U+1FBC->U+03B1, U+1FC2->U+03B7, U+1FC3->U+03B7,
U+1FC4->U+03B7, U+1FC6->U+03B7, U+1FC7->U+03B7, U+1FC8->U+03B5, U+1FC9->U+03B5, U+1FCA->U+03B7, U+1FCB->U+03B7, U+1FCC->U+03B7,
U+1FD0->U+03B9, U+1FD1->U+03B9, U+1FD2->U+03B9, U+1FD3->U+03B9, U+1FD6->U+03B9, U+1FD7->U+03B9, U+1FD8->U+03B9, U+1FD9->U+03B9,
U+1FDA->U+03B9, U+1FDB->U+03B9, U+1FE0->U+03C5, U+1FE1->U+03C5, U+1FE2->U+03C5, U+1FE3->U+03C5, U+1FE4->U+03C1, U+1FE5->U+03C1,
U+1FE6->U+03C5, U+1FE7->U+03C5, U+1FE8->U+03C5, U+1FE9->U+03C5, U+1FEA->U+03C5, U+1FEB->U+03C5, U+1FEC->U+03C1, U+1FF2->U+03C9,
U+1FF3->U+03C9, U+1FF4->U+03C9, U+1FF6->U+03C9, U+1FF7->U+03C9, U+1FF8->U+03BF, U+1FF9->U+03BF, U+1FFA->U+03C9, U+1FFB->U+03C9,
U+1FFC->U+03C9, U+0391..U+03A1->U+03B1..U+03C1, U+03B1..U+03C1, U+03A3..U+03A9->U+03C3..U+03C9, U+03C3..U+03C9, U+03C2, U+03D9,
U+03DB, U+03DD, U+03DF, U+03E1, U+03E3, U+03E5, U+03E7, U+03E9, U+03EB, U+03ED, U+03EF, U+03F3, U+03F8, U+03FB

##################################################
# Gujarati
U+0A85..U+0A8C, U+0A8F, U+0A90, U+0A93..U+0AB0, U+0AB2, U+0AB3, U+0AB5..U+0AB9, U+0AE0, U+0AE1, U+0AE6..U+0AEF

##################################################
# Gurmukhi
U+0A33->U+0A32, U+0A36->U+0A38, U+0A59->U+0A16, U+0A5A->U+0A17, U+0A5B->U+0A1C, U+0A5E->U+0A2B, U+0A05..U+0A0A, U+0A0F, U+0A10,
U+0A13..U+0A28, U+0A2A..U+0A30, U+0A32, U+0A35, U+0A38, U+0A39, U+0A5C, U+0A66..U+0A6F

#################################################
# Hebrew*
U+FB1D->U+05D9, U+FB1F->U+05F2, U+FB20->U+05E2, U+FB21->U+05D0, U+FB22->U+05D3, U+FB23->U+05D4, U+FB24->U+05DB, U+FB25->U+05DC,
U+FB26->U+05DD, U+FB27->U+05E8, U+FB28->U+05EA, U+FB2A->U+05E9, U+FB2B->U+05E9, U+FB2C->U+05E9, U+FB2D->U+05E9, U+FB2E->U+05D0,
U+FB2F->U+05D0, U+FB30->U+05D0, U+FB31->U+05D1, U+FB32->U+05D2, U+FB33->U+05D3, U+FB34->U+05D4, U+FB35->U+05D5, U+FB36->U+05D6,
U+FB38->U+05D8, U+FB39->U+05D9, U+FB3A->U+05DA, U+FB3B->U+05DB, U+FB3C->U+05DC, U+FB3E->U+05DE, U+FB40->U+05E0, U+FB41->U+05E1,
U+FB43->U+05E3, U+FB44->U+05E4, U+FB46->U+05E6, U+FB47->U+05E7, U+FB48->U+05E8, U+FB49->U+05E9, U+FB4A->U+05EA, U+FB4B->U+05D5,
U+FB4C->U+05D1, U+FB4D->U+05DB, U+FB4E->U+05E4, U+FB4F->U+05D0, U+05D0..U+05F2

#################################################
# Kannada
U+0C85..U+0C8C, U+0C8E..U+0C90, U+0C92..U+0CA8, U+0CAA..U+0CB3, U+0CB5..U+0CB9, U+0CE0, U+0CE1, U+0CE6..U+0CEF

#################################################
# Limbu
U+1900..U+191C, U+1930..U+1938, U+1946..U+194F

#################################################
# Malayalam
U+0D05..U+0D0C, U+0D0E..U+0D10, U+0D12..U+0D28, U+0D2A..U+0D39, U+0D60, U+0D61, U+0D66..U+0D6F

#################################################
# Tamil
U+0B94->U+0B92, U+0B85..U+0B8A, U+0B8E..U+0B90, U+0B92, U+0B93, U+0B95, U+0B99, U+0B9A, U+0B9C, U+0B9E, U+0B9F, U+0BA3, U+0BA4,
U+0BA8..U+0BAA, U+0BAE..U+0BB9, U+0BE6..U+0BEF

#################################################
# Thai
U+0E01..U+0E30, U+0E32, U+0E33, U+0E40..U+0E46, U+0E50..U+0E5B

##################################################
# Common
U+FF10..U+FF19->0..9, U+FF21..U+FF3A->a..z, U+FF41..U+FF5A->a..z, 0..9, A..Z->a..z, a..z
"""

# The expected value format is a commas-separated list of mappings.
# Two simplest mappings simply declare a character as valid, and map a single character
# to another single character, respectively. But specifying the whole table in such
# form would result in bloated and barely manageable specifications. So there are
# several syntax shortcuts that let you map ranges of characters at once. The complete
# list is as follows:
#
# A->a
#     Single char mapping, declares source char 'A' as allowed to occur within keywords
#     and maps it to destination char 'a' (but does not declare 'a' as allowed). 
# A..Z->a..z
#     Range mapping, declares all chars in source range as allowed and maps them to
#     the destination range. Does not declare destination range as allowed. Also checks
#     ranges' lengths (the lengths must be equal). 
# a
#     Stray char mapping, declares a character as allowed and maps it to itself.
#     Equivalent to a->a single char mapping. 
# a..z
#     Stray range mapping, declares all characters in range as allowed and maps them to
#     themselves. Equivalent to a..z->a..z range mapping. 
# A..Z/2
#     Checkerboard range map. Maps every pair of chars to the second char.
#     More formally, declares odd characters in range as allowed and maps them to the
#     even ones; also declares even characters as allowed and maps them to themselves.
#     For instance, A..Z/2 is equivalent to A->B, B->B, C->D, D->D, ..., Y->Z, Z->Z.
#     This mapping shortcut is helpful for a number of Unicode blocks where uppercase
#     and lowercase letters go in such interleaved order instead of contiguous chunks. 

_dewhite = re.compile(r"\s")
_char = r"((?:U\+[0-9A-Fa-f]{4,6})|.)"
_char_map = re.compile("^" + _char + "->" + _char + "$")
_range_map = re.compile("^" + _char + r"\.\." + _char + "->" + _char + ".." + _char + "$")
_stray_char = re.compile("^" + _char + "$")
_stray_range = re.compile("^" + _char + r"\.\." + _char + "$")
_checker_range = re.compile("^" + _char + r"\.\." + _char + "/2$")

def charspec_to_int(string):
    # Converts a character specification of the form 'A' or 'U+23BC'
    # to an integer
    if string.startswith("U+"):
        return int(string[2:], 16)
    elif len(string) == 1:
        return ord(string)
    else:
        raise Exception("Can't convert charspec: %r" % string)

def charset_table_to_dict(tablestring):
    """Takes a string with the contents of a Sphinx charset table file and
    returns a mapping object (a defaultdict, actually) of the kind expected by
    the unicode.translate() method: that is, it maps a character number to a unicode
    character or None if the character is not a valid word character.
    
    The Sphinx charset table format is described at
    http://www.sphinxsearch.com/docs/current.html#conf-charset-table.
    """
    
    #map = {}
    map = defaultdict(lambda: None)
    for line in tablestring.split("\n"):
        if not line or line.startswith("#"): continue
        line = _dewhite.sub("", line)
        for item in line.split(","):
            if not item: continue
            match = _range_map.match(item)
            if match:
                start1 = charspec_to_int(match.group(1))
                end1 = charspec_to_int(match.group(2))
                start2 = charspec_to_int(match.group(3))
                end2 = charspec_to_int(match.group(4))
                assert (end1 - start1) == (end2 - start2)
                try:
                    for fromord, tooord in izip(xrange(start1, end1+1), xrange(start2, end2+1)):
                        map[fromord] = unichr(tooord)
                except ValueError:
                    pass
                continue
            
            match = _char_map.match(item)
            if match:
                fromord = charspec_to_int(match.group(1))
                toord = charspec_to_int(match.group(2))
                try:
                    map[fromord] = unichr(toord)
                except ValueError:
                    pass
                continue
            
            match = _stray_char.match(item)
            if match:
                ord = charspec_to_int(match.group(0))
                try:
                    map[ord] = unichr(ord)
                except ValueError:
                    pass
                continue
            
            match = _stray_range.match(item)
            if match:
                start = charspec_to_int(match.group(1))
                end = charspec_to_int(match.group(2))
                try:
                    for ord in xrange(start, end+1):
                            map[ord] = unichr(ord)
                except ValueError:
                    pass
                continue
                    
            match = _checker_range.match(item)
            if match:
                fromord = charspec_to_int(match.group(1))
                toord = charspec_to_int(match.group(2))
                assert toord-fromord % 2 == 0
                for ord in xrange(fromord, toord + 1, 2):
                    try:
                        map[ord] = unichr(ord+1)
                        map[ord+1] = unichr(ord+1)
                    except ValueError:
                        pass
                continue
            
            raise Exception("Don't know what to do with %r" % item)
    return map















