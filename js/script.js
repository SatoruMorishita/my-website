//index.html
　function login() {
    const user = document.getElementById("username").value;
    const pass = document.getElementById("password").value;

    if (user === "admin" && pass === "1234") {
      // ローディング表示
      document.getElementById("loading").style.display = "block";

      // 1秒待ってから遷移
      setTimeout(() => {
        window.location.href = "about.html";
      }, 1000);
    } else {
      alert("ユーザー名またはパスワードが違います");
    }
  }


//about.html
document.getElementById("searchInput").addEventListener("keydown", function(event) {
    if (event.key === "Enter") {
      highlightAll();
    }
  });

  function sayHello() {
    alert("こんにちは！JavaScriptが動いています！");
  }

  function logout() {
  const confirmLogout = confirm("ログアウトします。よろしいですか？");
  if (confirmLogout) {
    // 「はい」が選ばれた場合のみログイン画面へ遷移
    window.location.href = "index.html?status=loggedout";
  } else {
    // 「いいえ」の場合は何もしない（キャンセル）
    console.log("ログアウトをキャンセルしました。");
  }
}

  function highlightAll() {
    const keyword = document.getElementById("searchInput").value.trim();
    if (!keyword) return;

    document.querySelectorAll('.highlight').forEach(el => {
      el.outerHTML = el.innerText;
    });

    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null, false);
    let found = false;

    while (walker.nextNode()) {
      const node = walker.currentNode;
      const parent = node.parentNode;

      if (node.nodeValue.includes(keyword)) {
        const span = document.createElement('span');
        span.className = 'highlight';
        const regex = new RegExp(`(${keyword})`, 'gi');
        span.innerHTML = node.nodeValue.replace(regex, '<mark>$1</mark>');
        parent.replaceChild(span, node);
        found = true;
      }
    }

    if (!found) {
      alert("該当する項目が見つかりませんでした。");
    }
  }

document.body.addEventListener("click", function (event) {
  // 検索ボックスや検索ボタンをクリックした場合は除外
  const isSearchRelated =
    event.target.id === "searchInput" ||
    event.target.tagName === "BUTTON";

  if (isSearchRelated) return;

  document.querySelectorAll(".highlight").forEach((el) => {
    el.outerHTML = el.innerText;
  });
});


document.getElementById("searchInput").addEventListener("keydown", function(event) {
    if (event.key === "Enter") {
      highlightAll();
    }
  });
