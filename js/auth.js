function openAuthModal() {
    const m = document.getElementById('authModal');
    if (m) m.classList.remove('hidden');
}

function closeAuthModal() {
    const m = document.getElementById('authModal');
    if (m) m.classList.add('hidden');
}

(function () {
    const API_BASE = "http://47.238.241.178:80/api";

    const STORAGE_KEYS = {
      isLoggedIn: 'isLoggedIn',
      username: 'username',
      currentUser: 'currentUser',
    };

    function setLogin(u) {
      sessionStorage.setItem(STORAGE_KEYS.isLoggedIn, 'true');
      sessionStorage.setItem(STORAGE_KEYS.username, u || '');
      notifyProfileChanged();
    }

    function clearLogin() {
      sessionStorage.removeItem(STORAGE_KEYS.isLoggedIn);
      sessionStorage.removeItem(STORAGE_KEYS.username);
      sessionStorage.removeItem(STORAGE_KEYS.currentUser);
      notifyProfileChanged();
    }

    function isLoggedIn() {
      return sessionStorage.getItem(STORAGE_KEYS.isLoggedIn) === 'true';
    }

    function getUsername() {
      return sessionStorage.getItem(STORAGE_KEYS.username) || '';
    }

    function openModal() {
        openAuthModal();
    }
  
    const profileTargets = new Set();
    function notifyProfileChanged() {
        const u = getUsername();
        const logged = isLoggedIn();
        profileTargets.forEach(el => {
            if (!el) return;
            el.textContent = logged && u ? u : '登录';
        });
    }

    window.Auth = {
        init() {
          this.loadAuthUI();
          this.bindEvents();
        },
      
        loadAuthUI() {
            const container = document.getElementById("authContainer");
            if (!container) return;
            container.innerHTML = `
              <div id="authModal" class="auth-modal hidden">
                <div class="auth-box" role="dialog" aria-modal="true" aria-labelledby="authTitle">
                  <div class="auth-box-header">
                    <h2 id="authTitle">登录</h2>
                    <button type="button" class="auth-close" id="authCloseBtn" aria-label="关闭">×</button>
                  </div>
          
                  <div id="loginForm" class="auth-form">
                    <input type="email" id="loginEmail" class="auth-input" placeholder="邮箱" autocomplete="email">
                    <input type="password" id="loginPassword" class="auth-input" placeholder="密码" autocomplete="current-password">
                    <p id="loginError" class="error-msg"></p>
                    <button id="authSubmit" class="auth-box-button">登录</button>
                    <p class="switch-text">没有账号？<a href="#" id="authSwitchLink">注册</a></p>
                  </div>
          
                  <div id="registerForm" class="auth-form hidden">
                    <input type="email" id="registerEmail" class="auth-input" placeholder="邮箱" autocomplete="email">
                    <div class="username-with-title">
                        <input type="text" id="registerUsername" class="auth-input" placeholder="姓名/用户名" autocomplete="username">
                        <select id="registerTitle">
                            <option value="教授" selected>教授</option>
                            <option value="博士">博士</option>
                            <option value="先生">先生</option>
                            <option value="女士">女士</option>
                        </select>
                    </div>
                    <input type="text" id="registerWorkplace" class="auth-input" placeholder="工作单位（选填）">
                    <input type="password" id="registerPassword" class="auth-input" placeholder="密码" autocomplete="new-password">
                    <p id="registerError" class="error-msg"></p>
                    <button id="authSubmitRegister" class="auth-box-button">注册</button>
                    <p class="switch-text">已有账号？<a href="#" id="authSwitchLink">登录</a></p>
                  </div>
                </div>
              </div>
            `;
        },          
        
        bindEvents() {
            document.addEventListener("click", (e) => {
                if (e.target && e.target.id === "authSwitchLink") {
                    e.preventDefault();
                    const isLoginVisible = !document.getElementById("loginForm")?.classList.contains("hidden");
                    if (isLoginVisible) {
                        this.showRegister();
                    } else {
                        this.showLogin();
                    }
                    return;
                }
            
                if (e.target && e.target.id === "authSubmit") {
                    e.preventDefault();
                    this.login();
                    return;
                }

                if (e.target && e.target.id === "authSubmitRegister") {
                    e.preventDefault();
                    this.register();
                    return;
                }
            
                if (e.target && e.target.id === "authCloseBtn") {
                    e.preventDefault();
                    closeAuthModal();
                    return;
                }
            });
          

            document.addEventListener("mousedown", (e) => {
                const modal = document.getElementById("authModal");
                const box = document.querySelector(".auth-box");
                if (!modal || !box) return;
                if (!modal.classList.contains("hidden") && e.target === modal) {
                    closeAuthModal();
                }
            });

            document.addEventListener("keydown", (e) => {
                if (e.key === "Escape") {
                    const modal = document.getElementById("authModal");
                    if (modal && !modal.classList.contains("hidden")) {
                        closeAuthModal();
                    }
                }
            });
        },          
        
        showLogin() {
            const modal = document.getElementById("authModal");
            const login = document.getElementById("loginForm");
            const reg = document.getElementById("registerForm");
            if (!modal || !login || !reg) return;
          
            document.getElementById("authTitle").textContent = "登录";
            login.classList.remove("hidden");
            reg.classList.add("hidden");

            const err = document.getElementById("loginError");
            if (err) err.textContent = "";
          
            const emailEl = document.getElementById("loginEmail");
            if (emailEl) emailEl.value = "";
            const passEl = document.getElementById("loginPassword");
            if (passEl) passEl.value = "";
          
            openAuthModal();
        },
          
        showRegister() {
            const modal = document.getElementById("authModal");
            const login = document.getElementById("loginForm");
            const reg = document.getElementById("registerForm");
            if (!modal || !login || !reg) return;
          
            document.getElementById("authTitle").textContent = "注册";
            login.classList.add("hidden");
            reg.classList.remove("hidden");
          
            const err = document.getElementById("registerError");
            if (err) err.textContent = "";

            const emailEL = document.getElementById("registerEmail");
            if (emailEL) emailEL.value = "";
            const userEL = document.getElementById("registerUsername");
            if (userEL) userEL.value = "";
            const passEL = document.getElementById("registerPassword");
            if (passEL) passEL.value = "";
            const workEL = document.getElementById("registerWorkplace");
            if (workEL) workEL.value = "";
            const titleEL = document.getElementById("registerTitle");
            if (titleEL) titleEL.value = "教授";
          
            openAuthModal();
        },          

        async login() {
            const email = document.getElementById("loginEmail").value.trim();
            const password = document.getElementById("loginPassword").value.trim();
            const error = document.getElementById("loginError");

            error.textContent = "";

            if (!email || !password) {
                error.textContent = "请填写邮箱和密码";
                return;
            }

            try {
                const resp = await fetch(`${API_BASE}/login`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ email, password })
                });

                const data = await resp.json();

                if (!resp.ok || !data.success) {
                    error.textContent = (data && data.message) || "登录失败";
                    return;
                }

                const u = data.user || {};
                const userObj = {
                    id: u.id,
                    email: u.email,
                    username: u.username,
                    title: u.title || "教授",
                    workplace: u.workplace || "",
                    created_at: u.created_at || null,
                };

                sessionStorage.setItem("currentUser", JSON.stringify(userObj));
                sessionStorage.setItem("isLoggedIn", "true");
                sessionStorage.setItem("username", userObj.username);
                closeAuthModal();
                this.bindProfileName('#userStatus');
                pop_up("登录成功", "g");
            } catch (err) {
                console.error("登录请求出错:", err);
                error.textContent = "登录失败，请检查网络连接";
            }
        },
        
        async register() {
            const email = document.getElementById("registerEmail").value.trim();
            const username = document.getElementById("registerUsername").value.trim();
            const title = document.getElementById("registerTitle").value;
            const workplace = document.getElementById("registerWorkplace").value.trim();
            const password = document.getElementById("registerPassword").value.trim();
            const error = document.getElementById("registerError");
        
            error.textContent = "";

            if (!email || !username || !password) {
                error.textContent = "请填写所有必填字段";
                return;
            }

            try {
                const resp = await fetch(`${API_BASE}/register`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ email, username, password, title, workplace })
                });

                const data = await resp.json();

                if (!resp.ok || !data.success) {
                    error.textContent = (data && data.message) || "注册失败";
                    return;
                }

                const u = data.user || {};
                const userObj = {
                    id: u.id,
                    email: u.email,
                    username: u.username,
                    title: u.title || "教授",
                    workplace: u.workplace || "",
                    created_at: u.created_at || null,
                };

                sessionStorage.setItem("currentUser", JSON.stringify(userObj));
                sessionStorage.setItem("isLoggedIn", "true");
                sessionStorage.setItem("username", userObj.username);
                closeAuthModal();
                this.bindProfileName('#userStatus');
            } catch (err) {
                console.error("注册请求出错:", err);
                error.textContent = "注册失败，请检查网络连接";
            }
        },
        
        logout() {
            sessionStorage.removeItem("currentUser");
            sessionStorage.removeItem("isLoggedIn");
            sessionStorage.removeItem("username");
            notifyProfileChanged();
        },
        
        isLoggedIn() {
            return !!sessionStorage.getItem("currentUser");
        },
        
        getCurrentUser() {
            return JSON.parse(sessionStorage.getItem("currentUser"));
        },
        
        bindProfileName(selector) {
            const user = this.getCurrentUser();
            const span = document.querySelector(selector);
            if (span) span.textContent = user ? user.username : "登录";
        },
        
        requireLogin(callback) {
            if (this.isLoggedIn()) callback();
            else this.showLogin();
        }
    };      
})();
