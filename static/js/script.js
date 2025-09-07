//クローズボタン追加

document.addEventListener("DOMContentLoaded", function () {
  const closeBtn = document.getElementById('api-close-btn');
  if (closeBtn) {
    closeBtn.addEventListener('click', function () {
      alert("クリックされたよ！");
      window.location.href = 'https://satorumorishita.github.io/my-website/about.html';
    });
  }
});
