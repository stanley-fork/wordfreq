from html.entities import name2codepoint
from wordfreq import tokenize, TOKEN_RE, NON_PUNCT_RANGE
import re
import pycld2

CLD2_BAD_CHAR_RANGE = "".join([
    '[',
    '\x00-\x08',
    '\x0b',
    '\x0e-\x1f',
    '\x7f-\x9f',
    '\ud800-\udfff',
    '\ufdd0-\ufdef'] +
    [chr(65534+65536*x+y) for x in range(17) for y in range(2)] +
    [']'])
CLD2_BAD_CHARS_RE = re.compile(CLD2_BAD_CHAR_RANGE)

TWITTER_HANDLE_RE = re.compile('@{0}+'.format(NON_PUNCT_RANGE))
TCO_RE = re.compile('http(?:s)?://t.co/[a-zA-Z0-9]+'.format(NON_PUNCT_RANGE))


def cld2_surface_tokenizer(text):
    """
    Uses CLD2 to detect the language and wordfreq tokenizer to create tokens
    """
    text = remove_handles_and_urls(text)
    lang = cld2_detect_language(text)
    tokens = tokenize(text, lang)
    return lang, tokens

def cld2_detect_language(text):
    """
    Uses CLD2 to detect the language
    """
    text = CLD2_BAD_CHARS_RE.sub('', text)
    return pycld2.detect(text)[2][0][1]

def remove_handles_and_urls(text):
    text = fix_entities(text)
    text = TWITTER_HANDLE_RE.sub('', text)
    text = TCO_RE.sub('', text)
    return text

def last_tab(line):
    """
    Read lines by keeping only the last tab-separated value.
    """
    return line.split('\t')[-1].strip()

def lowercase_text_filter(token):
    """
    If this looks like a token that we want to count, return it, lowercased.
    If not, filter it out by returning None.
    """
    if TOKEN_RE.search(token):
        return token.lower()
    else:
        return None

def tokenize_file(in_filename, out_prefix, tokenizer, line_reader=last_tab):
    """
    Process a file by running it through the given tokenizer, sorting the
    results by the language of each line, and inserting newlines
    to mark the token boundaries.
    """
    out_files = {}
    with open(in_filename, encoding='utf-8') as in_file:
        for line in in_file:
            text = line_reader(line)
            language, tokens = tokenizer(text)
            if language != 'un':
                tokenized = '\n'.join(tokens)
                out_filename = '%s.%s.txt' % (out_prefix, language)
                if out_filename in out_files:
                    out_file = out_files[out_filename]
                else:
                    out_file = open(out_filename, 'w', encoding='utf-8')
                    out_files[out_filename] = out_file
                print(tokenized, file=out_file)
    for out_file in out_files.values():
        out_file.close()

ENTITY_RE = re.compile(r'& ?(amp|quot|lt|gt) ?;')

def fix_entities(text):
    """
    Fix the few HTML entities that Twitter uses -- even if they've
    already been tokenized.
    """
    def replace_entity(match):
        return chr(name2codepoint[match.group(1)])
    return ENTITY_RE.sub(replace_entity, text)

def monolingual_tokenize_file(in_filename, out_filename, language,
                              tokenizer, line_reader=last_tab,
                              token_filter=lowercase_text_filter,
                              sample_proportion=100):
    """
    Apply a tokenizer that can distinguish different languages, but only
    keep the lines that are in the language we're asking for.
    """
    with open(in_filename, encoding='utf-8', errors='replace') as in_file:
        with open(out_filename, 'w', encoding='utf-8') as out_file:
            for i, line in enumerate(in_file):
                if i % sample_proportion == 0:
                    text = line_reader(line)
                    tokens, line_language = tokenizer(text)
                    if line_language == language:
                        for token in tokens:
                            print(token, file=out_file)
