import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import { readdirSync, readFileSync } from 'fs';
import { join, basename } from 'path';
import { fileURLToPath } from 'url';

const docsDir = join(fileURLToPath(import.meta.url), '../../docs');

function getTitle(filePath) {
  try {
    const m = readFileSync(filePath, 'utf-8').match(/^title:\s*(.+)$/m);
    return m ? m[1].trim() : basename(filePath, '.md');
  } catch { return basename(filePath, '.md'); }
}

function mdFiles(dir, exclude = ['index.md', 'template.md']) {
  return readdirSync(dir)
    .filter(f => f.endsWith('.md') && !exclude.includes(f))
    .sort()
    .reverse();
}

function timeReportItems(subdir) {
  const dir = join(docsDir, subdir);
  return mdFiles(dir).map(f => ({
    label: basename(f, '.md'),
    link: `/${subdir}/${basename(f, '.md')}`,
  }));
}

function reportsBySectionItems() {
  const dir = join(docsDir, 'reports');
  const files = mdFiles(dir);
  const months = {};
  for (const f of files) {
    const m = f.match(/^(\d{6})/);
    if (!m) continue;
    const key = m[1];
    (months[key] ??= []).push(f);
  }
  return Object.keys(months).sort().reverse().map(key => ({
    label: `${key.slice(0, 4)}-${key.slice(4, 6)}`,
    collapsed: true,
    items: months[key].map(f => ({
      label: getTitle(join(dir, f)),
      link: `/reports/${basename(f, '.md')}`,
    })),
  }));
}

export default defineConfig({
  site: 'https://useakat.github.io',
  base: '/xClaude',
  integrations: [
    starlight({
      title: 'xClaude Wiki',
      description: 'X・note 発信プロジェクトのドキュメント',
      social: [
        { icon: 'github', label: 'GitHub', href: 'https://github.com/useakat/xClaude' },
      ],
      sidebar: [
        {
          label: 'はじめに',
          items: [
            { label: 'プロジェクト概要', link: '/' },
            { label: 'アーキテクチャ', link: '/architecture' },
            { label: 'データベース', link: '/database' },
            { label: '変更ログ', link: '/changelog' },
          ],
        },
        {
          label: 'スキル',
          items: [
            { label: 'スキル一覧', link: '/skills' },
          ],
        },
        {
          label: 'ワークフロー',
          autogenerate: { directory: 'workflows' },
        },
        {
          label: 'スクリプト',
          autogenerate: { directory: 'scripts' },
        },
        {
          label: 'スタイルガイド',
          autogenerate: { directory: 'style' },
        },
        {
          label: '報告書',
          items: [
            { label: '日報', collapsed: true, items: timeReportItems('reports/daily') },
            { label: '週報', collapsed: true, items: timeReportItems('reports/weekly') },
            { label: '月報', collapsed: true, items: timeReportItems('reports/monthly') },
            { label: '計画', collapsed: true, autogenerate: { directory: 'plans' } },
            { label: '変更報告書', collapsed: true, items: reportsBySectionItems() },
          ],
        },
      ],
    }),
  ],
});
