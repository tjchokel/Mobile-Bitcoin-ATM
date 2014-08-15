from datetime import datetime
import re

DRY_RUN = False

# TODO: pass these in as inputs
INPUT_FILE = 'locale/cs/LC_MESSAGES/django.po'
OUTPUT_FILE = 'locale/cs/LC_MESSAGES/django_%s.po' % datetime.now().strftime("%Y%m%d_%H%M%S")

input_handler = open(INPUT_FILE, 'r')

if not DRY_RUN:
    output_handler = open(OUTPUT_FILE, 'w', 0)


def msgid_startswith_newline(msgid_list):
    if msgid_list[0] == '\\n':
        return True

    if len(msgid_list) > 2:
        if msgid_list[1].startswith('\\n'):
            return True

    return False


def msgid_endswith_newline(msgid_list):
    if msgid_list[-1] == '\\n':
        return True

    if len(msgid_list) > 2 and False:
        if msgid_list[-2].endswith('\\n'):
            return True

    return False

errors = []
is_header, file_id = True, None
msgid_list, msgstr_list = [], []
in_msgid_section, in_msgstr_section = False, False
for cnt, line in enumerate(input_handler):

    #print 'cnt: %s, is_header: %s, in_msgstr_section: %s   | %s' % (cnt, is_header, in_msgstr_section, line)

    # copy header verbatim
    if is_header:
        if line.startswith('#: '):
            is_header = False
        else:
            if not DRY_RUN:
                output_handler.write(line)
            continue

    # blank line between sections
    if in_msgstr_section and not line.strip():

        in_msgid_section, in_msgstr_section = False, False

        if len(msgid_list) > 1:
            assert msgid_list[0] == '', 'We assume below to skip this entry'
            msgid_full = 'msgid ""\n' + '\n'.join(['"%s"' % x for x in msgid_list[1:]])
        else:
            msgid_full = 'msgid "%s"' % msgid_list[0]

        # piece together the translation
        msgstr_full = ' '.join(msgstr_list).strip()
        msgstr_full = msgstr_full.replace('\n', ' ')
        msgstr_full = msgstr_full.replace('\\n', ' ')
        msgstr_full = msgstr_full.replace('  ', ' ')

        if not msgstr_full:
            # no translation, skip this altogether
            msgid_list, msgstr_list = [], []
            continue

        # handle newlines
        if msgid_startswith_newline(msgid_list):
            msgstr_full = '\\n' + msgstr_full
        if msgid_endswith_newline(msgid_list):
            msgstr_full = msgstr_full + '\\n'

        msgstr_full = 'msgstr "%s"' % msgstr_full

        # Be sure all string interpolations match before writing
        for keyword in re.findall('%\((.*?)\)s', msgid_full):
            interpolator = '%%(%s)s' % keyword
            if interpolator not in msgstr_full:
                errors.append('Line %s (ish) error: %s not in translation' % (cnt, interpolator))

        for keyword in re.findall('%\((.*?)\)s', msgstr_full):
            interpolator = '%%(%s)s' % keyword
            if interpolator not in msgid_full:
                errors.append('Line %s (ish) error: %s in translation but not original' % (cnt, interpolator))

        # write everything
        if not DRY_RUN:
            output_handler.write(file_id)
            output_handler.write(msgid_full+'\n')
            output_handler.write(msgstr_full+'\n')
            output_handler.write('\n')

        # reset vars
        msgid_list, msgstr_list = [], []

        continue

    # comment line
    if line.startswith('#~ '):
        continue

    # file id line
    if line.startswith('#: '):
        file_id = line
        msgid, msgstr = None, None
        continue

    # comment line
    if line.startswith('#, '):
        # python-format and fuzzy
        continue

    # begin msgid
    if line.startswith('msgid "'):
        in_msgid_section = True
        in_msgstr_section = False
        msgid_list.append(re.findall('msgid "(.*)"', line)[0])
        continue

    # begin msgstr
    if line.startswith('msgstr "'):
        in_msgstr_section = True
        in_msgid_section = False
        msgstr_list.append(re.findall('msgstr "(.*)"', line.strip())[0])
        continue

    if in_msgid_section:
        msgid_list.append(re.findall('"(.*)"', line)[0])
        continue

    if in_msgstr_section:
        msgstr_list.append(re.findall('"(.*)"', line.strip())[0])
        continue

errors.reverse()
for error in errors:
    print error
print '%s errors found' % len(errors)

input_handler.close()
if DRY_RUN:
    'Dry run complete, no file saved.'
else:
    '%s saved' % OUTPUT_FILE
    output_handler.close()
