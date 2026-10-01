/* ==========================================================
   主页交互逻辑
   数据源: data/posts.js  (由 tools/publish.py 自动扫描生成)
   设计要点: 使用 <script src> 而非 fetch，保证本地 file:// 双击也能打开
   ========================================================== */
(function () {
  'use strict';

  var POSTS = (window.SITE_POSTS || []).slice();

  // 分类定义：优先使用 publish.py 生成的清单，保证新增分类目录后无需改代码
  var DEFAULT_CATS = {
    semiconductor: { label: '半导体' },
    finance: { label: '财经简报' }
  };
  var CLS_MAP = { semiconductor: 'cat-semi', finance: 'cat-fin' };

  function catLabel(id) {
    var c = (window.SITE_CATS || []).filter(function (x) { return x.id === id; })[0];
    if (c) return c.label;
    return (DEFAULT_CATS[id] || { label: id }).label;
  }
  function catCls(id) { return CLS_MAP[id] || ''; }

  var state = { cat: 'all', q: '', month: '', tag: '' };

  var $ = function (s) { return document.querySelector(s); };

  /* ---------- 主题 ---------- */
  function initTheme() {
    var saved = localStorage.getItem('site-theme');
    var sysDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    applyTheme(saved || (sysDark ? 'dark' : 'light'));
    $('#themeBtn').addEventListener('click', function () {
      var cur = document.documentElement.getAttribute('data-theme');
      var next = cur === 'dark' ? 'light' : 'dark';
      applyTheme(next);
      localStorage.setItem('site-theme', next);
    });
  }
  function applyTheme(t) {
    document.documentElement.setAttribute('data-theme', t);
    var b = $('#themeBtn');
    if (b) b.textContent = t === 'dark' ? '☀' : '☾';
  }

  /* ---------- 工具 ---------- */
  function pad(n) { return n < 10 ? '0' + n : '' + n; }

  function fmtParts(dstr) {
    var p = (dstr || '').split('-');
    if (p.length < 3) return { y: '—', ym: '', day: '--' };
    return { y: p[0], ym: p[0] + '-' + p[1], day: p[2] };
  }

  function monthLabel(ym) {
    var p = ym.split('-');
    return p[0] + ' 年 ' + parseInt(p[1], 10) + ' 月';
  }

  function escapeHtml(s) {
    return String(s || '').replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  /* ---------- 统计 ---------- */
  function renderStats() {
    var semi = POSTS.filter(function (p) { return p.category === 'semiconductor'; }).length;
    var fin = POSTS.filter(function (p) { return p.category === 'finance'; }).length;
    $('#statTotal').textContent = POSTS.length;
    $('#statSemi').textContent = semi;
    $('#statFin').textContent = fin;

    if (POSTS.length) {
      var latest = POSTS.map(function (p) { return p.date; }).sort().pop();
      var t = fmtParts(latest);
      $('#statLast').textContent = parseInt(t.ym.split('-')[1], 10) + '/' + t.day;
    } else {
      $('#statLast').textContent = '—';
    }

    renderTabs();
  }

  /* ---------- 分类页签（支持自动发现新分类） ---------- */
  function renderTabs() {
    var box = $('#catTabs');
    if (!box) return;
    var list = (window.SITE_CATS && window.SITE_CATS.length)
      ? window.SITE_CATS.slice().sort(function (a, b) { return b.count - a.count; })
      : Object.keys(DEFAULT_CATS).map(function (k) { return { id: k, label: DEFAULT_CATS[k].label }; });

    var html = '<button class="tab active" data-cat="all">全部 <span class="cnt">' + POSTS.length + '</span></button>';
    list.forEach(function (c) {
      var n = POSTS.filter(function (p) { return p.category === c.id; }).length;
      html += '<button class="tab" data-cat="' + c.id + '">' + catLabel(c.id) +
              ' <span class="cnt">' + n + '</span></button>';
    });
    box.innerHTML = html;
    bindTabs();
  }

  function bindTabs() {
    document.querySelectorAll('#catTabs .tab').forEach(function (tb) {
      tb.addEventListener('click', function () {
        document.querySelectorAll('#catTabs .tab').forEach(function (x) { x.classList.remove('active'); });
        tb.classList.add('active');
        state.cat = tb.getAttribute('data-cat');
        renderList();
      });
    });
  }

  /* ---------- 过滤 ---------- */
  function filtered() {
    var q = state.q.trim().toLowerCase();
    return POSTS.filter(function (p) {
      if (state.cat !== 'all' && p.category !== state.cat) return false;
      if (state.month && fmtParts(p.date).ym !== state.month) return false;
      if (state.tag && (p.tags || []).indexOf(state.tag) === -1) return false;
      if (q) {
        var hay = (p.title + ' ' + (p.desc || '') + ' ' + (p.tags || []).join(' ') + ' ' + p.date).toLowerCase();
        if (hay.indexOf(q) === -1) return false;
      }
      return true;
    }).sort(function (a, b) {
      return a.date === b.date ? a.title.localeCompare(b.title, 'zh') : (a.date < b.date ? 1 : -1);
    });
  }

  /* ---------- 卡片 ---------- */
  function cardHtml(p) {
    var t = fmtParts(p.date);
    var tags = (p.tags || []).slice(0, 4).map(function (g) {
      return '<span class="chip tag">' + escapeHtml(g) + '</span>';
    }).join('');
    return '' +
      '<article class="card">' +
        '<div class="card-date">' +
          '<div class="card-day">' + t.day + '</div>' +
          '<div class="card-ym">' + t.ym + '</div>' +
        '</div>' +
        '<div class="card-body">' +
          '<h2 class="card-title"><a href="' + encodeURI(p.url) + '">' + escapeHtml(p.title) + '</a></h2>' +
          (p.desc ? '<p class="card-desc">' + escapeHtml(p.desc) + '</p>' : '') +
          '<div class="card-meta">' +
            '<span class="chip ' + catCls(p.category) + '">' + escapeHtml(catLabel(p.category)) + '</span>' +
            tags +
            '<span class="card-go">阅读全文 →</span>' +
          '</div>' +
        '</div>' +
      '</article>';
  }

  function renderList() {
    var list = filtered();
    var box = $('#postList');

    if (!POSTS.length) {
      box.innerHTML =
        '<div class="empty"><strong>还没有文章</strong>' +
        '把写好的 html 放进 <code>posts/finance/</code> 或 <code>posts/semiconductor/</code>，' +
        '然后双击运行 <code>发布更新.bat</code>，本页会自动出现链接。</div>';
      return;
    }
    if (!list.length) {
      box.innerHTML = '<div class="empty"><strong>没有匹配的内容</strong>试试换个关键词，或点击上方「全部」查看全部文章。</div>';
      return;
    }

    var html = '', curMonth = '';
    list.forEach(function (p) {
      var ym = fmtParts(p.date).ym;
      if (ym !== curMonth) {
        curMonth = ym;
        var cnt = list.filter(function (x) { return fmtParts(x.date).ym === ym; }).length;
        html += '<div class="month-head"><span>' + monthLabel(ym) + '</span><span>' + cnt + ' 篇</span></div>';
      }
      html += cardHtml(p);
    });
    box.innerHTML = html;
  }

  /* ---------- 侧栏 ---------- */
  function renderSide() {
    // 归档
    var byMonth = {};
    POSTS.forEach(function (p) {
      var ym = fmtParts(p.date).ym;
      byMonth[ym] = (byMonth[ym] || 0) + 1;
    });
    var months = Object.keys(byMonth).sort().reverse();
    $('#archiveList').innerHTML = months.map(function (m) {
      return '<li><a href="#" data-month="' + m + '">' +
             '<span>' + monthLabel(m) + '</span><span class="n">' + byMonth[m] + '</span></a></li>';
    }).join('') || '<li style="color:var(--text-mute);font-size:.85rem">暂无归档</li>';

    // 标签
    var tg = {};
    POSTS.forEach(function (p) { (p.tags || []).forEach(function (t) { tg[t] = (tg[t] || 0) + 1; }); });
    var names = Object.keys(tg).sort(function (a, b) { return tg[b] - tg[a]; }).slice(0, 18);
    $('#tagCloud').innerHTML = names.map(function (t) {
      return '<a class="chip tag" href="#" data-tag="' + escapeHtml(t) + '">' + escapeHtml(t) + ' · ' + tg[t] + '</a>';
    }).join('') || '<span style="color:var(--text-mute);font-size:.85rem">暂无标签</span>';
  }

  /* ---------- 筛选提示条 ---------- */
  function renderActiveFilter() {
    var box = $('#activeFilter');
    var parts = [];
    if (state.month) parts.push({ k: 'month', t: '归档：' + monthLabel(state.month) });
    if (state.tag) parts.push({ k: 'tag', t: '标签：#' + state.tag });
    if (!parts.length) { box.innerHTML = ''; return; }
    box.innerHTML = parts.map(function (p) {
      return '<button class="chip" data-clear="' + p.k + '" style="cursor:pointer">✕ ' + escapeHtml(p.t) + '</button>';
    }).join('') + '<button class="chip" data-clear="all" style="cursor:pointer">清除全部</button>';
  }

  function refresh() {
    renderList();
    renderSide();
    renderActiveFilter();
  }

  /* ---------- 事件绑定 ---------- */
  function initEvents() {
    var si = $('#searchInput');
    si.addEventListener('input', function () { state.q = si.value; renderList(); });

    $('#archiveList').addEventListener('click', function (e) {
      var a = e.target.closest('[data-month]');
      if (!a) return;
      e.preventDefault();
      var m = a.getAttribute('data-month');
      state.month = state.month === m ? '' : m;
      refresh();
    });

    $('#tagCloud').addEventListener('click', function (e) {
      var a = e.target.closest('[data-tag]');
      if (!a) return;
      e.preventDefault();
      var t = a.getAttribute('data-tag');
      state.tag = state.tag === t ? '' : t;
      refresh();
    });

    $('#activeFilter').addEventListener('click', function (e) {
      var b = e.target.closest('[data-clear]');
      if (!b) return;
      var k = b.getAttribute('data-clear');
      if (k === 'all') { state.month = ''; state.tag = ''; state.q = ''; $('#searchInput').value = ''; }
      else if (k === 'month') state.month = '';
      else if (k === 'tag') state.tag = '';
      refresh();
    });
  }

  /* ---------- 启动 ---------- */
  document.addEventListener('DOMContentLoaded', function () {
    initTheme();
    renderStats();
    initEvents();
    refresh();
    if (!window.SITE_POSTS) {
      console.warn('未加载到 data/posts.js，请运行 发布更新.bat 生成文章索引');
    }
  });
})();
