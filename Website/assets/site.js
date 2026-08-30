(function () {
  'use strict';

  var root = document.documentElement;
  var themeButton = document.getElementById('theme-toggle');
  var media = window.matchMedia ? window.matchMedia('(prefers-color-scheme: dark)') : null;
  var storageKey = 'sabaaccessory-theme';

  function currentTheme() {
    var explicit = root.getAttribute('data-theme');
    if (explicit === 'light' || explicit === 'dark') return explicit;
    return media && media.matches ? 'dark' : 'light';
  }

  function syncTheme() {
    if (!themeButton) return;
    var theme = currentTheme();
    var dark = theme === 'dark';
    themeButton.setAttribute('aria-pressed', dark ? 'true' : 'false');
    themeButton.setAttribute('title', dark ? 'ライトテーマに切り替える' : 'ダークテーマに切り替える');

    var themeColors = document.querySelectorAll('meta[name="theme-color"]');
    for (var index = 0; index < themeColors.length; index += 1) {
      var color = dark ? '#0d1118' : '#f3f5f9';
      var explicit = root.getAttribute('data-theme') === theme;
      themeColors[index].setAttribute('content', explicit ? color : themeColors[index].getAttribute('data-color'));
    }
  }

  if (themeButton) {
    themeButton.addEventListener('click', function () {
      var next = currentTheme() === 'dark' ? 'light' : 'dark';
      root.setAttribute('data-theme', next);
      try { localStorage.setItem(storageKey, next); } catch (error) {}
      syncTheme();
    });
    themeButton.hidden = false;
    syncTheme();
  }

  if (media && media.addEventListener) media.addEventListener('change', syncTheme);

  var repositoryUrl = new URL('index.json', window.location.href).href;
  var repositoryNode = document.getElementById('repository-url');
  var addButton = document.getElementById('add-repository');
  var copyButton = document.getElementById('copy-button');
  var copyStatus = document.getElementById('copy-status');
  var packageList = document.getElementById('package-list');

  if (repositoryNode) repositoryNode.textContent = repositoryUrl;
  if (addButton) addButton.href = 'vcc://vpm/addRepo?url=' + encodeURIComponent(repositoryUrl);

  function copyText(value) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      return navigator.clipboard.writeText(value);
    }

    return new Promise(function (resolve, reject) {
      var input = document.createElement('textarea');
      input.value = value;
      input.setAttribute('readonly', '');
      input.style.position = 'fixed';
      input.style.opacity = '0';
      document.body.appendChild(input);
      input.select();
      try {
        if (!document.execCommand('copy')) throw new Error('copy command failed');
        resolve();
      } catch (error) {
        reject(error);
      } finally {
        input.remove();
      }
    });
  }

  if (copyButton) {
    copyButton.addEventListener('click', function () {
      copyText(repositoryUrl).then(function () {
        copyButton.textContent = 'コピー済み';
        if (copyStatus) copyStatus.textContent = 'Repository URL をコピーしました。';
        window.setTimeout(function () {
          copyButton.textContent = 'コピー';
          if (copyStatus) copyStatus.textContent = '';
        }, 1800);
      }).catch(function () {
        if (copyStatus) copyStatus.textContent = 'コピーできませんでした。URL を選択してコピーしてください。';
      });
    });
  }

  function element(tag, className, value) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (value != null) node.textContent = value;
    return node;
  }

  function parseSemver(value) {
    var match = /^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$/.exec(value);
    if (!match) return null;
    return {
      core: [Number(match[1]), Number(match[2]), Number(match[3])],
      prerelease: match[4] ? match[4].split('.') : []
    };
  }

  function compareSemver(left, right) {
    var leftVersion = parseSemver(left);
    var rightVersion = parseSemver(right);
    if (!leftVersion || !rightVersion) return left.localeCompare(right);

    for (var coreIndex = 0; coreIndex < 3; coreIndex += 1) {
      if (leftVersion.core[coreIndex] !== rightVersion.core[coreIndex]) {
        return leftVersion.core[coreIndex] - rightVersion.core[coreIndex];
      }
    }

    var leftPrerelease = leftVersion.prerelease;
    var rightPrerelease = rightVersion.prerelease;
    if (!leftPrerelease.length || !rightPrerelease.length) {
      if (leftPrerelease.length === rightPrerelease.length) return 0;
      return leftPrerelease.length ? -1 : 1;
    }

    var length = Math.max(leftPrerelease.length, rightPrerelease.length);
    for (var index = 0; index < length; index += 1) {
      if (index >= leftPrerelease.length) return -1;
      if (index >= rightPrerelease.length) return 1;
      var leftIdentifier = leftPrerelease[index];
      var rightIdentifier = rightPrerelease[index];
      if (leftIdentifier === rightIdentifier) continue;
      var leftNumeric = /^\d+$/.test(leftIdentifier);
      var rightNumeric = /^\d+$/.test(rightIdentifier);
      if (leftNumeric && rightNumeric) return Number(leftIdentifier) - Number(rightIdentifier);
      if (leftNumeric !== rightNumeric) return leftNumeric ? -1 : 1;
      return leftIdentifier < rightIdentifier ? -1 : 1;
    }
    return 0;
  }

  function latestManifest(entry) {
    var versions = entry && entry.versions ? entry.versions : {};
    var names = Object.keys(versions);
    if (!names.length) return null;
    var latest = names[0];
    for (var index = 1; index < names.length; index += 1) {
      if (compareSemver(names[index], latest) > 0) latest = names[index];
    }
    return versions[latest];
  }

  function appendTags(card, manifest) {
    var values = ['PC Avatar'];
    if (manifest.unity) values.push('Unity ' + manifest.unity);
    var keywords = Array.isArray(manifest.keywords) ? manifest.keywords.slice(0, 3) : [];
    values = values.concat(keywords);

    var tags = element('ul', 'package-tags');
    for (var index = 0; index < values.length; index += 1) {
      tags.appendChild(element('li', null, values[index]));
    }
    card.appendChild(tags);
  }

  function renderPackages(listing) {
    if (!packageList) return;
    packageList.textContent = '';
    var packages = listing && listing.packages ? listing.packages : {};
    var ids = Object.keys(packages);

    if (!ids.length) {
      packageList.appendChild(element('article', 'package-card', '公開済みパッケージはありません。'));
      return;
    }

    for (var index = 0; index < ids.length; index += 1) {
      var id = ids[index];
      var manifest = latestManifest(packages[id]);
      if (!manifest) continue;

      var card = element('article', 'package-card');
      var header = element('div', 'package-card-header');
      var titleGroup = element('div');
      titleGroup.appendChild(element('h3', null, manifest.displayName || id));
      titleGroup.appendChild(element('span', 'package-id', id));
      header.appendChild(titleGroup);
      header.appendChild(element('span', 'package-version', 'v' + (manifest.version || 'unknown')));
      card.appendChild(header);
      card.appendChild(element('p', 'package-description', manifest.description || '説明はありません。'));
      appendTags(card, manifest);

      var links = element('div', 'package-links');
      var guide = element('a', null, '使用ガイドを開く');
      guide.href = 'docs/' + encodeURIComponent(id) + '/index.html';
      links.appendChild(guide);
      var changelog = element('a', null, '変更履歴');
      changelog.href = 'docs/' + encodeURIComponent(id) + '/changelog.html';
      links.appendChild(changelog);
      card.appendChild(links);
      packageList.appendChild(card);
    }
  }

  if (packageList) {
    fetch('index.json', { cache: 'no-cache' })
      .then(function (response) {
        if (!response.ok) throw new Error(response.status + ' ' + response.statusText);
        return response.json();
      })
      .then(function (listing) {
        var configuredUrl = listing && listing.url ? listing.url : repositoryUrl;
        repositoryUrl = configuredUrl;
        if (repositoryNode) repositoryNode.textContent = configuredUrl;
        if (addButton) addButton.href = 'vcc://vpm/addRepo?url=' + encodeURIComponent(configuredUrl);
        renderPackages(listing);
      })
      .catch(function () {
        packageList.textContent = '';
        var card = element('article', 'package-card package-error');
        card.appendChild(element('p', null, 'パッケージ情報を読み込めませんでした。'));
        var link = element('a', null, 'GitHub でパッケージを確認');
        link.href = 'https://github.com/sabas0ba/vrc_sabaaccessory/tree/main/Packages';
        card.appendChild(link);
        packageList.appendChild(card);
      });
  }
})();
