"""Validate source packs and build reproducible release archives."""
import hashlib
import io
import json
from pathlib import Path
import re
import shutil
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'src'
DIST = ROOT / 'dist'
MASTER = 'Flesh2Leather-myzticdev-All-Versions.zip'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f'Duplicate JSON key: {key}')
        result[key] = value
    return result


def invalid_constant(value):
    raise ValueError(f'Invalid JSON constant: {value}')


def parse(data):
    return json.loads(data, object_pairs_hook=unique_object, parse_constant=invalid_constant)


def archive(files):
    stream = io.BytesIO()
    # Stored entries avoid compression-library differences across platforms.
    with zipfile.ZipFile(stream, 'w', compression=zipfile.ZIP_STORED) as output:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            output.writestr(info, data)
    data = stream.getvalue()
    with zipfile.ZipFile(io.BytesIO(data)) as packed:
        require(packed.testzip() is None, 'ZIP integrity failure')
        require(packed.namelist() == sorted(files), 'Unexpected ZIP layout')
        for name, content in files.items():
            require(packed.read(name) == content, f'ZIP content mismatch: {name}')
    return data


def check_recipe(recipe, fmt, smoking):
    expected = {
        'type': 'minecraft:smoking' if smoking else 'minecraft:smelting',
        'ingredient': 'minecraft:rotten_flesh' if fmt >= 57 else {'item': 'minecraft:rotten_flesh'},
        'result': {'id': 'minecraft:leather'} if fmt >= 41 else 'minecraft:leather',
        'experience': 0.35,
        'cookingtime': 100 if smoking and fmt < 121 else 200,
    }
    if 'category' in recipe:
        expected['category'] = 'misc'
    require(recipe == expected, f'Invalid recipe for format {fmt}')


def recipe_paths(prefix, fmt, smoker=True):
    folder = 'recipe' if fmt >= 48 else 'recipes'
    base = f'{prefix}data/flesh2leather/{folder}/rotten_flesh_to_leather'
    paths = {base + '.json': False}
    if smoker:
        paths[base + '_smoking.json'] = True
    return paths


def check_pack(files, target):
    meta = parse(files['pack.mcmeta'])
    pack = meta['pack']
    fmt = target['pack_format']
    require(type(fmt) is int and fmt > 0, 'Invalid target format')
    require(pack['pack_format'] == fmt, 'Target and metadata format mismatch')
    require(pack['description'] == 'Flesh2Leather by myzticdev - Smelt rotten flesh into leather.',
            'Unexpected description')
    expected = {'pack.mcmeta', 'README.txt'}
    paths = recipe_paths('', fmt, target['range'] != '1.13.x')
    for path, smoking in paths.items():
        check_recipe(parse(files[path]), fmt, smoking)
    expected.update(paths)
    if target['modern']:
        require(fmt == 18, 'Modern pack must start at format 18')
        require(set(meta) == {'pack', 'overlays'}, 'Unexpected metadata section')
        require(set(pack) == {'description', 'pack_format', 'supported_formats', 'min_format', 'max_format'},
                'Unexpected pack fields')
        require(pack['supported_formats'] == {'min_inclusive': 18, 'max_inclusive': 81},
                'Invalid old-format range')
        require(pack['min_format'] == [18, 0] and pack['max_format'] == [121, 0],
                'Invalid modern compatibility range')
        bounds = [(41, 47), (48, 56), (57, 120), (121, 121)]
        entries = meta['overlays']['entries']
        require(len(entries) == len(bounds), 'Missing or extra overlays')
        for entry, (low, high) in zip(entries, bounds):
            directory = entry['directory']
            require(re.match(r'^[a-z0-9_-]+\Z', directory), 'Unsafe overlay path')
            require(set(entry) == {'directory', 'formats', 'min_format', 'max_format'},
                    'Unexpected overlay fields')
            old_range = low if low == high else {'min_inclusive': low, 'max_inclusive': high}
            require(entry['formats'] == old_range, 'Invalid overlay legacy range')
            require(entry['min_format'] == [low, 0], 'Invalid overlay minimum')
            require(entry['max_format'] == [high, 0 if high == 121 else 2147483647],
                    'Invalid overlay maximum')
            paths = recipe_paths(directory + '/', low)
            for path, smoking in paths.items():
                check_recipe(parse(files[path]), low, smoking)
            expected.update(paths)
        for version in range(18, 122):
            effective = dict(files)
            for entry, (low, high) in zip(entries, bounds):
                if low <= version <= high:
                    prefix = entry['directory'] + '/'
                    effective.update({name[len(prefix):]: content for name, content in files.items()
                                      if name.startswith(prefix)})
            for path, smoking in recipe_paths('', version).items():
                check_recipe(parse(effective[path]), version, smoking)
    else:
        require(set(meta) == {'pack'} and set(pack) == {'pack_format', 'description'},
                'Legacy pack must use single-format metadata')
    require(set(files) == expected, 'Unexpected or missing pack files')


def build():
    targets = parse((SRC / 'targets.json').read_text(encoding='utf-8-sig'))
    require(isinstance(targets, list) and targets, 'Missing release targets')
    names = [target['range'] for target in targets]
    require(len(names) == len(set(names)), 'Duplicate release targets')
    require(all(re.match(r'^[0-9.x-]+\Z', name) for name in names), 'Unsafe target path')
    require(sum(target['modern'] is True for target in targets) == 1, 'Exactly one modern release required')
    require({path.name for path in SRC.iterdir()} == set(names) | {'targets.json'}, 'Unlisted source content')
    releases = {}
    for target in targets:
        source = SRC / target['range']
        require(not source.is_symlink() and source.resolve() == source, 'Unsafe source path')
        files = {}
        for path in sorted(source.rglob('*')):
            require(not path.is_symlink(), f'Source links are not supported: {path.name}')
            if path.is_file():
                text = path.read_text(encoding='utf-8-sig')
                if path.suffix in {'.json', '.mcmeta'}:
                    text = json.dumps(parse(text), indent=2, ensure_ascii=False) + '\n'
                files[path.relative_to(source).as_posix()] = text.replace('\r\n', '\n').encode()
        check_pack(files, target)
        releases[f"Flesh2Leather-{target['range']}.zip"] = archive(files)
    releases['SHA256SUMS.txt'] = ''.join(
        f'{hashlib.sha256(data).hexdigest()}  {name}\n' for name, data in sorted(releases.items())).encode()
    bundle = archive(releases)
    require(not DIST.is_symlink() and DIST.resolve() == ROOT / 'dist', 'Refusing redirected dist directory')
    if DIST.exists():
        require(DIST.is_dir(), 'dist must be a directory')
        require(not any(path.is_symlink() or path.resolve() != DIST / path.relative_to(DIST)
                        for path in DIST.rglob('*')), 'Refusing links inside dist')
        shutil.rmtree(DIST)
    DIST.mkdir()
    for name, data in releases.items():
        (DIST / name).write_bytes(data)
    (DIST / MASTER).write_bytes(bundle)
    print(f'Validated {len(targets)} packs; wrote {len(releases) + 1} release files to dist/.')


if __name__ == '__main__':
    try:
        build()
    except (ValueError, OSError, KeyError, TypeError, zipfile.BadZipFile) as error:
        print(f'Build failed: {error}', file=sys.stderr)
        sys.exit(1)
