// === LOADER ===
const LOADER_HIDE_DELAY_MS = 300;

window.addEventListener('load', () => {
  setTimeout(() => {
    const loader = document.getElementById('loader');
    if (loader) { loader.classList.add('hidden'); }
  }, LOADER_HIDE_DELAY_MS);
});

// === DARK MODE ===
const darkToggle = document.getElementById('darkToggle');
const body = document.body;

function readStorage(key) {
  try {
    return localStorage.getItem(key);
  } catch (error) {
    return null;
  }
}

function writeStorage(key, value) {
  try {
    localStorage.setItem(key, value);
  } catch (error) {
    // Storage can fail in private or locked-down browsers.
  }
}

function applyTheme(dark) {
  body.classList.toggle('dark', dark);
  writeStorage('velora-dark', dark ? '1' : '0');
  if (darkToggle) {
    darkToggle.innerHTML = dark
      ? '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>'
      : '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';
  }
}

const savedDark = readStorage('velora-dark') === '1';
applyTheme(savedDark);

if (darkToggle) {
  darkToggle.addEventListener('click', () => {
    applyTheme(!body.classList.contains('dark'));
  });
}

// === MOBILE NAV ===
const hamburger = document.getElementById('hamburger');
const mobileNav = document.getElementById('mobileNav');
const mobileClose = document.getElementById('mobileClose');

if (hamburger && mobileNav) {
  hamburger.addEventListener('click', () => {
    mobileNav.classList.add('open');
    hamburger.setAttribute('aria-expanded', 'true');
  });
}
if (mobileClose && mobileNav) {
  mobileClose.addEventListener('click', closeMobileNav);
}
function closeMobileNav() {
  if (mobileNav) mobileNav.classList.remove('open');
  if (hamburger) hamburger.setAttribute('aria-expanded', 'false');
}
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') closeMobileNav();
});

// === SCROLL REVEAL ===
const revealEls = document.querySelectorAll('.reveal, .reveal-scale');
if ('IntersectionObserver' in window) {
  const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.classList.add('visible');
        revealObserver.unobserve(e.target);
      }
    });
  }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });

  revealEls.forEach(el => revealObserver.observe(el));
} else {
  revealEls.forEach(el => el.classList.add('visible'));
}

// === NAVBAR SCROLL EFFECT ===
const navbar = document.querySelector('.navbar');
window.addEventListener('scroll', () => {
  const y = window.scrollY;
  if (navbar) {
    if (y > 60) {
      navbar.style.boxShadow = '0 1px 0 rgba(0,0,0,.12)';
    } else {
      navbar.style.boxShadow = 'none';
    }
  }
}, { passive: true });

// === CONTACT FORM ===
const contactForm = document.getElementById('contactForm');
if (contactForm) {
  const serviceSelect = document.getElementById('service');
  const budgetSelect = document.getElementById('budget');
  const domainSelect = document.getElementById('internshipDomain');
  const companyInput = document.getElementById('company');
  const messageTextarea = document.getElementById('message');

  const handleServiceChange = () => {
    if (!serviceSelect) return;
    const val = serviceSelect.value;
    if (val === 'internship') {
      if (budgetSelect) {
        budgetSelect.style.display = 'none';
        budgetSelect.value = '';
      }
      if (domainSelect) {
        domainSelect.style.display = '';
      }
      if (companyInput) {
        companyInput.placeholder = 'College / University / Organization';
      }
      if (messageTextarea) {
        messageTextarea.placeholder = 'Tell us about your background, skills, and what domain you are interested in (e.g., Frontend, AI/ML, SaaS) — why would you like to intern with us?';
      }
    } else {
      if (budgetSelect) {
        budgetSelect.style.display = '';
      }
      if (domainSelect) {
        domainSelect.style.display = 'none';
        domainSelect.value = '';
      }
      if (companyInput) {
        companyInput.placeholder = 'Company / Organization';
      }
      if (messageTextarea) {
        messageTextarea.placeholder = 'Tell us about your project — the more detail, the better.';
      }
    }
  };

  if (serviceSelect) {
    serviceSelect.addEventListener('change', handleServiceChange);

    // Initial check for URL query params on page load
    const urlParams = new URLSearchParams(window.location.search);
    const serviceParam = urlParams.get('service');
    const courseParam = urlParams.get('course');
    if (serviceParam) {
      for (let option of serviceSelect.options) {
        if (option.value === serviceParam) {
          serviceSelect.value = serviceParam;
          handleServiceChange();
          break;
        }
      }
      if (serviceParam === 'internship' && courseParam && domainSelect) {
        for (let option of domainSelect.options) {
          if (option.value === courseParam) {
            domainSelect.value = courseParam;
            break;
          }
        }
      }
    }
  }

  contactForm.addEventListener('submit', e => {
    e.preventDefault();
    const btn = contactForm.querySelector('.btn-submit');
    const originalText = btn.textContent;
    btn.textContent = 'Sending...';
    btn.disabled = true;

    // Validate that domain is selected if internship is chosen
    if (serviceSelect && serviceSelect.value === 'internship' && domainSelect && !domainSelect.value) {
      showNotification('✗ Please select an internship domain.');
      btn.textContent = originalText;
      btn.disabled = false;
      return;
    }

    const formData = new FormData(contactForm);
    // Bind internship domain to the 'budget' field in the form payload
    if (serviceSelect && serviceSelect.value === 'internship' && domainSelect && domainSelect.value) {
      const selectedText = domainSelect.options[domainSelect.selectedIndex].text;
      formData.set('budget', selectedText);
    }

    fetch('/api/submit', { 
      method: 'POST', 
      body: new URLSearchParams(formData) 
    })
    .then(response => {
      if (!response.ok) {
        return response.json().then(err => { throw new Error(err.message || 'Error occurred'); });
      }
      return response.json();
    })
    .then(data => {
      btn.textContent = originalText;
      btn.disabled = false;
      showNotification('✓ Submission received! We\'ll be in touch soon.');
      contactForm.reset();
      handleServiceChange();
    })
    .catch(error => {
      console.error('Error!', error.message);
      btn.textContent = originalText;
      btn.disabled = false;
      showNotification(`✗ ${error.message || 'Error sending message.'}`);
    });
  });
}

function showNotification(msg) {
  const n = document.getElementById('notification');
  if (!n) return;
  n.textContent = msg;
  n.classList.add('show');
  setTimeout(() => n.classList.remove('show'), 4000);
}

// === ACTIVE NAV LINK ===
const currentPage = window.location.pathname.split('/').pop() || 'index.html';
document.querySelectorAll('.nav-link').forEach(link => {
  const href = link.getAttribute('href');
  link.classList.toggle('active', href === currentPage || (currentPage === '' && href === 'index.html'));
});

// === PARALLAX HERO ===
const heroBg = document.querySelector('.hero-bg');
let parallaxTicking = false;
window.addEventListener('scroll', () => {
  if (!heroBg || parallaxTicking || window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    return;
  }
  parallaxTicking = true;
  requestAnimationFrame(() => {
    if (window.scrollY < window.innerHeight) {
      heroBg.style.transform = `translateY(${window.scrollY * 0.3}px)`;
    }
    parallaxTicking = false;
  });
}, { passive: true });

// === COUNT UP ANIMATION ===
function animateCount(el, target, suffix) {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    el.textContent = target + suffix;
    return;
  }
  let start = 0;
  const duration = 1500;
  const step = (timestamp) => {
    if (!start) start = timestamp;
    const progress = Math.min((timestamp - start) / duration, 1);
    const val = Math.floor(progress * target);
    el.textContent = val + suffix;
    if (progress < 1) requestAnimationFrame(step);
    else el.textContent = target + suffix;
  };
  requestAnimationFrame(step);
}

const statNums = document.querySelectorAll('.stat-num');
if ('IntersectionObserver' in window) {
  const statObserver = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        const text = e.target.textContent;
        const num = parseInt(text.replace(/\D/g, ''), 10);
        if (!Number.isNaN(num)) {
          const suffix = text.replace(/[0-9]/g, '');
          animateCount(e.target, num, suffix);
        }
        statObserver.unobserve(e.target);
      }
    });
  }, { threshold: 0.5 });
  statNums.forEach(el => statObserver.observe(el));
}

// === DYNAMIC COOKIE CONSENT BANNER ===
document.addEventListener('DOMContentLoaded', () => {
  if (!readStorage('velora-cookie-consent')) {
    const banner = document.createElement('div');
    banner.id = 'cookieBanner';
    banner.style.cssText = `
      position: fixed;
      bottom: 24px;
      left: 24px;
      right: 24px;
      max-width: 440px;
      background: rgba(17, 17, 17, 0.85);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 16px;
      padding: 20px;
      box-shadow: 0 12px 40px rgba(0, 0, 0, 0.5);
      z-index: 10000;
      color: #fff;
      font-family: 'Inter', sans-serif;
      display: flex;
      flex-direction: column;
      gap: 12px;
      animation: cookieSlideUp 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    `;
    
    banner.innerHTML = `
      <div style="font-weight: 600; font-size: 14px; letter-spacing: -0.2px; display: flex; align-items: center; gap: 8px;">
        <span>🍪</span> Cookie & Privacy Consent
      </div>
      <div style="font-size: 11.5px; color: #86868b; line-height: 1.5;">
        We use cookies to optimize site performance, analyze traffic, and enhance your digital experience. By clicking "Accept", you agree to our privacy standards.
      </div>
      <div style="display: flex; gap: 8px; justify-content: flex-end; margin-top: 4px;">
        <button id="cookieReject" style="background: none; border: 1px solid rgba(255,255,255,0.1); color: #86868b; font-size: 11px; font-weight: 500; padding: 6px 14px; border-radius: 80px; cursor: pointer; transition: all 0.2s;">Decline</button>
        <button id="cookieAccept" style="background: #fff; border: none; color: #000; font-size: 11px; font-weight: 600; padding: 6px 16px; border-radius: 80px; cursor: pointer; transition: all 0.2s;">Accept</button>
      </div>
    `;

    const style = document.createElement('style');
    style.textContent = `
      @keyframes cookieSlideUp {
        from { transform: translateY(100px); opacity: 0; }
        to { transform: translateY(0); opacity: 1; }
      }
      #cookieAccept:hover { background: #e8e8ed !important; transform: scale(1.02); }
      #cookieReject:hover { color: #fff !important; border-color: rgba(255,255,255,0.2) !important; }
    `;
    document.head.appendChild(style);
    document.body.appendChild(banner);

    document.getElementById('cookieAccept').addEventListener('click', () => {
      writeStorage('velora-cookie-consent', 'accepted');
      banner.style.display = 'none';
    });
    
    document.getElementById('cookieReject').addEventListener('click', () => {
      writeStorage('velora-cookie-consent', 'declined');
      banner.style.display = 'none';
    });
  }
});
