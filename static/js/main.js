/* ===== OmniNexus — main.js v2 (Premium) ===== */

let currentCategory = 'general';
let currentPage     = 1;
let currentArticleId = null;
let currentLang     = localStorage.getItem('omni_lang') || 'en';
let savedIds        = JSON.parse(localStorage.getItem('omni_saved') || '[]');
let heroArticle     = null;

// ======= INIT =======
document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('langSelect').value = currentLang;
  loadNews();

  // Category buttons
  document.querySelectorAll('.cat-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.cat-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentCategory = btn.dataset.cat;
      currentPage = 1;
      const titles = {
        general: 'Latest Headlines', technology: 'Technology',
        business: 'Business & Finance', science: 'Science & Research',
        health: 'Health & Wellness', sports: 'Sports', entertainment: 'Entertainment'
      };
      const el = document.getElementById('sectionTitle');
      if (el) el.textContent = titles[currentCategory] || 'Latest Headlines';
      loadNews(true);
    });
  });

  // Search
  const searchBtn = document.getElementById('searchBtn');
  const searchInput = document.getElementById('searchInput');
  if (searchBtn) searchBtn.addEventListener('click', doSearch);
  if (searchInput) {
    searchInput.addEventListener('keydown', e => { if (e.key === 'Enter') doSearch(); });
  }

  // Language — UI language only, does NOT reload news
  document.getElementById('langSelect')?.addEventListener('change', e => {
    currentLang = e.target.value;
    localStorage.setItem('omni_lang', currentLang);
    const label = e.target.options[e.target.selectedIndex].text;
    showToast('Language changed to ' + label, 'success');
  });

  // Load more
  document.getElementById('loadMoreBtn')?.addEventListener('click', () => {
    currentPage++;
    loadNews(false);
  });

  // Comment submit
  document.getElementById('submitComment')?.addEventListener('click', submitComment);
  document.getElementById('commentInput')?.addEventListener('keydown', e => {
    if (e.key === 'Enter' && e.ctrlKey) submitComment();
  });
});

// ======= NEWS LOADING =======
async function loadNews(reset = true) {
  if (reset) {
    currentPage = 1;
    showSkeletons();
    document.getElementById('heroSlot').innerHTML = '';
  }

  try {
    const resp = await fetch(`/news/?category=${currentCategory}&page=${currentPage}`);
    const data = await resp.json();

    const grid = document.getElementById('newsGrid');

    if (reset) grid.innerHTML = '';

    if (!data.articles || data.articles.length === 0) {
      if (reset) {
        grid.innerHTML = `
          <div class="empty-state">
            <div class="empty-state-icon">🔎</div>
            <div class="empty-state-title">No articles found</div>
            <div class="empty-state-sub">Try a different category or check back later.</div>
          </div>`;
        document.getElementById('heroSlot').innerHTML = '';
      }
      document.getElementById('loadMoreBtn').style.display = 'none';
      return;
    }

    // Hero card: first article on first page
    if (reset && data.articles.length > 0) {
      heroArticle = data.articles[0];
      renderHero(heroArticle);
      data.articles.slice(1).forEach((a, i) => {
        const card = createCard(a, i);
        grid.appendChild(card);
      });
    } else {
      data.articles.forEach((a, i) => {
        const card = createCard(a, i);
        grid.appendChild(card);
      });
    }

    document.getElementById('loadMoreBtn').style.display =
      data.articles.length >= 19 ? 'inline-flex' : 'none';

  } catch (err) {
    document.getElementById('newsGrid').innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">⚠️</div>
        <div class="empty-state-title">Could not load news</div>
        <div class="empty-state-sub">Please check your NewsAPI key in Railway environment variables.</div>
      </div>`;
  }
}

function showSkeletons() {
  const grid = document.getElementById('newsGrid');
  grid.innerHTML = Array(6).fill(0).map(() => `
    <div class="skeleton-card">
      <div class="skeleton skeleton-img"></div>
      <div class="skeleton-body">
        <div class="skeleton skeleton-src"></div>
        <div class="skeleton skeleton-t1"></div>
        <div class="skeleton skeleton-t2"></div>
        <div class="skeleton skeleton-d1"></div>
        <div class="skeleton skeleton-d2"></div>
        <div class="skeleton skeleton-ft"></div>
      </div>
    </div>`).join('');
}

// ======= HERO CARD =======
function renderHero(article) {
  const slot = document.getElementById('heroSlot');
  if (!slot || !article) return;
  const date = article.publishedAt
    ? new Date(article.publishedAt).toLocaleDateString(undefined, { weekday:'long', month:'long', day:'numeric', year:'numeric' })
    : '';
  const isSaved = savedIds.includes(article.id);

  const heroImg = article.urlToImage
    ? `/news/imgproxy?url=${encodeURIComponent(article.urlToImage)}`
    : null;

  slot.innerHTML = `
    <div class="hero-card" onclick="window.open('${escHtml(article.url)}','_blank')">
      ${heroImg
        ? `<img class="hero-img" src="${escHtml(heroImg)}" alt=""
             onerror="this.style.background='linear-gradient(135deg,#1a2236,#0d1424)';this.style.opacity='.5'" />`
        : `<div style="width:100%;height:100%;background:linear-gradient(135deg,#1a2236 0%,#0d1424 100%)"></div>`}
      <div class="hero-overlay"></div>
      <div class="hero-content">
        <div class="hero-badges">
          <span class="badge badge-source">${escHtml(article.source?.name || 'News')}</span>
          <span class="badge badge-breaking">Breaking</span>
        </div>
        <h2 class="hero-title">${escHtml(article.title || '')}</h2>
        ${article.description ? `<p class="hero-desc">${escHtml(article.description)}</p>` : ''}
        <div class="hero-meta">
          <span class="hero-date">📅 ${date}</span>
          <div class="hero-actions" onclick="event.stopPropagation()">
            <button class="btn btn-sm ${isSaved ? 'btn-primary' : ''}" onclick="toggleSave(event,this,'${article.id}',${JSON.stringify(article).replace(/"/g,'&quot;').replace(/'/g,"\\'")})" title="Save">
              🔖 ${isSaved ? 'Saved' : 'Save'}
            </button>
            <button class="btn btn-sm" onclick="openComments('${article.id}')">💬 Discuss</button>
            <button class="btn btn-sm btn-primary" onclick="window.open('${escHtml(article.url)}','_blank')">Read →</button>
          </div>
        </div>
      </div>
    </div>`;
}

// ======= CARD =======
function createCard(article, index = 0) {
  const card = document.createElement('div');
  card.className = 'news-card';
  card.style.animationDelay = `${0.05 + index * 0.05}s`;
  card.dataset.id = article.id;

  const isSaved = savedIds.includes(article.id);
  const pubDate = article.publishedAt
    ? new Date(article.publishedAt).toLocaleDateString(undefined, { month:'short', day:'numeric' })
    : '';
  const source = article.source?.name || '';

  const imgSrc = article.urlToImage
    ? `/news/imgproxy?url=${encodeURIComponent(article.urlToImage)}`
    : null;

  card.innerHTML = `
    <div class="card-img-wrap">
      ${imgSrc
        ? `<img class="card-img" src="${escHtml(imgSrc)}" alt="" loading="lazy"
             onerror="this.closest('.card-img-wrap').innerHTML='<div class=\\'card-img-placeholder\\'>📰<div class=\\'card-img-src\\'>${escHtml(source)}</div></div>'" />`
        : `<div class="card-img-placeholder">📰<div class="card-img-src">${escHtml(source)}</div></div>`}
      ${imgSrc ? `<div class="card-img-overlay"></div><div class="card-img-src">${escHtml(source)}</div>` : ''}
    </div>
    <div class="card-body">
      <a class="card-title" href="${escHtml(article.url)}" target="_blank" rel="noopener"
         onclick="event.stopPropagation()">${escHtml(article.title || '')}</a>
      ${article.description
        ? `<p class="card-desc" data-orig="${escAttr(article.description)}">${escHtml(article.description)}</p>
           <div class="card-translate">
             <button class="translate-btn" onclick="translateDesc(this,'${escAttr(article.description)}')">🌐 Translate</button>
           </div>` : ''}
      <div class="card-footer">
        <span class="card-date">${pubDate}</span>
        <div class="card-actions">
          <button class="icon-btn ${isSaved ? 'saved' : ''}" title="${isSaved ? 'Saved' : 'Save article'}"
            onclick="toggleSave(event,this,'${article.id}',${JSON.stringify(article).replace(/"/g,'&quot;').replace(/'/g,"\\'")})">
            🔖
          </button>
          <button class="icon-btn" title="Comments" onclick="openComments('${article.id}')">
            💬 Discuss
          </button>
          <a class="icon-btn" href="${escHtml(article.url)}" target="_blank" rel="noopener" title="Open article">↗</a>
        </div>
      </div>
    </div>`;
  return card;
}

// ======= SEARCH =======
async function doSearch() {
  const q = document.getElementById('searchInput')?.value.trim();
  if (!q) return;
  document.getElementById('heroSlot').innerHTML = '';
  const titleEl = document.getElementById('sectionTitle');
  if (titleEl) titleEl.textContent = `Results for "${q}"`;
  showSkeletons();
  document.getElementById('loadMoreBtn').style.display = 'none';

  try {
    const resp = await fetch(`/news/search?q=${encodeURIComponent(q)}`);
    const data = await resp.json();
    const grid = document.getElementById('newsGrid');
    grid.innerHTML = '';
    if (!data.articles?.length) {
      grid.innerHTML = `<div class="empty-state"><div class="empty-state-icon">🔎</div>
        <div class="empty-state-title">No results for "${escHtml(q)}"</div></div>`;
      return;
    }
    data.articles.forEach((a, i) => grid.appendChild(createCard(a, i)));
  } catch {
    showToast('Search failed', 'error');
  }
}

// ======= TRANSLATE =======
async function translateDesc(btn, text) {
  if (!text) return;
  const orig = btn.textContent;
  btn.textContent = '⏳';
  btn.disabled = true;
  try {
    const resp = await fetch('/translate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, target: currentLang })
    });
    const data = await resp.json();
    const descEl = btn.closest('.card-body')?.querySelector('.card-desc');
    if (descEl && data.translated) {
      descEl.textContent = data.translated;
      btn.textContent = '↩ Original';
      btn.disabled = false;
      btn.onclick = () => {
        descEl.textContent = text;
        btn.textContent = '🌐 Translate';
        btn.onclick = () => translateDesc(btn, text);
      };
      return;
    }
  } catch {}
  btn.textContent = orig;
  btn.disabled = false;
  showToast('Translation unavailable', 'error');
}

// ======= SAVE =======
async function toggleSave(event, btn, articleId, article) {
  event.preventDefault(); event.stopPropagation();
  try {
    const parsed = typeof article === 'string' ? JSON.parse(article) : article;
    const resp = await fetch('/news/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        article_id: articleId,
        title: parsed.title, url: parsed.url,
        image: parsed.urlToImage, source: parsed.source?.name
      })
    });
    if (resp.status === 401) { openModal('loginModal'); return; }
    const data = await resp.json();
    if (data.saved) {
      btn.classList.add('saved');
      if (!savedIds.includes(articleId)) savedIds.push(articleId);
      showToast('Article saved!', 'success');
    } else {
      btn.classList.remove('saved');
      savedIds = savedIds.filter(id => id !== articleId);
      showToast('Removed from saved');
    }
    localStorage.setItem('omni_saved', JSON.stringify(savedIds));
  } catch { showToast('Failed to save', 'error'); }
}

// ======= COMMENTS =======
function openComments(articleId) {
  currentArticleId = articleId;
  const panel = document.getElementById('commentsPanel');
  panel.classList.remove('hidden');
  const iw = document.getElementById('commentInputWrap');
  if (iw) iw.style.display = 'flex';
  loadComments(articleId);
}
function closeComments() {
  document.getElementById('commentsPanel').classList.add('hidden');
  currentArticleId = null;
}
async function loadComments(articleId) {
  const body = document.getElementById('commentsBody');
  body.innerHTML = '<div style="text-align:center;padding:32px;color:var(--text3)">Loading...</div>';
  try {
    const resp = await fetch(`/comments/${articleId}`);
    const data = await resp.json();
    body.innerHTML = '';
    if (!data.comments?.length) {
      body.innerHTML = '<div style="text-align:center;padding:32px;color:var(--text3)">No comments yet.<br>Be the first to share your thoughts!</div>';
      return;
    }
    data.comments.forEach(c => body.appendChild(createCommentEl(c)));
  } catch {
    body.innerHTML = '<div style="text-align:center;padding:32px;color:var(--red)">Failed to load comments.</div>';
  }
}
function createCommentEl(c) {
  const el = document.createElement('div');
  el.className = 'comment-item';
  el.innerHTML = `
    <div class="comment-author">👤 ${escHtml(c.author)}</div>
    <div class="comment-content">${escHtml(c.content)}</div>
    <div class="comment-footer">
      <span class="comment-date">${new Date(c.created_at).toLocaleDateString()}</span>
      <button class="like-btn ${c.liked?'liked':''}" onclick="likeComment(this,${c.id})">❤ ${c.like_count}</button>
      <button class="icon-btn" style="font-size:11px" onclick="replyTo(${c.id})">↩ Reply</button>
    </div>
    ${c.replies?.length ? `<div class="replies">${c.replies.map(r=>`
      <div class="comment-item">
        <div class="comment-author">👤 ${escHtml(r.author)}</div>
        <div class="comment-content">${escHtml(r.content)}</div>
        <div class="comment-date" style="font-size:11px;color:var(--text3)">${new Date(r.created_at).toLocaleDateString()}</div>
      </div>`).join('')}</div>` : ''}`;
  return el;
}
async function submitComment() {
  const input = document.getElementById('commentInput');
  const content = input?.value.trim();
  if (!content || !currentArticleId) return;
  try {
    const resp = await fetch('/comments/add', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ article_id: currentArticleId, content })
    });
    if (resp.status === 401) { openModal('loginModal'); return; }
    const data = await resp.json();
    if (data.success) {
      input.value = '';
      loadComments(currentArticleId);
      showToast('Comment posted!', 'success');
    }
  } catch { showToast('Failed to post comment', 'error'); }
}
async function likeComment(btn, commentId) {
  try {
    const resp = await fetch(`/comments/like/${commentId}`, { method: 'POST' });
    if (resp.status === 401) { openModal('loginModal'); return; }
    const data = await resp.json();
    btn.className = `like-btn ${data.liked?'liked':''}`;
    btn.textContent = `❤ ${data.like_count}`;
  } catch {}
}
let replyParentId = null;
function replyTo(parentId) {
  replyParentId = parentId;
  const input = document.getElementById('commentInput');
  if (input) { input.placeholder = `Replying to #${parentId}...`; input.focus(); }
}

// ======= AUTH =======
async function doLogin() {
  const email    = document.getElementById('loginEmail')?.value;
  const password = document.getElementById('loginPassword')?.value;
  const errEl    = document.getElementById('loginError');
  errEl?.classList.add('hidden');
  try {
    const resp = await fetch('/auth/login', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    const data = await resp.json();
    if (data.success) {
      showToast(`Welcome back, ${data.username}! 👋`, 'success');
      setTimeout(() => location.reload(), 900);
    } else {
      if (errEl) { errEl.textContent = data.error || 'Login failed'; errEl.classList.remove('hidden'); }
    }
  } catch {
    if (errEl) { errEl.textContent = 'Network error. Please try again.'; errEl.classList.remove('hidden'); }
  }
}
async function doRegister() {
  const username = document.getElementById('regUsername')?.value;
  const email    = document.getElementById('regEmail')?.value;
  const password = document.getElementById('regPassword')?.value;
  const errEl    = document.getElementById('registerError');
  errEl?.classList.add('hidden');
  try {
    const resp = await fetch('/auth/register', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, email, password })
    });
    const data = await resp.json();
    if (data.success) {
      showToast(`Welcome to OmniNexus, ${data.username}! 🎉`, 'success');
      setTimeout(() => location.reload(), 900);
    } else {
      if (errEl) { errEl.textContent = data.error || 'Registration failed'; errEl.classList.remove('hidden'); }
    }
  } catch {
    if (errEl) { errEl.textContent = 'Network error. Please try again.'; errEl.classList.remove('hidden'); }
  }
}

// ======= MODALS =======
function openModal(id) {
  const overlay = document.getElementById('modal-overlay');
  if (overlay) { overlay.style.display = 'flex'; switchTab(id); return; }
  document.getElementById(id)?.classList.remove('hidden');
}
function closeModal(id) {
  const overlay = document.getElementById('modal-overlay');
  if (overlay) { overlay.style.display = 'none'; return; }
  if (id) document.getElementById(id)?.classList.add('hidden');
}
function switchModal(from, to) { closeModal(from); openModal(to); }
function switchTab(tab) {
  const lf = document.getElementById('form-login');
  const rf = document.getElementById('form-register');
  const tl = document.getElementById('tab-login');
  const tr = document.getElementById('tab-register');
  if (lf) lf.style.display = tab === 'login'    ? '' : 'none';
  if (rf) rf.style.display = tab === 'register' ? '' : 'none';
  if (tl) tl.classList.toggle('active', tab === 'login');
  if (tr) tr.classList.toggle('active', tab === 'register');
}
async function submitAuth(event, type) {
  event.preventDefault();
  const form  = document.getElementById('form-' + type);
  const data  = Object.fromEntries(new FormData(form));
  const errEl = document.getElementById(type + '-error');
  if (errEl) errEl.textContent = '';
  try {
    const resp = await fetch('/auth/' + type, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    const result = await resp.json();
    if (result.success) {
      showToast(type === 'login' ? 'Welcome back, ' + result.username + '!' : 'Welcome to OmniNexus, ' + result.username + '!', 'success');
      closeModal();
      setTimeout(() => location.reload(), 900);
    } else {
      if (errEl) errEl.textContent = result.error || (type === 'login' ? 'Login failed' : 'Registration failed');
    }
  } catch {
    if (errEl) errEl.textContent = 'Network error. Please try again.';
  }
}
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') {
    ['loginModal','registerModal'].forEach(id => document.getElementById(id)?.classList.add('hidden'));
    closeComments();
  }
});

// ======= TOAST =======
let toastTimer;
function showToast(msg, type = '') {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.className = `toast${type ? ' ' + type : ''}`;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.classList.add('hidden'), 3200);
}

// ======= UTILS =======
function escHtml(s) {
  return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
function escAttr(s) {
  return String(s||'').replace(/"/g,'&quot;').replace(/'/g,'&#39;');
}
