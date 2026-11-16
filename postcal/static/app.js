// 字数カウンタ（空白・改行を除いた文字数。brand の字数基準と同じ数え方）
document.querySelectorAll("textarea[data-counter]").forEach(function (ta) {
  var out = document.getElementById(ta.dataset.counter);
  if (!out) return;
  var update = function () { out.textContent = ta.value.replace(/\s/g, "").length; };
  ta.addEventListener("input", update);
  update();
});

// メディア選択時の簡易チェック（サーバー側でも検証する）
var fileInput = document.querySelector('input[type=file][name=media]');
if (fileInput) {
  fileInput.addEventListener("change", function () {
    var imgs = 0, vids = 0, msgs = [];
    Array.from(fileInput.files).forEach(function (f) {
      var ext = (f.name.split(".").pop() || "").toLowerCase();
      if (ext === "mp4" || ext === "mov") { vids++; if (f.size > 512 * 1024 * 1024) msgs.push(f.name + ": 512MB 超"); }
      else if (["png", "jpg", "jpeg", "gif"].indexOf(ext) >= 0) { imgs++; var lim = ext === "gif" ? 15 : 5; if (f.size > lim * 1024 * 1024) msgs.push(f.name + ": " + lim + "MB 超"); }
      else msgs.push(f.name + ": 非対応の形式");
    });
    if (vids > 1) msgs.push("動画は 1 本まで");
    if (vids && imgs) msgs.push("画像と動画は混在不可");
    if (imgs > 4) msgs.push("画像は 4 枚まで");
    if (msgs.length) { alert(msgs.join("\n")); fileInput.value = ""; }
  });
}
