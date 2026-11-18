/**
 * Chama Digital — Authentication & Two-Path Registration Controller
 */
(function (global) {
  'use strict';

  function showAlert(boxId, message, type) {
    const box = document.getElementById(boxId);
    if (!box) return;
    box.className = 'alert alert-' + (type || 'danger') + ' small mb-3';
    box.textContent = message;
    box.classList.remove('d-none');
  }

  function hideAlert(boxId) {
    const box = document.getElementById(boxId);
    if (box) box.classList.add('d-none');
  }

  function initRegisterPage() {
    const memberForm = document.getElementById('memberRegisterForm');
    const officialForm = document.getElementById('officialRegisterForm');

    if (memberForm) {
      memberForm.addEventListener('submit', function (e) {
        e.preventDefault();
        hideAlert('memberRegAlert');

        const fullName = document.getElementById('member-fullname').value;
        const email = document.getElementById('member-email').value;
        const phone = document.getElementById('member-phone').value;
        const nationalId = document.getElementById('member-id-number').value;
        const inviteCode = document.getElementById('member-chama-code').value;
        const password = document.getElementById('member-password').value;
        const confirm = document.getElementById('member-confirm').value;

        if (password.length < 6) {
          showAlert('memberRegAlert', 'Password must be at least 6 characters long.');
          return;
        }
        if (password !== confirm) {
          showAlert('memberRegAlert', 'Passwords do not match. Please re-enter carefully.');
          return;
        }

        const res = global.ChamaStore.registerMember({
          fullName: fullName,
          email: email,
          phone: phone,
          nationalId: nationalId,
          inviteCode: inviteCode,
          password: password
        });

        if (!res.ok) {
          showAlert('memberRegAlert', res.message);
          return;
        }

        global.location.href = 'pending-approval.html';
      });
    }

    if (officialForm) {
      officialForm.addEventListener('submit', function (e) {
        e.preventDefault();
        hideAlert('officialRegAlert');

        const chamaName = document.getElementById('official-chama-name').value;
        const role = document.getElementById('official-role').value;
        const fullName = document.getElementById('official-fullname').value;
        const email = document.getElementById('official-email').value;
        const phone = document.getElementById('official-phone').value;
        const password = document.getElementById('official-password').value;
        const confirm = document.getElementById('official-confirm').value;

        if (password.length < 6) {
          showAlert('officialRegAlert', 'Password must be at least 6 characters long.');
          return;
        }
        if (password !== confirm) {
          showAlert('officialRegAlert', 'Passwords do not match.');
          return;
        }

        const res = global.ChamaStore.registerOfficial({
          chamaName: chamaName,
          role: role,
          fullName: fullName,
          email: email,
          phone: phone,
          password: password
        });

        if (!res.ok) {
          showAlert('officialRegAlert', res.message);
          return;
        }

        global.location.href = global.ChamaUI.getDashboardUrlForUser(res.user);
      });
    }
  }

  function initLoginPage() {
    const loginForm = document.getElementById('loginForm');
    if (!loginForm) return;

    const params = new URLSearchParams(global.location.search);
    if (params.get('status') === 'rejected') {
      showAlert('loginAlert', 'Your membership application was declined by the Chairperson. Please contact your Chama Chairperson for clarification.', 'danger');
    } else if (params.get('reason') === 'auth') {
      showAlert('loginAlert', 'Please log in with your registered credentials to access your dashboard.', 'warning');
    }

    loginForm.addEventListener('submit', function (e) {
      e.preventDefault();
      hideAlert('loginAlert');

      const identifier = document.getElementById('login-identifier').value;
      const password = document.getElementById('login-password').value;

      const res = global.ChamaStore.authenticate(identifier, password);
      if (res.ok) {
        global.location.href = global.ChamaUI.getDashboardUrlForUser(res.user);
        return;
      }

      if (res.reason === 'PENDING_APPROVAL') {
        global.location.href = 'pending-approval.html';
        return;
      }

      if (res.reason === 'REJECTED') {
        showAlert('loginAlert', 'Your membership application was rejected by the Chairperson and cannot access the member dashboard.', 'danger');
        return;
      }

      showAlert('loginAlert', 'Invalid email/phone number or password. You can use the demo sign-in buttons below to explore each role.');
    });

    // Quick Demo Login Buttons
    document.querySelectorAll('[data-demo-user]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        const userId = btn.getAttribute('data-demo-user');
        const state = global.ChamaStore.loadState();
        const user = state.users.find(function (u) { return u.id === userId; });
        if (!user) return;
        if (user.status === 'REJECTED') {
          showAlert('loginAlert', 'This member account is marked Rejected and cannot access the dashboard.', 'danger');
          return;
        }
        global.ChamaStore.setCurrentUser(user.id);
        global.location.href = global.ChamaUI.getDashboardUrlForUser(user);
      });
    });

    const resetBtn = document.getElementById('resetDemoStateBtn');
    if (resetBtn) {
      resetBtn.addEventListener('click', function () {
        global.ChamaStore.resetDemoData();
        showAlert('loginAlert', 'Demo data reset to initial sample records.', 'success');
      });
    }
  }

  document.addEventListener('DOMContentLoaded', function () {
    initRegisterPage();
    initLoginPage();
  });
})(window);
