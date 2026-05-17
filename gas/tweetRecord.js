/**
 * X API ツイートメトリクス取得スクリプト (OAuth2版)
 * 1回分の処理のみ - サーバー側から15分ごとに実行してください
 */

// ========================================
// 設定項目（必ず編集してください）
// ========================================
// 注意: 以下の変数は env.gs ファイルで定義されている必要があります
// - CLIENT_ID
// - CLIENT_SECRET
// - USER_ID
// - SPREADSHEET_ID
// - CONFIG オブジェクト

function wrapRecordNTweets(){
  recordLatestNTweets(1,false);
}

function removeTweet(){
   removeTweetConfig('2044687241369600000');
  // removeTweetConfig('2035702093567389851');
}

// CONFIGオブジェクトの存在確認（ファイル読み込み順序対策）
if (typeof CONFIG === 'undefined') {
  throw new Error('CONFIG が定義されていません。env.gs ファイルを確認してください。');
}

// 複数のポストを追跡する場合は、CONFIG.TWEET_CONFIGS に配列で設定
CONFIG.TWEET_CONFIGS = [
  {
    TWEET_ID: 'YOUR_TWEET_ID_1',
    SHEET_NAME: 'ポスト1メトリクス'
  },
  {
    TWEET_ID: 'YOUR_TWEET_ID_2',
    SHEET_NAME: 'ポスト2メトリクス'
  }
  // 必要に応じて追加
];

// ========================================
// 注意: 以下は別ファイル (env.gs) で定義されています
// - CLIENT_ID, CLIENT_SECRET (認証情報)
// - USER_ID, SPREADSHEET_ID (設定)
// - CONFIG オブジェクト
//
// ファイルの読み込み順序:
// GASはファイル名のアルファベット順に読み込まれます。
// env.gs が x_metrics_simple.gs より先に読み込まれるように、
// env.gs のファイル名を「0_env.gs」などに変更することを推奨します。
//
// また、OAuth2認証関連の関数も別ファイルで定義されています:
// - getXOAuth2Service(), authorizeX(), authCallback(), 
//   checkAuthStatus(), resetAuth(), logAPIError()
// ========================================

// ========================================
// API呼び出し（メトリクス取得専用）
// ========================================

/**
 * X API を呼び出す
 */
function callXAPI(url, context) {
  const service = getXOAuth2Service();
  
  if (!service.hasAccess()) {
    throw new Error('未認証です。authorizeX() を実行してください');
  }
  
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
    logAPIError(statusCode, responseText, context);
    throw new Error(`API呼び出し失敗: ${context}`);
  }
  
  return JSON.parse(responseText);
}

/**
 * ツイートメトリクスを取得
 */
function getTweetMetrics(tweetId) {
  const url = `https://api.x.com/2/tweets/${tweetId}?tweet.fields=public_metrics,non_public_metrics,organic_metrics`;
  
  const data = callXAPI(url, 'ツイートメトリクス取得');
  
  if (!data.data) {
    throw new Error('ツイートデータが取得できませんでした');
  }
  
  const metrics = {
    ...data.data.public_metrics || {},
    ...data.data.non_public_metrics || {},
    ...data.data.organic_metrics || {}
  };
  
  Logger.log(`✅ ツイートメトリクス取得成功`);
  Logger.log(`  インプレッション: ${metrics.impression_count || 0}`);
  Logger.log(`  いいね: ${metrics.like_count || 0}`);
  
  return {
    impressions: metrics.impression_count || 0,
    likes: metrics.like_count || 0,
    retweets: metrics.retweet_count || 0,
    replies: metrics.reply_count || 0,
    bookmarks: metrics.bookmark_count || 0,
    profileClicks: metrics.user_profile_clicks || 0,
    urlLinkClicks: metrics.url_link_clicks || 0,
    detailExpands: (metrics.url_link_clicks || 0) + (metrics.detail_expands || 0),
    engagements: (metrics.user_profile_clicks || 0) + 
                 (metrics.url_link_clicks || 0) + 
                 (metrics.like_count || 0) + 
                 (metrics.retweet_count || 0) + 
                 (metrics.reply_count || 0) + 
                 (metrics.bookmark_count || 0)
  };
}

/**
 * ユーザー名から数値のユーザーIDを取得
 */
function getUserIdByUsername(username) {
  // @ を削除
  const cleanUsername = username.replace('@', '');
  
  const url = `https://api.x.com/2/users/by/username/${cleanUsername}?user.fields=public_metrics`;
  
  const data = callXAPI(url, 'ユーザーID取得');
  
  if (!data.data) {
    throw new Error('ユーザー情報が取得できませんでした');
  }
  
  Logger.log(`✅ ユーザーID取得成功: @${cleanUsername} → ${data.data.id}`);
  return data.data.id;
}

/**
 * フォロワー数を取得
 */
function getFollowerCount() {
  let userId = CONFIG.USER_ID;
  
  // USER_IDが数値形式でない場合（ユーザー名の場合）、数値IDに変換
  // 数値形式の判定: 数字のみで構成されているか
  if (!/^\d+$/.test(String(userId))) {
    Logger.log(`USER_IDがユーザー名です。数値IDに変換します...`);
    userId = getUserIdByUsername(userId);
  }
  
  const url = `https://api.x.com/2/users/${userId}?user.fields=public_metrics`;
  
  const data = callXAPI(url, 'フォロワー数取得');
  
  if (!data.data || !data.data.public_metrics) {
    throw new Error('フォロワー数が取得できませんでした');
  }
  
  const followerCount = data.data.public_metrics.followers_count;
  Logger.log(`✅ フォロワー数取得成功: ${followerCount}`);
  
  return followerCount;
}

// ========================================
// スプレッドシート操作
// ========================================

/**
 * スプレッドシートに記録
 */
function recordToSheet(metrics, followerCount, sheetName, tweetId) {
  const spreadsheet = SpreadsheetApp.openById(CONFIG.SPREADSHEET_ID);
  let sheet = spreadsheet.getSheetByName(sheetName);
  
  // シートが存在しない場合は作成
  if (!sheet) {
    // 4番目のシートとして作成（インデックス3）
    const sheetCount = spreadsheet.getSheets().length;
    if (sheetCount >= 3) {
      // 既に3つ以上シートがある場合は4番目の位置に挿入
      sheet = spreadsheet.insertSheet(sheetName, 3);
    } else {
      // 3つ未満の場合は末尾に追加
      sheet = spreadsheet.insertSheet(sheetName);
    }
    Logger.log(`✅ シート「${sheetName}」を作成しました（位置: ${sheet.getIndex()}）`);
  }
  
  // 1行目と2行目が存在しない場合は追加
  if (sheet.getLastRow() < 2) {
    // 1行目: ツイートURL
    const tweetUrl = `https://twitter.com/i/web/status/${tweetId}`;
    const labelText = 'ツイートURL: ';
    const fullText = labelText + tweetUrl;
    
    // テキストを設定
    sheet.getRange(1, 1).setValue(fullText);
    sheet.getRange(1, 1).setFontWeight('bold');
    sheet.getRange(1, 1).setFontSize(11);
    
    // ハイパーリンクを設定（URL部分のみ）
    const startIndex = labelText.length;
    const endIndex = fullText.length;
    
    const richText = SpreadsheetApp.newRichTextValue()
      .setText(fullText)
      .setLinkUrl(startIndex, endIndex, tweetUrl)
      .build();
    sheet.getRange(1, 1).setRichTextValue(richText);
    
    Logger.log(`✅ ツイートURLを1行目に追加しました`);
    
    // 2行目: ヘッダー行
    const headers = [
      '取得日時',
      'インプレッション',
      'いいね',
      'リツイート',
      'コメント',
      'ブックマーク',
      'プロフアクセス',
      '詳細クリック',
      'エンゲージメント',
      'フォロワー数',
      'インプ差分',
      'いいね差分',
      'リツイート差分',
      'プロフ差分',
      'フォロワー差分'
    ];
    
    sheet.getRange(2, 1, 1, headers.length).setValues([headers]);
    sheet.getRange(2, 1, 1, headers.length).setFontWeight('bold');
    sheet.getRange(2, 1, 1, headers.length).setBackground('#4285f4');
    sheet.getRange(2, 1, 1, headers.length).setFontColor('#ffffff');
    sheet.setFrozenRows(2);  // 1行目と2行目を固定
    
    Logger.log(`✅ ヘッダー行を2行目に追加しました`);
  }
  
  // 前回のデータを取得（差分計算用）
  const lastRow = sheet.getLastRow();
  let prevImpressions = 0;
  let prevLikes = 0;
  let prevRetweets = 0;
  let prevProfileClicks = 0;
  let prevFollowerCount = 0;
  
  if (lastRow >= 3) {
    // 前回データが存在する場合
    const prevData = sheet.getRange(lastRow, 1, 1, 10).getValues()[0];
    prevImpressions = prevData[1] || 0;      // B列: インプレッション
    prevLikes = prevData[2] || 0;            // C列: いいね
    prevRetweets = prevData[3] || 0;         // D列: リツイート
    prevProfileClicks = prevData[6] || 0;    // G列: プロフアクセス
    prevFollowerCount = prevData[9] || 0;    // J列: フォロワー数
  }
  
  // 差分を計算
  const diffImpressions = metrics.impressions - prevImpressions;
  const diffLikes = metrics.likes - prevLikes;
  const diffRetweets = metrics.retweets - prevRetweets;
  const diffProfileClicks = metrics.profileClicks - prevProfileClicks;
  const diffFollowerCount = followerCount - prevFollowerCount;
  
  // データ行を追加
  const timestamp = new Date();
  const row = [
    timestamp,
    metrics.impressions,
    metrics.likes,
    metrics.retweets,
    metrics.replies,
    metrics.bookmarks,
    metrics.profileClicks,
    metrics.detailExpands,
    metrics.engagements,
    followerCount,
    diffImpressions,
    diffLikes,
    diffRetweets,
    diffProfileClicks,
    diffFollowerCount
  ];
  
  sheet.appendRow(row);
  
  // 書式設定
  const newLastRow = sheet.getLastRow();
  sheet.getRange(newLastRow, 1).setNumberFormat('yyyy/mm/dd hh:mm:ss');
  sheet.getRange(newLastRow, 2, 1, 14).setNumberFormat('#,##0');
  
  // 差分列に色を付ける（見やすくするため）
  sheet.getRange(newLastRow, 11, 1, 5).setBackground('#f3f3f3');
  
  Logger.log(`✅ データを記録しました (行: ${newLastRow})`);
  Logger.log(`  差分 - インプ:${diffImpressions}, いいね:${diffLikes}, RT:${diffRetweets}, プロフ:${diffProfileClicks}, フォロワー:${diffFollowerCount}`);
}

// ========================================
// メイン処理（この関数を15分ごとに実行）
// ========================================

/**
 * メトリクスを取得してスプレッドシートに記録
 * サーバー側から15分ごとにこの関数を呼び出してください
 */
function collectMetrics() {
  try {
    Logger.log('\n' + '='.repeat(60));
    Logger.log('メトリクス取得開始: ' + new Date());
    Logger.log('='.repeat(60));
    
    // 認証チェック
    if (!checkAuthStatus()) {
      throw new Error('認証が必要です');
    }
    
    // PropertiesServiceから設定を読み込み（recordLatestTweetで保存された設定を復元）
    const scriptProperties = PropertiesService.getScriptProperties();
    const savedConfigs = scriptProperties.getProperty('TWEET_CONFIGS');
    
    if (savedConfigs) {
      CONFIG.TWEET_CONFIGS = JSON.parse(savedConfigs);
      Logger.log(`📥 保存された設定を読み込みました: ${CONFIG.TWEET_CONFIGS.length}件`);
    }
    
    // 記録するツイートがあるかチェック
    if (!CONFIG.TWEET_CONFIGS || CONFIG.TWEET_CONFIGS.length === 0) {
      Logger.log('\n記録するツイートがありません。終了します。');
      Logger.log('='.repeat(60) + '\n');
      return;
    }
    
    // フォロワー数を取得（全ポスト共通）
    const followerCount = getFollowerCount();
    
    // 各ポストのメトリクスを取得
    let successCount = 0;
    let errorCount = 0;
    
    CONFIG.TWEET_CONFIGS.forEach((tweetConfig, index) => {
      try {
        Logger.log(`\n--- ポスト ${index + 1}/${CONFIG.TWEET_CONFIGS.length}: ${tweetConfig.SHEET_NAME} ---`);
        
        // ツイートメトリクスを取得
        const tweetMetrics = getTweetMetrics(tweetConfig.TWEET_ID);
        
        // スプレッドシートに記録
        recordToSheet(tweetMetrics, followerCount, tweetConfig.SHEET_NAME, tweetConfig.TWEET_ID);
        
        successCount++;
      } catch (error) {
        Logger.log(`❌ ポスト ${index + 1} でエラー: ${error.message}`);
        errorCount++;
      }
    });
    
    Logger.log('\n' + '='.repeat(60));
    Logger.log(`✅ メトリクス取得完了: 成功 ${successCount}件, エラー ${errorCount}件`);
    Logger.log('='.repeat(60) + '\n');
    
  } catch (error) {
    Logger.log('\n' + '='.repeat(60));
    Logger.log('❌ エラー発生: ' + error.message);
    Logger.log('='.repeat(60) + '\n');
    throw error;
  }
}

// ========================================
// 最新ツイート取得・記録
// ========================================

/**
 * 最新ツイートを取得してメトリクスを記録
 */
function recordLatestTweet() {
  try {
    Logger.log('\n' + '='.repeat(60));
    Logger.log('最新ツイート取得・記録開始: ' + new Date());
    Logger.log('='.repeat(60));
    
    // 認証チェック
    if (!checkAuthStatus()) {
      throw new Error('認証が必要です');
    }
    
    Logger.log('最新ツイートIDを取得中...');
    
    // 最新ツイートIDを取得
    const latestTweetId = getLatestTweetId();
    
    Logger.log(`取得したツイートID: ${latestTweetId} (型: ${typeof latestTweetId})`);
    
    if (!latestTweetId) {
      Logger.log('⚠️ 最新ツイートが取得できませんでした');
      return;
    }
    
    Logger.log(`✅ 最新ツイートID: ${latestTweetId}`);
    
    // PropertiesServiceから既存の設定を読み込み
    const scriptProperties = PropertiesService.getScriptProperties();
    const savedConfigs = scriptProperties.getProperty('TWEET_CONFIGS');
    
    let existingConfigs = [];
    if (savedConfigs) {
      existingConfigs = JSON.parse(savedConfigs);
      Logger.log(`📥 既存の設定を読み込みました: ${existingConfigs.length}件`);
    } else {
      Logger.log(`📥 既存の設定はありません`);
    }
    
    // 既に同じツイートIDが登録されているかチェック
    const isDuplicate = existingConfigs.some(config => config.TWEET_ID === latestTweetId);
    
    if (isDuplicate) {
      Logger.log(`ℹ️ ツイートID ${latestTweetId} は既に登録されています。スキップします。`);
      Logger.log(`既存の設定でメトリクスを記録します。`);
      
      // 既存の設定でメトリクスを記録
      CONFIG.TWEET_CONFIGS = existingConfigs;
      collectMetrics();
      return;
    }
    
    // 新しいツイートを追加
    const newConfig = {
      TWEET_ID: latestTweetId,
      SHEET_NAME: latestTweetId
    };
    
    existingConfigs.push(newConfig);
    
    // CONFIG.TWEET_CONFIGSを更新
    CONFIG.TWEET_CONFIGS = existingConfigs;
    
    // PropertiesServiceに保存（永続化）
    scriptProperties.setProperty('TWEET_CONFIGS', JSON.stringify(CONFIG.TWEET_CONFIGS));
    
    Logger.log(`➕ 新しいツイートを追加: TWEET_ID=${latestTweetId}, SHEET_NAME=${latestTweetId}`);
    Logger.log(`📝 合計設定数: ${CONFIG.TWEET_CONFIGS.length}件`);
    Logger.log(`CONFIG.TWEET_CONFIGS: ${JSON.stringify(CONFIG.TWEET_CONFIGS)}`);
    Logger.log(`✅ PropertiesServiceに保存しました`);
    
    // メトリクスを記録
    collectMetrics();
    
  } catch (error) {
    Logger.log('\n' + '='.repeat(60));
    Logger.log('❌ エラー発生: ' + error.message);
    Logger.log('='.repeat(60) + '\n');
    throw error;
  }
}

/**
 * 最新n個のツイートを設定してメトリクスを記録
 * @param {number} count - 取得するツイート数（デフォルト: 1、最大: 100）
 * @param {boolean} replaceAll - true: 既存の設定を削除して置き換え、false: 既存の設定に追加（デフォルト: false）
 */
function recordLatestNTweets(count, replaceAll) {
  try {
    const n = count || 1;
    const replace = replaceAll || false;
    
    Logger.log('\n' + '='.repeat(60));
    Logger.log(`最新${n}個のツイート取得・記録開始: ` + new Date());
    Logger.log('='.repeat(60));
    
    // 認証チェック
    if (!checkAuthStatus()) {
      throw new Error('認証が必要です');
    }
    
    Logger.log(`最新${n}個のツイートIDを取得中...`);
    
    // 最新n個のツイートIDを取得
    const tweetIds = getLatestNTweetIds(n);
    
    if (!tweetIds || tweetIds.length === 0) {
      Logger.log('⚠️ ツイートが取得できませんでした');
      return;
    }
    
    Logger.log(`✅ ${tweetIds.length}個のツイートIDを取得しました`);
    tweetIds.forEach((id, index) => {
      Logger.log(`  ${index + 1}. ${id}`);
    });
    
    // PropertiesServiceから既存の設定を読み込み
    const scriptProperties = PropertiesService.getScriptProperties();
    let existingConfigs = [];
    
    if (!replace) {
      const savedConfigs = scriptProperties.getProperty('TWEET_CONFIGS');
      if (savedConfigs) {
        existingConfigs = JSON.parse(savedConfigs);
        Logger.log(`📥 既存の設定を読み込みました: ${existingConfigs.length}件`);
      }
    } else {
      Logger.log(`🔄 既存の設定を置き換えます`);
    }
    
    // 新しいツイートを追加
    let addedCount = 0;
    let skippedCount = 0;
    
    tweetIds.forEach(tweetId => {
      // 既に登録されているかチェック
      const isDuplicate = existingConfigs.some(config => config.TWEET_ID === tweetId);
      
      if (isDuplicate) {
        Logger.log(`  ⏭️  スキップ: ${tweetId} (既に登録済み)`);
        skippedCount++;
        return;
      }
      
      // 新しいツイートを追加
      existingConfigs.push({
        TWEET_ID: tweetId,
        SHEET_NAME: tweetId
      });
      
      Logger.log(`  ➕ 追加: ${tweetId}`);
      addedCount++;
    });
    
    // CONFIG.TWEET_CONFIGSを更新
    CONFIG.TWEET_CONFIGS = existingConfigs;
    
    // PropertiesServiceに保存（永続化）
    scriptProperties.setProperty('TWEET_CONFIGS', JSON.stringify(CONFIG.TWEET_CONFIGS));
    
    Logger.log(`\n📝 追加: ${addedCount}件, スキップ: ${skippedCount}件`);
    Logger.log(`📝 合計設定数: ${CONFIG.TWEET_CONFIGS.length}件`);
    Logger.log(`✅ PropertiesServiceに保存しました`);
    
    // メトリクスを記録
    collectMetrics();
    
  } catch (error) {
    Logger.log('\n' + '='.repeat(60));
    Logger.log('❌ エラー発生: ' + error.message);
    Logger.log('='.repeat(60) + '\n');
    throw error;
  }
}

/**
 * 最新のツイートIDを取得
 */
function getLatestTweetId() {
  Logger.log('getLatestTweetId: 開始');
  
  const service = getXOAuth2Service();
  
  if (!service.hasAccess()) {
    throw new Error('未認証です');
  }
  
  let userId = CONFIG.USER_ID;
  Logger.log(`CONFIG.USER_ID: ${userId} (型: ${typeof userId})`);
  
  // ユーザー名の場合は数値IDに変換
  if (!/^\d+$/.test(String(userId))) {
    Logger.log(`USER_IDがユーザー名です。数値IDに変換します...`);
    userId = getUserIdByUsername(userId);
    Logger.log(`変換後のユーザーID: ${userId}`);
  }
  
  // 最新ツイートを1件取得（リプライとリツイートを除外）
  const url = `https://api.x.com/2/users/${userId}/tweets?max_results=5&exclude=replies,retweets`;
  Logger.log(`API URL: ${url}`);
  
  const options = {
    method: 'get',
    headers: {
      'Authorization': `Bearer ${service.getAccessToken()}`
    },
    muteHttpExceptions: true
  };
  
  const response = UrlFetchApp.fetch(url, options);
  const statusCode = response.getResponseCode();
  Logger.log(`HTTPステータス: ${statusCode}`);
  
  if (statusCode !== 200) {
    const responseText = response.getContentText();
    Logger.log(`エラーレスポンス: ${responseText}`);
    logAPIError(statusCode, responseText, '最新ツイート取得');
    throw new Error('最新ツイートの取得に失敗しました');
  }
  
  const data = JSON.parse(response.getContentText());
  Logger.log(`取得データ: ${JSON.stringify(data)}`);
  
  if (data.data && data.data.length > 0) {
    const tweetId = data.data[0].id;
    Logger.log(`最新ツイートID: ${tweetId}`);
    return tweetId;
  }
  
  Logger.log('ツイートデータが空です');
  return null;
}

/**
 * 最新n個のツイートIDを取得
 * @param {number} count - 取得するツイート数（最大100）
 * @returns {Array<string>} ツイートIDの配列
 */
function getLatestNTweetIds(count) {
  Logger.log(`getLatestNTweetIds: 開始 (count=${count})`);
  
  const service = getXOAuth2Service();
  
  if (!service.hasAccess()) {
    throw new Error('未認証です');
  }
  
  let userId = CONFIG.USER_ID;
  Logger.log(`CONFIG.USER_ID: ${userId} (型: ${typeof userId})`);
  
  // ユーザー名の場合は数値IDに変換
  if (!/^\d+$/.test(String(userId))) {
    Logger.log(`USER_IDがユーザー名です。数値IDに変換します...`);
    userId = getUserIdByUsername(userId);
    Logger.log(`変換後のユーザーID: ${userId}`);
  }
  
  // X APIの制限: max_resultsは5〜100の範囲
  const maxResults = Math.max(5, Math.min(count, 100));
  
  // ツイートを取得（リプライとリツイートを除外）
  const url = `https://api.x.com/2/users/${userId}/tweets?max_results=${maxResults}&exclude=replies,retweets`;
  Logger.log(`API URL: ${url}`);
  
  const options = {
    method: 'get',
    headers: {
      'Authorization': `Bearer ${service.getAccessToken()}`
    },
    muteHttpExceptions: true
  };
  
  const response = UrlFetchApp.fetch(url, options);
  const statusCode = response.getResponseCode();
  Logger.log(`HTTPステータス: ${statusCode}`);
  
  if (statusCode !== 200) {
    const responseText = response.getContentText();
    Logger.log(`エラーレスポンス: ${responseText}`);
    logAPIError(statusCode, responseText, '最新ツイート取得');
    throw new Error('最新ツイートの取得に失敗しました');
  }
  
  const data = JSON.parse(response.getContentText());
  
  if (data.data && data.data.length > 0) {
    // 必要な数だけ取得（APIは最低5件返すが、指定された数だけ返す）
    const tweetIds = data.data.slice(0, count).map(tweet => tweet.id);
    Logger.log(`取得したツイート数: ${tweetIds.length}件 (要求: ${count}件, API取得: ${data.data.length}件)`);
    return tweetIds;
  }
  
  Logger.log('ツイートデータが空です');
  return [];
}

// ========================================
// 設定管理
// ========================================

/**
 * 保存されている設定を表示
 */
function showSavedConfigs() {
  const scriptProperties = PropertiesService.getScriptProperties();
  const savedConfigs = scriptProperties.getProperty('TWEET_CONFIGS');
  
  Logger.log('\n' + '='.repeat(60));
  Logger.log('保存されている設定');
  Logger.log('='.repeat(60));
  
  if (savedConfigs) {
    const configs = JSON.parse(savedConfigs);
    Logger.log(`設定数: ${configs.length}件\n`);
    configs.forEach((config, index) => {
      Logger.log(`${index + 1}. TWEET_ID: ${config.TWEET_ID}`);
      Logger.log(`   SHEET_NAME: ${config.SHEET_NAME}`);
    });
  } else {
    Logger.log('保存されている設定はありません');
  }
  
  Logger.log('='.repeat(60) + '\n');
}

/**
 * 設定を手動で追加
 * @param {string} tweetId - ツイートID
 * @param {string} sheetName - シート名（省略時はツイートIDを使用）
 */
function addTweetConfig(tweetId, sheetName) {
  if (!tweetId) {
    Logger.log('❌ エラー: ツイートIDを指定してください');
    Logger.log('使い方: addTweetConfig("1234567890", "シート名")');
    return;
  }
  
  const scriptProperties = PropertiesService.getScriptProperties();
  const savedConfigs = scriptProperties.getProperty('TWEET_CONFIGS');
  
  let configs = [];
  if (savedConfigs) {
    configs = JSON.parse(savedConfigs);
  }
  
  // 重複チェック
  const isDuplicate = configs.some(config => config.TWEET_ID === tweetId);
  if (isDuplicate) {
    Logger.log(`⚠️ ツイートID ${tweetId} は既に登録されています`);
    return;
  }
  
  // 新しい設定を追加
  configs.push({
    TWEET_ID: tweetId,
    SHEET_NAME: sheetName || tweetId
  });
  
  scriptProperties.setProperty('TWEET_CONFIGS', JSON.stringify(configs));
  Logger.log(`✅ 追加しました: TWEET_ID=${tweetId}, SHEET_NAME=${sheetName || tweetId}`);
  Logger.log(`合計: ${configs.length}件`);
}

/**
 * 特定のツイート設定を削除
 * @param {string} tweetId - 削除するツイートID
 */
function removeTweetConfig(tweetId) {
  if (!tweetId) {
    Logger.log('❌ エラー: ツイートIDを指定してください');
    Logger.log('使い方: removeTweetConfig("1234567890")');
    return;
  }
  
  const scriptProperties = PropertiesService.getScriptProperties();
  const savedConfigs = scriptProperties.getProperty('TWEET_CONFIGS');
  
  if (!savedConfigs) {
    Logger.log('保存されている設定はありません');
    return;
  }
  
  let configs = JSON.parse(savedConfigs);
  const beforeCount = configs.length;
  
  configs = configs.filter(config => config.TWEET_ID !== tweetId);
  
  if (configs.length === beforeCount) {
    Logger.log(`⚠️ ツイートID ${tweetId} は見つかりませんでした`);
    return;
  }
  
  scriptProperties.setProperty('TWEET_CONFIGS', JSON.stringify(configs));
  Logger.log(`✅ 削除しました: TWEET_ID=${tweetId}`);
  Logger.log(`残り: ${configs.length}件`);
}

/**
 * シート名を変更
 * @param {string} tweetId - ツイートID
 * @param {string} newSheetName - 新しいシート名
 */
function updateSheetName(tweetId, newSheetName) {
  if (!tweetId || !newSheetName) {
    Logger.log('❌ エラー: ツイートIDと新しいシート名を指定してください');
    Logger.log('使い方: updateSheetName("1234567890", "新しいシート名")');
    return;
  }
  
  const scriptProperties = PropertiesService.getScriptProperties();
  const savedConfigs = scriptProperties.getProperty('TWEET_CONFIGS');
  
  if (!savedConfigs) {
    Logger.log('保存されている設定はありません');
    return;
  }
  
  let configs = JSON.parse(savedConfigs);
  let found = false;
  
  configs = configs.map(config => {
    if (config.TWEET_ID === tweetId) {
      found = true;
      return {
        ...config,
        SHEET_NAME: newSheetName
      };
    }
    return config;
  });
  
  if (!found) {
    Logger.log(`⚠️ ツイートID ${tweetId} は見つかりませんでした`);
    return;
  }
  
  scriptProperties.setProperty('TWEET_CONFIGS', JSON.stringify(configs));
  Logger.log(`✅ シート名を変更しました: TWEET_ID=${tweetId}, SHEET_NAME=${newSheetName}`);
}

/**
 * 設定を直接編集（上級者向け）
 * 配列を直接指定して設定を上書き
 */
function setTweetConfigs(configs) {
  if (!Array.isArray(configs)) {
    Logger.log('❌ エラー: 配列を指定してください');
    Logger.log('使い方: setTweetConfigs([{TWEET_ID: "123", SHEET_NAME: "シート名"}])');
    return;
  }
  
  const scriptProperties = PropertiesService.getScriptProperties();
  scriptProperties.setProperty('TWEET_CONFIGS', JSON.stringify(configs));
  Logger.log(`✅ 設定を更新しました: ${configs.length}件`);
  
  configs.forEach((config, index) => {
    Logger.log(`${index + 1}. TWEET_ID: ${config.TWEET_ID}, SHEET_NAME: ${config.SHEET_NAME}`);
  });
}

/**
 * 保存されている設定をクリア
 */
function clearSavedConfigs() {
  const scriptProperties = PropertiesService.getScriptProperties();
  scriptProperties.deleteProperty('TWEET_CONFIGS');
  Logger.log('✅ 保存されている設定をクリアしました');
}

// ========================================
// セットアップ用関数
// ========================================

/**
 * 自分のユーザーIDを確認（初回セットアップ用）
 */
function checkMyUserId() {
  const username = CONFIG.USER_ID.replace('@', '');
  
  Logger.log('\n' + '='.repeat(60));
  Logger.log('ユーザーID確認');
  Logger.log('='.repeat(60));
  
  try {
    const userId = getUserIdByUsername(username);
    Logger.log(`\n✅ あなたのユーザーID: ${userId}`);
    Logger.log(`\nCONFIGを以下のように更新できます:`);
    Logger.log(`USER_ID: '${userId}',  // 数値ID`);
    Logger.log(`または`);
    Logger.log(`USER_ID: '${username}',  // ユーザー名（自動変換されます）`);
  } catch (error) {
    Logger.log(`\n❌ エラー: ${error.message}`);
  }
  
  Logger.log('='.repeat(60) + '\n');
}

/**
 * 初期セットアップ（最初に1回だけ実行）
 */
function initialSetup() {
  Logger.log('\n' + '='.repeat(60));
  Logger.log('初期セットアップ');
  Logger.log('='.repeat(60));
  
  Logger.log('\n📋 設定確認:');
  Logger.log(`  TWEET_ID: ${CONFIG.TWEET_ID}`);
  Logger.log(`  USER_ID: ${CONFIG.USER_ID}`);
  Logger.log(`  SPREADSHEET_ID: ${CONFIG.SPREADSHEET_ID}`);
  
  try {
    OAuth2.createService('test');
    Logger.log('\n✅ OAuth2ライブラリ: インストール済み');
  } catch (e) {
    Logger.log('\n❌ OAuth2ライブラリがインストールされていません');
    Logger.log('スクリプトID: 1B7FSrk5Zi6L1rSxxTDgDEUsPzlukDsi4KGuTMorsTQHhGBzBkMun4iDF');
    return;
  }
  
  Logger.log('\n🔐 OAuth2認証を開始します...');
  authorizeX();
  
  Logger.log('\n='.repeat(60));
  Logger.log('次のステップ:');
  Logger.log('1. 上記URLで認証');
  Logger.log('2. checkAuthStatus() で確認');
  Logger.log('3. collectMetrics() でテスト');
  Logger.log('4. サーバー側から15分ごとに collectMetrics() を呼び出す');
  Logger.log('='.repeat(60) + '\n');
}