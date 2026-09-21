# Flesh2Leather

A Minecraft Java datapack maintained by **myzticdev**. Cook **1 Rotten Flesh into
1 Leather** in a furnace (10 seconds), or a smoker from 1.14 onward (5 seconds).
Each recipe awards 0.35 experience. No resource pack, functions, tick loop, or
other gameplay changes.

## Compatibility

| Download suffix | Java versions | Data pack format |
| --- | --- | --- |
| `1.13.x` | 1.13–1.13.2 (furnace only) | 4 |
| `1.14.x` | 1.14–1.14.4 | 4 |
| `1.15-1.16.1` | 1.15–1.16.1 | 5 |
| `1.16.2-1.16.5` | 1.16.2–1.16.5 | 6 |
| `1.17.x` | 1.17–1.17.1 | 7 |
| `1.18-1.18.1` | 1.18–1.18.1 | 8 |
| `1.18.2` | 1.18.2 | 9 |
| `1.19-1.19.3` | 1.19–1.19.3 | 10 |
| `1.19.4` | 1.19.4 | 12 |
| `1.20-1.20.1` | 1.20–1.20.1 | 15 |
| `1.20.2-26.3` | 1.20.2–26.3 | 18–121.0 |

26.3 is the official version name, without a `1.` prefix. Snapshot support is
not promised. Validation checks JSON, metadata, recipe schemas, effective overlay
selection, and archive structure. In-game testing across these releases is still
pending; schema validation alone does not establish tested gameplay compatibility.

## Install

1. Download the matching `Flesh2Leather-<range>.zip` from
   [Releases](https://github.com/myzticdev/flesh2leather/releases).
2. Place that ZIP in your world's `datapacks/` folder. Install only one variant.
3. Reopen the world or run `/reload` with appropriate permissions.
4. Check `/datapack list enabled`, then cook rotten flesh with fuel.

If using the all-versions bundle, extract it first and choose one inner ZIP.
Do not install the master bundle itself.

## Build

Requires Python 3.11 or newer; no third-party packages. From the repository root:

```sh
python scripts/build.py
```

On Windows installations using the Python launcher, use `py scripts/build.py`.
The command validates all source JSON and pack metadata, recipe contents, overlay
ranges, and ZIP roots. It safely recreates `dist/` and writes archives in sorted
order with fixed timestamps and permissions. Each ZIP is checked for integrity
and exact contents. Validation errors exit nonzero. ZIPs use uncompressed entries
for identical output across platforms and compression-library versions.

Editable packs and `targets.json` live in `src/`; tooling lives in `scripts/`.
`dist/` is ignored by Git and contains only these reproducible outputs:

- Eleven `Flesh2Leather-<range>.zip` files matching the table above.
- `SHA256SUMS.txt`, covering the eleven individual ZIPs.
- `Flesh2Leather-myzticdev-All-Versions.zip`, containing those ZIPs and checksums.

Never edit `dist/` files. Edit source and rebuild.

## Maintaining compatibility

Before adding a release, check its official technical changelog and test the pack
in that version: enable/reload without recipe errors, then verify one leather per
rotten flesh, furnace/smoker timing, and no unrelated recipes.

For a legacy split, copy the closest pack under `src/`, update its `pack.mcmeta`
and `README.txt`, and add the version range and format to `src/targets.json`.
Split on format or recipe incompatibility; 1.13 and 1.14 are separate because
smokers were introduced in 1.14 despite both using format 4.

For the modern pack, update its metadata, target name, source directory, and the
explicit format boundaries in `scripts/build.py` together. Add an overlay when
recipe syntax, directory layout, or cooking behavior changes. Keep both old and
new metadata representations consistent and cap the range at the checked release.
Current overlays cover result stacks (41), singular recipe paths (48), simplified
ingredients (57), and revised smoker timing (121). The old `supported_formats`
range ends at 81; `min_format`/`max_format` cover 18.0–121.0. Update this table and
the changelog after checking boundaries. Do not extend the range speculatively.

Technical references: [multi-version packs](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-20-2),
[result stacks](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-20-5),
[directory names](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-21),
[ingredients](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-21-2),
[pack metadata](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-21-9),
[26.3 cooking recipes](https://www.minecraft.net/en-us/article/minecraft-java-edition-26-3).

## Release

Pushes and pull requests run `.github/workflows/ci.yml` and retain build artifacts.
After validation and in-game checks, add a dated `CHANGELOG.md` entry, commit the
source, and push a `vMAJOR.MINOR.PATCH` tag (for example `v1.0.0`).
`.github/workflows/release.yml` runs the same build, requires a matching changelog
entry, and publishes all thirteen files with that entry as release notes.
