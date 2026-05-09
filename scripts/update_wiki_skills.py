#!/usr/bin/env python3
"""
Wiki スキル一覧を自動更新するスクリプト
.claude/skills/ をスキャンして metadata.yaml を更新し、docs/skills/index.md を生成
"""

import os
import yaml
from pathlib import Path
from collections import defaultdict

def get_skill_info(skill_path):
    """SKILL.md から name と description を抽出"""
    skill_md = skill_path / 'SKILL.md'
    if not skill_md.exists():
        return None

    with open(skill_md) as f:
        content = f.read()

    skill_name = skill_path.name
    info = {'name': skill_name, 'description': ''}

    # frontmatter をパース
    if content.startswith('---'):
        lines = content.split('\n')
        frontmatter_end = -1
        for i, line in enumerate(lines[1:], 1):
            if line.startswith('---'):
                frontmatter_end = i
                break

        if frontmatter_end != -1:
            frontmatter = '\n'.join(lines[1:frontmatter_end])
            for line in frontmatter.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    if key in ['name', 'description']:
                        info[key] = value

    # description が empty の場合、スキル名をそのまま使用
    if not info['description']:
        info['description'] = f"{skill_name} スキル"

    return info


def update_metadata(skills_dir, metadata_path):
    """metadata.yaml を更新（新規スキルを自動追加）"""

    # 既存メタデータを読み込み
    if metadata_path.exists():
        with open(metadata_path) as f:
            metadata = yaml.safe_load(f) or {'skills': {}}
    else:
        metadata = {'skills': {}}

    # .claude/skills/ をスキャン
    existing_skills = set()
    for skill_dir in sorted(skills_dir.iterdir()):
        if not skill_dir.is_dir() or skill_dir.name.startswith('.'):
            continue

        skill_name = skill_dir.name
        existing_skills.add(skill_name)

        # 新規スキルの場合、メタデータに追加（カテゴリは「その他」）
        if skill_name not in metadata['skills']:
            metadata['skills'][skill_name] = {'category': 'その他'}

    # 削除されたスキルを metadata から削除
    removed_skills = set(metadata['skills'].keys()) - existing_skills
    for skill_name in removed_skills:
        del metadata['skills'][skill_name]

    # metadata.yaml に保存
    with open(metadata_path, 'w') as f:
        yaml.dump(metadata, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    return metadata


def generate_wiki_index(skills_dir, metadata, output_path):
    """docs/skills/index.md を生成"""

    # スキル情報を取得
    skills_info = {}
    for skill_name in metadata['skills'].keys():
        skill_path = skills_dir / skill_name
        info = get_skill_info(skill_path)
        if info:
            skills_info[skill_name] = info

    # カテゴリごとにグループ化
    categories = defaultdict(list)
    for skill_name, skill_meta in sorted(metadata['skills'].items()):
        category = skill_meta.get('category', 'その他')
        if skill_name in skills_info:
            categories[category].append({
                'name': skill_name,
                'description': skills_info[skill_name]['description'],
            })

    # wiki を生成
    wiki_content = """---
title: スキル一覧
description: Claude Code で使用できるスキルの一覧
---

スキルは `.claude/skills/` に定義されており、チャットで `/スキル名` と入力して呼び出す。

"""

    # カテゴリーの順序を定義
    category_order = [
        'コンテンツ制作',
        'レポート生成',
        'リサーチ・分析',
        '品質チェック',
        'メール・通知',
        '画像・同期',
        '運用・記録',
        '設定・保守',
    ]

    for category in category_order:
        if category not in categories:
            continue

        wiki_content += f"## {category}\n\n"
        wiki_content += "| スキル | 用途 |\n"
        wiki_content += "|---|---|\n"

        for skill in sorted(categories[category], key=lambda x: x['name']):
            wiki_content += f"| `/{skill['name']}` | {skill['description']} |\n"

        wiki_content += "\n"

    # その他のカテゴリ
    if 'その他' in categories:
        wiki_content += "## その他\n\n"
        wiki_content += "| スキル | 用途 |\n"
        wiki_content += "|---|---|\n"

        for skill in sorted(categories['その他'], key=lambda x: x['name']):
            wiki_content += f"| `/{skill['name']}` | {skill['description']} |\n"

    # ファイルに保存
    with open(output_path, 'w') as f:
        f.write(wiki_content)


def main():
    repo_root = Path(os.environ.get('GIT_WORK_TREE', '/root/xClaude'))
    skills_dir = repo_root / '.claude' / 'skills'
    metadata_path = skills_dir / 'metadata.yaml'
    wiki_path = repo_root / 'docs' / 'skills' / 'index.md'

    # metadata.yaml を更新
    metadata = update_metadata(skills_dir, metadata_path)

    # wiki を生成
    generate_wiki_index(skills_dir, metadata, wiki_path)

    print(f"✅ metadata.yaml を更新: {metadata_path}")
    print(f"✅ wiki を生成: {wiki_path}")


if __name__ == '__main__':
    main()
