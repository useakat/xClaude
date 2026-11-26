// 字数カウンタ（空白・改行を除いた文字数。brand の字数基準と同じ数え方）
function bindCounter(ta, out) {
  if (!ta || !out) return;
  var update = function () { out.textContent = ta.value.replace(/\s/g, "").length; };
  ta.addEventListener("input", update);
  update();
}
document.querySelectorAll("textarea[data-counter]").forEach(function (ta) {
  bindCounter(ta, document.getElementById(ta.dataset.counter));
});

// 続きの投稿（スレッド）: カード 1 枚 = 1 投稿。追加・削除のたびに「n 本目」を振り直す
(function () {
  var box = document.getElementById("thread-items");
  if (!box) return;
  var total = document.getElementById("thread-total");
  var tpl = document.getElementById("thread-item-tpl");
  var addBtn = document.getElementById("thread-add");

  function renumber() {
    var items = box.querySelectorAll(".thread-item");
    items.forEach(function (it, i) { it.querySelector(".thread-no").textContent = (i + 2) + " 本目"; });
    if (total) total.textContent = items.length ? "全 " + (items.length + 1) + " 本" : "";
  }
  function setup(item) {
    var ta = item.querySelector("textarea");
    bindCounter(ta, item.querySelector(".count"));
    var rm = item.querySelector(".thread-remove");
    if (rm) rm.addEventListener("click", function () {
      if (ta.value.trim() && !confirm("この投稿を削除しますか？")) return;
      item.remove();
      renumber();
    });
  }
  box.querySelectorAll(".thread-item").forEach(setup);
  renumber();
  if (addBtn && tpl) addBtn.addEventListener("click", function () {
    var item = tpl.content.firstElementChild.cloneNode(true);
    box.appendChild(item);
    setup(item);
    renumber();
    item.querySelector("textarea").focus();
  });
})();

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
