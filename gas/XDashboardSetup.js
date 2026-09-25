/**
 * X分析ダッシュボード（「発信記録」スプレッドシートの「Xダッシュボード」タブ）の
 * データ検証・グラフ設定を行う一回限りのセットアップ関数。
 *
 * mcp-gsheets（MCP ツール）にはデータ検証設定・グラフの積み上げ/色指定を行う
 * API が無いため、GAS 側から Apps Script の SpreadsheetApp API で設定する。
 *
 * 実行方法: Apps Script エディタでこのファイルを開き、
 * 関数 setupXDashboardExtras を選択して実行するか、
 * `clasp run setupXDashboardExtras` で実行する。
 *
 * 冪等: 何度実行してもデータ検証・グラフ設定は上書きされるだけで副作用はない。
 */

function setupXDashboardExtras() {
  const SPREADSHEET_ID = '1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c'; // 発信記録
  const DASHBOARD_SHEET_NAME = 'Xダッシュボード';
  const FOLLOW_CHART_ID = 688896550; // 「新規フォロー／フォロー解除」グラフ

  const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  const dash = ss.getSheetByName(DASHBOARD_SHEET_NAME);
  if (!dash) {
    throw new Error(`シート "${DASHBOARD_SHEET_NAME}" が見つかりません`);
  }

  // ── データ検証: 対象期間_Start / End は日付のみ ──────────────
  const dateRule = SpreadsheetApp.newDataValidation()
    .requireDate()
    .setAllowInvalid(false)
    .setHelpText('日付を入力してください（例: 2026/09/14）')
    .build();
  dash.getRange('C3:C4').setDataValidation(dateRule);

  // ── データ検証: グラフ粒度はリストから選択 ──────────────────
  const granularityRule = SpreadsheetApp.newDataValidation()
    .requireValueInList(['日次', '週次', '月次'], true)
    .setAllowInvalid(false)
    .setHelpText('日次・週次・月次のいずれかを選択してください')
    .build();
  dash.getRange('C6').setDataValidation(granularityRule);

  Logger.log('データ検証を設定しました: C3:C4=日付 / C6=リスト(日次,週次,月次)');

  // ── グラフ④「新規フォロー／フォロー解除」を積み上げ縦棒＋色指定に変更 ──
  const charts = dash.getCharts();
  let target = charts.find(c => c.getChartId() === FOLLOW_CHART_ID);

  if (!target) {
    // フォールバック: タイトル一致で検索（チャートID変更時の保険）
    target = charts.find(c => {
      const title = c.getOptions().get('title');
      return title === '新規フォロー／フォロー解除';
    });
  }

  if (!target) {
    Logger.log('警告: 対象のグラフが見つかりませんでした（chartId=' + FOLLOW_CHART_ID + '）。手動確認が必要です。');
    return;
  }

  const updated = target.modify()
    .setOption('isStacked', true)
    .setOption('series', {
      0: { color: '#1D9BF0' }, // 新規フォロー = 青
      1: { color: '#F4212E' }, // フォロー解除（負値） = 赤
    })
    .build();
  dash.updateChart(updated);

  Logger.log('グラフを積み上げ縦棒（青=新規フォロー / 赤=フォロー解除）に更新しました: chartId=' + updated.getChartId());
  Logger.log('セットアップ完了');
}
