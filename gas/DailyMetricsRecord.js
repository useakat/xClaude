/**
 * X 日次メトリクス自動記録スクリプト
 * 「日次記録」シートに前日のメトリクスを記録
 */

// ========================================
// 設定
// ========================================
// 注意: CLIENT_ID、CLIENT_SECRET、USER_ID、SPREADSHEET_ID は
// env.gs ファイルで定義されている必要があります

const DAILY_METRICS_CONFIG = {
  SHEET_NAME: '日次記録',
  
  // noteのクリエイターID（URLのusephys部分）
  NOTE_USER_ID: 'takaesu7431',  // 例: 'usephys'
  
  // 列の位置（A列=1, B列=2...）
  // 日付,曜日,ポスト数,引用数,セルフリプ数,リプ数,新規リプ数,既存リプ数,リプ返し数,活動合計,
  // 新規フォロー数,フォロバ率,新規フォロヷ数,アンフォロワ数,フォロワ純増,
  // 総フォロワ数,総フォロー数,インプ,プロフ,ブルバフォロワ数, noteフォロワ数, ..., 3M累計インプ
  COLUMNS: {
    DATE: 1,              // A: 日付
    DAY_OF_WEEK: 2,       // B: 曜日
    POST_COUNT: 3,        // C: ポスト数
    QUOTE_COUNT: 4,       // D: 引用数
    SELF_REPLY_COUNT: 5,  // E: セルフリプ数
    REPLY_COUNT: 6,       // F: リプ数
    // G: 新規リプ数（手動）
    // H: 既存リプ数（手動）
    // I: リプ返し数（手動）
    ACTIVITY_TOTAL: 10,   // J: 活動合計（自動）
    // K: 新規フォロー数（手動）
    // L: フォロバ率（手動）
    // M: 新規フォロヷ数（手動）
    // N: アンフォロワ数（手動）
    FOLLOWER_NET: 15,     // O: フォロワ純増（数式）
    TOTAL_FOLLOWERS: 16,  // P: 総フォロワ数
    TOTAL_FOLLOWING: 17,  // Q: 総フォロー数
    // R: インプ（手動）
    // S: プロフ（手動）
    // T: ブルバフォロワ数（手動）
    NOTE_FOLLOWERS: 21,   // U: noteフォロワ数（自動）
    IMPRESSIONS_3M: 26,   // Z: 3M累計インプ（数式）
  }
};

// ========================================
// メイン処理
// ========================================

/**
 * 前日の日次メトリクスを記録
 * 毎朝実行することを想定
 */
function recordDailyMetrics() {
  try {
    Logger.log('\n' + '='.repeat(60));
    Logger.log('日次メトリクス記録開始: ' + new Date());
    Logger.log('='.repeat(60));
    
    // 認証チェック
    if (!checkAuthStatus()) {
      throw new Error('認証が必要です');
    }
    
    // 前日の日付（記入先 & データ取得期間）
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    yesterday.setHours(0, 0, 0, 0);
    
    const yesterdayStr = Utilities.formatDate(yesterday, Session.getScriptTimeZone(), 'yyyy/MM/dd');
    Logger.log(`📅 記入先 / データ取得期間: ${yesterdayStr}`);
    
    // スプレッドシートを開く
    const spreadsheet = SpreadsheetApp.openById(CONFIG.SPREADSHEET_ID);
    let sheet = spreadsheet.getSheetByName(DAILY_METRICS_CONFIG.SHEET_NAME);
    
    if (!sheet) {
      Logger.log(`⚠️ シート「${DAILY_METRICS_CONFIG.SHEET_NAME}」が見つかりません`);
      Logger.log('シートを作成してください');
      return;
    }
    
    // 前日の日付の行を検索、なければ作成
    let targetRow = findRowByDate(sheet, yesterdayStr);
    
    if (!targetRow) {
      const lastRow = sheet.getLastRow();
      targetRow = lastRow + 1;
      const cols = DAILY_METRICS_CONFIG.COLUMNS;
      sheet.getRange(targetRow, cols.DATE).setValue(yesterday);
      sheet.getRange(targetRow, cols.DATE).setNumberFormat('yyyy/mm/dd');
      
      // 曜日を記入
      const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
      const dayOfWeek = dayNames[yesterday.getDay()];
      sheet.getRange(targetRow, cols.DAY_OF_WEEK).setValue(dayOfWeek);
      
      Logger.log(`➕ 新しい行を作成しました: ${targetRow}行目 (${dayOfWeek})`);
    }
    
    Logger.log(`✅ 対象行: ${targetRow}行目`);
    
    // 各メトリクスを取得
    Logger.log('\n--- メトリクス取得開始 ---');
    
    // 1. ポスト数、引用数、セルフリプ数、リプライ数を取得（前日の分）
    const { postCount, quoteCount, selfReplyCount, replyCount } = getPostCounts(yesterday);
    Logger.log(`✅ ポスト数: ${postCount}件（${yesterdayStr}分）`);
    Logger.log(`✅ 引用数: ${quoteCount}件（${yesterdayStr}分）`);
    Logger.log(`✅ セルフリプ数: ${selfReplyCount}件（${yesterdayStr}分）`);
    Logger.log(`✅ リプ数: ${replyCount}件（${yesterdayStr}分）`);
    
    // 2. フォロワー関連を取得（現時点の総数）
    const followerMetrics = getFollowerMetrics();
    Logger.log(`✅ 総フォロワ数: ${followerMetrics.totalFollowers}人`);
    Logger.log(`✅ 総フォロー数: ${followerMetrics.totalFollowing}人`);
    
    // 3. noteフォロワ数を取得
    const noteFollowers = getNoteFollowers();
    Logger.log(`✅ noteフォロワ数: ${noteFollowers}人`);
    
    // シートに書き込み
    Logger.log('\n--- シートに書き込み ---');
    
    const cols = DAILY_METRICS_CONFIG.COLUMNS;
    sheet.getRange(targetRow, cols.POST_COUNT).setValue(postCount);
    sheet.getRange(targetRow, cols.QUOTE_COUNT).setValue(quoteCount);
    sheet.getRange(targetRow, cols.SELF_REPLY_COUNT).setValue(selfReplyCount);
    sheet.getRange(targetRow, cols.REPLY_COUNT).setValue(replyCount);
    
    // 活動合計 = ポスト数 + 引用数 + セルフリプ数 + リプ数
    const activityTotal = postCount + quoteCount + selfReplyCount + replyCount;
    sheet.getRange(targetRow, cols.ACTIVITY_TOTAL).setValue(activityTotal);
    
    sheet.getRange(targetRow, cols.TOTAL_FOLLOWERS).setValue(followerMetrics.totalFollowers);
    sheet.getRange(targetRow, cols.TOTAL_FOLLOWING).setValue(followerMetrics.totalFollowing);
    sheet.getRange(targetRow, cols.NOTE_FOLLOWERS).setValue(noteFollowers);
    
    // フォロワ純増 = 新規フォロヷ数(M) - アンフォロワ数(N)
    sheet.getRange(targetRow, cols.FOLLOWER_NET).setFormula(
      `=IF(M${targetRow}<>"",M${targetRow}-N${targetRow},"")`
    );
    
    // 3M累計インプ（Z列）
    sheet.getRange(targetRow, cols.IMPRESSIONS_3M).setFormula(
      `=IF(R${targetRow}<>"",SUMIFS(R:R,A:A,">="&EDATE(A${targetRow},-3),A:A,"<="&A${targetRow}),)`
    );
    
    Logger.log('✅ シートへの書き込み完了');
    
    Logger.log('\n' + '='.repeat(60));
    Logger.log('✅ 日次メトリクス記録完了');
    Logger.log('='.repeat(60) + '\n');
    
  } catch (error) {
    Logger.log('\n' + '='.repeat(60));
    Logger.log('❌ エラー発生: ' + error.message);
    Logger.log(error.stack);
    Logger.log('='.repeat(60) + '\n');
    throw error;
  }
}

// ========================================
// ヘルパー関数
// ========================================

/**
 * 指定日の0:00:00〜23:59:59のUTC ISO文字列を返す
 * タイムゾーンを正しく考慮する
 */
function getDayTimeRange(date) {
  const timeZone = Session.getScriptTimeZone();
  
  // 指定日の日付文字列（yyyy-MM-dd）をタイムゾーン基準で取得
  const dateStr = Utilities.formatDate(date, timeZone, 'yyyy-MM-dd');
  
  // その日の0:00:00と23:59:59をDateオブジェクトに変換（ローカル時間として解釈）
  const startLocal = new Date(dateStr + 'T00:00:00');
  const endLocal = new Date(dateStr + 'T23:59:59');
  
  // toISOString()はUTCに変換して返す（X APIはUTCのISO8601を受け付ける）
  const tz = Session.getScriptTimeZone();
  return {
    startTimeStr: startLocal.toISOString(),
    endTimeStr: endLocal.toISOString(),
    startJST: Utilities.formatDate(startLocal, tz, 'yyyy-MM-dd HH:mm:ss'),
    endJST: Utilities.formatDate(endLocal, tz, 'yyyy-MM-dd HH:mm:ss')
  };
}

/**
 * シートから日付に対応する行を検索
 */
function findRowByDate(sheet, targetDate) {
  const dateColumn = DAILY_METRICS_CONFIG.COLUMNS.DATE;
  const lastRow = sheet.getLastRow();
  
  if (lastRow < 2) {
    return null;
  }
  
  const dates = sheet.getRange(2, dateColumn, lastRow - 1, 1).getValues();
  
  for (let i = 0; i < dates.length; i++) {
    const cellDate = dates[i][0];
    if (!cellDate) continue;
    
    const formattedDate = Utilities.formatDate(
      new Date(cellDate),
      Session.getScriptTimeZone(),
      'yyyy/MM/dd'
    );
    
    if (formattedDate === targetDate) {
      return i + 2; // 2行目から開始なので+2
    }
  }
  
  return null;
}

/**
 * 前日のポスト数、引用数、リプライ数を取得
 */
function getPostCounts(yesterday) {
  const service = getXOAuth2Service();
  
  if (!service.hasAccess()) {
    throw new Error('未認証です');
  }
  
  let userId = CONFIG.USER_ID;
  
  // ユーザー名の場合は数値IDに変換
  if (!/^\d+$/.test(String(userId))) {
    userId = getUserIdByUsername(userId);
  }
  
  // 前日の開始と終了時刻（タイムゾーン考慮）
  const { startTimeStr, endTimeStr, startJST, endJST } = getDayTimeRange(yesterday);
  Logger.log(`取得期間: ${startJST} 〜 ${endJST} JST`);
  
  const options = {
    method: 'get',
    headers: {
      'Authorization': `Bearer ${service.getAccessToken()}`
    },
    muteHttpExceptions: true
  };
  
  // --- ポスト数と引用数を取得（リプライ・リツイートを除外） ---
  let url1 = `https://api.x.com/2/users/${userId}/tweets?`;
  url1 += `max_results=100`;
  url1 += `&start_time=${startTimeStr}`;
  url1 += `&end_time=${endTimeStr}`;
  url1 += `&tweet.fields=referenced_tweets`;
  url1 += `&exclude=replies,retweets`;
  
  const response1 = UrlFetchApp.fetch(url1, options);
  
  if (response1.getResponseCode() !== 200) {
    logAPIError(response1.getResponseCode(), response1.getContentText(), 'ポスト数取得');
    throw new Error('ポスト数の取得に失敗しました');
  }
  
  const data1 = JSON.parse(response1.getContentText());
  
  let postCount = 0;
  let quoteCount = 0;
  let selfReplyCount = 0;
  
  if (data1.data && data1.data.length > 0) {
    data1.data.forEach(tweet => {
      // セルフリプライを除外してカウント（replied_toがある場合はリプライ）
      const isReply = tweet.referenced_tweets &&
                     tweet.referenced_tweets.some(ref => ref.type === 'replied_to');
      if (isReply) {
        selfReplyCount++;
        return;
      }
      
      const isQuote = tweet.referenced_tweets && 
                     tweet.referenced_tweets.some(ref => ref.type === 'quoted');
      
      if (isQuote) {
        quoteCount++;
      }
      
      postCount++;
    });
  }
  
  // --- リプライ数を取得（リツイートのみ除外） ---
  let url2 = `https://api.x.com/2/users/${userId}/tweets?`;
  url2 += `max_results=100`;
  url2 += `&start_time=${startTimeStr}`;
  url2 += `&end_time=${endTimeStr}`;
  url2 += `&tweet.fields=referenced_tweets`;
  url2 += `&exclude=retweets`;
  
  const response2 = UrlFetchApp.fetch(url2, options);
  
  if (response2.getResponseCode() !== 200) {
    logAPIError(response2.getResponseCode(), response2.getContentText(), 'リプライ数取得');
    throw new Error('リプライ数の取得に失敗しました');
  }
  
  const data2 = JSON.parse(response2.getContentText());
  
  let replyCount = 0;
  
  if (data2.data && data2.data.length > 0) {
    // セルフリプライのIDセットを作成（data1で取得済み）
    const selfReplyIds = new Set();
    if (data1.data) {
      data1.data.forEach(tweet => {
        const isSelfReply = tweet.referenced_tweets &&
                           tweet.referenced_tweets.some(ref => ref.type === 'replied_to');
        if (isSelfReply) selfReplyIds.add(tweet.id);
      });
    }
    
    data2.data.forEach(tweet => {
      const isReply = tweet.referenced_tweets && 
                     tweet.referenced_tweets.some(ref => ref.type === 'replied_to');
      
      // リプライかつセルフリプライでない場合のみカウント
      if (isReply && !selfReplyIds.has(tweet.id)) {
        replyCount++;
      }
    });
  }
  
  return { postCount, quoteCount, selfReplyCount, replyCount };
}

/**
 * フォロワー関連メトリクスを取得
 */
function getFollowerMetrics() {
  const service = getXOAuth2Service();
  
  if (!service.hasAccess()) {
    throw new Error('未認証です');
  }
  
  let userId = CONFIG.USER_ID;
  
  // ユーザー名の場合は数値IDに変換
  if (!/^\d+$/.test(String(userId))) {
    userId = getUserIdByUsername(userId);
  }
  
  // ユーザー情報を取得
  const url = `https://api.x.com/2/users/${userId}?user.fields=public_metrics`;
  
  const options = {
    method: 'get',
    headers: {
      'Authorization': `Bearer ${service.getAccessToken()}`
    },
    muteHttpExceptions: true
  };
  
  const response = UrlFetchApp.fetch(url, options);
  const statusCode = response.getResponseCode();
  
  if (statusCode !== 200) {
    const responseText = response.getContentText();
    logAPIError(statusCode, responseText, 'フォロワー情報取得');
    throw new Error('フォロワー情報の取得に失敗しました');
  }
  
  const data = JSON.parse(response.getContentText());
  const metrics = data.data.public_metrics;
  
  return {
    totalFollowers: metrics.followers_count || 0,
    totalFollowing: metrics.following_count || 0
  };
}

/**
 * noteのフォロワー数を取得（非公式API）
 */
function getNoteFollowers() {
  const noteUserId = DAILY_METRICS_CONFIG.NOTE_USER_ID;
  
  if (!noteUserId || noteUserId === 'YOUR_NOTE_USER_ID_HERE') {
    Logger.log('⚠️ NOTE_USER_IDが設定されていません');
    return 0;
  }
  
  const url = `https://note.com/api/v2/creators/${noteUserId}`;
  
  const response = UrlFetchApp.fetch(url, {
    muteHttpExceptions: true
  });
  
  if (response.getResponseCode() !== 200) {
    Logger.log(`⚠️ note API エラー: ステータス ${response.getResponseCode()}`);
    return 0;
  }
  
  const data = JSON.parse(response.getContentText());
  return data.data.followerCount || 0;
}

// ========================================
// トリガー設定
// ========================================

/**
 * デバッグ用: 指定日のツイート内容を確認
 * 実行してログを共有してください
 */
function debugPostCounts() {
  const service = getXOAuth2Service();
  let userId = CONFIG.USER_ID;
  if (!/^\d+$/.test(String(userId))) {
    userId = getUserIdByUsername(userId);
  }
  
  // 確認したい日付を指定
  const targetDate = new Date('2026-04-17T00:00:00');
  const { startTimeStr, endTimeStr, startJST, endJST } = getDayTimeRange(targetDate);
  Logger.log(`取得期間: ${startJST} 〜 ${endJST} JST`);
  
  const options = {
    method: 'get',
    headers: { 'Authorization': `Bearer ${service.getAccessToken()}` },
    muteHttpExceptions: true
  };
  
  let url = `https://api.x.com/2/users/${userId}/tweets?`;
  url += `max_results=100`;
  url += `&start_time=${startTimeStr}`;
  url += `&end_time=${endTimeStr}`;
  url += `&tweet.fields=referenced_tweets,created_at,text`;
  url += `&exclude=replies,retweets`;
  
  const response = UrlFetchApp.fetch(url, options);
  const data = JSON.parse(response.getContentText());
  
  Logger.log(`取得件数: ${data.data ? data.data.length : 0}件`);
  
  if (data.data) {
    data.data.forEach((tweet, i) => {
      const isQuote = tweet.referenced_tweets &&
                      tweet.referenced_tweets.some(ref => ref.type === 'quoted');
      Logger.log(`\n--- ツイート ${i + 1} ---`);
      Logger.log(`ID: ${tweet.id}`);
      Logger.log(`投稿時刻: ${Utilities.formatDate(new Date(tweet.created_at), Session.getScriptTimeZone(), 'yyyy-MM-dd HH:mm:ss')} JST`);
      Logger.log(`引用RT: ${isQuote}`);
      Logger.log(`本文: ${tweet.text.substring(0, 80)}`);
      if (tweet.referenced_tweets) {
        Logger.log(`referenced_tweets: ${JSON.stringify(tweet.referenced_tweets)}`);
      }
    });
  }
}

/**
 * デバッグ用: 指定日のリプライ内容を確認
 */
function debugReplyCounts() {
  const service = getXOAuth2Service();
  let userId = CONFIG.USER_ID;
  if (!/^\d+$/.test(String(userId))) {
    userId = getUserIdByUsername(userId);
  }
  
  // 確認したい日付を指定
  const targetDate = new Date('2026-04-17T00:00:00');
  const { startTimeStr, endTimeStr, startJST, endJST } = getDayTimeRange(targetDate);
  Logger.log(`取得期間: ${startJST} 〜 ${endJST} JST`);
  
  const options = {
    method: 'get',
    headers: { 'Authorization': `Bearer ${service.getAccessToken()}` },
    muteHttpExceptions: true
  };
  
  // リツイートのみ除外（リプライを含める）
  let url = `https://api.x.com/2/users/${userId}/tweets?`;
  url += `max_results=100`;
  url += `&start_time=${startTimeStr}`;
  url += `&end_time=${endTimeStr}`;
  url += `&tweet.fields=referenced_tweets,created_at,text`;
  url += `&exclude=retweets`;
  
  const response = UrlFetchApp.fetch(url, options);
  const data = JSON.parse(response.getContentText());
  
  let replyCount = 0;
  
  Logger.log(`取得件数: ${data.data ? data.data.length : 0}件`);
  
  if (data.data) {
    data.data.forEach((tweet, i) => {
      const isReply = tweet.referenced_tweets &&
                      tweet.referenced_tweets.some(ref => ref.type === 'replied_to');
      
      if (!isReply) return;
      
      replyCount++;
      Logger.log(`\n--- リプライ ${replyCount} ---`);
      Logger.log(`ID: ${tweet.id}`);
      Logger.log(`投稿時刻: ${Utilities.formatDate(new Date(tweet.created_at), Session.getScriptTimeZone(), 'yyyy-MM-dd HH:mm:ss')} JST`);
      Logger.log(`本文: ${tweet.text.substring(0, 80)}`);
      Logger.log(`referenced_tweets: ${JSON.stringify(tweet.referenced_tweets)}`);
    });
  }
  
  Logger.log(`\nリプライ合計: ${replyCount}件`);
}

/**
 * 毎朝実行するトリガーを設定
 * この関数を1回手動実行すると、以降は自動的に毎朝6時にrecordDailyMetricsが実行されます
 */
function setupDailyTrigger() {
  // 既存のトリガーを削除
  const triggers = ScriptApp.getProjectTriggers();
  triggers.forEach(trigger => {
    if (trigger.getHandlerFunction() === 'recordDailyMetrics') {
      ScriptApp.deleteTrigger(trigger);
      Logger.log('既存のトリガーを削除しました');
    }
  });
  
  // 新しいトリガーを作成（毎朝6時）
  ScriptApp.newTrigger('recordDailyMetrics')
    .timeBased()
    .atHour(6)
    .everyDays(1)
    .create();
  
  Logger.log('✅ トリガーを設定しました: recordDailyMetrics を毎朝6時に実行');
}