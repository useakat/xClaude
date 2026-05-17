/**
 * 自分の投稿をスプレッドシートに書き出すスクリプト
 * OAuth2認証関数は既存のものを再利用
 * 
 * 必要な既存変数:
 * - CONFIG.USER_ID (既存のCONFIGから参照)
 * - CONFIG.SPREADSHEET_ID (既存のCONFIGから参照)
 * 
 * 設定可能な項目:
 * - USE_DATE_RANGE: 取得期間の指定方法（true: 日付範囲, false: 日数）
 * - DAYS_BACK: 取得期間（日数、USE_DATE_RANGE=falseの場合）
 * - START_DATE, END_DATE: 取得期間（日付、USE_DATE_RANGE=trueの場合）
 * - INCLUDE_REPLIES: リプライを含めるか（true/false）
 * - INCLUDE_RETWEETS: 他人のリポストを含めるか（true/false）
 */

// ========================================
// 設定項目
// ========================================

const MY_TWEETS_CONFIG = {
  // 注意: USER_ID と SPREADSHEET_ID は既存のCONFIGから参照されます
  
  // シート名
  SHEET_NAME: 'X投稿一覧',
  
  // 取得期間の設定方法（どちらか一方を使用）
  // 方法1: 日数で指定
  DAYS_BACK: 8,  // 過去N日分を取得（USE_DATE_RANGEがfalseの場合に使用）
  
  // 方法2: 開始日と終了日で指定
  USE_DATE_RANGE: false,  // true: 日付範囲で指定, false: 日数で指定
  START_DATE: '2024-01-01',  // 開始日（YYYY-MM-DD形式、USE_DATE_RANGEがtrueの場合に使用）
  END_DATE: '2024-12-31',    // 終了日（YYYY-MM-DD形式、USE_DATE_RANGEがtrueの場合に使用）
  
  // 1回のAPI呼び出しで取得する件数（最大100）
  MAX_RESULTS: 100,
  
  // リプライ（コメント）を含めるか
  INCLUDE_REPLIES: false,  // true: リプライも取得, false: リプライを除外
  
  // 他人のリポストを含めるか（自分の投稿のRTは常に含まれます）
  INCLUDE_RETWEETS: false  // true: 他人のポストのリポストも取得, false: 他人のリポストを除外
};

// ========================================
// 注意: 以下の関数は既存ファイルで定義されています
// - getXOAuth2Service()
// - checkAuthStatus()
// - logAPIError()
// - getUserIdByUsername()
// ========================================

// ========================================
// ポスト取得
// ========================================

/**
 * 自分のポストを取得（ページネーション対応）
 */
function getMyTweets() {
  const service = getXOAuth2Service();
  
  if (!service.hasAccess()) {
    throw new Error('未認証です。authorizeX() を実行してください');
  }
  
  // CONFIG.USER_IDを使用（既存の設定）
  if (!CONFIG.USER_ID || CONFIG.USER_ID === 'YOUR_USER_ID_HERE') {
    throw new Error('CONFIG.USER_ID を設定してください');
  }
  
  let userId = CONFIG.USER_ID;
  
  // ユーザー名の場合は数値IDに変換
  if (!/^\d+$/.test(String(userId))) {
    Logger.log(`USER_IDがユーザー名です。数値IDに変換します...`);
    userId = getUserIdByUsername(userId);
  }
  
  // 取得開始日時・終了日時を計算
  let startTimeStr, endTimeStr;
  
  if (MY_TWEETS_CONFIG.USE_DATE_RANGE) {
    // 日付範囲で指定
    const startDate = new Date(MY_TWEETS_CONFIG.START_DATE);
    const endDate = new Date(MY_TWEETS_CONFIG.END_DATE);
    
    // 終了日の23:59:59に設定
    endDate.setHours(23, 59, 59, 999);
    
    startTimeStr = startDate.toISOString();
    endTimeStr = endDate.toISOString();
    
    Logger.log(`\n取得期間: ${startDate.toLocaleDateString()} 〜 ${endDate.toLocaleDateString()}`);
  } else {
    // 日数で指定
    const startTime = new Date();
    startTime.setDate(startTime.getDate() - MY_TWEETS_CONFIG.DAYS_BACK);
    startTimeStr = startTime.toISOString();
    
    Logger.log(`\n取得期間: ${startTime.toLocaleDateString()} 〜 ${new Date().toLocaleDateString()}`);
  }
  
  const allTweets = [];
  const allMediaInfo = {};  // メディア情報を保存
  let nextToken = null;
  let pageCount = 0;
  
  do {
    pageCount++;
    Logger.log(`\nページ ${pageCount} を取得中...`);
    
    // URLパラメータを構築
    const params = {
      'max_results': MY_TWEETS_CONFIG.MAX_RESULTS,
      'tweet.fields': 'created_at,public_metrics,non_public_metrics,organic_metrics,referenced_tweets,text,note_tweet,entities,attachments',
      'start_time': startTimeStr,
      'expansions': 'referenced_tweets.id,attachments.media_keys',
      'media.fields': 'type,url,preview_image_url'
    };
    
    // 日付範囲モードの場合は終了日も指定
    if (MY_TWEETS_CONFIG.USE_DATE_RANGE && endTimeStr) {
      params['end_time'] = endTimeStr;
    }
    
    // 除外するポスト種類を設定
    const excludeTypes = [];
    if (!MY_TWEETS_CONFIG.INCLUDE_REPLIES) {
      excludeTypes.push('replies');
    }
    if (!MY_TWEETS_CONFIG.INCLUDE_RETWEETS) {
      excludeTypes.push('retweets');
    }
    
    if (excludeTypes.length > 0) {
      params['exclude'] = excludeTypes.join(',');
    }
    
    if (nextToken) {
      params['pagination_token'] = nextToken;
    }
    
    const queryString = Object.keys(params).map(key => {
      return encodeURIComponent(key) + '=' + encodeURIComponent(params[key]);
    }).join('&');
    
    const url = `https://api.x.com/2/users/${userId}/tweets?${queryString}`;
    
    const options = {
      method: 'get',
      headers: {
        'Authorization': `Bearer ${service.getAccessToken()}`
      },
      muteHttpExceptions: true
    };
    
    const response = UrlFetchApp.fetch(url, options);
    const statusCode = response.getResponseCode();
    const responseText = response.getContentText();
    
    if (statusCode !== 200) {
      logAPIError(statusCode, responseText, 'ポスト取得');
      break;
    }
    
    const data = JSON.parse(responseText);
    
    if (data.data && data.data.length > 0) {
      allTweets.push(...data.data);
      Logger.log(`  ${data.data.length}件取得 (累計: ${allTweets.length}件)`);
      
      // メディア情報も保存
      if (data.includes && data.includes.media) {
        data.includes.media.forEach(media => {
          allMediaInfo[media.media_key] = media;
        });
      }
    } else {
      Logger.log(`  データなし`);
      break;
    }
    
    // 次のページがあるかチェック
    nextToken = data.meta && data.meta.next_token ? data.meta.next_token : null;
    
    // レート制限対策: 少し待機
    if (nextToken) {
      Utilities.sleep(1000); // 1秒待機
    }
    
  } while (nextToken);
  
  Logger.log(`\n✅ 取得完了: 合計 ${allTweets.length}件`);
  return {
    tweets: allTweets,
    media: allMediaInfo
  };
}

/**
 * ポストの種類を判定
 */
function getTweetType(tweet) {
  if (!tweet.referenced_tweets || tweet.referenced_tweets.length === 0) {
    return '通常ポスト';
  }
  
  const refType = tweet.referenced_tweets[0].type;
  
  if (refType === 'retweeted') {
    return 'リポスト';
  } else if (refType === 'replied_to') {
    return 'リプライ';
  } else if (refType === 'quoted') {
    return '引用RT';
  }
  
  return '通常ポスト';
}

// ========================================
// デバッグ用関数
// ========================================

/**
 * 最新のポスト1件のメトリクスを確認（デバッグ用）
 */
function debugTweetMetrics() {
  const service = getXOAuth2Service();
  
  if (!service.hasAccess()) {
    Logger.log('❌ 未認証です');
    return;
  }
  
  let userId = CONFIG.USER_ID;
  if (!/^\d+$/.test(String(userId))) {
    userId = getUserIdByUsername(userId);
  }
  
  const url = `https://api.x.com/2/users/${userId}/tweets?max_results=5&tweet.fields=created_at,public_metrics,non_public_metrics,organic_metrics,text,note_tweet`;
  
  const options = {
    method: 'get',
    headers: {
      'Authorization': `Bearer ${service.getAccessToken()}`
    },
    muteHttpExceptions: true
  };
  
  const response = UrlFetchApp.fetch(url, options);
  const statusCode = response.getResponseCode();
  const data = JSON.parse(response.getContentText());
  
  Logger.log('\n' + '='.repeat(60));
  Logger.log('APIレスポンス確認');
  Logger.log('='.repeat(60));
  Logger.log(`HTTPステータス: ${statusCode}`);
  
  if (data.data && data.data.length > 0) {
    Logger.log(`取得件数: ${data.data.length}件\n`);
    
    // 最新5件のメトリクスを表示
    data.data.forEach((tweet, index) => {
      Logger.log('─'.repeat(60));
      Logger.log(`ポスト ${index + 1}`);
      Logger.log('─'.repeat(60));
      Logger.log(`ID: ${tweet.id}`);
      Logger.log(`投稿日時: ${tweet.created_at}`);
      Logger.log(`本文: ${(tweet.text || '').substring(0, 50)}...`);
      
      Logger.log('\n【public_metrics】:');
      if (tweet.public_metrics) {
        Object.keys(tweet.public_metrics).forEach(key => {
          Logger.log(`  ${key}: ${tweet.public_metrics[key]}`);
        });
      } else {
        Logger.log('  なし');
      }
      
      Logger.log('\n【non_public_metrics】:');
      if (tweet.non_public_metrics) {
        Object.keys(tweet.non_public_metrics).forEach(key => {
          Logger.log(`  ${key}: ${tweet.non_public_metrics[key]}`);
        });
      } else {
        Logger.log('  なし');
      }
      
      Logger.log('\n【organic_metrics】:');
      if (tweet.organic_metrics) {
        Object.keys(tweet.organic_metrics).forEach(key => {
          Logger.log(`  ${key}: ${tweet.organic_metrics[key]}`);
        });
      } else {
        Logger.log('  なし');
      }
      Logger.log('');
    });
    
    Logger.log('='.repeat(60) + '\n');
  } else {
    Logger.log('ポストが取得できませんでした');
    Logger.log('APIレスポンス:');
    Logger.log(JSON.stringify(data, null, 2));
    Logger.log('='.repeat(60) + '\n');
  }
}

// ========================================
// スプレッドシート出力
// ========================================

/**
 * スプレッドシートに書き出し（追記モード）
 */
function writeToSheet(tweets, mediaInfo) {
  mediaInfo = mediaInfo || {};  // メディア情報がない場合は空オブジェクト
  const spreadsheet = SpreadsheetApp.openById(CONFIG.SPREADSHEET_ID);
  let sheet = spreadsheet.getSheetByName(MY_TWEETS_CONFIG.SHEET_NAME);
  
  // シートが存在しない場合は作成
  if (!sheet) {
    sheet = spreadsheet.insertSheet(MY_TWEETS_CONFIG.SHEET_NAME);
    
    // ヘッダー行を作成（26列）
    const headers = [
      '投稿日時',         // A
      'ポストURL',        // B
      'ポスト本文',       // C
      'ポスト種類',       // D
      '文字数',           // E
      'ハッシュタグ',     // F
      '画像枚数',         // G
      '画像URL',          // H
      '画像プレビュー',   // I
      '親ポストID',       // J
      'インプレッション', // K
      'いいね',           // L
      'リポスト',         // M
      'リプライ',         // N
      'ブックマーク',     // O
      'エンゲージメント', // P
      'プロフアクセス',   // Q
      'エンゲ率',         // R
      'いいね率',         // S
      'リポスト率',       // T
      'プロフ率',         // U
      'ブクマ率',         // V
      'エンゲリポスト率', // W
      'エンゲプロフ率',   // X
      'エンゲブクマ率',   // Y
      '目的'              // Z
    ];
    
    sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
    sheet.getRange(1, 1, 1, headers.length).setFontWeight('bold');
    sheet.getRange(1, 1, 1, headers.length).setBackground('#4285f4');
    sheet.getRange(1, 1, 1, headers.length).setFontColor('#ffffff');
    sheet.setFrozenRows(1);
    
    Logger.log(`✅ シート「${MY_TWEETS_CONFIG.SHEET_NAME}」を作成しました`);
  }
  
  // 既存のポストIDとその行番号を取得（重複チェック＆更新用）
  const existingTweetIds = new Map();  // key: tweetId, value: row number
  const lastRow = sheet.getLastRow();
  
  if (lastRow > 1) {
    // ポストURL列（B列=2列目）からIDを抽出
    const urlColumn = sheet.getRange(2, 2, lastRow - 1, 1).getValues();
    urlColumn.forEach((row, index) => {
      const url = row[0];
      // urlが文字列かつ空でない場合のみ処理
      if (url && typeof url === 'string') {
        // URLからポストIDを抽出
        const match = url.match(/status\/(\d+)/);
        if (match) {
          existingTweetIds.set(match[1], index + 2);  // 行番号（2行目から開始）
        }
      }
    });
    
    Logger.log(`既存データ: ${existingTweetIds.size}件`);
  }
  
  // データ行を作成（重複を除外、既存ポストは更新）
  const newRows = [];
  const updateRows = [];  // 更新対象のポスト
  let duplicateCount = 0;
  let updateCount = 0;
  
  tweets.forEach(tweet => {
    const publicMetrics = tweet.public_metrics || {};
    const nonPublicMetrics = tweet.non_public_metrics || {};
    const organicMetrics = tweet.organic_metrics || {};
    
    const createdAt = new Date(tweet.created_at);
    const tweetType = getTweetType(tweet);
    
    // ポスト本文（全文）
    let text = '';
    if (tweet.note_tweet && tweet.note_tweet.text) {
      text = tweet.note_tweet.text;
    } else {
      text = tweet.text || '';
    }
    
    const charCount = text.length;
    
    // ハッシュタグの抽出
    let hashtags = '';
    if (tweet.entities && tweet.entities.hashtags) {
      const hashtagList = tweet.entities.hashtags.map(tag => '#' + tag.tag);
      hashtags = hashtagList.join(', ');
    }
    
    // 画像枚数の取得と画像URLの抽出
    let imageCount = 0;
    let imageUrls = '';
    if (tweet.attachments && tweet.attachments.media_keys) {
      imageCount = tweet.attachments.media_keys.length;
      const urls = [];
      tweet.attachments.media_keys.forEach(mediaKey => {
        const media = mediaInfo[mediaKey];
        if (media) {
          const mediaUrl = media.url || media.preview_image_url;
          if (mediaUrl) {
            urls.push(mediaUrl);
          }
        }
      });
      imageUrls = urls.join('\n');
    }
    
    const tweetUrl = `https://twitter.com/i/web/status/${tweet.id}`;
    
    // 親ポストURLの取得（リプライの場合のみ）
    let parentPostUrl = '';
    if (tweet.referenced_tweets && tweet.referenced_tweets[0].type === 'replied_to') {
      const parentPostId = tweet.referenced_tweets[0].id;
      parentPostUrl = `https://twitter.com/i/web/status/${parentPostId}`;
    }
    
    // メトリクスを取得
    const impressions = nonPublicMetrics.impression_count || 
                       organicMetrics.impression_count || 
                       publicMetrics.impression_count || 0;
    
    const profileClicks = organicMetrics.user_profile_clicks || 
                         nonPublicMetrics.user_profile_clicks || 0;
    
    const engagements = nonPublicMetrics.engagements || 
                       organicMetrics.engagements || 0;
    
    // 各種率の計算
    const engagementRate = impressions > 0 ? engagements / impressions : 0;
    const likeRate = impressions > 0 ? (publicMetrics.like_count || 0) / impressions : 0;
    const retweetRate = impressions > 0 ? (publicMetrics.retweet_count || 0) / impressions : 0;
    const profileRate = impressions > 0 ? profileClicks / impressions : 0;
    const bookmarkRate = impressions > 0 ? (publicMetrics.bookmark_count || 0) / impressions : 0;
    const engageRetweetRate = engagements > 0 ? (publicMetrics.retweet_count || 0) / engagements : 0;
    const engageProfileRate = engagements > 0 ? profileClicks / engagements : 0;
    const engageBookmarkRate = engagements > 0 ? (publicMetrics.bookmark_count || 0) / engagements : 0;
    
    // 重複チェック
    if (existingTweetIds.has(tweet.id)) {
      // 既存ポストの場合はメトリクスのみ更新
      const rowNumber = existingTweetIds.get(tweet.id);
      updateRows.push({
        row: rowNumber,
        parentPostUrl: parentPostUrl,
        metrics: [
          impressions,                           // K
          publicMetrics.like_count || 0,         // L
          publicMetrics.retweet_count || 0,      // M
          publicMetrics.reply_count || 0,        // N
          publicMetrics.bookmark_count || 0,     // O
          engagements,                           // P
          profileClicks,                         // Q
          engagementRate,                        // R
          likeRate,                              // S
          retweetRate,                           // T
          profileRate,                           // U
          bookmarkRate,                          // V
          engageRetweetRate,                     // W
          engageProfileRate,                     // X
          engageBookmarkRate                     // Y
        ]
      });
      updateCount++;
      return; // 新規追加はスキップ
    }
    
    // 新規ポストの場合（26列）
    newRows.push([
      createdAt,                             // A 投稿日時
      tweetUrl,                              // B ポストURL
      text,                                  // C ポスト本文
      tweetType,                             // D ポスト種類
      charCount,                             // E 文字数
      hashtags,                              // F ハッシュタグ
      imageCount,                            // G 画像枚数
      imageUrls,                             // H 画像URL
      '',                                    // I 画像プレビュー
      parentPostUrl,                         // J 親ポストURL
      impressions,                           // K インプレッション
      publicMetrics.like_count || 0,         // L いいね
      publicMetrics.retweet_count || 0,      // M リポスト
      publicMetrics.reply_count || 0,        // N リプライ
      publicMetrics.bookmark_count || 0,     // O ブックマーク
      engagements,                           // P エンゲージメント
      profileClicks,                         // Q プロフアクセス
      engagementRate,                        // R エンゲ率
      likeRate,                              // S いいね率
      retweetRate,                           // T リポスト率
      profileRate,                           // U プロフ率
      bookmarkRate,                          // V ブクマ率
      engageRetweetRate,                     // W エンゲリポスト率
      engageProfileRate,                     // X エンゲプロフ率
      engageBookmarkRate,                    // Y エンゲブクマ率
      ''                                     // Z 目的（手動入力）
    ]);
  });
  
  // 既存ポストのメトリクスを更新
  if (updateRows.length > 0) {
    updateRows.forEach(update => {
      // K列（11列目）からY列（25列目）まで15列を更新
      sheet.getRange(update.row, 11, 1, 15).setValues([update.metrics]);
      
      // J列（親ポストURL）が空白かつ parentPostUrl がある場合のみ書き込む
      const existingParentPostUrl = sheet.getRange(update.row, 10).getValue();
      if (!existingParentPostUrl && update.parentPostUrl) {
        sheet.getRange(update.row, 10).setValue(update.parentPostUrl);
      }
    });
    Logger.log(`🔄 既存ポストのメトリクスを${updateRows.length}件更新しました`);
  }
  
  // 新規データを追記
  if (newRows.length > 0) {
    const startRow = sheet.getLastRow() + 1;
    sheet.getRange(startRow, 1, newRows.length, 26).setValues(newRows);  // 26列
    
    // 書式設定
    sheet.getRange(startRow, 1, newRows.length, 1).setNumberFormat('yyyy/mm/dd hh:mm:ss');  // A列 日時
    sheet.getRange(startRow, 11, newRows.length, 7).setNumberFormat('#,##0');                // K〜Q メトリクス
    sheet.getRange(startRow, 18, newRows.length, 8).setNumberFormat('0.0000');               // R〜Y 率
    
    // ポスト本文列と画像URL列の折り返し設定
    sheet.getRange(startRow, 3, newRows.length, 1).setWrap(true);  // C列 ポスト本文
    sheet.getRange(startRow, 8, newRows.length, 1).setWrap(true);  // H列 画像URL
    
    // 画像プレビュー列（I列=9列目）にIMAGE数式を設定
    for (let i = 0; i < newRows.length; i++) {
      const row = startRow + i;
      const imageUrl = newRows[i][7];  // H列（インデックス7）
      
      if (imageUrl) {
        // 複数画像がある場合は最初の画像のみ表示
        const firstImageUrl = imageUrl.split('\n')[0];
        const formula = `=IFERROR(IMAGE("${firstImageUrl}", 1), "")`;
        sheet.getRange(row, 9).setFormula(formula);  // I列（9列目）
      }
    }
    
    // 列幅調整（初回のみ）
    if (lastRow === 0 || lastRow === 1) {
      sheet.autoResizeColumns(1, 26);
      sheet.setColumnWidth(3, 500);   // C列 ポスト本文を広めに
      sheet.setColumnWidth(6, 200);   // F列 ハッシュタグを広めに
      sheet.setColumnWidth(8, 300);   // H列 画像URLを広めに
      sheet.setColumnWidth(9, 150);   // I列 画像プレビュー
      sheet.setColumnWidth(10, 200);  // J列 親ポストID
    }
    
    // 画像プレビュー列の行の高さを調整
    for (let i = 0; i < newRows.length; i++) {
      const row = startRow + i;
      if (newRows[i][7]) {  // H列（インデックス7）に画像がある場合
        sheet.setRowHeight(row, 120);
      }
    }
    
    Logger.log(`✅ スプレッドシート「${MY_TWEETS_CONFIG.SHEET_NAME}」に${newRows.length}件追記しました`);
  } else if (updateRows.length === 0) {
    Logger.log(`⚠️ 追記する新規データはありませんでした`);
  }
}

// ========================================
// メイン処理
// ========================================

/**
 * 過去N日の投稿を取得してスプレッドシートに書き出し
 */
function exportMyTweets() {
  try {
    Logger.log('\n' + '='.repeat(60));
    Logger.log('自分の投稿取得開始');
    Logger.log('='.repeat(60));
    
    // 認証チェック
    if (!checkAuthStatus()) {
      throw new Error('認証が必要です。authorizeX() を実行してください');
    }
    
    // 設定チェック
    if (!CONFIG.USER_ID || CONFIG.USER_ID === 'YOUR_USER_ID_HERE') {
      Logger.log('\n❌ エラー: CONFIG.USER_ID が設定されていません');
      Logger.log('\nCONFIG.USER_ID を設定してください');
      return;
    }
    
    if (!CONFIG.SPREADSHEET_ID || CONFIG.SPREADSHEET_ID === 'YOUR_SPREADSHEET_ID_HERE') {
      Logger.log('\n❌ エラー: CONFIG.SPREADSHEET_ID が設定されていません');
      Logger.log('\nCONFIG.SPREADSHEET_ID を設定してください');
      return;
    }
    
    // 設定確認
    Logger.log(`\n📋 設定:`);
    Logger.log(`  ユーザーID: ${CONFIG.USER_ID}`);
    
    if (MY_TWEETS_CONFIG.USE_DATE_RANGE) {
      Logger.log(`  取得期間: ${MY_TWEETS_CONFIG.START_DATE} 〜 ${MY_TWEETS_CONFIG.END_DATE} （日付指定）`);
    } else {
      Logger.log(`  取得期間: 過去${MY_TWEETS_CONFIG.DAYS_BACK}日`);
    }
    
    Logger.log(`  リプライを含める: ${MY_TWEETS_CONFIG.INCLUDE_REPLIES ? 'はい' : 'いいえ'}`);
    Logger.log(`  他人のリポストを含める: ${MY_TWEETS_CONFIG.INCLUDE_RETWEETS ? 'はい' : 'いいえ'}`);
    Logger.log(`  スプレッドシートID: ${CONFIG.SPREADSHEET_ID.substring(0, 20)}...`);
    
    // ポストを取得
    const result = getMyTweets();
    const tweets = result.tweets;
    const mediaInfo = result.media;
    
    if (tweets.length === 0) {
      Logger.log('\n⚠️ ポストが取得できませんでした');
      return;
    }
    
    // スプレッドシートに書き出し
    writeToSheet(tweets, mediaInfo);
    
    // 統計情報を表示
    Logger.log('\n' + '='.repeat(60));
    Logger.log('統計情報');
    Logger.log('='.repeat(60));
    
    const tweetTypes = {};
    let totalImpressions = 0;
    let totalLikes = 0;
    
    tweets.forEach(tweet => {
      const type = getTweetType(tweet);
      tweetTypes[type] = (tweetTypes[type] || 0) + 1;
      
      const metrics = tweet.public_metrics || {};
      totalImpressions += metrics.impression_count || 0;
      totalLikes += metrics.like_count || 0;
    });
    
    Logger.log(`総ポスト数: ${tweets.length}件`);
    Logger.log(`\nポスト種類別:`);
    Object.keys(tweetTypes).forEach(type => {
      Logger.log(`  ${type}: ${tweetTypes[type]}件`);
    });
    
    Logger.log(`\n合計インプレッション: ${totalImpressions.toLocaleString()}`);
    Logger.log(`合計いいね: ${totalLikes.toLocaleString()}`);
    Logger.log(`平均インプレッション: ${Math.round(totalImpressions / tweets.length).toLocaleString()}`);
    Logger.log(`平均いいね: ${Math.round(totalLikes / tweets.length).toLocaleString()}`);
    
    Logger.log('\n' + '='.repeat(60));
    Logger.log('✅ 完了');
    Logger.log('='.repeat(60) + '\n');
    
  } catch (error) {
    Logger.log('\n' + '='.repeat(60));
    Logger.log('❌ エラー発生: ' + error.message);
    Logger.log('='.repeat(60) + '\n');
    throw error;
  }
}

// ========================================
// ユーティリティ関数
// ========================================

/**
 * 特定期間のポストを取得
 * 使用例: exportTweetsByDateRange(new Date('2025-01-01'), new Date('2025-12-31'))
 */
function exportTweetsByDateRange(startDate, endDate) {
  const originalDaysBack = MY_TWEETS_CONFIG.DAYS_BACK;
  
  try {
    Logger.log(`期間指定: ${startDate.toLocaleDateString()} 〜 ${endDate.toLocaleDateString()}`);
    
    const service = getXOAuth2Service();
    if (!service.hasAccess()) {
      throw new Error('未認証です');
    }
    
    let userId = CONFIG.USER_ID;
    if (!/^\d+$/.test(String(userId))) {
      userId = getUserIdByUsername(userId);
    }
    
    const allTweets = [];
    const allMediaInfo = {};
    let nextToken = null;
    
    do {
      const params = {
        'max_results': MY_TWEETS_CONFIG.MAX_RESULTS,
        'tweet.fields': 'created_at,public_metrics,non_public_metrics,organic_metrics,referenced_tweets,text,note_tweet,entities,attachments',
        'start_time': startDate.toISOString(),
        'end_time': endDate.toISOString(),
        'expansions': 'referenced_tweets.id,attachments.media_keys',
        'media.fields': 'type,url,preview_image_url'
      };
      
      // 除外するポスト種類を設定
      const excludeTypes = [];
      if (!MY_TWEETS_CONFIG.INCLUDE_REPLIES) {
        excludeTypes.push('replies');
      }
      if (!MY_TWEETS_CONFIG.INCLUDE_RETWEETS) {
        excludeTypes.push('retweets');
      }
      
      if (excludeTypes.length > 0) {
        params['exclude'] = excludeTypes.join(',');
      }
      
      if (nextToken) {
        params['pagination_token'] = nextToken;
      }
      
      const queryString = Object.keys(params).map(key => {
        return encodeURIComponent(key) + '=' + encodeURIComponent(params[key]);
      }).join('&');
      
      const url = `https://api.x.com/2/users/${userId}/tweets?${queryString}`;
      
      const options = {
        method: 'get',
        headers: {
          'Authorization': `Bearer ${service.getAccessToken()}`
        },
        muteHttpExceptions: true
      };
      
      const response = UrlFetchApp.fetch(url, options);
      const data = JSON.parse(response.getContentText());
      
      if (data.data) {
        allTweets.push(...data.data);
        if (data.includes && data.includes.media) {
          data.includes.media.forEach(media => {
            allMediaInfo[media.media_key] = media;
          });
        }
      }
      
      nextToken = data.meta && data.meta.next_token ? data.meta.next_token : null;
      
      if (nextToken) {
        Utilities.sleep(1000);
      }
      
    } while (nextToken);
    
    Logger.log(`取得完了: ${allTweets.length}件`);
    writeToSheet(allTweets, allMediaInfo);
    
  } finally {
    MY_TWEETS_CONFIG.DAYS_BACK = originalDaysBack;
  }
}

/**
 * 月別にポストを集計
 */
function analyzeTweetsByMonth() {
  const result = getMyTweets();
  const tweets = result.tweets;
  
  const monthlyStats = {};
  
  tweets.forEach(tweet => {
    const date = new Date(tweet.created_at);
    const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
    
    if (!monthlyStats[monthKey]) {
      monthlyStats[monthKey] = {
        count: 0,
        impressions: 0,
        likes: 0
      };
    }
    
    monthlyStats[monthKey].count++;
    
    const metrics = tweet.public_metrics || {};
    monthlyStats[monthKey].impressions += metrics.impression_count || 0;
    monthlyStats[monthKey].likes += metrics.like_count || 0;
  });
  
  Logger.log('\n月別統計:');
  Object.keys(monthlyStats).sort().forEach(month => {
    const stats = monthlyStats[month];
    Logger.log(`${month}: ${stats.count}件, インプ:${stats.impressions.toLocaleString()}, いいね:${stats.likes.toLocaleString()}`);
  });
}