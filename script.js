
  <script>
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

  // Enterキーでもログイン
  document.addEventListener("keydown", function(event) {
    if (event.key === "Enter") {
      login();
    }
  });
　
　// ページ表示時にアラートを1秒だけ表示
window.addEventListener("load", () => {
  const alertBox = document.getElementById("loginAlert");
  alertBox.style.display = "block";

  setTimeout(() => {
    alertBox.style.display = "none";
  }, 1000);
});
    window.addEventListener("load", () => {
    document.getElementById("username").focus();
  });
  </script>
