// ─── Custom Research Requests ───
// Handles form submission, validation, and mailto link creation for custom research.

document.addEventListener('DOMContentLoaded', function() {
  if (typeof initMobileMenu === 'function') initMobileMenu();

  var form = document.getElementById('research-form');
  if (!form) return;

  // Wire tier CTA buttons to scroll to form
  var tierCTAs = document.querySelectorAll('.tier-cta');
  tierCTAs.forEach(function(btn) {
    btn.addEventListener('click', function(e) {
      e.preventDefault();
      var tierCard = btn.closest('.tier-card');
      var tierName = tierCard ? tierCard.querySelector('.tier-name') : null;
      if (tierName) {
        var tierSelect = document.getElementById('research-tier');
        if (tierSelect) {
          var wanted = tierName.textContent.trim();
          for (var i = 0; i < tierSelect.options.length; i++) {
            if (tierSelect.options[i].value.indexOf(wanted) === 0) {
              tierSelect.selectedIndex = i;
              break;
            }
          }
        }
      }
      var formContainer = document.getElementById('research-form-container');
      if (formContainer) {
        formContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });

  form.addEventListener('submit', function(e) {
    e.preventDefault();

    var data = {
      topic: (document.getElementById('research-topic').value || '').trim(),
      questions: (document.getElementById('research-questions').value || '').trim(),
      deadline: document.getElementById('research-deadline').value || 'Flexible',
      tier: document.getElementById('research-tier').value || 'Not a member yet',
      name: (document.getElementById('research-name').value || '').trim(),
      email: (document.getElementById('research-email').value || '').trim(),
      org: (document.getElementById('research-org').value || '').trim()
    };

    if (!data.topic || !data.questions || !data.email || !data.name) {
      alert('Please fill in all required fields (Research Topic, Specific Questions, Name, and Email).');
      return;
    }

    // Simple email validation
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data.email)) {
      alert('Please enter a valid email address.');
      return;
    }

    // Build mailto link
    var subject = 'Custom Research Request: ' + data.topic;
    var body = 'RESEARCH REQUEST\n\n';
    body += 'Topic: ' + data.topic + '\n\n';
    body += 'Specific Questions:\n' + data.questions + '\n\n';
    body += 'Deadline: ' + data.deadline + '\n';
    body += 'Member Tier: ' + data.tier + '\n\n';
    body += 'From: ' + data.name + ' (' + data.email + ')\n';
    body += 'Organization: ' + (data.org || 'N/A') + '\n\n';
    body += '---\n';
    body += 'Submitted via The Innovators League research portal.';

    var mailto = 'mailto:research@rationaloptimistsociety.com?subject=' + encodeURIComponent(subject) + '&body=' + encodeURIComponent(body);

    // Show confirmation
    var formContainer = document.getElementById('research-form-container');
    var confirmation = document.getElementById('research-confirmation');
    if (formContainer) formContainer.style.display = 'none';
    if (confirmation) confirmation.style.display = 'block';

    // Scroll to top of confirmation
    window.scrollTo({ top: 0, behavior: 'smooth' });

    // Open email client after short delay
    setTimeout(function() {
      window.location.href = mailto;
    }, 500);
  });
});

// Helper: initMobileMenu (in case not loaded from utils)
if (typeof initMobileMenu === 'undefined') {
  window.initMobileMenu = function() {
    var btn = document.querySelector('.mobile-menu-btn');
    var links = document.querySelector('.nav-links');
    if (btn && links) {
      btn.addEventListener('click', function() {
        links.classList.toggle('open');
        btn.classList.toggle('open');
      });
    }
  };
}
