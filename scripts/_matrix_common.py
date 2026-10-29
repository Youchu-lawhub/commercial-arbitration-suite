#!/usr/bin/env python3
"""Offline matrix primitives: strict YAML, phased gates, safe output and CLI.

OQ paths use dotted keys and zero-based indexes, e.g. facts.0.source.
An open OQ covers its listed paths (including descendants), or entity targets.
OQ is substantive case state, NOT pending.py's document-level Q placeholder.
"""
import argparse
import datetime as dt
import json
import math
import os
import re
import sys
from pathlib import Path
from decimal import Decimal, InvalidOperation

from _pymin import require_python

require_python(script_name=Path(__file__).name)
try:
    import yaml
except ImportError:
    yaml = None

ROOT = Path(__file__).resolve().parents[1]
BANNER = 'DRAFT — 待确认草案，不得提交'
SOURCE_RE = re.compile(r'\[source:[^\]\r\n]+\]')
ANCHOR_RE = re.compile(r'^\s*#!\s*锚点\s*[:：]\s*(.*?)\s*$')
ID_RE = re.compile(r'(?:F-\d{3,}|E-(?:CL|DF)\d{2,}-\d{2,}|CL-\d{2,}|DF-\d{2,}|EV-\d{3,}|R-\d{2,}|A-\d{2,}|T-\d{2,})\Z')
UNKNOWN_WORDS = {'unknown', 'unverified', 'to be confirmed', '待确认', '待核验'}


class MatrixError(Exception):
    def __init__(self, code, path, message, exit_code=2):
        self.issue = {'code': code, 'path': str(path), 'message': message}
        self.exit_code = exit_code
        super().__init__(message)


def issue(code, path, message):
    return {'code': code, 'path': str(path), 'message': message}


def failure(exc, stage='draft'):
    return {'exit_code': exc.exit_code, 'decision': 'unsupported' if exc.exit_code == 4 else 'malformed',
            'errors': [exc.issue], 'warnings': [], 'allowed_to_draft': False,
            'submission_ready': False, 'checked_stage': stage}


def unknown(value):
    return value is None or (isinstance(value, str) and
           (value.strip().lower() in UNKNOWN_WORDS or '[[' in value))


def filled(value):
    return not unknown(value) and value not in ('', [], {})


def decimal(value):
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
        return None
    try:
        result = Decimal(str(value))
        if not result.is_finite() or len(result.as_tuple().digits) > 1000 or abs(result.adjusted()) > 1000:
            return None
        return result
    except (InvalidOperation, ValueError, OverflowError):
        return None


def iso_date(value):
    if isinstance(value, dt.datetime):
        return False
    if isinstance(value, dt.date):
        return True
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        return False
    try:
        dt.date.fromisoformat(value)
        return True
    except ValueError:
        return False


if yaml is not None:
    class UniqueSafeLoader(yaml.SafeLoader):
        pass

    def _mapping(loader, node, deep=False):
        loader.flatten_mapping(node)
        result = {}
        for key_node, value_node in node.value:
            key = loader.construct_object(key_node, deep=deep)
            if not isinstance(key, str):
                raise MatrixError('YAML_KEY_TYPE', '$', 'YAML 映射键必须是字符串')
            if key in result:
                raise MatrixError('YAML_DUPLICATE_KEY', '$', 'YAML 含重复键')
            result[key] = loader.construct_object(value_node, deep=deep)
        return result

    UniqueSafeLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _mapping)


def _safe_tree(value, ancestors=None, depth=0, budget=None):
    ancestors = set() if ancestors is None else ancestors
    budget = [100000] if budget is None else budget
    budget[0] -= 1
    if depth > 60 or budget[0] < 0:
        raise MatrixError('YAML_LIMIT', '$', '输入嵌套或展开规模超限')
    if isinstance(value, (dict, list)):
        if id(value) in ancestors:
            raise MatrixError('YAML_CYCLE', '$', '不支持递归 YAML 别名')
        ancestors.add(id(value))
        for child in (value.values() if isinstance(value, dict) else value):
            _safe_tree(child, ancestors, depth + 1, budget)
        ancestors.remove(id(value))
    elif not isinstance(value, (str, int, float, bool, type(None), dt.date)):
        raise MatrixError('YAML_VALUE_TYPE', '$', '不支持该 YAML 数据类型')
    elif isinstance(value, float) and not math.isfinite(value):
        raise MatrixError('NUMBER', '$', '数值必须有限')


def load_yaml(path):
    if yaml is None:
        raise MatrixError('DEPENDENCY', '$', '需要现有依赖 PyYAML', 4)
    try:
        text = Path(path).read_text(encoding='utf-8')
        if len(text) > 8 * 1024 * 1024:
            raise MatrixError('INPUT_LIMIT', '$', '输入文件过大', 4)
        data = yaml.load(text, Loader=UniqueSafeLoader)
        _safe_tree(data)
        if not isinstance(data, dict):
            raise MatrixError('TYPE', '$', '顶层必须是映射')
        return data
    except MatrixError:
        raise
    except (OSError, UnicodeError, ValueError, RecursionError, yaml.YAMLError):
        raise MatrixError('INPUT', str(path), '文件不存在、不可读或 YAML 不合法') from None


def dump_yaml(data):
    if yaml is None:
        raise MatrixError('DEPENDENCY', '$', '需要现有依赖 PyYAML', 4)
    return yaml.safe_dump(data, allow_unicode=True, sort_keys=False)


def resolve_path(value, workdir=None):
    p = Path(value).expanduser()
    if not p.is_absolute():
        p = Path(workdir or os.getcwd()).expanduser().resolve() / p
    return p.resolve()


def safe_write(path, text, force=False):
    """Resolve symlinks before policy checks; never write case data into a skill."""
    try:
        raw = Path(path).expanduser().absolute()
        p = raw.resolve()
        for candidate in (raw, p):
            parts = candidate.parts
            if candidate == ROOT or ROOT in candidate.parents or 'data' in parts:
                raise MatrixError('OUTPUT_FORBIDDEN', str(p), '禁止写入技能目录或 data 目录')
            if 'commercial-arbitration-suite' in parts:
                raise MatrixError('OUTPUT_FORBIDDEN', str(p), '禁止写入技能安装目录')
            if any(parent.name == 'skills' and parent.parent.name in ('.qoder', '.claude', '.agents')
                   for parent in candidate.parents):
                raise MatrixError('OUTPUT_FORBIDDEN', str(p), '禁止写入技能安装目录')
        if not p.parent.is_dir():
            raise MatrixError('OUTPUT_PARENT', str(p), '输出父目录必须已存在')
        with p.open('w' if force else 'x', encoding='utf-8') as stream:
            stream.write(text)
        return str(p)
    except MatrixError:
        raise
    except FileExistsError:
        raise MatrixError('OUTPUT_EXISTS', str(path), '输出已存在；显式 --force 才可覆盖') from None
    except (OSError, ValueError, RuntimeError):
        raise MatrixError('OUTPUT', str(path), '不能写入输出路径') from None


class Check:
    def __init__(self, data, stage='draft', profile=None, strict=False):
        self.data, self.stage, self.profile, self.strict = data, stage, profile, strict
        self.errors, self.blocks, self.warnings = [], [], []
        self.questions, self.entities = [], {}
        self._registered_unknown = set()

    def error(self, code, path, message):
        self.errors.append(issue(code, path, message))

    def block(self, code, path, message):
        item = issue(code, path, message)
        if item not in self.blocks:
            self.blocks.append(item)

    def warn(self, code, path, message):
        item = issue(code, path, message)
        if item not in self.warnings:
            self.warnings.append(item)

    def mapping(self, value, path):
        if not isinstance(value, dict):
            self.error('TYPE', path, '必须是映射')
            return {}
        return value

    def listing(self, value, path):
        if not isinstance(value, list):
            self.error('TYPE', path, '必须是列表')
            return []
        return value

    def text(self, value, path):
        if not isinstance(value, str) and value is not None:
            self.error('TYPE', path, '必须是字符串或显式未知')
            return False
        return True

    def enum(self, value, choices, path):
        if not isinstance(value, str) or value not in choices:
            self.error('ENUM', path, '必须使用规定的字符串枚举')
            return False
        return True

    def boolean(self, value, path, tristate=False):
        if type(value) is bool or (tristate and (value is None or value == 'unknown')):
            return True
        self.error('TYPE', path, '必须为布尔值' + ('或 unknown/null' if tristate else ''))
        return False

    def number(self, value, path, minimum=0, allow_unknown=True):
        if unknown(value) and allow_unknown:
            self.gap(path)
            return None
        n = decimal(value)
        if n is None or n < minimum:
            self.error('NUMBER', path, '必须为有限非负数；布尔值不是数值')
            return None
        return n

    def required(self, obj, keys, path):
        for key in keys:
            if key not in obj:
                self.error('MISSING', path + '.' + key if path else key, '缺少结构字段')

    def schema(self, version):
        v = self.data.get('schema')
        if type(v) is not int:
            raise MatrixError('SCHEMA_TYPE', 'schema', 'schema 必须为整数，不能是布尔值')
        if v != version:
            raise MatrixError('SCHEMA_UNSUPPORTED', 'schema', '不支持该 schema；旧案请显式迁移', 4)
        if 'version' in self.data and (type(self.data['version']) is not int or self.data['version'] < 1):
            self.error('VERSION', 'version', 'version 必须为正整数')

    def index(self, name, pattern):
        rows = self.listing(self.data.get(name), name)
        result = {}
        for i, raw in enumerate(rows):
            path = '%s.%s' % (name, i)
            row = self.mapping(raw, path)
            ident = row.get('id')
            if not isinstance(ident, str) or not re.fullmatch(pattern, ident):
                self.error('ID', path + '.id', '编号格式不合法')
            elif ident in result or ident in self.entities:
                self.error('DUPLICATE_ID', path + '.id', '编号重复')
            else:
                result[ident] = row
                self.entities[ident] = path
        return result

    def refs(self, values, index, path, many=True):
        values = self.listing(values, path) if many else [values]
        for i, value in enumerate(values):
            if not isinstance(value, str) or value not in index:
                self.error('DANGLING_REFERENCE', path + ('.%s' % i if many else ''), '引用不存在或类型不合法')
        return [v for v in values if isinstance(v, str) and v in index]

    def load_questions(self):
        rows = self.listing(self.data.get('open_questions'), 'open_questions')
        seen = set()
        for i, raw in enumerate(rows):
            p = 'open_questions.%s' % i
            row = self.mapping(raw, p)
            ident = row.get('id')
            if not isinstance(ident, str) or not re.fullmatch(r'OQ-\d{2,}', ident) or ident in seen:
                self.error('OQ_ID', p + '.id', 'OQ 编号须独立且唯一，如 OQ-01')
            else:
                seen.add(ident)
            self.required(row, ('question', 'owner', 'due', 'impact'), p)
            for key in ('question', 'owner', 'impact'):
                if not isinstance(row.get(key), str) or not row.get(key):
                    self.error('OQ_FIELD', p + '.' + key, '待确认项说明、影响与负责人必须非空')
            due = row.get('due')
            if due not in (None, '', 'unknown') and not iso_date(due):
                self.error('DATE', p + '.due', '期限必须为 ISO 日期或 unknown')
            status = row.get('status', 'open')
            self.enum(status, ('open', 'resolved'), p + '.status')
            if 'blocking' in row:
                self.boolean(row['blocking'], p + '.blocking')
            if 'type' in row:
                self.enum(row['type'], ('fact', 'policy', 'decision', 'legal'), p + '.type')
            paths = row.get('paths', [row['path']] if 'path' in row else [])
            paths = self.listing(paths, p + '.paths')
            targets = self.listing(row.get('targets', []), p + '.targets')
            profiles = self.listing(row.get('profiles', []), p + '.profiles')
            for key, values in (('paths', paths), ('targets', targets), ('profiles', profiles)):
                if any(not isinstance(v, str) or not v for v in values):
                    self.error('TYPE', p + '.' + key, '必须为非空字符串列表')
            if status == 'open':
                self.questions.append(dict(row, paths=[v for v in paths if isinstance(v, str)],
                                           targets=[v for v in targets if isinstance(v, str)]))
                relevant = not profiles or self.profile in profiles
                if row.get('blocking') is True and relevant:
                    self.block('OPEN_BLOCKING_QUESTION', p, '存在适用于本产物的未解决阻断项')

    def covered(self, path):
        for q in self.questions:
            if any(path == p or path.startswith(p + '.') for p in q['paths']):
                return True
            if any(path == self.entities.get(t) or path.startswith(self.entities.get(t, '\0') + '.')
                   for t in q['targets']):
                return True
        return False

    def gap(self, path, critical=False):
        if not self.covered(path):
            if path not in self._registered_unknown:
                self.error('UNREGISTERED_UNKNOWN', path, '未知或缺口须以 OQ paths/targets 登记')
                self._registered_unknown.add(path)
        else:
            self.warn('REGISTERED_GAP', path, '待确认：已登记 OQ，不可表述为已核验')
        if critical:
            self.block('UNVERIFIED', path, '实际依赖内容尚未核验或补齐')

    def need(self, value, path, critical=True):
        if not filled(value):
            self.gap(path, critical)
            return False
        return True

    def unknowns(self, value=None, path=''):
        value = self.data if value is None and not path else value
        if isinstance(value, dict):
            for key, child in value.items():
                if key in ('open_questions', 'legacy_payload'):
                    continue
                child_path = path + '.' + key if path else key
                if key in ('verified', 'relied_on', 'self_review', 'adverse', 'background',
                           'own_weakness_reviewed', 'counsel_confirmed', 'bilingual_required',
                           'consent_award_requested'):
                    self.boolean(child, child_path)
                elif key in ('ny', 'flag', 'applicable', 'state_link'):
                    self.boolean(child, child_path, tristate=True)
                self.unknowns(child, child_path)
        elif isinstance(value, list):
            for i, child in enumerate(value):
                self.unknowns(child, path + '.' + str(i))
        elif unknown(value):
            self.gap(path)

    def result(self, **extra):
        errors = self.errors + (self.blocks if self.strict else [])
        code = 2 if self.errors else 3 if self.strict and self.blocks else 0
        warnings = self.warnings + ([] if self.strict else self.blocks)
        result = {'exit_code': code, 'decision': 'malformed' if self.errors else 'blocked' if code else 'pass',
                  'errors': errors, 'warnings': warnings, 'allowed_to_draft': not self.errors,
                  'submission_ready': not self.errors and not self.blocks, 'checked_stage': self.stage,
                  'profile': self.profile}
        result.update(extra)
        return result


def question(number, paths, text='请根据用户材料核实并补齐此块', blocking=False, kind='fact'):
    return {'id': 'OQ-%02d' % number, 'question': text, 'type': kind,
            'paths': paths, 'impact': '影响相应字段的核验与使用', 'owner': 'user',
            'due': 'unknown', 'status': 'open', 'blocking': blocking}


def render_view(data, result, title, workflow, profile):
    workflow_id = {'case-construction': '01-case-file', 'clause-audit': '02-clause-diagnosis',
                   'enforcement': '14-cross-border-enforcement'}.get(workflow, workflow)
    meta = {'case': data.get('case', ''), 'pair': False, 'delivery_state': 'draft',
            'submission_ready': False, 'workflow': workflow_id, 'profile': profile,
            'generated_view': True}
    lines = ['---', dump_yaml(meta).rstrip(), '---', '# ' + title, '', BANNER, '',
             '内部完整阅读视图；不得作为仲裁庭提交件。修改数据源后重新生成。',
             '“已核验”仅表示填报核验状态，脚本不代替律师阅卷或法律判断。', '']
    if workflow == 'case-construction':
        lines += ['法律家族只用于组织论证，不自动产生法域或准据法结论。', '']
    for key, value in data.items():
        lines += ['## ' + key, '']
        rows = value if isinstance(value, list) else [value]
        if not rows:
            lines += ['无登记条目。', '']
        for row in rows:
            verified = isinstance(row, dict) and row.get('verified') is True
            lines += ['**已核验（填报）**' if verified else '**待确认／未声明核验**', '']
            text = dump_yaml(row).rstrip()
            fence = '`' * max(3, max((len(x) for x in re.findall(r'`+', text)), default=0) + 1)
            lines += [fence + 'yaml', text, fence, '']
    lines += ['## 校验状态（不替代交付校验）', '', '```json',
              json.dumps(result, ensure_ascii=False, indent=2, default=str), '```', '']
    return '\n'.join(lines)


def checked_file(path, stage, profile, validator):
    try:
        return validator(load_yaml(path), stage=stage, profile=profile, base_path=Path(path).resolve())
    except MatrixError as exc:
        return failure(exc, stage)
    except (TypeError, ValueError, KeyError, IndexError, AttributeError, RecursionError, OverflowError):
        return failure(MatrixError('TYPE', '$', '字段类型或嵌套结构不合法'), stage)


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise MatrixError('ARGUMENTS', '$', '命令参数不合法；请使用 --help', 4)


def cli(module, argv=None):
    """Shared commands; module implements optional extra_parser/extra_command."""
    argv = list(sys.argv[1:] if argv is None else argv)
    stage = 'draft'
    try:
        parser = Parser(description=module.__doc__)
        parser.add_argument('--json', action='store_true')
        parser.add_argument('--workdir')
        commands = parser.add_subparsers(dest='command', required=True)
        for name in ('init', 'check', 'render', 'summary'):
            sub = commands.add_parser(name)
            sub.add_argument('--json', action='store_true', default=argparse.SUPPRESS)
            sub.add_argument('--workdir', default=argparse.SUPPRESS)
            sub.add_argument('--profile')
            if name == 'init':
                sub.add_argument('--case', default='')
                sub.add_argument('--out', required=True)
                sub.add_argument('--force', action='store_true')
            else:
                sub.add_argument('--in', dest='input', required=True)
                sub.add_argument('--stage', default='draft')
                if name == 'render':
                    sub.add_argument('--out', required=True)
                    sub.add_argument('--force', action='store_true')
        if hasattr(module, 'extra_parser'):
            module.extra_parser(commands)
        args = parser.parse_args(argv)
        stage = getattr(args, 'stage', 'draft')
        workdir = getattr(args, 'workdir', None)
        for key in ('input', 'out', 'draft', 'file'):
            if getattr(args, key, None):
                value = Path(getattr(args, key)).expanduser()
                if key == 'out':
                    # Preserve the lexical output path as well as its resolved target.
                    value = value if value.is_absolute() else Path(workdir or os.getcwd()).resolve() / value
                else:
                    value = resolve_path(value, workdir)
                setattr(args, key, value)
        if args.command == 'init':
            data = module.init_data(args.case, args.profile)
            out = safe_write(args.out, dump_yaml(data), args.force)
            result = module.check_file(out, profile=args.profile)
            result['output'] = out
        elif args.command in ('check', 'summary', 'render'):
            result = module.check_file(args.input, stage=stage, profile=args.profile)
            if args.command == 'summary' and result['exit_code'] not in (2, 4):
                result['summary'] = module.summarize(load_yaml(args.input))
            if args.command == 'render' and result['exit_code'] not in (2, 4):
                text = module.render(load_yaml(args.input), result, args.profile)
                result['output'] = safe_write(args.out, text, args.force)
        else:
            result = module.extra_command(args)
    except MatrixError as exc:
        result = failure(exc, stage)
    except (OSError, UnicodeError, ValueError, TypeError, RuntimeError):
        result = failure(MatrixError('INPUT', '$', '输入路径或参数不合法'), stage)
    if '--json' in argv:
        print(json.dumps(result, ensure_ascii=False, default=str))
    else:
        print('%s (exit %s)' % (result['decision'], result['exit_code']))
        for item in result['errors'] + result['warnings']:
            print('%s %s: %s' % (item['code'], item['path'], item['message']), file=sys.stderr)
        if 'summary' in result:
            print(json.dumps(result['summary'], ensure_ascii=False, default=str))
        if 'output' in result:
            print(result['output'])
        for key in ('candidates', 'comparisons'):
            if key in result:
                print(json.dumps(result[key], ensure_ascii=False, default=str))
    return result['exit_code']
