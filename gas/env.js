/**
 * 環境変数・認証情報の設定ファイル
 * このファイルに認証情報を一元管理します
 */
 
// ========================================
// X API 認証情報
// ========================================
 
// Bearer Token認証用（旧API）
const API_KEY = '05ca9oZDsrtyYgIkY5m9mGZbx';
const API_SECRET = 'bqIo5y93Hrdln8wv6AYelvdijQxz1nrTBoZnqLNYNJV3a5RNMf';
const ACCESS_TOKEN = '548606471-ckJWIDAG8xqvmcIuy65JcXZl2puApJoziRk7QrsC';
const ACCESS_TOKEN_SECRET = '3tAtrBbHThxoyXonDp6ZKtiSFsTBM2axDGs5GmjUkCdJy';
 
// OAuth2 認証情報（現在使用中）
const CLIENT_ID = 'eGQ2YU5OSndqS3lKRGZmYTR6OU06MTpjaQ';
const CLIENT_SECRET = 'xNGu-t7m3stTb2LOt_HEx93vRfQIfkDe9kdfBTjrqg3e3E5hug';
 
// ========================================
// ユーザー情報
// ========================================
 
const USER_ID = 'usephys';  // 数値IDまたはユーザー名（例: 'usephys' または '548606471'）
 
// ========================================
// Googleスプレッドシート設定
// ========================================
 
const SPREADSHEET_ID = '1_0317hOqbgGfcSZQ9D9-JlwgqvKxzQuRaw08U-5nw0c';
 
// ========================================
// CONFIG オブジェクト（他のスクリプトから参照用）
// ========================================
 
const CONFIG = {
  // X API 認証情報
  API_KEY: API_KEY,
  API_SECRET: API_SECRET,
  ACCESS_TOKEN: ACCESS_TOKEN,
  ACCESS_TOKEN_SECRET: ACCESS_TOKEN_SECRET,
  
  // OAuth2 認証情報
  CLIENT_ID: CLIENT_ID,
  CLIENT_SECRET: CLIENT_SECRET,
  
  // ユーザー情報
  USER_ID: USER_ID,
  
  // スプレッドシート設定
  SPREADSHEET_ID: SPREADSHEET_ID
};
