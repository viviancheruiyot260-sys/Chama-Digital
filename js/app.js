/**
 * Chama Digital — Shared UI Helpers, Role Guards, Sidebar & Receipt Generation
 */
(function (global) {
  'use strict';

  function formatKES(amount) {
    const num = Number(amount || 0);
    return 'KES ' + num.toLocaleString('en-KE');
  }

  function formatDate(isoString) {
    if (!isoString || isoString === 'Completed' || isoString === 'Pending Approval' || isoString === 'Declined') {
      return isoString || '—';
    }
    const d = new Date(isoString);
    if (isNaN(d.getTime())) return isoString;
    return d.toLocaleDateString('en-KE', {
      day: '2-digit',
      month: 'short',
      year: 'numeric'
    });
  }

  function formatDateTime(isoString) {
    const d = new Date(isoString);
    if (isNaN(d.getTime())) return isoString;
    return d.toLocaleString('en-KE', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  function getDashboardUrlForUser(user) {
    if (!user) return 'login.html';
    if (user.status === 'PENDING') return 'pending-approval.html';
    if (user.status === 'REJECTED') return 'login.html?status=rejected';
    switch ((user.role || '').toUpperCase()) {
      case 'CHAIRPERSON':
        return 'chairperson-dashboard.html';
      case 'TREASURER':
        return 'treasurer-dashboard.html';
      case 'SECRETARY':
        return 'secretary-dashboard.html';
      default:
        return 'member-dashboard.html';
    }
  }

  /**
   * Frontend Role-Based Access Guard.
   * Ensures unauthenticated, pending, rejected, or wrong-role users are routed cleanly.
   */
  function requireAuth(allowedRoles) {
    const user = global.ChamaStore.getCurrentUser();
    if (!user) {
      global.location.href = 'login.html?reason=auth';
      return null;
    }
    if (user.status === 'PENDING') {
      global.location.href = 'pending-approval.html';
      return null;
    }
    if (user.status === 'REJECTED') {
      global.ChamaStore.logout();
      global.location.href = 'login.html?status=rejected';
      return null;
    }
    if (Array.isArray(allowedRoles) && allowedRoles.length > 0) {
      if (allowedRoles.indexOf(user.role) === -1) {
        global.location.href = getDashboardUrlForUser(user);
        return null;
      }
    }
    return user;
  }

  function escapeHtml(str) {
    return String(str || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function initSharedShell() {
    const user = global.ChamaStore.getCurrentUser();

    // Update top navbar auth actions when user is logged in
    const authActions = document.getElementById('navAuthActions');
    if (authActions) {
      if (user && user.status === 'ACTIVE') {
        const dashUrl = getDashboardUrlForUser(user);
        authActions.innerHTML =
          '<a href="' + dashUrl + '" class="btn btn-link text-decoration-none fw-semibold text-chama-green px-3">' +
          escapeHtml(user.fullName.split(' ')[0]) + ' Portal</a>' +
          '<button type="button" class="btn btn-chama-outline btn-chama-sm" data-action="logout">Logout</button>';
      } else if (user && user.status === 'PENDING') {
        authActions.innerHTML =
          '<a href="pending-approval.html" class="btn btn-link text-decoration-none fw-semibold text-chama-gold px-3">Approval Status</a>' +
          '<button type="button" class="btn btn-chama-outline btn-chama-sm" data-action="logout">Logout</button>';
      }
    }

    // Wire logout buttons
    document.querySelectorAll('[data-action="logout"]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        global.ChamaStore.logout();
        global.location.href = 'login.html';
      });
    });

    // Wire collapsible dashboard sidebar toggle
    const sidebarToggle = document.getElementById('sidebarToggleBtn');
    const dashboardShell = document.getElementById('dashboardShell');
    if (sidebarToggle && dashboardShell) {
      sidebarToggle.addEventListener('click', function () {
        dashboardShell.classList.toggle('sidebar-collapsed');
      });
    }
  }

  function buildReceiptText(tx, chamaName) {
    return [
      '============================================',
      '        CHAMA DIGITAL OFFICIAL RECEIPT      ',
      '============================================',
      'Group:              ' + (chamaName || 'Umoja Table Banking Chama'),
      'Receipt Number:     ' + tx.receiptNo,
      'Transaction Ref:    ' + tx.reference,
      'Date & Time:        ' + formatDateTime(tx.date),
      '--------------------------------------------',
      'Member Name:        ' + tx.memberName,
      'M-Pesa Phone:       ' + tx.phone,
      'Payment Type:       ' + tx.type,
      'Contribution Month: ' + tx.monthLabel,
      'Payment Method:     ' + tx.method,
      'Status:             ' + tx.status,
      '--------------------------------------------',
      'TOTAL AMOUNT PAID:  ' + formatKES(tx.amount),
      '--------------------------------------------',
      'Email Notification: ' + (tx.emailNotified ? 'Simulated dispatch to ' + (tx.email || 'member email') : 'Not requested'),
      'SMS Notification:   ' + (tx.smsNotified ? 'Simulated SMS sent to ' + tx.phone : 'Not requested'),
      '============================================',
      'Note: Frontend prototype receipt. Future Django',
      'backend will verify via Safaricom Daraja API.'
    ].join('\n');
  }

  function downloadReceipt(tx) {
    const state = global.ChamaStore.loadState();
    const content = buildReceiptText(tx, state.chama.name);
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = (tx.receiptNo || tx.reference) + '.txt';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }

  function openReceiptModal(txId) {
    const state = global.ChamaStore.loadState();
    const tx = state.transactions.find(function (t) { return t.id === txId; });
    if (!tx) return;

    const modalEl = document.getElementById('receiptModal');
    if (!modalEl) return;

    const setEl = function (id, val) {
      const el = document.getElementById(id);
      if (el) el.textContent = val;
    };

    setEl('modalReceiptGroup', state.chama.name);
    setEl('modalReceiptNo', 'Receipt No. ' + tx.receiptNo);
    setEl('modalReceiptMember', tx.memberName);
    setEl('modalReceiptPhone', tx.phone);
    setEl('modalReceiptMonth', tx.monthLabel);
    setEl('modalReceiptMethod', tx.method + ' (' + tx.type + ')');
    setEl('modalReceiptRef', tx.reference);
    setEl('modalReceiptDate', formatDateTime(tx.date));
    setEl('modalReceiptAmount', formatKES(tx.amount));
    setEl('modalReceiptStatus', tx.status);
    setEl(
      'modalReceiptNotifications',
      (tx.emailNotified ? 'Email notice queued for ' + (tx.email || 'member') : 'Email disabled') +
      ' · ' +
      (tx.smsNotified ? 'SMS notice queued for ' + tx.phone : 'SMS disabled')
    );

    const downloadBtn = document.getElementById('modalDownloadReceiptBtn');
    if (downloadBtn) {
      downloadBtn.onclick = function () { downloadReceipt(tx); };
    }

    if (global.bootstrap && global.bootstrap.Modal) {
      global.bootstrap.Modal.getOrCreateInstance(modalEl).show();
    }
  }

  document.addEventListener('DOMContentLoaded', initSharedShell);

  global.ChamaUI = {
    formatKES: formatKES,
    formatDate: formatDate,
    formatDateTime: formatDateTime,
    getDashboardUrlForUser: getDashboardUrlForUser,
    requireAuth: requireAuth,
    escapeHtml: escapeHtml,
    downloadReceipt: downloadReceipt,
    openReceiptModal: openReceiptModal
  };
})(window);
