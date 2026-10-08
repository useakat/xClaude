/**
 * X 投稿インプレッション通知（Google Apps Script 版）
 *
 * 自分の X 投稿が「投稿から WINDOW_HOURS 時間以内に THRESHOLD インプ」に達したら
 * メールで知らせます（1投稿につき1回だけ）。
 *
 * 対象: 自分のオリジナル投稿＋引用RT（リポストと自分のリプライは除外）
 * 課金: X API は従量課金（返ってきた投稿1件ごと、自分の投稿は $0.001/件）。
 *       start_time で時間窓内の投稿だけを取得するので、投稿が無い時間帯は課金ゼロです。
 *       目安: 1日10投稿・30分間隔で月 $2 前後。
 *
 * ── 使い方（スマホのブラウザだけで完結します）──────────────────
 *  1. 下の CONFIG を書き換える（X_BEARER_TOKEN / X_USERNAME / NOTIFY_TO）
 *  2. 画面上部の関数選択で「setup」を選んで ▶ 実行 → 権限の承認画面が出るので許可
 *     （30分おきの自動実行が登録されます。setup は何度実行しても二重登録されません）
 *  3. 「testRun」を実行すると、メールを送らずに判定結果だけ「実行ログ」に出ます
 *  4. 「sendTestMail」を実行すると、通知メールの見本が NOTIFY_TO に届きます
 *  止めたいときは「teardown」を実行してください。
 * ────────────────────────────────────────────────────────────
 */

// ===== ここを書き換える =====================================================
const CONFIG = {
  X_BEARER_TOKEN: "ここに X Developer Portal で発行した Bearer Token を貼る",
  X_USERNAME: "your_x_username",   // @ を付けない自分の X ユーザー名
  NOTIFY_TO: "you@example.com",    // 通知を受け取るメールアドレス
  THRESHOLD: 1000,                 // インプ閾値
  WINDOW_HOURS: 3,                 // 投稿からの時間窓（時間）
  CHECK_INTERVAL_MIN: 30,          // チェック間隔（分）。1 / 5 / 10 / 15 / 30 のいずれか
};
// ==========================================================================

const MAX_RESULTS = 10;        // 1回あたりの最大取得数（start_time で絞るので安全弁）
const START_MARGIN_MIN = 10;   // start_time の余裕（分）。時計ずれ対策
const STATE_KEEP_DAYS = 7;     // 通知済み記録の保持日数
const TZ = "Asia/Tokyo";

const PROPS = PropertiesService.getScriptProperties();

// ───────────────────────────── 公開関数（メニューから実行するもの） ─────

/** 初回セットアップ：設定確認・ユーザーID取得・定期トリガー登録 */
function setup() {
  validateConfig_();
  const userId = resolveUserId_();
  teardown_(false);
  ScriptApp.newTrigger("check").timeBased().everyMinutes(CONFIG.CHECK_INTERVAL_MIN).create();
  console.log(`セットアップ完了: @${CONFIG.X_USERNAME} (id=${userId}) を ${CONFIG.CHECK_INTERVAL_MIN} 分おきに監視します`);
  console.log(`閾値: 投稿から ${CONFIG.WINDOW_HOURS} 時間以内に ${CONFIG.THRESHOLD} インプ → ${CONFIG.NOTIFY_TO} へ通知`);
}

/** 監視を止める（トリガー削除）。通知済み記録は残す */
function teardown() {
  teardown_(true);
}

/** 本番と同じ判定をするが、メール送信と記録保存はしない */
function testRun() {
  run_({ dryRun: true });
}

/** 通知メールの見本を送る（API は呼ばない） */
function sendTestMail() {
  validateConfig_();
  const sample = {
    id: "0000000000000000000",
    text: "これはテスト通知です。実際の投稿が閾値に達すると、この形式でメールが届きます。",
    created_at: new Date(Date.now() - 95 * 60 * 1000).toISOString(),
    referenced_tweets: [],
    public_metrics: { impression_count: 1234, like_count: 56, retweet_count: 7, quote_count: 2, reply_count: 8, bookmark_count: 11 },
  };
  const posted = new Date(sample.created_at);
  const mail = buildMail_(sample, posted, Date.now() - posted.getTime());
  MailApp.sendEmail(CONFIG.NOTIFY_TO, "[テスト] " + mail.subject, mail.body);
  console.log(`テストメールを ${CONFIG.NOTIFY_TO} に送りました`);
}

/** 定期実行の本体（トリガーから呼ばれる） */
function check() {
  run_({ dryRun: false });
}

// ───────────────────────────── 内部処理 ───────────────────────────────

function run_(opt) {
  validateConfig_();
  const now = new Date();
  const state = loadState_();
  pruneState_(state, now);

  let tweets;
  try {
    tweets = fetchRecentPosts_(now);
    clearApiError_();
  } catch (e) {
    console.error("X API エラー: " + e.message);
    notifyApiErrorOnce_(e.message);
    return;
  }

  const windowMs = CONFIG.WINDOW_HOURS * 3600 * 1000;
  let checked = 0, notified = 0;

  for (const t of tweets) {
    if (!isTarget_(t)) continue;
    const postedAt = new Date(t.created_at);
    const ageMs = now.getTime() - postedAt.getTime();
    if (ageMs > windowMs) continue;
    checked++;
    const imp = t.public_metrics.impression_count;
    const ageMin = Math.floor(ageMs / 60000);
    if (imp < CONFIG.THRESHOLD) {
      if (opt.dryRun) console.log(`[dry-run] ${t.id} 経過${ageMin}分 ${fmt_(imp)}インプ（未達）`);
      continue;
    }
    if (state.notified[t.id]) continue;
    const mail = buildMail_(t, postedAt, ageMs);
    if (opt.dryRun) {
      console.log(`[dry-run] 通知対象: ${t.id} ${fmt_(imp)}インプ\n--- 件名: ${mail.subject}\n${mail.body}\n---`);
      continue;
    }
    MailApp.sendEmail(CONFIG.NOTIFY_TO, mail.subject, mail.body);
    state.notified[t.id] = { notified_at: now.toISOString(), impressions: imp, age_minutes: ageMin };
    notified++;
    console.log(`通知: https://x.com/${CONFIG.X_USERNAME}/status/${t.id} ${fmt_(imp)}インプ`);
  }

  if (!opt.dryRun) saveState_(state);
  console.log(`完了: 時間窓内${checked}件を確認、通知${notified}件${opt.dryRun ? "（dry-run）" : ""}`);
}

function fetchRecentPosts_(now) {
  const userId = resolveUserId_();
  const startTime = new Date(now.getTime() - (CONFIG.WINDOW_HOURS * 60 + START_MARGIN_MIN) * 60 * 1000);
  const params = {
    max_results: MAX_RESULTS,
    exclude: "retweets",
    start_time: startTime.toISOString().replace(/\.\d{3}Z$/, "Z"),
    "tweet.fields": "created_at,public_metrics,referenced_tweets,text",
  };
  const url = `https://api.x.com/2/users/${userId}/tweets?` + toQuery_(params);
  const data = apiGet_(url);
  return data.data || [];
}

/** ユーザー名 → ユーザーID。初回だけ API を呼び、以後はキャッシュを使う */
function resolveUserId_() {
  const key = "USER_ID:" + CONFIG.X_USERNAME.toLowerCase();
  const cached = PROPS.getProperty(key);
  if (cached) return cached;
  const data = apiGet_(`https://api.x.com/2/users/by/username/${encodeURIComponent(CONFIG.X_USERNAME)}`);
  if (!data.data || !data.data.id) throw new Error("ユーザーが見つかりません: @" + CONFIG.X_USERNAME);
  PROPS.setProperty(key, data.data.id);
  return data.data.id;
}

function apiGet_(url) {
  const res = UrlFetchApp.fetch(url, {
    method: "get",
    headers: { Authorization: "Bearer " + CONFIG.X_BEARER_TOKEN.trim() },
    muteHttpExceptions: true,
  });
  const code = res.getResponseCode();
  const text = res.getContentText();
  if (code !== 200) {
    const hint = { 401: "Bearer Token が無効です", 402: "X API のクレジット残高が不足しています", 403: "この操作の権限がありません", 429: "レート制限に達しました" }[code] || "";
    throw new Error(`HTTP ${code} ${hint} ${text.slice(0, 200)}`);
  }
  return JSON.parse(text);
}

function isTarget_(t) {
  return !(t.referenced_tweets || []).some(r => r.type === "replied_to");
}

function buildMail_(t, postedAt, ageMs) {
  const pm = t.public_metrics;
  const kind = (t.referenced_tweets || []).some(r => r.type === "quoted") ? "引用RT" : "オリジナル";
  const mins = Math.floor(ageMs / 60000);
  const ageStr = `${Math.floor(mins / 60)}時間${mins % 60}分`;
  const textHead = (t.text || "").replace(/\n/g, " ").slice(0, 100);
  const subject = `【Xインプ通知】投稿から${ageStr}で${fmt_(pm.impression_count)}インプ到達`;
  const body = [
    `投稿から${CONFIG.WINDOW_HOURS}時間以内に${fmt_(CONFIG.THRESHOLD)}インプに達した投稿があります。`,
    "",
    `URL: https://x.com/${CONFIG.X_USERNAME}/status/${t.id}`,
    `種類: ${kind}`,
    `投稿時刻: ${Utilities.formatDate(postedAt, TZ, "yyyy-MM-dd HH:mm")} JST`,
    `経過時間: ${ageStr}`,
    "",
    `インプレッション: ${fmt_(pm.impression_count)}`,
    `いいね: ${fmt_(pm.like_count)} / リポスト: ${fmt_(pm.retweet_count)} / 引用: ${fmt_(pm.quote_count)}`,
    `リプライ: ${fmt_(pm.reply_count)} / ブックマーク: ${fmt_(pm.bookmark_count || 0)}`,
    "",
    `本文冒頭: ${textHead}`,
  ].join("\n");
  return { subject, body };
}

// 状態（通知済み記録）はスクリプトプロパティに JSON で保存
function loadState_() {
  try {
    const raw = PROPS.getProperty("STATE");
    if (raw) {
      const s = JSON.parse(raw);
      if (s && typeof s.notified === "object") return s;
    }
  } catch (e) {
    console.warn("state が壊れているため初期化します");
  }
  return { notified: {} };
}

function saveState_(state) {
  PROPS.setProperty("STATE", JSON.stringify(state));
}

function pruneState_(state, now) {
  const cutoff = now.getTime() - STATE_KEEP_DAYS * 24 * 3600 * 1000;
  for (const id of Object.keys(state.notified)) {
    const at = Date.parse((state.notified[id] || {}).notified_at);
    if (isNaN(at) || at < cutoff) delete state.notified[id];
  }
}

// API エラーは同じ内容なら1回だけメールする（毎回送ってスパムにならないように）
function notifyApiErrorOnce_(msg) {
  const key = msg.slice(0, 40);
  if (PROPS.getProperty("LAST_API_ERROR") === key) return;
  PROPS.setProperty("LAST_API_ERROR", key);
  MailApp.sendEmail(CONFIG.NOTIFY_TO, "【Xインプ通知】X API エラー", "監視が失敗しました。設定・クレジット残高を確認してください。\n\n" + msg);
}

function clearApiError_() {
  PROPS.deleteProperty("LAST_API_ERROR");
}

function teardown_(verbose) {
  let n = 0;
  for (const tr of ScriptApp.getProjectTriggers()) {
    if (tr.getHandlerFunction() === "check") { ScriptApp.deleteTrigger(tr); n++; }
  }
  if (verbose) console.log(`監視を停止しました（トリガー ${n} 件を削除）`);
}

function validateConfig_() {
  const c = CONFIG;
  const bad = [];
  if (!c.X_BEARER_TOKEN || /ここに/.test(c.X_BEARER_TOKEN)) bad.push("X_BEARER_TOKEN");
  if (!c.X_USERNAME || c.X_USERNAME === "your_x_username" || /^@/.test(c.X_USERNAME)) bad.push("X_USERNAME（@ は付けない）");
  if (!c.NOTIFY_TO || !/@/.test(c.NOTIFY_TO) || c.NOTIFY_TO === "you@example.com") bad.push("NOTIFY_TO");
  if (!(c.THRESHOLD > 0)) bad.push("THRESHOLD");
  if (!(c.WINDOW_HOURS > 0)) bad.push("WINDOW_HOURS");
  if (![1, 5, 10, 15, 30].includes(c.CHECK_INTERVAL_MIN)) bad.push("CHECK_INTERVAL_MIN（1/5/10/15/30 のいずれか）");
  if (bad.length) throw new Error("CONFIG を確認してください: " + bad.join(", "));
}

function toQuery_(params) {
  return Object.keys(params).map(k => encodeURIComponent(k) + "=" + encodeURIComponent(params[k])).join("&");
}

function fmt_(n) {
  return Number(n || 0).toLocaleString("en-US");
}
