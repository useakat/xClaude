/**
 * Drive の analytics_tmp フォルダにある X アナリティクス CSV を読み込み、
 * X投稿一覧シートの 詳細表示（AA）・リンククリック（AB）・フォロー増（AC）を更新する
 *
 * 実行方法: updateXAnalytics() を手動またはトリガーから呼び出す
 */

const X_ANALYTICS_CONFIG = {
  FOLDER_ID: '1J45co5hN74gzxNateNRyeDtswZu0lMr3', // Xanalytics/tmp フォルダID
  SHEET_NAME: 'X投稿一覧',

  // CSV列インデックス（0始まり）
  CSV_COL_POST_LINK:     3,
  CSV_COL_NEW_FOLLOWS:   9,
  CSV_COL_DETAIL_EXPANDS: 13,
  CSV_COL_URL_CLICKS:    14,

  // スプレッドシート列番号（1始まり）
  COL_POST_URL:       2,  // B列
  COL_DETAIL_EXPANDS: 27, // AA列
  COL_URL_CLICKS:     28, // AB列
  COL_NEW_FOLLOWS:    29, // AC列
};

// ========================================
// メイン処理
// ========================================

/**
 * analytics_tmp フォルダの最新 CSV → X投稿一覧 AA:AC 列を更新
 */
function updateXAnalytics() {
  Logger.log('='.repeat(60));
  Logger.log('X アナリティクス更新開始');
  Logger.log('='.repeat(60));

  const csvFile = getLatestAnalyticsCsv_();
  if (!csvFile) {
    Logger.log('❌ CSV ファイルが見つかりません');
    return;
  }
  Logger.log('CSV ファイル: ' + csvFile.getName());

  const csvText = csvFile.getBlob().getDataAsString('UTF-8');
  const csvMap  = parseAnalyticsCsv_(csvText);
  const csvTotal = Object.keys(csvMap).length;
  Logger.log('CSV 投稿数: ' + csvTotal + ' 件');

  if (csvTotal === 0) {
    Logger.log('❌ CSV に有効なデータがありません');
    return;
  }

  const spreadsheet = SpreadsheetApp.openById(CONFIG.SPREADSHEET_ID);
  const sheet = spreadsheet.getSheetByName(X_ANALYTICS_CONFIG.SHEET_NAME);
  if (!sheet) {
    Logger.log('❌ シート「' + X_ANALYTICS_CONFIG.SHEET_NAME + '」が見つかりません');
    return;
  }

  ensureAnalyticsHeaders_(sheet);

  const sheetMap = getSheetStatusIdMap_(sheet);
  Logger.log('シート投稿数: ' + Object.keys(sheetMap).length + ' 件');

  // マッチングして更新対象を収集
  const updates = [];
  Object.keys(csvMap).forEach(function(statusId) {
    if (!sheetMap[statusId]) return;
    updates.push({
      row:    sheetMap[statusId],
      values: [
        csvMap[statusId].detail_expands,
        csvMap[statusId].url_clicks,
        csvMap[statusId].new_follows
      ]
    });
  });

  Logger.log('マッチ件数: ' + updates.length + ' 件 / ' + csvTotal + ' 件');

  if (updates.length === 0) {
    Logger.log('⚠️ 更新対象なし（CSV と シートの投稿が一致しませんでした）');
    return;
  }

  // 行番号順にソートして連続範囲をまとめて一括書き込み
  updates.sort(function(a, b) { return a.row - b.row; });
  batchWriteUpdates_(sheet, updates);

  Logger.log('');
  Logger.log('✅ X投稿一覧 アナリティクス更新完了');
  Logger.log('   CSV ファイル: ' + csvFile.getName());
  Logger.log('   マッチ件数: ' + updates.length + ' 件 / ' + csvTotal + ' 件');
  Logger.log('   更新列: 詳細表示（AA）・リンククリック（AB）・フォロー増（AC）');
  Logger.log('='.repeat(60));
}

// ========================================
// 内部ユーティリティ
// ========================================

/**
 * analytics_tmp フォルダから更新日時が最も新しい CSV ファイルを返す
 */
function getLatestAnalyticsCsv_() {
  const folder = DriveApp.getFolderById(X_ANALYTICS_CONFIG.FOLDER_ID);
  const files  = folder.getFilesByType(MimeType.CSV);

  let latestFile = null;
  let latestDate = new Date(0);

  while (files.hasNext()) {
    const file = files.next();
    const mod  = file.getLastUpdated();
    if (mod > latestDate) {
      latestDate = mod;
      latestFile = file;
    }
  }

  return latestFile;
}

/**
 * CSV テキストをパースして {statusId: {detail_expands, url_clicks, new_follows}} を返す
 *
 * CSV 列レイアウト（0始まり）:
 *   3  = Post Link (https://x.com/usephys/status/{ID})
 *   9  = New follows
 *   13 = Detail Expands
 *   14 = URL Clicks
 */
function parseAnalyticsCsv_(csvText) {
  const rows   = Utilities.parseCsv(csvText);
  const csvMap = {};

  rows.forEach(function(row) {
    if (row.length <= X_ANALYTICS_CONFIG.CSV_COL_URL_CLICKS) return;

    const postLink = row[X_ANALYTICS_CONFIG.CSV_COL_POST_LINK] || '';
    const match    = postLink.match(/\/status\/(\d+)/);
    if (!match) return;

    const statusId = match[1];
    csvMap[statusId] = {
      detail_expands: parseInt(row[X_ANALYTICS_CONFIG.CSV_COL_DETAIL_EXPANDS], 10) || 0,
      url_clicks:     parseInt(row[X_ANALYTICS_CONFIG.CSV_COL_URL_CLICKS],     10) || 0,
      new_follows:    parseInt(row[X_ANALYTICS_CONFIG.CSV_COL_NEW_FOLLOWS],    10) || 0
    };
  });

  return csvMap;
}

/**
 * X投稿一覧 B列のURL群から {statusId: rowNumber} マップを返す（2行目〜）
 */
function getSheetStatusIdMap_(sheet) {
  const lastRow = sheet.getLastRow();
  if (lastRow < 2) return {};

  const urls = sheet.getRange(2, X_ANALYTICS_CONFIG.COL_POST_URL, lastRow - 1, 1).getValues();
  const map  = {};

  urls.forEach(function(row, index) {
    const url   = String(row[0] || '');
    const match = url.match(/\/status\/(\d+)/);
    if (match) {
      map[match[1]] = index + 2; // 行番号（1始まり）
    }
  });

  return map;
}

/**
 * AA1:AC1 にヘッダーがなければ設定する
 */
function ensureAnalyticsHeaders_(sheet) {
  const headerRange = sheet.getRange(1, X_ANALYTICS_CONFIG.COL_DETAIL_EXPANDS, 1, 3);
  const existing    = headerRange.getValues()[0];

  if (existing[0] || existing[1] || existing[2]) return; // 既にある

  headerRange.setValues([['詳細表示', 'リンククリック', 'フォロー増']]);
  headerRange.setFontWeight('bold');
  headerRange.setBackground('#4285f4');
  headerRange.setFontColor('#ffffff');
  Logger.log('ℹ️ AA:AC 列ヘッダーを追加しました');
}

/**
 * 連続する行をまとめてバッチ書き込み（API 呼び出し回数を削減）
 */
function batchWriteUpdates_(sheet, sortedUpdates) {
  let i = 0;
  while (i < sortedUpdates.length) {
    // 連続する行を探す
    let j = i + 1;
    while (j < sortedUpdates.length &&
           sortedUpdates[j].row === sortedUpdates[j - 1].row + 1) {
      j++;
    }

    // i〜j-1 が連続ブロック
    const batchValues = sortedUpdates.slice(i, j).map(function(u) { return u.values; });
    sheet.getRange(
      sortedUpdates[i].row,
      X_ANALYTICS_CONFIG.COL_DETAIL_EXPANDS,
      batchValues.length,
      3
    ).setValues(batchValues);

    Logger.log('  行 ' + sortedUpdates[i].row + '〜' + sortedUpdates[j - 1].row +
               ' (' + batchValues.length + ' 件) 更新');

    i = j;
  }
}

// ========================================
// トリガー設定ヘルパー
// ========================================

/**
 * 毎週月曜 7:00 に updateXAnalytics を実行するトリガーを設定する（初回のみ手動実行）
 */
function setWeeklyAnalyticsTrigger() {
  // 既存トリガーを削除
  ScriptApp.getProjectTriggers().forEach(function(trigger) {
    if (trigger.getHandlerFunction() === 'updateXAnalytics') {
      ScriptApp.deleteTrigger(trigger);
    }
  });

  ScriptApp.newTrigger('updateXAnalytics')
    .timeBased()
    .onWeekDay(ScriptApp.WeekDay.MONDAY)
    .atHour(7)
    .create();

  Logger.log('✅ 毎週月曜 7:00 のトリガーを設定しました');
}
