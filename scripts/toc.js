// Builds an "On This Page" sidebar nav from the h2/h3 headings inside
// .post-content, and wraps the content in a .post-layout grid so the
// nav can sit alongside it. Skipped entirely on pages with < 2 headings.

function slugify(text) {
  return text
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

document.addEventListener('DOMContentLoaded', function () {
  var postContent = document.querySelector('.post-content');
  if (!postContent) return;

  var headings = Array.prototype.slice.call(postContent.querySelectorAll('h2, h3'));
  if (headings.length < 2) return;

  headings.forEach(function (heading) {
    if (heading.id) return;
    var base = slugify(heading.textContent) || 'section';
    var id = base;
    var n = 2;
    while (document.getElementById(id)) {
      id = base + '-' + n++;
    }
    heading.id = id;
  });

  // Leave room above the target so an anchor jump lands it inside the
  // IntersectionObserver's watched band below, not flush at the very top.
  headings.forEach(function (heading) { heading.style.scrollMarginTop = '110px'; });

  var nav = document.createElement('nav');
  nav.className = 'toc-nav';
  nav.setAttribute('aria-label', 'Table of contents');

  var label = document.createElement('span');
  label.className = 'toc-label';
  label.textContent = 'On This Page';
  nav.appendChild(label);

  var list = document.createElement('ul');
  var lastH2Item = null;
  var watchedHeadings = headings;

  var pageTitle = document.querySelector('h1');
  if (pageTitle) {
    if (!pageTitle.id) pageTitle.id = 'top';
    pageTitle.style.scrollMarginTop = '110px';
    var topItem = document.createElement('li');
    var topLink = document.createElement('a');
    topLink.href = '#' + pageTitle.id;
    topLink.textContent = pageTitle.textContent;
    topLink.className = 'toc-top-link';
    topItem.appendChild(topLink);
    list.appendChild(topItem);
    watchedHeadings = [pageTitle].concat(headings);
  }

  headings.forEach(function (heading) {
    var item = document.createElement('li');
    var link = document.createElement('a');
    link.href = '#' + heading.id;
    link.textContent = heading.textContent;
    item.appendChild(link);

    if (heading.tagName === 'H2') {
      list.appendChild(item);
      lastH2Item = item;
      return;
    }

    var parentList = list;
    if (lastH2Item) {
      var subList = lastH2Item.querySelector(':scope > ul');
      if (!subList) {
        subList = document.createElement('ul');
        lastH2Item.appendChild(subList);
      }
      parentList = subList;
    }
    parentList.appendChild(item);
  });

  nav.appendChild(list);

  var layout = document.createElement('div');
  layout.className = 'post-layout';
  postContent.parentNode.insertBefore(layout, postContent);

  var main = document.createElement('div');
  main.className = 'post-main';
  main.appendChild(postContent);

  layout.appendChild(main);
  layout.appendChild(nav);

  var links = Array.prototype.slice.call(nav.querySelectorAll('a'));
  links.forEach(function (link) {
    link.addEventListener('click', function () {
      links.forEach(function (l) { l.classList.remove('active'); });
      link.classList.add('active');
    });
  });

  // Marker line matches the scroll-margin-top above. The active heading is
  // always the last one (in document order) whose top has crossed it - a
  // single deterministic pick, unlike IntersectionObserver's band approach
  // which can flag several closely-spaced headings at once and flicker
  // between them.
  var markerLine = 110;
  var ticking = false;

  function updateActiveHeading() {
    var current = watchedHeadings[0];
    for (var i = 0; i < watchedHeadings.length; i++) {
      if (watchedHeadings[i].getBoundingClientRect().top <= markerLine) {
        current = watchedHeadings[i];
      } else {
        break;
      }
    }
    var link = nav.querySelector('a[href="#' + current.id + '"]');
    if (!link) return;
    links.forEach(function (l) { l.classList.remove('active'); });
    link.classList.add('active');
  }

  window.addEventListener('scroll', function () {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(function () {
      updateActiveHeading();
      ticking = false;
    });
  }, { passive: true });

  updateActiveHeading();
});
