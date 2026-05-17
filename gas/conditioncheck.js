/**
 * 「交流候補リスト」シートからアカウント情報を取得
 */
function getAccountsFromSheet() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName('交流候補リスト');
  
  if (!sheet) {
    Logger.log('❌ 「交流候補リスト」シートが見つかりません');
    return [];
  }
  
  const data = sheet.getDataRange().getValues();
  
  if (data.length <= 1) {
    Logger.log('❌ データがありません');
    return [];
  }
  
  // ヘッダー行を取得
  const headers = data[0];
  Logger.log(`ヘッダー: ${headers.join(', ')}`);
  
  // データ行を解析
  const accounts = [];
  for (let i = 1; i < data.length; i++) {
    const row = data[i];
    
    // ユーザー名が空の行はスキップ
    if (!row[0]) continue;
    
    const account = {
      username: row[0],
      name: row[1],
      description: row[2],
      public_metrics: {
        followers_count: Number(row[3]) || 0,
        following_count: Number(row[4]) || 0
      },
      latest_tweet_date: row[6] ? new Date(row[6]) : null,
      url: row[7]
    };
    
    accounts.push(account);
  }
  
  Logger.log(`${accounts.length}件のアカウントを読み込みました`);
  return accounts;
}

/**
 * 統計情報を表示する関数（シート版）
 */
function analyzeFailureReasons() {
  Logger.log('=== 除外理由の統計分析 ===\n');
  Logger.log('「交流候補リスト」シートからデータを読み込みます...\n');
  
  const accounts = getAccountsFromSheet();
  
  if (accounts.length === 0) {
    Logger.log('❌ アカウントデータが取得できませんでした');
    return;
  }
  
  const stats = {
    total: 0,
    failedFollowers: 0,
    failedRatio: 0,
    failedKeyword: 0,
    failedTweet: 0,
    passed: 0
  };
  
  accounts.forEach(account => {
    stats.total++;
    const metrics = account.public_metrics;
    const bio = account.description || '';
    
    // フォロワー数チェック
    if (metrics.followers_count < MIN_FOLLOWERS || metrics.followers_count >= MAX_FOLLOWERS) {
      stats.failedFollowers++;
      return;
    }
    
    // 比率チェック
    if (metrics.followers_count === 0) {
      stats.failedRatio++;
      return;
    }
    const ratio = metrics.following_count / metrics.followers_count;
    if (ratio < MIN_FOLLOW_RATIO || ratio >= MAX_FOLLOW_RATIO) {
      stats.failedRatio++;
      return;
    }
    
    // キーワードチェック
    const hasKeyword = KEYWORDS.some(kw => bio.includes(kw));
    if (!hasKeyword) {
      stats.failedKeyword++;
      return;
    }
    
    // 最終投稿日チェック
    if (!account.latest_tweet_date) {
      stats.failedTweet++;
      return;
    }
    
    const daysSinceTweet = (new Date() - account.latest_tweet_date) / (1000 * 60 * 60 * 24);
    
    if (daysSinceTweet > MAX_DAYS_SINCE_TWEET) {
      stats.failedTweet++;
      return;
    }
    
    stats.passed++;
  });
  
  Logger.log('\n=== 結果サマリー ===');
  Logger.log(`総アカウント数: ${stats.total}`);
  Logger.log(`フォロワー数で除外: ${stats.failedFollowers} (${(stats.failedFollowers/stats.total*100).toFixed(1)}%)`);
  Logger.log(`フォロー比率で除外: ${stats.failedRatio} (${(stats.failedRatio/stats.total*100).toFixed(1)}%)`);
  Logger.log(`キーワードなしで除外: ${stats.failedKeyword} (${(stats.failedKeyword/stats.total*100).toFixed(1)}%)`);
  Logger.log(`最終投稿日で除外: ${stats.failedTweet} (${(stats.failedTweet/stats.total*100).toFixed(1)}%)`);
  Logger.log(`条件クリア: ${stats.passed} (${(stats.passed/stats.total*100).toFixed(1)}%)`);
  
  Logger.log('\n=== 推奨アクション ===');
  if (stats.failedFollowers > stats.total * 0.3) {
    Logger.log('💡 フォロワー数の条件を緩和することを検討してください');
  }
  if (stats.failedRatio > stats.total * 0.3) {
    Logger.log('💡 フォロー/フォロワー比率の条件を緩和することを検討してください');
  }
  if (stats.failedKeyword > stats.total * 0.3) {
    Logger.log('💡 キーワードを追加または変更することを検討してください');
  }
  if (stats.failedTweet > stats.total * 0.3) {
    Logger.log('💡 最終投稿日の条件を緩和することを検討してください');
  }
}

/**
 * 最初の数件だけ詳細チェック（シート版）
 */
function debugFirstFewAccounts() {
  Logger.log('=== 最初の5件を詳細チェック ===\n');
  Logger.log('「交流候補リスト」シートからデータを読み込みます...\n');
  
  const accounts = getAccountsFromSheet();
  
  if (accounts.length === 0) {
    Logger.log('❌ アカウントデータが取得できませんでした');
    return;
  }
  
  const toCheck = accounts.slice(0, 5); // 最初の5件
  
  toCheck.forEach(account => {
    meetsAllCriteria(account, true); // debug = true
  });
}

/**
 * 条件に合致するアカウントだけを新しいシートに出力
 */
function filterAndOutputQualifiedAccounts() {
  Logger.log('=== 条件に合致するアカウントをフィルタリング ===\n');
  
  const accounts = getAccountsFromSheet();
  
  if (accounts.length === 0) {
    Logger.log('❌ アカウントデータが取得できませんでした');
    return;
  }
  
  const qualifiedAccounts = accounts.filter(account => meetsAllCriteria(account, false));
  
  Logger.log(`\n条件クリア: ${qualifiedAccounts.length}/${accounts.length}件`);
  
  if (qualifiedAccounts.length === 0) {
    Logger.log('⚠️ 条件に合致するアカウントがありませんでした');
    return;
  }
  
  // 新しいシートに出力
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName('フィルタ結果');
  
  if (!sheet) {
    sheet = ss.insertSheet('フィルタ結果');
  } else {
    sheet.clear();
  }
  
  // ヘッダー
  const headers = [
    'ユーザー名', '表示名', 'プロフィール', 
    'フォロワー数', 'フォロー数', 'フォロー/フォロワー比率',
    '最終投稿日', 'URL'
  ];
  
  sheet.appendRow(headers);
  
  // データ
  qualifiedAccounts.forEach(account => {
    const metrics = account.public_metrics;
    const ratio = (metrics.following_count / metrics.followers_count).toFixed(2);
    
    const lastTweetDate = account.latest_tweet_date 
      ? account.latest_tweet_date.toLocaleDateString('ja-JP') 
      : '不明';
    
    const row = [
      account.username,
      account.name,
      account.description,
      metrics.followers_count,
      metrics.following_count,
      ratio,
      lastTweetDate,
      account.url
    ];
    
    sheet.appendRow(row);
  });
  
  // 列幅を自動調整
  sheet.autoResizeColumns(1, headers.length);
  
  Logger.log(`\n✅ 「フィルタ結果」シートに${qualifiedAccounts.length}件出力しました`);
}

/**
 * 条件をカスタマイズしてテスト
 */
function testWithCustomConditions() {
  Logger.log('=== カスタム条件でテスト ===\n');
  
  // テスト用に条件を一時変更
  const ORIGINAL_MIN_FOLLOWERS = MIN_FOLLOWERS;
  const ORIGINAL_MAX_FOLLOWERS = MAX_FOLLOWERS;
  const ORIGINAL_MIN_RATIO = MIN_FOLLOW_RATIO;
  const ORIGINAL_MAX_RATIO = MAX_FOLLOW_RATIO;
  const ORIGINAL_MAX_DAYS = MAX_DAYS_SINCE_TWEET;
  
  // ここで条件を変更してテスト
  Logger.log('現在の条件:');
  Logger.log(`  フォロワー数: ${MIN_FOLLOWERS}〜${MAX_FOLLOWERS}未満`);
  Logger.log(`  フォロー比率: ${MIN_FOLLOW_RATIO}〜${MAX_FOLLOW_RATIO}未満`);
  Logger.log(`  最終投稿: ${MAX_DAYS_SINCE_TWEET}日以内\n`);
  
  analyzeFailureReasons();
}