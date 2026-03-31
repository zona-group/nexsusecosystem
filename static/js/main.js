// State
let currentCat = 'all';
let currentPage = 1;
let currentLang = 'en';
let currentArticle = null;
let deferredPrompt = null;
let isLoggedIn = false;
let currentUsername = '';

// Init
document.addEventListener('DOMContentLoaded', async () => {
  await checkAuth();
  loadNews('all');
  loadTrending();
  initPWA();
});

// AUTH CHECK
async function checkAuth() {
  try {
    const r = await fetch('/auth/me');
    const d = await r.json();
    isLoggedIn = d.logged_in;
    if (isLoggedIn) currentUsername = d.username;
  } catch {}
}

// NEWS
async function loadNews(cat, btnEl) {
  currentCat = cat;
  currentPage = 1;
  if (btnEl) {
    document.querySelectorAll('.cat').forEach(c => c.classList.remove('active'));
    btnEl.classList.add('active');
  }
  const grid = document.getElementById('news-grid');
  grid.innerHTML = '<div class="loading-state"><div class="spinner"></div><span>Loading news...</span></div>';
  document.getElementById('load-more').style.display = 'none';

  const endpoint = cat === 'all' ? '/news/api/news/all' : `/news/api/news?cat=${cat}&lang=${currentLang}`;
  try {
    const r = await fetch(endpoint);
    const d = await r.json();
    renderNews(d.articles, false);
    if (d.articles && d.articles.length >= 12) {
      document.getElementById('load-more').style.display = 'inline-block';
    }
  } catch {
    grid.innerHTML = '<div class="loading-state">Failed to load news. Please refresh.</div>';
  }
}

function loadCat(cat, el) {
  loadNews(cat, el);
}

async function loadMore() {
  currentPage++;
  const endpoint = `/news/api/news?cat=${currentCat}&lang=${currentLang}&page=${currentPage}`;
  try {
    const r = await fetch(endpoint);
    const d = await r.json();
    renderNews(d.articles, true);
    if (!d.articles || d.articles.length < 12) {
      document.getElementById('load-more').style.display = 'none';
    }
  } catch {}
}

function renderNews(articles, append) {
  const grid = document.getElementById('news-grid');
  if (!append) grid.innerHTML = '';
  if (!articles || articles.length === 0) {
    if (!append) grid.innerHTML = '<div class="loading-state">No articles found.</div>';
    return;
  }
  articles.forEach((a, i) => {
    const card = document.createElement('div');
    card.className = 'news-card' + (i === 0 && !append ? ' featured' : '');
    card.onclick = () => openArticle(a);
    const badgeClass = 'badge-' + (a.category || 'tech');
    const timeAgo = formatTime(a.published);
    card.innerHTML = `
      ${a.image ? `<img class="news-image" src="${a.image}" alt="" onerror="this.style.display='none'">` : ''}
      <span class="badge ${badgeClass}">${a.category || 'tech'}</span>
      <h3>${escHtml(a.title)}</h3>
      <p>${escHtml(a.description || '')}</p>
      <div class="news-meta">
        <span>${escHtml(a.source || '')}</span>
        <span>·</span>
        <span>${timeAgo}</span>
      </div>`;
    grid.appendChild(card);
  });
}

async function loadTrending() {
  try {
    const r = await fetch('/news/api/news/all');
    const d = await r.json();
    const list = document.getElementById('trending-list');
    list.innerHTML = '';
    (d.articles || []).slice(0, 5).forEach((a, i) => {
      const item = document.createElement('div');
      item.className = 'trending-item';
      item.onclick = () => openArticle(a);
      item.innerHTML = `
        <span class="trend-num">0${i+1}</span>
        <div><div class="trend-text">${escHtml(a.title)}</div>
        <span class="badge badge-${a.category || 'tech'}" style="margin-top:4px;display:inline-block">${a.category||'tech'}</span></div>`;
      list.appendChild(item);
    });
  } catch {}
}

// ARTICLE MODAL
function openArticle(article) {
  currentArticle = article;
  const overlay = document.getElementById('article-overlay');
  const content = document.getElementById('article-content');
  content.innerHTML = `
    ${article.image ? `<img style="width:100%;height:200px;object-fit:cover;border-radius:4px;margin-bottom:16px" src="${article.image}" onerror="this.style.display='none'">` : ''}
    <span class="badge badge-${article.category || 'tech'}">${article.category || 'tech'}</span>
    <h2 style="margin-top:8px">${escHtml(article.title)}</h2>
    <div class="article-meta">${article.source || ''} · ${formatTime(article.published)}</div>
    <p>${escHtml(article.description || 'No description available.')}</p>
    ${article.url && article.url !== '#' ? `<a href="${article.url}" target="_blank" class="article-link">Read Full Article →</a>` : ''}
  `;
  loadComments(article.id);
  overlay.classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closeArticle() {
  document.getElementById('article-overlay').classList.remove('open');
  document.body.style.overflow = '';
}

// COMMENTS
async function loadComments(articleId) {
  const list = document.getElementById('comments-list');
  const formWrap = document.getElementById('comment-form-wrap');
  list.innerHTML = '<div style="padding:12px 0;font-size:12px;color:var(--text3)">Loading comments...</div>';

  try {
    const r = await fetch(`/comments/api/comments/${articleId}`);
    const d = await r.json();
    list.innerHTML = '';

    if (!d.comments || d.comments.length === 0) {
      list.innerHTML = '<div style="padding:12px 0;font-size:12px;color:var(--text3)">No comments yet. Be the first!</div>';
    } else {
      d.comments.forEach(c => {
        list.appendChild(buildCommentEl(c, articleId));
      });
    }

    if (isLoggedIn) {
      formWrap.innerHTML = `
        <div class="comment-form">
          <textarea id="comment-input" placeholder="Write a comment..."></textarea>
          <button class="comment-submit" onclick="postComment('${articleId}')">Post Comment</button>
        </div>`;
    } else {
      formWrap.innerHTML = `<div class="login-prompt">
        <a onclick="openModal('login')">Login</a> or <a onclick="openModal('register')">register</a> to comment.
      </div>`;
    }
  } catch {
    list.innerHTML = '<div style="font-size:12px;color:#ff6655;padding:12px 0">Failed to load comments.</div>';
  }
}

function buildCommentEl(c, articleId) {
  const div = document.createElement('div');
  div.className = 'comment-item';
  div.id = `comment-${c.id}`;
  const initial = (c.author || 'U')[0].toUpperCase();
  div.innerHTML = `
    <div class="comment-header">
      <div class="comment-avatar">${initial}</div>
      <span class="comment-username">${escHtml(c.author)}</span>
      <span class="comment-date">${c.created}</span>
    </div>
    <div class="comment-text">${escHtml(c.content)}</div>
    <div class="comment-actions">
      <button class="comment-action ${c.liked ? 'liked' : ''}" id="like-btn-${c.id}" onclick="likeComment(${c.id})">
        ♥ <span id="like-count-${c.id}">${c.likes}</span>
      </button>
      ${isLoggedIn ? `<button class="comment-action" onclick="showReplyForm(${c.id},'${articleId}')">Reply</button>` : ''}
    </div>
    <div id="reply-form-${c.id}"></div>
    <div id="replies-${c.id}" style="margin-left:28px">
      ${(c.replies || []).map(r => `
        <div class="comment-item" style="border-bottom:none;padding:8px 0">
          <div class="comment-header">
            <div class="comment-avatar" style="width:22px;height:22px;font-size:10px">${(r.author||'U')[0].toUpperCase()}</div>
            <span class="comment-username">${escHtml(r.author)}</span>
            <span class="comment-date">${r.created}</span>
          </div>
          <div class="comment-text">${escHtml(r.content)}</div>
        </div>`).join('')}
    </div>`;
  return div;
}

async function postComment(articleId) {
  const input = document.getElementById('comment-input');
  const content = input.value.trim();
  if (!content) return;
  try {
    const r = await fetch(`/comments/api/comments/${articleId}`, {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({content})
    });
    if (r.ok) {
      input.value = '';
      loadComments(articleId);
      showToast('Comment posted!');
    }
  } catch {}
}

function showReplyForm(commentId, articleId) {
  const wrap = document.getElementById(`reply-form-${commentId}`);
  if (wrap.innerHTML) { wrap.innerHTML = ''; return; }
  wrap.innerHTML = `
    <div class="comment-form" style="margin-left:28px;margin-top:8px">
      <textarea id="reply-input-${commentId}" placeholder="Write a reply..." style="min-height:60px"></textarea>
      <button class="comment-submit" style="font-size:11px;padding:6px 14px" onclick="postReply(${commentId},'${articleId}')">Reply</button>
    </div>`;
}

async function postReply(parentId, articleId) {
  const input = document.getElementById(`reply-input-${parentId}`);
  const content = input.value.trim();
  if (!content) return;
  try {
    const r = await fetch(`/comments/api/comments/${articleId}`, {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({content, parent_id: parentId})
    });
    if (r.ok) { loadComments(articleId); showToast('Reply posted!'); }
  } catch {}
}

async function likeComment(commentId) {
  if (!isLoggedIn) { openModal('login'); return; }
  try {
    const r = await fetch(`/comments/api/comments/${commentId}/like`, {method:'POST'});
    const d = await r.json();
    const btn = document.getElementById(`like-btn-${commentId}`);
    const count = document.getElementById(`like-count-${commentId}`);
    if (btn) btn.className = `comment-action ${d.liked ? 'liked' : ''}`;
    if (count) count.textContent = d.likes;
  } catch {}
}

// AUTH MODAL
function openModal(mode) {
  document.getElementById('modal-overlay').classList.add('open');
  switchTab(mode);
  document.body.style.overflow = 'hidden';
}

function closeModal() {
  document.getElementById('modal-overlay').classList.remove('open');
  document.body.style.overflow = '';
}

function switchTab(tab) {
  document.getElementById('form-login').style.display = tab === 'login' ? 'block' : 'none';
  document.getElementById('form-register').style.display = tab === 'register' ? 'block' : 'none';
  document.getElementById('tab-login').classList.toggle('active', tab === 'login');
  document.getElementById('tab-register').classList.toggle('active', tab === 'register');
}

async function submitAuth(e, type) {
  e.preventDefault();
  const form = e.target;
  const data = {};
  new FormData(form).forEach((v, k) => data[k] = v);
  const errEl = document.getElementById(`${type}-error`);
  errEl.textContent = '';

  try {
    const r = await fetch(`/auth/${type}`, {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify(data)
    });
    const d = await r.json();
    if (d.success) {
      closeModal();
      showToast(`Welcome, ${d.username}!`);
      setTimeout(() => location.reload(), 800);
    } else {
      errEl.textContent = d.error || 'Something went wrong.';
    }
  } catch {
    errEl.textContent = 'Network error. Please try again.';
  }
}

function toggleUserMenu() {
  document.getElementById('user-dropdown').classList.toggle('open');
}

// TRANSLATION
async function setLang(lang) {
  currentLang = lang;
  if (lang === 'en') { loadNews(currentCat); return; }
  const headlines = document.querySelectorAll('.news-card h3');
  for (const el of headlines) {
    const original = el.dataset.original || el.textContent;
    el.dataset.original = original;
    try {
      const r = await fetch('/api/translate', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({text: original, target: lang})
      });
      const d = await r.json();
      if (d.translated) el.textContent = d.translated;
    } catch {}
  }
}

// PWA
function initPWA() {
  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    document.getElementById('pwa-btn').style.display = 'block';
    setTimeout(() => { document.getElementById('pwa-banner').style.display = 'flex'; }, 3000);
  });
  window.addEventListener('appinstalled', () => {
    document.getElementById('pwa-banner').style.display = 'none';
    showToast('OmniNexus installed!');
  });
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/static/sw.js').catch(() => {});
  }
}

function installPWA() {
  if (deferredPrompt) {
    deferredPrompt.prompt();
    deferredPrompt.userChoice.then(r => {
      if (r.outcome === 'accepted') showToast('Installing OmniNexus...');
      deferredPrompt = null;
    });
  } else {
    showToast('Open in browser and tap "Add to Home Screen"');
  }
}

// UTILS
function toggleMenu() {
  document.getElementById('nav-links').classList.toggle('open');
}

function showToast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.style.display = 'block';
  setTimeout(() => { t.style.display = 'none'; }, 3000);
}

function escHtml(str) {
  if (!str) return '';
  return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function formatTime(iso) {
  if (!iso) return '';
  const diff = (Date.now() - new Date(iso)) / 1000;
  if (diff < 3600) return Math.floor(diff/60) + 'm ago';
  if (diff < 86400) return Math.floor(diff/3600) + 'h ago';
  return Math.floor(diff/86400) + 'd ago';
}
