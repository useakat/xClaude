import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

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
            { label: '日報', collapsed: true, autogenerate: { directory: 'reports/daily' } },
            { label: '週報', collapsed: true, autogenerate: { directory: 'reports/weekly' } },
            { label: '月報', collapsed: true, autogenerate: { directory: 'reports/monthly' } },
            { label: '計画', collapsed: true, autogenerate: { directory: 'plans' } },
          ],
        },
      ],
    }),
  ],
});
