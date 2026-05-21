/**
 * リプライ・引用RT一覧を取得してスプレッドシートに書き出すスクリプト
 *
 * 依存関係（既存ファイルで定義済み）:
 * - CONFIG.USER_ID, CONFIG.SPREADSHEET_ID (env.js)
 * - getXOAuth2Service(), checkAuthStatus(), logAPIError() (Code.js)
 * - callXAPI(), getUserIdByUsername() (tweetRecord.js)
 */

// ========================================
// 設定
// ========================================

const REPLY_QUOTE_CONFIG = {
  SHEET_NAME: 'リプ・引用一覧',
  DAYS_BACK: 2  // 過去2日分を取得（漏れ防止のため余裕を持たせる）
};

// ========================================
// メイン処理
// ========================================

/**
 * リプライ・引用RTを取得してシートを更新（トリガーからも呼ぶ）
 */
function updateRepliesAndQuotes() {
  try {
    Logger.log('\n' + '='.repeat(60));
    Logger.log('リプライ・引用RT 取得開始');
    Logger.log('='.repeat(60));

    if (!checkAuthStatus()) {
      throw new Error('認証が必要です。authorizeX() を実行してください');
    }

    // ユーザー名 → 数値IDに変換
    let numericUserId = CONFIG.USER_ID;
    if (!/^\d+$/.test(String(numericUserId))) {
      Logger.log('数値IDに変換中...');
      numericUserId = getUserIdByUsername(numericUserId);
    }
    Logger.log(`ユーザーID: ${numericUserId}`);

    const startTime = new Date();
    startTime.setDate(startTime.getDate() - REPLY_QUOTE_CONFIG.DAYS_BACK);
    const startTimeStr = startTime.toISOString();
    Logger.log(`取得期間: ${startTime.toLocaleDateString()} 〜 今`);

    // リプライ取得
    Logger.log('\n--- リプライ取得 ---');
    const replies = fetchReplies(numericUserId, startTimeStr);
    Logger.log(`リプライ: ${replies.length}件`);

    // 引用RT取得
    Logger.log('\n--- 引用RT取得 ---');
    const quotes = fetchQuoteRTs(startTimeStr);
    Logger.log(`引用RT: ${quotes.length}件`);

    const allItems = replies.concat(quotes);
    Logger.log(`\n合計: ${allItems.length}件`);

    if (allItems.length > 0) {
      writeRepliesAndQuotesToSheet(allItems);
    } else {
      Logger.log('⚠️ 新規データなし');
    }

    Logger.log('\n' + '='.repeat(60));
    Logger.log('✅ 完了');
    Logger.log('='.repeat(60) + '\n');

  } catch (error) {
    Logger.log('\n❌ エラー: ' + error.message);
    throw error;
  }
}

// ========================================
// データ取得
// ========================================

/**
 * メンション API からリプライを取得（セルフリプ除外）
 */
function fetchReplies(numericUserId, startTimeStr) {
  const service = getXOAuth2Service();
  const replies = [];
  let nextToken = null;

  do {
    const params = {
      'tweet.fields': 'created_at,text,referenced_tweets,author_id,note_tweet',
      'expansions': 'referenced_tweets.id',
      'max_results': 100,
      'start_time': startTimeStr
    };
    if (nextToken) {
      params['pagination_token'] = nextToken;
    }

    const queryString = Object.keys(params)
      .map(k => encodeURIComponent(k) + '=' + encodeURIComponent(params[k]))
      .join('&');

    const url = `https://api.x.com/2/users/${numericUserId}/mentions?${queryString}`;
    const options = {
      method: 'get',
      headers: { 'Authorization': `Bearer ${service.getAccessToken()}` },
      muteHttpExceptions: true
    };

    const response = UrlFetchApp.fetch(url, options);
    const statusCode = response.getResponseCode();
    const responseText = response.getContentText();

    if (statusCode !== 200) {
      logAPIError(statusCode, responseText, 'メンション取得');
      break;
    }

    const data = JSON.parse(responseText);

    if (data.data && data.data.length > 0) {
      data.data.forEach(tweet => {
        // セルフリプ除外
        if (tweet.author_id === numericUserId) return;

        // リプライのみ採用（replied_to を参照しているもの）
        const ref = tweet.referenced_tweets && tweet.referenced_tweets[0];
        if (!ref || ref.type !== 'replied_to') return;

        const parentId = ref.id;
        replies.push({
          id: tweet.id,
          created_at: tweet.created_at,
          text: (tweet.note_tweet && tweet.note_tweet.text) || tweet.text || '',
          type: 'リプライ',
          parentUrl: `https://x.com/usephys/status/${parentId}`
        });
      });
    } else {
      break;
    }

    nextToken = data.meta && data.meta.next_token ? data.meta.next_token : null;
    if (nextToken) Utilities.sleep(1000);

  } while (nextToken);

  return replies;
}

/**
 * 検索 API から引用RTを取得
 */
function fetchQuoteRTs(startTimeStr) {
  const service = getXOAuth2Service();
  const username = CONFIG.USER_ID.replace('@', '');
  const quotes = [];
  let nextToken = null;

  // よーんの投稿URLを含む（=引用RT）かつ自分の投稿を除外
  const query = `(url:"x.com/${username}/status" OR url:"twitter.com/${username}/status") -from:${username}`;

  do {
    const params = {
      'query': query,
      'tweet.fields': 'created_at,text,referenced_tweets,author_id,note_tweet',
      'expansions': 'referenced_tweets.id',
      'max_results': 100,
      'start_time': startTimeStr
    };
    if (nextToken) {
      params['next_token'] = nextToken;
    }

    const queryString = Object.keys(params)
      .map(k => encodeURIComponent(k) + '=' + encodeURIComponent(params[k]))
      .join('&');

    const url = `https://api.x.com/2/tweets/search/recent?${queryString}`;
    const options = {
      method: 'get',
      headers: { 'Authorization': `Bearer ${service.getAccessToken()}` },
      muteHttpExceptions: true
    };

    const response = UrlFetchApp.fetch(url, options);
    const statusCode = response.getResponseCode();
    const responseText = response.getContentText();

    if (statusCode !== 200) {
      logAPIError(statusCode, responseText, '引用RT検索');
      break;
    }

    const data = JSON.parse(responseText);

    Logger.log(`  検索結果: ${data.meta ? data.meta.result_count + '件' : 'meta なし'}`);

    if (data.data && data.data.length > 0) {
      data.data.forEach(tweet => {
        const refs = tweet.referenced_tweets || [];
        // referenced_tweets の中から quoted を探す（先頭固定にしない）
        const quotedRef = refs.find(r => r.type === 'quoted');
        if (!quotedRef) return;

        const parentId = quotedRef.id;
        quotes.push({
          id: tweet.id,
          created_at: tweet.created_at,
          text: (tweet.note_tweet && tweet.note_tweet.text) || tweet.text || '',
          type: '引用RT',
          parentUrl: `https://x.com/${username}/status/${parentId}`
        });
      });
    } else {
      break;
    }

    nextToken = data.meta && data.meta.next_token ? data.meta.next_token : null;
    if (nextToken) Utilities.sleep(1000);

  } while (nextToken);

  return quotes;
}

// ========================================
// シート書き出し
// ========================================

/**
 * シートにヘッダーを設定
 */
function initReplySheet(sheet) {
  const headers = ['投稿日時', 'ポストURL', 'ポスト本文', 'ポスト種類', '親ポストURL'];
  sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
  sheet.getRange(1, 1, 1, headers.length).setFontWeight('bold');
  sheet.getRange(1, 1, 1, headers.length).setBackground('#34a853');
  sheet.getRange(1, 1, 1, headers.length).setFontColor('#ffffff');
  sheet.setFrozenRows(1);
  sheet.setColumnWidth(1, 160);
  sheet.setColumnWidth(2, 220);
  sheet.setColumnWidth(3, 500);
  sheet.setColumnWidth(4, 80);
  sheet.setColumnWidth(5, 220);
}

/**
 * 既存データの tweet ID を Map で取得（重複排除用）
 */
function getExistingTweetIds(sheet) {
  const existingIds = new Map();
  const lastRow = sheet.getLastRow();
  if (lastRow <= 1) return existingIds;

  const urls = sheet.getRange(2, 2, lastRow - 1, 1).getValues();
  urls.forEach((row, index) => {
    const url = row[0];
    if (url && typeof url === 'string') {
      const match = url.match(/status\/(\d+)/);
      if (match) {
        existingIds.set(match[1], index + 2);
      }
    }
  });
  return existingIds;
}

/**
 * リプライ・引用RTをシートに追記
 */
function writeRepliesAndQuotesToSheet(items) {
  const spreadsheet = SpreadsheetApp.openById(CONFIG.SPREADSHEET_ID);
  let sheet = spreadsheet.getSheetByName(REPLY_QUOTE_CONFIG.SHEET_NAME);

  if (!sheet) {
    sheet = spreadsheet.insertSheet(REPLY_QUOTE_CONFIG.SHEET_NAME);
    initReplySheet(sheet);
    Logger.log(`✅ シート「${REPLY_QUOTE_CONFIG.SHEET_NAME}」を作成しました`);
  }

  const existingIds = getExistingTweetIds(sheet);
  Logger.log(`既存データ: ${existingIds.size}件`);

  const newRows = [];
  let skipCount = 0;

  items.forEach(item => {
    if (existingIds.has(item.id)) {
      skipCount++;
      return;
    }

    const createdAt = new Date(item.created_at);
    const tweetUrl = `https://x.com/i/web/status/${item.id}`;

    newRows.push([
      createdAt,       // A 投稿日時
      tweetUrl,        // B ポストURL
      item.text,       // C ポスト本文
      item.type,       // D ポスト種類
      item.parentUrl   // E 親ポストURL
    ]);
  });

  if (skipCount > 0) {
    Logger.log(`⏭️ 重複スキップ: ${skipCount}件`);
  }

  if (newRows.length === 0) {
    Logger.log('⚠️ 追記する新規データはありません');
    return;
  }

  const startRow = sheet.getLastRow() + 1;
  sheet.getRange(startRow, 1, newRows.length, 5).setValues(newRows);
  sheet.getRange(startRow, 1, newRows.length, 1).setNumberFormat('yyyy/mm/dd hh:mm:ss');
  sheet.getRange(startRow, 3, newRows.length, 1).setWrap(true);

  Logger.log(`✅ ${newRows.length}件を追記しました`);
}

// ========================================
// トリガー管理
// ========================================

/**
 * 毎日AM4:00（JST）に updateRepliesAndQuotes を実行するトリガーを設定
 */
function setupDailyTrigger() {
  // 既存のトリガーを確認して重複防止
  const triggers = ScriptApp.getProjectTriggers();
  for (const trigger of triggers) {
    if (trigger.getHandlerFunction() === 'updateRepliesAndQuotes') {
      Logger.log('⚠️ トリガーはすでに存在します。削除してから再設定する場合は deleteDailyTrigger() を実行してください');
      return;
    }
  }

  ScriptApp.newTrigger('updateRepliesAndQuotes')
    .timeBased()
    .atHour(4)
    .everyDays(1)
    .inTimezone('Asia/Tokyo')
    .create();

  Logger.log('✅ 毎日AM4:00（JST）のトリガーを設定しました');
}

// ========================================
// デバッグ用
// ========================================

/**
 * 引用RT検索APIのレスポンスをそのまま Logger に出力して問題を診断する
 * GASエディタから手動実行して Logger を確認する
 */
function debugQuoteRTSearch() {
  const service = getXOAuth2Service();
  if (!service.hasAccess()) {
    Logger.log('❌ 未認証です。authorizeX() を実行してください');
    return;
  }

  const username = CONFIG.USER_ID.replace('@', '');
  const startTime = new Date();
  startTime.setDate(startTime.getDate() - 7);  // 過去7日で広めに確認
  const startTimeStr = startTime.toISOString();

  const query = `(url:"x.com/${username}/status" OR url:"twitter.com/${username}/status") -from:${username}`;
  Logger.log(`クエリ: ${query}`);
  Logger.log(`開始日時: ${startTimeStr}`);

  const params = {
    'query': query,
    'tweet.fields': 'created_at,text,referenced_tweets,author_id,note_tweet',
    'expansions': 'referenced_tweets.id',
    'max_results': 10,
    'start_time': startTimeStr
  };

  const queryString = Object.keys(params)
    .map(k => encodeURIComponent(k) + '=' + encodeURIComponent(params[k]))
    .join('&');

  const url = `https://api.x.com/2/tweets/search/recent?${queryString}`;
  Logger.log(`URL: ${url}`);

  const response = UrlFetchApp.fetch(url, {
    method: 'get',
    headers: { 'Authorization': `Bearer ${service.getAccessToken()}` },
    muteHttpExceptions: true
  });

  const statusCode = response.getResponseCode();
  const responseText = response.getContentText();
  Logger.log(`HTTPステータス: ${statusCode}`);
  Logger.log('レスポンス:\n' + JSON.stringify(JSON.parse(responseText), null, 2));
}

/**
 * updateRepliesAndQuotes のトリガーを削除
 */
function deleteDailyTrigger() {
  const triggers = ScriptApp.getProjectTriggers();
  let deleted = 0;
  for (const trigger of triggers) {
    if (trigger.getHandlerFunction() === 'updateRepliesAndQuotes') {
      ScriptApp.deleteTrigger(trigger);
      deleted++;
    }
  }
  Logger.log(deleted > 0 ? `✅ ${deleted}件のトリガーを削除しました` : '⚠️ 削除対象のトリガーが見つかりませんでした');
}
