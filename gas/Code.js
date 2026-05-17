/**
 * OAuth 1.0aを使用したX API検索スクリプト（レート制限対策版）
 */

// // X Developer Portalから取得した認証情報
// const API_KEY = '05ca9oZDsrtyYgIkY5m9mGZbx';
// const API_SECRET = 'bqIo5y93Hrdln8wv6AYelvdijQxz1nrTBoZnqLNYNJV3a5RNMf';
// const ACCESS_TOKEN = '548606471-ckJWIDAG8xqvmcIuy65JcXZl2puApJoziRk7QrsC';
// const ACCESS_TOKEN_SECRET = '3tAtrBbHThxoyXonDp6ZKtiSFsTBM2axDGs5GmjUkCdJy';

// // OAuth2 認証情報
// const CLIENT_ID = 'eGQ2YU5OSndqS3lKRGZmYTR6OU06MTpjaQ';
// const CLIENT_SECRET = 'xNGu-t7m3stTb2LOt_HEx93vRfQIfkDe9kdfBTjrqg3e3E5hug';

// 検索条件: 天体写真界隈

// ツイート検索用キーワード
const KEYWORDS = [
  '天体写真','星景写真','オリオン大星雲','アンドロメダ銀河','プレアデス星団','馬頭星雲','ばら星雲','北アメリカ星雲','NGC7000','ヘラクレス座球状星団','カリフォルニア星雲','NGC1499','シーイング'
];
// プロフィールフィルター用キーワード（KEYWORDS と独立して設定可能）。null にすると KEYWORDS をそのまま使う
const BIO_KEYWORDS = [
  '天体写真', '星景写真', '天体観測', '星', '宇宙', '天文','望遠鏡', 'アマチュア天文', '星空', '観望'
];

const MAX_RESULTS = 10;
const MIN_FOLLOWERS = 100;
const MAX_FOLLOWERS = 6000;
const MIN_FOLLOW_RATIO = 0.4;
const MAX_FOLLOW_RATIO = 3.0;
const MAX_DAYS_SINCE_TWEET = 7;

// ツイート検索時にユーザー情報も一緒に取得するか
// true  → expansions=author_id を付けてユーザー情報も取得（user READ の料金がかかる）
// false → ツイートのみ取得（post READ の料金のみ）
const FETCH_USER_INFO = true;

// 「交流候補リスト」にすでにいるアカウントを除外するか
// true  → 除外する
// false → 除外しない
const EXCLUDE_EXISTING = true;

// 絞り込み条件のオン/オフ
const FILTER_KEYWORD = false;
const FILTER_FOLLOWERS = true;
const FILTER_RATIO = true;
const FILTER_TWEET_DATE = false;  // users/searchでは取得不可のためfalse推奨

// ===================================================
// OAuth2 認証関連
// ===================================================

/**
 * ランダムなcode_verifierを生成
 */
function generateCodeVerifier() {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~';
  let result = '';
  for (let i = 0; i < 64; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return result;
}

/**
 * OAuth2サービスを取得
 */
function getXOAuth2Service() {
  const properties = PropertiesService.getUserProperties();
  let codeVerifier = properties.getProperty('code_verifier');

  if (!codeVerifier) {
    codeVerifier = generateCodeVerifier();
    properties.setProperty('code_verifier', codeVerifier);
    Logger.log(`code_verifier を生成・保存しました`);
  }

  // code_challenge を生成（S256方式）
  const codeChallenge = Utilities.base64EncodeWebSafe(
    Utilities.computeDigest(
      Utilities.DigestAlgorithm.SHA_256,
      codeVerifier,
      Utilities.Charset.UTF_8
    )
  ).replace(/=+$/, '');

  return OAuth2.createService('x_oauth2')
    .setAuthorizationBaseUrl('https://twitter.com/i/oauth2/authorize')
    .setTokenUrl('https://api.x.com/2/oauth2/token')
    .setClientId(CLIENT_ID)
    .setClientSecret(CLIENT_SECRET)
    .setCallbackFunction('authCallback')
    .setPropertyStore(PropertiesService.getUserProperties())
    .setScope('tweet.read users.read offline.access')
    .setParam('code_challenge', codeChallenge)
    .setParam('code_challenge_method', 'S256')
    .setTokenPayloadHandler(function(payload) {
      // トークン取得時に code_verifier を追加
      const props = PropertiesService.getUserProperties();
      const verifier = props.getProperty('code_verifier');
      Logger.log(`トークンリクエストに code_verifier を追加: ${verifier}`);
      payload['code_verifier'] = verifier;
      return payload;
    });
}

/**
 * 認証URLを表示（最初に一度だけ実行）
 */
function authorizeX() {
  const service = getXOAuth2Service();
  
  if (service.hasAccess()) {
    Logger.log('✅ すでに認証済みです');
    Logger.log(`トークン: ${service.getAccessToken().substring(0, 20)}...`);
    return;
  }
  
  const authUrl = service.getAuthorizationUrl();
  Logger.log('以下のURLをブラウザで開いて認証してください：');
  Logger.log(authUrl);
  Logger.log('\n認証後、自動的にコールバックが呼ばれます');
}

/**
 * 認証コールバック
 */
function authCallback(request) {
  const service = getXOAuth2Service();
  const isAuthorized = service.handleCallback(request);
  
  // 認証完了後にcode_verifierを削除
  if (isAuthorized) {
    PropertiesService.getUserProperties().deleteProperty('code_verifier');
    return HtmlService.createHtmlOutput('✅ 認証成功！このタブを閉じてGASに戻ってください。');
  } else {
    return HtmlService.createHtmlOutput('❌ 認証失敗。もう一度お試しください。');
  }
}

/**
 * 認証状態を確認
 */
function checkAuthStatus() {
  const service = getXOAuth2Service();
  
  if (service.hasAccess()) {
    Logger.log('✅ 認証済み');
    Logger.log(`アクセストークン: ${service.getAccessToken().substring(0, 20)}...`);
    return true;
  } else {
    Logger.log('❌ 未認証');
    Logger.log('authorizeX() を実行して認証してください');
    return false;
  }
}

/**
 * 認証をリセット（再認証したい場合）
 */
function resetAuth() {
  const service = getXOAuth2Service();
  service.reset();
  Logger.log('🔄 認証をリセットしました。authorizeX() を実行して再認証してください');
}

// ===================================================
// API関連
// ===================================================

/**
 * APIエラーを詳細に表示
 */
function logAPIError(statusCode, responseText, context) {
  Logger.log(`\n${'='.repeat(60)}`);
  Logger.log(`❌ APIエラー発生: ${context}`);
  Logger.log(`${'='.repeat(60)}`);
  Logger.log(`ステータスコード: ${statusCode}`);
  
  try {
    const errorData = JSON.parse(responseText);
    Logger.log(`エラータイプ: ${errorData.type || '不明'}`);
    Logger.log(`エラータイトル: ${errorData.title || '不明'}`);
    Logger.log(`エラー詳細: ${errorData.detail || '不明'}`);
    
    if (errorData.errors) {
      Logger.log('エラー情報:');
      errorData.errors.forEach((err, index) => {
        Logger.log(`  ${index + 1}. ${JSON.stringify(err)}`);
      });
    }
  } catch (e) {
    Logger.log(`生のレスポンス:\n${responseText}`);
  }
  
  Logger.log(`${'='.repeat(60)}\n`);
  
  if (statusCode === 401) {
    Logger.log('💡 認証エラー: authorizeX() を実行して再認証してください');
  } else if (statusCode === 403) {
    Logger.log('💡 権限エラー: アプリのスコープ設定を確認してください');
  } else if (statusCode === 429) {
    Logger.log('💡 レート制限 または 月間上限超過');
    Logger.log('   - 月間上限の場合: 来月までお待ちください');
    Logger.log('   - 一時的な制限の場合: 15分後に再実行してください');
  } else if (statusCode === 400) {
    Logger.log('💡 リクエストエラー: クエリパラメータを確認してください');
  }
}

function searchUsersByKeyword() {  // 引数のkeywordを削除
  const service = getXOAuth2Service();
  if (!service.hasAccess()) {
    Logger.log('❌ 未認証です。先に authorizeX() を実行してください');
    return [];
  }

  const baseUrl = 'https://api.x.com/2/tweets/search/recent';

  // KEYWORDS を OR でつなげたクエリを生成
  const orQuery = KEYWORDS.map(k => `"${k}"`).join(' OR ');
  const query = `(${orQuery}) lang:ja`;
  Logger.log(`検索クエリ: ${query}`);

  // 変更後
  const params = {
    query: query,
    max_results: MAX_RESULTS,
    'tweet.fields': 'created_at'
  };

  if (FETCH_USER_INFO) {
    params['expansions'] = 'author_id';
    params['user.fields'] = 'id,username,name,description,public_metrics,created_at';
  }

  const queryString = Object.keys(params).map(key => {
    return encodeURIComponent(key) + '=' + encodeURIComponent(params[key]);
  }).join('&');

  const url = baseUrl + '?' + queryString;

  Logger.log(`URL: ${baseUrl}`);

  const options = {
    method: 'get',
    headers: {
      'Authorization': `Bearer ${service.getAccessToken()}`
    },
    muteHttpExceptions: true
  };

  try {
    const response = UrlFetchApp.fetch(url, options);
    const statusCode = response.getResponseCode();
    const responseText = response.getContentText();

    Logger.log(`ステータスコード: ${statusCode}`);

    if (statusCode === 429) {
      logAPIError(statusCode, responseText, 'ユーザー検索');
      return [];
    }

    if (statusCode !== 200) {
      logAPIError(statusCode, responseText, 'ユーザー検索');
      return [];
    }

    const data = JSON.parse(responseText);

    Logger.log(`✅ 成功`);
    if (data.meta) {
      Logger.log(`結果数: ${data.meta.result_count || 0}`);
    }

    if (data.data && data.includes && data.includes.users) {
      const tweets = data.data;
      const users = data.includes.users;

      Logger.log(`ツイート数: ${tweets.length}`);
      Logger.log(`ユーザー数: ${users.length}`);

      const userTweetMap = {};
      const tweetIdMap = {};

      tweets.forEach(tweet => {
        const authorId = tweet.author_id;
        const tweetDate = new Date(tweet.created_at);
        if (!userTweetMap[authorId] || tweetDate > userTweetMap[authorId]) {
          userTweetMap[authorId] = tweetDate;
          tweetIdMap[authorId] = tweet.id;
        }
      });

      return users.map(user => ({
        ...user,
        latest_tweet_date: userTweetMap[user.id] || null,
        latest_tweet_id: tweetIdMap[user.id] || null
      }));

    } else if (data.data && !FETCH_USER_INFO) {
      Logger.log(`ツイート数: ${data.data.length}（ユーザー情報なし）`);
      return data.data;

    } else {
      Logger.log('⚠️ ユーザー情報が含まれていません');
      Logger.log(`  data: ${data.data ? 'あり' : 'なし'}`);
      Logger.log(`  includes: ${data.includes ? 'あり' : 'なし'}`);
      if (data.includes) {
        Logger.log(`  includes.users: ${data.includes.users ? 'あり' : 'なし'}`);
      }
      return [];
    }

  } catch (error) {
    Logger.log(`❌ 例外エラー: ${error.message}`);
    return [];
  }
}

// ===================================================
// 条件チェック
// ===================================================

/**
 * すべての条件を満たすかチェック
 */
function meetsAllCriteria(account, debug = false) {
  if (!account) {
    if (debug) Logger.log(`❌ アカウント情報なし`);
    return false;
  }

  // public_metrics がない場合はフォロワー・比率チェックをスキップ
  const metrics = account.public_metrics || null;
  const username = account.username || account.author_id || '不明';

  if (debug) {
    Logger.log(`\n--- チェック: @${username} ---`);
    Logger.log(`プロフィール: ${account.description ? account.description.substring(0, 100) : 'なし'}`);
  }

  // 1. フォロワー数チェック（metrics がある場合のみ）
  if (FILTER_FOLLOWERS) {
    if (!metrics) {
      if (debug) Logger.log(`⏭️ フォロワー数チェック: ユーザー情報なしのためスキップ`);
    } else if (metrics.followers_count < MIN_FOLLOWERS || metrics.followers_count >= MAX_FOLLOWERS) {
      if (debug) Logger.log(`❌ フォロワー数: ${metrics.followers_count}`);
      return false;
    } else {
      if (debug) Logger.log(`✅ フォロワー数: ${metrics.followers_count}`);
    }
  } else {
    if (debug) Logger.log(`⏭️ フォロワー数チェック: スキップ (${metrics ? metrics.followers_count : 'N/A'})`);
  }

  // 2. フォロー/フォロワー比率チェック（metrics がある場合のみ）
  if (FILTER_RATIO) {
    if (!metrics) {
      if (debug) Logger.log(`⏭️ フォロー/フォロワー比率チェック: ユーザー情報なしのためスキップ`);
    } else if (metrics.followers_count === 0) {
      if (debug) Logger.log(`❌ フォロワー数が0`);
      return false;
    } else {
      const ratio = metrics.following_count / metrics.followers_count;
      if (ratio < MIN_FOLLOW_RATIO || ratio >= MAX_FOLLOW_RATIO) {
        if (debug) Logger.log(`❌ フォロー/フォロワー比率: ${ratio.toFixed(2)}`);
        return false;
      }
      if (debug) Logger.log(`✅ フォロー/フォロワー比率: ${ratio.toFixed(2)}`);
    }
  } else {
    if (debug) Logger.log(`⏭️ フォロー/フォロワー比率チェック: スキップ`);
  }

  // 3. プロフィールにキーワードが含まれるか確認（description がある場合のみ）
  if (FILTER_KEYWORD) {
    const bio = account.description || '';
    const keywordsForBio = (typeof BIO_KEYWORDS !== 'undefined' && BIO_KEYWORDS !== null)
      ? BIO_KEYWORDS
      : KEYWORDS;
    const hasKeyword = keywordsForBio.some(keyword => bio.includes(keyword));
    if (!hasKeyword) {
      if (debug) Logger.log(`❌ プロフィールにキーワードなし`);
      return false;
    }
    if (debug) {
      const matchedKeywords = keywordsForBio.filter(keyword => bio.includes(keyword));
      Logger.log(`✅ プロフィールにキーワードあり: ${matchedKeywords.join(', ')}`);
    }
  } else {
    if (debug) Logger.log(`⏭️ キーワードチェック: スキップ`);
  }

  // 4. 最終投稿日チェック
  if (FILTER_TWEET_DATE) {
    if (!account.latest_tweet_date) {
      if (debug) Logger.log(`❌ 最終投稿日情報なし`);
      return false;
    }
    const daysSinceTweet = (new Date() - account.latest_tweet_date) / (1000 * 60 * 60 * 24);
    if (daysSinceTweet > MAX_DAYS_SINCE_TWEET) {
      if (debug) Logger.log(`❌ 最終投稿: ${daysSinceTweet.toFixed(1)}日前`);
      return false;
    }
    if (debug) Logger.log(`✅ 最終投稿: ${daysSinceTweet.toFixed(1)}日前`);
  } else {
    if (debug) Logger.log(`⏭️ 最終投稿日チェック: スキップ`);
  }

  if (debug) Logger.log(`🎉 すべての条件をクリア！`);
  return true;
}

// ===================================================
// 出力・ユーティリティ
// ===================================================

/**
 * 重複を除去
 */
function removeDuplicates(accounts) {
  const unique = [];
  const ids = new Set();
  
  accounts.forEach(account => {
    if (!ids.has(account.id)) {
      ids.add(account.id);
      unique.push(account);
    }
  });
  
  return unique;
}

/**
 * スプレッドシートに出力
 */
function outputToSheet(accounts, sheetName) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName(sheetName);
  
  if (!sheet) {
    sheet = ss.insertSheet(sheetName);
  } else {
    sheet.clear();
  }
  
  const headers = [
    'ユーザー名', '表示名', 'プロフィール', 
    'フォロワー数', 'フォロー数', 'フォロー/フォロワー比率',
    '最終投稿日', 'アカウントURL', 'ツイートURL'
  ];
  
  sheet.appendRow(headers);
  
  accounts.forEach(account => {
    const metrics = account.public_metrics;

    const followers = metrics ? metrics.followers_count : '';
    const following = metrics ? metrics.following_count : '';
    const ratio = (metrics && metrics.followers_count > 0)
      ? (metrics.following_count / metrics.followers_count).toFixed(2)
      : '';

    // FETCH_USER_INFO=true のとき → latest_tweet_date
    // FETCH_USER_INFO=false のとき → created_at（ツイートオブジェクトの日時）
    const tweetDate = account.latest_tweet_date
      ? account.latest_tweet_date
      : (account.created_at ? new Date(account.created_at) : null);
    const lastTweetDate = tweetDate
      ? tweetDate.toLocaleDateString('ja-JP')
      : '';

    // FETCH_USER_INFO=true のとき → username からURL生成
    // FETCH_USER_INFO=false のとき → author_id しかないためURL生成不可
    const accountUrl = account.username
      ? `https://x.com/${account.username}`
      : '';

    // FETCH_USER_INFO=true のとき → latest_tweet_id
    // FETCH_USER_INFO=false のとき → id（ツイートオブジェクトのID）
    const tweetId = account.latest_tweet_id || account.id || '';
    const tweetUrl = (tweetId && account.username)
      ? `https://x.com/${account.username}/status/${tweetId}`
      : (tweetId ? `https://x.com/i/web/status/${tweetId}` : '');

    sheet.appendRow([
      account.username    || '',
      account.name        || '',
      account.description || '',
      followers,
      following,
      ratio,
      lastTweetDate,
      accountUrl,
      tweetUrl
    ]);
  });
  
  sheet.autoResizeColumns(1, headers.length);
}

/**
 * 「交流候補リスト」シートからユーザー名一覧を取得
 */
function getExistingUsernames() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName('交流候補リスト');

  if (!sheet) {
    Logger.log('「交流候補リスト」シートが存在しません');
    return new Set();
  }

  const lastRow = sheet.getLastRow();
  if (lastRow <= 1) {
    // ヘッダーのみ or 空
    return new Set();
  }

  // A列（ユーザー名）を1行目（ヘッダー）を除いて取得
  const values = sheet.getRange(2, 1, lastRow - 1, 1).getValues();
  const usernames = values
    .map(row => String(row[0]).toLowerCase().trim())
    .filter(name => name !== '');

  Logger.log(`交流候補リストの既存アカウント数: ${usernames.length}件`);
  return new Set(usernames);
}

// ===================================================
// メイン処理
// ===================================================

/**
 * メイン関数
 */
function searchQualifiedAccounts() {
  // 認証チェック
  if (!checkAuthStatus()) {
    Logger.log('\n先に authorizeX() を実行して認証してください');
    return [];
  }

  Logger.log(`\n${'='.repeat(60)}`);
  Logger.log('アカウント検索開始');
  Logger.log(`${'='.repeat(60)}\n`);

  Logger.log('検索条件:');
  Logger.log(`  キーワード: ${KEYWORDS.join(', ')}`);
  Logger.log(`  フォロワー数フィルター: ${FILTER_FOLLOWERS ? `${MIN_FOLLOWERS}〜${MAX_FOLLOWERS}未満` : 'オフ'}`);
  Logger.log(`  フォロー比率フィルター: ${FILTER_RATIO ? `${MIN_FOLLOW_RATIO}〜${MAX_FOLLOW_RATIO}未満` : 'オフ'}`);
  Logger.log(`  キーワードフィルター: ${FILTER_KEYWORD ? 'オン' : 'オフ'}`);
  Logger.log(`  最終投稿フィルター: ${FILTER_TWEET_DATE ? `${MAX_DAYS_SINCE_TWEET}日以内` : 'オフ'}\n`);

  const results = [];

  // 1回だけAPIを叩く
  const accounts = searchUsersByKeyword();

  if (accounts.length === 0) {
    Logger.log('⚠️ アカウントが取得できませんでした');
  } else {
    Logger.log(`\n取得したアカウント: ${accounts.length}件`);

    let matchCount = 0;
  accounts.forEach(account => {
    if (!account) {
      Logger.log('⚠️ スキップ: アカウント情報なし');
      return;
    }

    // FETCH_USER_INFO = false のときは public_metrics がなくてもスキップしない
    if (!account.public_metrics && FETCH_USER_INFO) {
      Logger.log('⚠️ スキップ: ユーザー情報不完全');
      return;
    }

    if (meetsAllCriteria(account)) {
      results.push(account);
      matchCount++;
      Logger.log(`  ✅ @${account.username || account.author_id}`);
    }
  });

    Logger.log(`条件一致: ${matchCount}件`);
  }

  const uniqueResults = removeDuplicates(results);

  Logger.log(`\n${'='.repeat(60)}`);
  Logger.log('最終結果');
  Logger.log(`${'='.repeat(60)}`);
  Logger.log(`重複除去前: ${results.length}件`);
  Logger.log(`重複除去後: ${uniqueResults.length}件`);

  if (uniqueResults.length === 0) {
    Logger.log('\n⚠️ 条件に一致するアカウントが見つかりませんでした');
    return [];
  }

  // 交流候補リストに既存のアカウントを除外
  let finalResults = uniqueResults;
  if (EXCLUDE_EXISTING) {
    const existingUsernames = getExistingUsernames();
    const beforeCount = finalResults.length;
    finalResults = finalResults.filter(account => {
      const username = account.username || '';
      return !existingUsernames.has(username.toLowerCase());
    });
    const excludedCount = beforeCount - finalResults.length;
    Logger.log(`既存アカウント除外: ${excludedCount}件除外 → ${finalResults.length}件残`);
  }

  if (finalResults.length === 0) {
    Logger.log('\n⚠️ 出力対象のアカウントが見つかりませんでした');
    return [];
  }

  try {
    outputToSheet(finalResults, '検索結果');
    Logger.log(`\n✅ スプレッドシート「検索結果」に出力しました`);
  } catch (e) {
    Logger.log(`\n❌ スプレッドシート出力エラー: ${e.message}`);
  }

  Logger.log(`${'='.repeat(60)}\n`);
  return uniqueResults;
}