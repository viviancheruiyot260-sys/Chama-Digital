/**
 * Chama Digital — Role-Based Dashboards Controller (Vanilla JS + localStorage)
 */
(function (global) {
  'use strict';

  function setText(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
  }

  function populateSidebarUser(user, state) {
    setText('sidebarChamaName', user.chamaName || state.chama.name);
    setText('sidebarUserName', user.fullName);
    setText('sidebarUserRole', user.role.charAt(0) + user.role.slice(1).toLowerCase() + ' · ' + user.memberNo);
    const avatar = document.getElementById('sidebarAvatar');
    if (avatar && user.avatar) {
      avatar.src = user.avatar;
    }
  }

  /* ========================================================================
     1. Pending Chairperson Approval Page
     ======================================================================== */
  function initPendingPage() {
    const page = document.getElementById('pendingApprovalPage');
    if (!page) return;
    const state = global.ChamaStore.loadState();
    const user = global.ChamaStore.getCurrentUser();
    if (user && user.status === 'ACTIVE') {
      global.location.href = global.ChamaUI.getDashboardUrlForUser(user);
      return;
    }
    if (user) {
      setText('pendingApplicantName', user.fullName);
      setText('pendingApplicantPhone', user.phone);
      setText('pendingChamaMeta', state.chama.name + ' · Invite Code ' + state.chama.inviteCode + ' · Applicant: ' + user.fullName);
      if (user.status === 'REJECTED') {
        setText('pendingStatusHeading', 'Application Declined');
        setText('pendingStatusBadge', 'Status: Rejected');
        setText('pendingStatusMessage', 'Your membership application was declined by the Chairperson. You do not have access to the member dashboard.');
      }
    }
  }

  /* ========================================================================
     2. Chairperson Dashboard
     ======================================================================== */
  function initChairpersonDashboard() {
    if (!document.getElementById('chairpersonDashboard')) return;
    const user = global.ChamaUI.requireAuth(['CHAIRPERSON']);
    if (!user) return;

    function render() {
      const state = global.ChamaStore.loadState();
      populateSidebarUser(user, state);
      setText('welcomeHeading', 'Chairperson Console — ' + user.fullName);

      const allMembers = state.users.filter(function (u) { return u.role === 'MEMBER'; });
      const activeMembers = state.users.filter(function (u) { return u.status === 'ACTIVE'; });
      const pendingApps = state.users.filter(function (u) { return u.status === 'PENDING'; });
      const totalSavings = state.users.reduce(function (sum, u) { return sum + Number(u.savingsBalance || 0); }, 0);
      const outstandingLoans = state.loans
        .filter(function (l) { return l.status === 'ACTIVE'; })
        .reduce(function (sum, l) { return sum + Number(l.balance || 0); }, 0);

      setText('chairTotalMembers', String(allMembers.length));
      setText('chairActiveMembers', String(activeMembers.length));
      setText('chairPendingCount', String(pendingApps.length));
      setText('chairPendingBadge', pendingApps.length + ' Pending');
      setText('chairTotalSavings', global.ChamaUI.formatKES(totalSavings));
      setText('chairOutstandingLoans', global.ChamaUI.formatKES(outstandingLoans));

      const appsBody = document.getElementById('chairApplicationsBody');
      if (appsBody) {
        const applicants = state.users.filter(function (u) { return u.role === 'MEMBER'; });
        appsBody.innerHTML = applicants.map(function (app) {
          const statusClass = app.status === 'ACTIVE'
            ? 'status-paid'
            : (app.status === 'REJECTED' ? 'status-overdue' : 'status-pending');
          const statusText = app.status === 'ACTIVE'
            ? 'Approved (ACTIVE)'
            : (app.status === 'REJECTED' ? 'Rejected' : 'Pending Approval');
          const actions = app.status === 'PENDING'
            ? '<button type="button" class="btn btn-chama-primary btn-chama-sm" data-approve-member="' + app.id + '">Approve</button> ' +
              '<button type="button" class="btn btn-chama-outline btn-chama-sm" data-reject-member="' + app.id + '">Reject</button>'
            : '<span class="small text-chama-muted">Decision recorded</span>';
          return '<tr>' +
            '<td><div class="fw-semibold">' + global.ChamaUI.escapeHtml(app.fullName) + '</div>' +
            '<div class="small text-chama-muted">' + global.ChamaUI.escapeHtml(app.email) + '</div></td>' +
            '<td class="mono-figure">' + global.ChamaUI.escapeHtml(app.phone) + '</td>' +
            '<td class="mono-figure">' + global.ChamaUI.escapeHtml(app.nationalId) + '</td>' +
            '<td class="mono-figure">' + global.ChamaUI.formatDate(app.joinedDate) + '</td>' +
            '<td><span class="status-label ' + statusClass + '">' + statusText + '</span></td>' +
            '<td class="text-end text-nowrap">' + actions + '</td>' +
          '</tr>';
        }).join('');

        appsBody.querySelectorAll('[data-approve-member]').forEach(function (btn) {
          btn.addEventListener('click', function () {
            const id = btn.getAttribute('data-approve-member');
            const updated = global.ChamaStore.setMemberStatus(id, 'ACTIVE');
            showChairBanner('Approved ' + updated.fullName + ' (' + updated.memberNo + '). Member can now log in to the full dashboard.', 'success');
            render();
          });
        });

        appsBody.querySelectorAll('[data-reject-member]').forEach(function (btn) {
          btn.addEventListener('click', function () {
            const id = btn.getAttribute('data-reject-member');
            const updated = global.ChamaStore.setMemberStatus(id, 'REJECTED');
            showChairBanner('Declined application for ' + updated.fullName + '. Access to the member dashboard remains blocked.', 'warning');
            render();
          });
        });
      }

      const loanAppsBody = document.getElementById('chairLoansBody');
      if (loanAppsBody) {
        loanAppsBody.innerHTML = state.loans.map(function (loan) {
          const stClass = loan.status === 'ACTIVE' || loan.status === 'COMPLETED'
            ? 'status-paid'
            : (loan.status === 'REJECTED' ? 'status-overdue' : 'status-pending');
          const actions = loan.status === 'PENDING'
            ? '<button type="button" class="btn btn-chama-primary btn-chama-sm" data-approve-loan="' + loan.id + '">Approve Loan</button> ' +
              '<button type="button" class="btn btn-chama-outline btn-chama-sm" data-reject-loan="' + loan.id + '">Reject</button>'
            : '<span class="small text-chama-muted">' + loan.status + '</span>';
          return '<tr>' +
            '<td class="mono-figure">' + loan.id + '</td>' +
            '<td>' + global.ChamaUI.escapeHtml(loan.memberName) + '</td>' +
            '<td>' + global.ChamaUI.escapeHtml(loan.purpose) + '</td>' +
            '<td class="text-end mono-figure">' + global.ChamaUI.formatKES(loan.principal) + '</td>' +
            '<td><span class="status-label ' + stClass + '">' + loan.status + '</span></td>' +
            '<td class="text-end text-nowrap">' + actions + '</td>' +
          '</tr>';
        }).join('');

        loanAppsBody.querySelectorAll('[data-approve-loan]').forEach(function (btn) {
          btn.addEventListener('click', function () {
            global.ChamaStore.setLoanStatus(btn.getAttribute('data-approve-loan'), 'ACTIVE');
            showChairBanner('Loan approved and activated for repayment tracking.', 'success');
            render();
          });
        });

        loanAppsBody.querySelectorAll('[data-reject-loan]').forEach(function (btn) {
          btn.addEventListener('click', function () {
            global.ChamaStore.setLoanStatus(btn.getAttribute('data-reject-loan'), 'REJECTED');
            showChairBanner('Loan application declined.', 'warning');
            render();
          });
        });
      }

      const txBody = document.getElementById('chairTxBody');
      if (txBody) {
        txBody.innerHTML = state.transactions.slice(0, 6).map(function (tx) {
          return '<tr>' +
            '<td class="mono-figure">' + global.ChamaUI.formatDate(tx.date) + '</td>' +
            '<td>' + global.ChamaUI.escapeHtml(tx.memberName) + '</td>' +
            '<td>' + global.ChamaUI.escapeHtml(tx.type) + '</td>' +
            '<td class="mono-figure">' + global.ChamaUI.escapeHtml(tx.reference) + '</td>' +
            '<td><span class="status-label ' + (tx.status === 'Successful' ? 'status-paid' : 'status-overdue') + '">' + tx.status + '</span></td>' +
            '<td class="text-end mono-figure">' + global.ChamaUI.formatKES(tx.amount) + '</td>' +
          '</tr>';
        }).join('');
      }
    }

    function showChairBanner(msg, type) {
      const el = document.getElementById('chairActionAlert');
      if (!el) return;
      el.className = 'alert alert-' + type + ' small mb-4';
      el.textContent = msg;
      el.classList.remove('d-none');
    }

    render();
  }

  /* ========================================================================
     3. Treasurer Dashboard (With Live Payment Notifications)
     ======================================================================== */
  function initTreasurerDashboard() {
    if (!document.getElementById('treasurerDashboard')) return;
    const user = global.ChamaUI.requireAuth(['TREASURER']);
    if (!user) return;

    function render() {
      const state = global.ChamaStore.loadState();
      populateSidebarUser(user, state);
      setText('welcomeHeading', 'Treasurer Console — ' + user.fullName);

      const totalSavings = state.users.reduce(function (sum, u) { return sum + Number(u.savingsBalance || 0); }, 0);
      const novContributions = state.transactions
        .filter(function (t) { return t.status === 'Successful' && t.month === '2026-11'; })
        .reduce(function (sum, t) { return sum + Number(t.amount || 0); }, 0);
      const totalLoansIssued = state.loans
        .filter(function (l) { return l.status !== 'REJECTED' && l.status !== 'PENDING'; })
        .reduce(function (sum, l) { return sum + Number(l.principal || 0); }, 0);
      const outstandingLoans = state.loans
        .filter(function (l) { return l.status === 'ACTIVE'; })
        .reduce(function (sum, l) { return sum + Number(l.balance || 0); }, 0);

      setText('treasurerTotalSavings', global.ChamaUI.formatKES(totalSavings));
      setText('treasurerMonthlyContrib', global.ChamaUI.formatKES(novContributions));
      setText('treasurerLoansIssued', global.ChamaUI.formatKES(totalLoansIssued));
      setText('treasurerOutstandingLoans', global.ChamaUI.formatKES(outstandingLoans));

      // Treasurer Payment Notifications Feed
      const notifications = state.treasurerNotifications || [];
      const unreadCount = notifications.filter(function (n) { return n.unread; }).length;
      setText('treasurerUnreadCount', unreadCount + ' Unread');

      const notifList = document.getElementById('treasurerNotificationsList');
      if (notifList) {
        notifList.innerHTML = notifications.length
          ? notifications.slice(0, 6).map(function (n) {
              return '<li class="list-group-item px-4 py-3 d-flex justify-content-between align-items-start gap-3">' +
                '<div>' +
                  '<div class="small fw-' + (n.unread ? 'semibold text-chama-green' : 'normal text-chama-ink') + '">' +
                    global.ChamaUI.escapeHtml(n.message) +
                  '</div>' +
                  '<div class="small text-chama-muted mono-figure">' + global.ChamaUI.formatDateTime(n.date) + '</div>' +
                '</div>' +
                '<span class="status-label ' + (n.unread ? 'status-pending' : 'status-paid') + '">' +
                  (n.unread ? 'New Payment' : 'Reviewed') +
                '</span>' +
              '</li>';
            }).join('')
          : '<li class="list-group-item px-4 py-3 small text-chama-muted">No member payment notifications yet.</li>';
      }

      const membersBody = document.getElementById('treasurerMembersBody');
      if (membersBody) {
        const activeMembers = state.users.filter(function (u) { return u.status === 'ACTIVE'; });
        membersBody.innerHTML = activeMembers.map(function (m) {
          const paidNov = global.ChamaStore.hasPaidMonth(m.id, '2026-11');
          return '<tr>' +
            '<td>' + global.ChamaUI.escapeHtml(m.fullName) + '</td>' +
            '<td class="mono-figure">' + global.ChamaUI.escapeHtml(m.memberNo) + '</td>' +
            '<td><span class="status-label ' + (paidNov ? 'status-paid' : 'status-pending') + '">' +
              (paidNov ? 'Paid (Nov)' : 'Outstanding (Nov)') + '</span></td>' +
            '<td class="text-end mono-figure">' + global.ChamaUI.formatKES(m.monthlyTarget) + '</td>' +
            '<td class="text-end mono-figure">' + global.ChamaUI.formatKES(m.savingsBalance) + '</td>' +
          '</tr>';
        }).join('');
      }

      const loansBody = document.getElementById('treasurerLoansBody');
      if (loansBody) {
        loansBody.innerHTML = state.loans.map(function (loan) {
          const stClass = loan.status === 'ACTIVE' || loan.status === 'COMPLETED'
            ? 'status-paid'
            : (loan.status === 'REJECTED' ? 'status-overdue' : 'status-pending');
          const actionBtn = loan.status === 'PENDING'
            ? '<button type="button" class="btn btn-chama-primary btn-chama-sm" data-t-approve-loan="' + loan.id + '">Approve</button>'
            : '<span class="small text-chama-muted">' + loan.status + '</span>';
          return '<tr>' +
            '<td class="mono-figure">' + loan.id + '</td>' +
            '<td>' + global.ChamaUI.escapeHtml(loan.memberName) + '</td>' +
            '<td class="mono-figure">' + global.ChamaUI.formatDate(loan.nextRepaymentDate) + '</td>' +
            '<td><span class="status-label ' + stClass + '">' + loan.status + '</span></td>' +
            '<td class="text-end mono-figure">' + global.ChamaUI.formatKES(loan.principal) + '</td>' +
            '<td class="text-end mono-figure">' + global.ChamaUI.formatKES(loan.balance) + '</td>' +
            '<td class="text-end">' + actionBtn + '</td>' +
          '</tr>';
        }).join('');

        loansBody.querySelectorAll('[data-t-approve-loan]').forEach(function (btn) {
          btn.addEventListener('click', function () {
            global.ChamaStore.setLoanStatus(btn.getAttribute('data-t-approve-loan'), 'ACTIVE');
            render();
          });
        });
      }

      const txBody = document.getElementById('treasurerTxBody');
      if (txBody) {
        txBody.innerHTML = state.transactions.slice(0, 8).map(function (tx) {
          return '<tr>' +
            '<td class="mono-figure">' + global.ChamaUI.formatDate(tx.date) + '</td>' +
            '<td>' + global.ChamaUI.escapeHtml(tx.memberName) + '</td>' +
            '<td>' + global.ChamaUI.escapeHtml(tx.monthLabel) + '</td>' +
            '<td>' + global.ChamaUI.escapeHtml(tx.method) + '</td>' +
            '<td class="mono-figure">' + global.ChamaUI.escapeHtml(tx.reference) + '</td>' +
            '<td><span class="status-label ' + (tx.status === 'Successful' ? 'status-paid' : 'status-overdue') + '">' + tx.status + '</span></td>' +
            '<td class="text-end mono-figure">' + global.ChamaUI.formatKES(tx.amount) + '</td>' +
          '</tr>';
        }).join('');
      }
    }

    const markReadBtn = document.getElementById('markNotificationsReadBtn');
    if (markReadBtn) {
      markReadBtn.addEventListener('click', function () {
        global.ChamaStore.markTreasurerNotificationsRead();
        render();
      });
    }

    const downloadCsvBtn = document.getElementById('exportLedgerCsvBtn');
    if (downloadCsvBtn) {
      downloadCsvBtn.addEventListener('click', function () {
        const state = global.ChamaStore.loadState();
        const rows = [['Date', 'Member', 'Month', 'Type', 'Method', 'Reference', 'Status', 'Amount (KES)']];
        state.transactions.forEach(function (t) {
          rows.push([t.date.slice(0, 10), t.memberName, t.monthLabel, t.type, t.method, t.reference, t.status, t.amount]);
        });
        const csv = rows.map(function (r) { return r.join(','); }).join('\n');
        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'chama-financial-report.csv';
        a.click();
        URL.revokeObjectURL(url);
      });
    }

    render();
  }

  /* ========================================================================
     4. Secretary Dashboard
     ======================================================================== */
  function initSecretaryDashboard() {
    if (!document.getElementById('secretaryDashboard')) return;
    const user = global.ChamaUI.requireAuth(['SECRETARY']);
    if (!user) return;

    function render() {
      const state = global.ChamaStore.loadState();
      populateSidebarUser(user, state);
      setText('welcomeHeading', 'Secretary Workspace — ' + user.fullName);

      const directoryBody = document.getElementById('secretaryDirectoryBody');
      if (directoryBody) {
        directoryBody.innerHTML = state.users.map(function (m) {
          const stClass = m.status === 'ACTIVE' ? 'status-paid' : (m.status === 'PENDING' ? 'status-pending' : 'status-overdue');
          return '<tr>' +
            '<td>' + global.ChamaUI.escapeHtml(m.fullName) + '</td>' +
            '<td class="mono-figure">' + global.ChamaUI.escapeHtml(m.memberNo) + '</td>' +
            '<td>' + global.ChamaUI.escapeHtml(m.role) + '</td>' +
            '<td class="mono-figure">' + global.ChamaUI.escapeHtml(m.phone) + '</td>' +
            '<td>' + global.ChamaUI.escapeHtml(m.email) + '</td>' +
            '<td><span class="status-label ' + stClass + '">' + m.status + '</span></td>' +
          '</tr>';
        }).join('');
      }

      const meetingsList = document.getElementById('secretaryMeetingsList');
      if (meetingsList) {
        meetingsList.innerHTML = state.meetings.map(function (mtg) {
          const isOccasion = mtg.eventType === 'Important Occasion';
          return '<li class="list-group-item px-4 py-3 d-flex justify-content-between align-items-start gap-3">' +
            '<div>' +
              '<div class="fw-semibold small">' + global.ChamaUI.escapeHtml(mtg.title) + '</div>' +
              '<div class="small text-chama-muted">' + global.ChamaUI.formatDate(mtg.date) + ' · ' + global.ChamaUI.escapeHtml(mtg.time) + ' · ' + global.ChamaUI.escapeHtml(mtg.venue) + '</div>' +
              '<div class="small text-chama-muted mt-1">' + global.ChamaUI.escapeHtml(mtg.description || '') + '</div>' +
              '<div class="small text-chama-green mt-1">' + global.ChamaUI.escapeHtml(mtg.attendanceSummary) + '</div>' +
            '</div>' +
            '<span class="status-label ' + (isOccasion ? 'status-pending' : 'status-paid') + '">' + global.ChamaUI.escapeHtml(mtg.eventType || mtg.status) + '</span>' +
          '</li>';
        }).join('');
      }

      const announcementsList = document.getElementById('secretaryAnnouncementsList');
      if (announcementsList) {
        announcementsList.innerHTML = state.announcements.map(function (ann) {
          return '<li class="list-group-item px-4 py-3">' +
            '<div class="d-flex justify-content-between gap-2 mb-1">' +
              '<div class="fw-semibold small">' + global.ChamaUI.escapeHtml(ann.title) + '</div>' +
              '<span class="mono-figure small text-chama-muted">' + global.ChamaUI.formatDate(ann.date) + '</span>' +
            '</div>' +
            '<div class="small text-chama-muted mb-1">' + global.ChamaUI.escapeHtml(ann.body) + '</div>' +
            '<div class="small text-chama-green">Posted by ' + global.ChamaUI.escapeHtml(ann.author) + '</div>' +
          '</li>';
        }).join('');
      }
    }

    const annForm = document.getElementById('addAnnouncementForm');
    if (annForm) {
      annForm.addEventListener('submit', function (e) {
        e.preventDefault();
        const title = document.getElementById('annTitle').value;
        const body = document.getElementById('annBody').value;
        global.ChamaStore.addAnnouncement({
          title: title,
          body: body,
          author: user.fullName + ' (Secretary)'
        });
        annForm.reset();
        render();
      });
    }

    const mtgForm = document.getElementById('addMeetingForm');
    if (mtgForm) {
      mtgForm.addEventListener('submit', function (e) {
        e.preventDefault();
        const typeEl = document.getElementById('mtgEventType');
        const descEl = document.getElementById('mtgDesc');
        global.ChamaStore.addMeeting({
          eventType: typeEl ? typeEl.value : 'Meeting',
          title: document.getElementById('mtgTitle').value,
          date: document.getElementById('mtgDate').value,
          time: document.getElementById('mtgTime').value,
          venue: document.getElementById('mtgVenue').value,
          description: descEl ? descEl.value : ''
        });
        mtgForm.reset();
        render();
      });
    }

    render();
  }

  /* ========================================================================
     5. Member Dashboard, Same-Chama Members, History, Loans & Profile
     ======================================================================== */
  function getMemberSummary(user, state) {
    const myLoans = state.loans.filter(function (l) { return l.userId === user.id; });
    const activeLoan = myLoans.find(function (l) { return l.status === 'ACTIVE'; });
    const totalBorrowed = myLoans
      .filter(function (l) { return l.status === 'ACTIVE' || l.status === 'COMPLETED'; })
      .reduce(function (sum, l) { return sum + Number(l.principal || 0); }, 0);
    const totalRepaid = myLoans
      .filter(function (l) { return l.status === 'ACTIVE' || l.status === 'COMPLETED'; })
      .reduce(function (sum, l) { return sum + Number(l.repaid || 0); }, 0);
    const loanBalance = activeLoan ? activeLoan.balance : 0;
    const myTxs = state.transactions.filter(function (t) { return t.userId === user.id; });
    return {
      myLoans: myLoans,
      activeLoan: activeLoan,
      totalBorrowed: totalBorrowed,
      totalRepaid: totalRepaid,
      loanBalance: loanBalance,
      myTxs: myTxs
    };
  }

  function initMemberDashboard() {
    if (!document.getElementById('memberDashboard')) return;
    const user = global.ChamaUI.requireAuth(['MEMBER']);
    if (!user) return;

    const methodSelect = document.getElementById('payment-method');
    const phoneLabel = document.getElementById('paymentAccountLabel');
    const phoneInput = document.getElementById('mpesa-phone');
    const bankRefWrap = document.getElementById('bankReferenceWrap');
    const methodHint = document.getElementById('paymentMethodInstructions');

    function updateMethodFields() {
      if (!methodSelect) return;
      const val = methodSelect.value;
      const isBank = val.toLowerCase().indexOf('bank') !== -1;
      const state = global.ChamaStore.loadState();

      if (isBank) {
        if (bankRefWrap) bankRefWrap.classList.remove('d-none');
        if (phoneLabel) phoneLabel.textContent = 'Phone for SMS Confirmation';
        if (methodHint) {
          methodHint.textContent = 'Bank Account: ' + state.chama.bankName + ' · Acc ' + state.chama.bankAccount + ' · Enter your bank slip or EFT reference below.';
        }
      } else if (val === 'M-Pesa Paybill') {
        if (bankRefWrap) bankRefWrap.classList.remove('d-none');
        if (phoneLabel) phoneLabel.textContent = 'M-Pesa Phone Number';
        if (methodHint) {
          methodHint.textContent = 'M-Pesa Paybill ' + state.chama.paybill + ' · Account No: ' + user.memberNo + '. Enter your M-Pesa confirmation code or leave blank to auto-generate.';
        }
      } else {
        if (bankRefWrap) bankRefWrap.classList.add('d-none');
        if (phoneLabel) phoneLabel.textContent = 'Registered M-Pesa Phone';
        if (methodHint) {
          methodHint.textContent = 'M-Pesa STK Push / USSD sends an instant prompt to your registered Safaricom/Airtel line.';
        }
      }
    }

    if (methodSelect) {
      methodSelect.addEventListener('change', updateMethodFields);
    }

    function render() {
      const state = global.ChamaStore.loadState();
      const freshUser = state.users.find(function (u) { return u.id === user.id; }) || user;
      populateSidebarUser(freshUser, state);
      const summary = getMemberSummary(freshUser, state);

      setText('memberWelcomeHeading', 'Welcome back, ' + freshUser.fullName);
      setText('cardTotalSavings', global.ChamaUI.formatKES(freshUser.savingsBalance));
      setText('cardLoanBalance', global.ChamaUI.formatKES(summary.loanBalance));
      setText('cardTotalBorrowed', global.ChamaUI.formatKES(summary.totalBorrowed));
      setText('cardTotalRepaid', global.ChamaUI.formatKES(summary.totalRepaid));
      setText('cardNextDueDate', global.ChamaUI.formatDate(state.chama.nextContributionDate));
      setText('cardMonthlyAmount', global.ChamaUI.formatKES(freshUser.monthlyTarget || state.chama.monthlyContribution));

      if (phoneInput && !phoneInput.value) {
        phoneInput.value = freshUser.phone;
      }
      updateMethodFields();

      // Next Meeting Highlight & Important Chama Occasions
      const sortedEvents = (state.meetings || []).slice().sort(function (a, b) {
        return String(a.date).localeCompare(String(b.date));
      });
      const nextMeeting = sortedEvents.find(function (m) { return m.eventType !== 'Important Occasion'; }) || sortedEvents[0];
      if (nextMeeting) {
        setText('nextMeetingTitle', nextMeeting.title);
        setText('nextMeetingDateMeta', global.ChamaUI.formatDate(nextMeeting.date) + ' · ' + nextMeeting.time + ' · ' + nextMeeting.venue);
        setText('nextMeetingDesc', nextMeeting.description || nextMeeting.attendanceSummary);
      }

      const occasionsList = document.getElementById('memberOccasionsList');
      if (occasionsList) {
        occasionsList.innerHTML = sortedEvents.map(function (ev) {
          const isOccasion = ev.eventType === 'Important Occasion';
          return '<li class="list-group-item px-4 py-3 d-flex justify-content-between align-items-start gap-2">' +
            '<div>' +
              '<div class="fw-semibold small">' + global.ChamaUI.escapeHtml(ev.title) + '</div>' +
              '<div class="small text-chama-muted mono-figure">' + global.ChamaUI.formatDate(ev.date) + ' · ' + global.ChamaUI.escapeHtml(ev.time) + '</div>' +
              '<div class="small text-chama-muted">' + global.ChamaUI.escapeHtml(ev.venue) + '</div>' +
            '</div>' +
            '<span class="status-label ' + (isOccasion ? 'status-pending' : 'status-paid') + '">' +
              global.ChamaUI.escapeHtml(ev.eventType || 'Meeting') +
            '</span>' +
          '</li>';
        }).join('');
      }

      // Group Announcements
      const announcementsList = document.getElementById('memberAnnouncementsList');
      if (announcementsList) {
        announcementsList.innerHTML = (state.announcements || []).map(function (a) {
          return '<li class="list-group-item px-4 py-3">' +
            '<div class="d-flex justify-content-between gap-2 mb-1">' +
              '<div class="fw-semibold small">' + global.ChamaUI.escapeHtml(a.title) + '</div>' +
              '<span class="mono-figure small text-chama-muted">' + global.ChamaUI.formatDate(a.date) + '</span>' +
            '</div>' +
            '<div class="small text-chama-muted mb-1">' + global.ChamaUI.escapeHtml(a.body) + '</div>' +
            '<div class="small text-chama-green">From ' + global.ChamaUI.escapeHtml(a.author) + '</div>' +
          '</li>';
        }).join('');
      }

      // Latest Receipt Card
      const latestTx = summary.myTxs.find(function (t) { return t.status === 'Successful'; }) || summary.myTxs[0];
      if (latestTx) {
        setText('latestReceiptBadge', 'Receipt #' + latestTx.receiptNo);
        setText('latestReceiptAmount', global.ChamaUI.formatKES(latestTx.amount));
        setText('latestReceiptMember', freshUser.fullName + ' (' + freshUser.memberNo + ')');
        setText('latestReceiptRef', latestTx.reference);
        setText('latestReceiptMonth', latestTx.monthLabel);
        setText('latestReceiptPhone', latestTx.phone);
        setText('latestReceiptDate', global.ChamaUI.formatDateTime(latestTx.date));
        setText('latestEmailNotice', latestTx.emailNotified ? 'Email confirmation sent to ' + freshUser.email : 'Email confirmation not requested');
        setText('latestSmsNotice', latestTx.smsNotified ? 'SMS confirmation sent to ' + latestTx.phone + ' · Treasurer notified' : 'Treasurer notified');

        const printBtn = document.getElementById('latestReceiptOpenBtn');
        if (printBtn) {
          printBtn.onclick = function () { global.ChamaUI.openReceiptModal(latestTx.id); };
        }
        const dlBtn = document.getElementById('latestReceiptDownloadBtn');
        if (dlBtn) {
          dlBtn.onclick = function () { global.ChamaUI.downloadReceipt(latestTx); };
        }
      }

      // Recent Payment History
      const txBody = document.getElementById('memberRecentTxBody');
      if (txBody) {
        txBody.innerHTML = summary.myTxs.slice(0, 6).map(function (tx) {
          const stClass = tx.status === 'Successful' ? 'status-paid' : (tx.status === 'Pending' ? 'status-pending' : 'status-overdue');
          const receiptBtn = tx.status === 'Successful'
            ? '<button type="button" class="btn btn-link btn-sm p-0 fw-semibold text-decoration-none text-chama-green" data-view-receipt="' + tx.id + '">View Receipt</button>'
            : '<span class="small text-chama-muted">—</span>';
          return '<tr>' +
            '<td class="mono-figure">' + global.ChamaUI.formatDate(tx.date) + '</td>' +
            '<td>' + global.ChamaUI.escapeHtml(tx.monthLabel) + '</td>' +
            '<td>' + global.ChamaUI.escapeHtml(tx.method) + '</td>' +
            '<td class="mono-figure">' + global.ChamaUI.escapeHtml(tx.reference) + '</td>' +
            '<td><span class="status-label ' + stClass + '">' + tx.status + '</span></td>' +
            '<td class="text-end mono-figure">' + global.ChamaUI.formatKES(tx.amount) + '</td>' +
            '<td class="text-end">' + receiptBtn + '</td>' +
          '</tr>';
        }).join('');

        txBody.querySelectorAll('[data-view-receipt]').forEach(function (btn) {
          btn.addEventListener('click', function () {
            global.ChamaUI.openReceiptModal(btn.getAttribute('data-view-receipt'));
          });
        });
      }
    }

    const payForm = document.getElementById('memberPaymentForm');
    if (payForm) {
      payForm.addEventListener('submit', function (e) {
        e.preventDefault();
        const alertEl = document.getElementById('paymentStatusAlert');
        const monthSel = document.getElementById('contribution-month');
        const monthVal = monthSel.value;
        const monthLabel = monthSel.options[monthSel.selectedIndex].text;
        const amount = Number(document.getElementById('payment-amount').value);
        const phone = document.getElementById('mpesa-phone').value.trim();
        const method = document.getElementById('payment-method').value;
        const customRefEl = document.getElementById('bankReferenceInput');
        const customRef = customRefEl ? customRefEl.value : '';
        const type = document.getElementById('payment-purpose').value;
        const allowAdditional = document.getElementById('allow-additional-contrib').checked;
        const outcome = document.getElementById('simulate-outcome').value;
        const notifyEmail = document.getElementById('confirm-email').checked;
        const notifySms = document.getElementById('confirm-sms').checked;

        if (!phone || amount < 100) {
          alertEl.className = 'alert alert-danger small mb-3';
          alertEl.textContent = 'Enter a valid phone number and an amount of at least KES 100.';
          alertEl.classList.remove('d-none');
          return;
        }

        if (type === 'Monthly Contribution' && global.ChamaStore.hasPaidMonth(user.id, monthVal) && !allowAdditional) {
          alertEl.className = 'alert alert-warning small mb-3';
          alertEl.textContent = 'Contribution for ' + monthLabel + ' is already paid. Check "Allow additional contribution" to submit an extra deposit.';
          alertEl.classList.remove('d-none');
          return;
        }

        alertEl.className = 'alert alert-info small mb-3';
        alertEl.textContent = 'Processing ' + method + ' payment... Status: Pending confirmation.';
        alertEl.classList.remove('d-none');

        setTimeout(function () {
          const res = global.ChamaStore.recordPayment({
            userId: user.id,
            phone: phone,
            month: monthVal,
            monthLabel: monthLabel,
            type: type,
            method: method,
            customRef: customRef,
            amount: amount,
            simulatedOutcome: outcome,
            notifyEmail: notifyEmail,
            notifySms: notifySms
          });

          if (!res.ok) return;

          if (res.transaction.status === 'Successful') {
            alertEl.className = 'alert alert-success small mb-3';
            alertEl.textContent = 'Payment Successful via ' + method + ' (Ref: ' + res.transaction.reference + '). Account balance updated and Treasurer notified.';
            if (customRefEl) customRefEl.value = '';
            render();
            global.ChamaUI.openReceiptModal(res.transaction.id);
          } else {
            alertEl.className = 'alert alert-danger small mb-3';
            alertEl.textContent = 'Simulated Payment Failed (Ref: ' + res.transaction.reference + '). Your balance was not modified.';
            render();
          }
        }, 650);
      });
    }

    render();
  }

  /* ========================================================================
     6. Same-Chama Fellow Members Page (Profiles Visible, Savings Hidden)
     ======================================================================== */
  function initChamaMembersPage() {
    if (!document.getElementById('chamaMembersPage')) return;
    const user = global.ChamaUI.requireAuth(['MEMBER']);
    if (!user) return;

    const state = global.ChamaStore.loadState();
    populateSidebarUser(user, state);
    const myChama = user.chamaName || state.chama.name;
    setText('fellowChamaTitle', myChama + ' — Member Directory');

    const gridEl = document.getElementById('chamaMembersGrid');
    const searchInput = document.getElementById('memberSearchInput');

    function renderDirectory() {
      const freshState = global.ChamaStore.loadState();
      const query = (searchInput ? searchInput.value : '').trim().toLowerCase();
      const peers = freshState.users.filter(function (u) {
        const sameChama = (u.chamaName || freshState.chama.name) === myChama;
        const isActive = u.status === 'ACTIVE';
        const matches = !query ||
          u.fullName.toLowerCase().indexOf(query) !== -1 ||
          u.role.toLowerCase().indexOf(query) !== -1 ||
          u.memberNo.toLowerCase().indexOf(query) !== -1;
        return sameChama && isActive && matches;
      });

      setText('fellowMembersCount', peers.length + ' Active Members in ' + myChama);

      if (peers.length === 0) {
        gridEl.innerHTML = '<div class="col-12"><div class="chama-card p-4 text-center text-chama-muted">No matching members found in your chama.</div></div>';
        return;
      }

      // Note: Intentionally omits savingsBalance and loan data to preserve member financial privacy.
      gridEl.innerHTML = peers.map(function (m) {
        const isSelf = m.id === user.id;
        return '<div class="col-md-6 col-xl-4">' +
          '<article class="chama-card p-4 h-100">' +
            '<div class="d-flex align-items-center gap-3 pb-3 mb-3 border-bottom">' +
              '<img src="' + global.ChamaUI.escapeHtml(m.avatar || 'images/avatar-member-amina.jpg') + '" alt="Profile photo of ' + global.ChamaUI.escapeHtml(m.fullName) + '" class="sidebar-avatar" style="width:56px;height:56px;">' +
              '<div>' +
                '<h2 class="h6 fw-bold mb-1">' + global.ChamaUI.escapeHtml(m.fullName) + (isSelf ? ' (You)' : '') + '</h2>' +
                '<div class="small text-chama-green fw-semibold">' + global.ChamaUI.escapeHtml(m.role) + ' &middot; <span class="mono-figure">' + global.ChamaUI.escapeHtml(m.memberNo) + '</span></div>' +
              '</div>' +
            '</div>' +
            '<div class="d-grid gap-2 small">' +
              '<div class="d-flex justify-content-between"><span class="text-chama-muted">Chama Group</span><strong>' + global.ChamaUI.escapeHtml(m.chamaName || myChama) + '</strong></div>' +
              '<div class="d-flex justify-content-between"><span class="text-chama-muted">Phone</span><span class="mono-figure">' + global.ChamaUI.escapeHtml(m.phone) + '</span></div>' +
              '<div class="d-flex justify-content-between"><span class="text-chama-muted">Email</span><span class="text-truncate" style="max-width:190px;">' + global.ChamaUI.escapeHtml(m.email) + '</span></div>' +
              '<div class="d-flex justify-content-between"><span class="text-chama-muted">Joined</span><span class="mono-figure">' + global.ChamaUI.formatDate(m.joinedDate) + '</span></div>' +
              '<div class="d-flex justify-content-between"><span class="text-chama-muted">Financials</span><span class="text-chama-muted fst-italic">Private to member</span></div>' +
            '</div>' +
          '</article>' +
        '</div>';
      }).join('');
    }

    if (searchInput) {
      searchInput.addEventListener('input', renderDirectory);
    }
    renderDirectory();
  }

  function initPaymentHistoryPage() {
    if (!document.getElementById('paymentHistoryPage')) return;
    const user = global.ChamaUI.requireAuth(['MEMBER']);
    if (!user) return;
    const state = global.ChamaStore.loadState();
    populateSidebarUser(user, state);

    const tbody = document.getElementById('historyTableBody');
    const statusFilter = document.getElementById('historyStatusFilter');

    function renderRows() {
      const freshState = global.ChamaStore.loadState();
      const filter = statusFilter ? statusFilter.value : 'ALL';
      const rows = freshState.transactions.filter(function (t) {
        return t.userId === user.id && (filter === 'ALL' || t.status === filter);
      });

      if (rows.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center py-4 text-chama-muted">No matching payment records found.</td></tr>';
        return;
      }

      tbody.innerHTML = rows.map(function (tx) {
        const stClass = tx.status === 'Successful' ? 'status-paid' : (tx.status === 'Pending' ? 'status-pending' : 'status-overdue');
        const actions = tx.status === 'Successful'
          ? '<button type="button" class="btn btn-chama-outline btn-chama-sm" data-view-receipt="' + tx.id + '">View Receipt</button>'
          : '<span class="small text-chama-muted">Unavailable</span>';
        return '<tr>' +
          '<td class="mono-figure">' + global.ChamaUI.formatDateTime(tx.date) + '</td>' +
          '<td>' + global.ChamaUI.escapeHtml(tx.monthLabel) + '</td>' +
          '<td class="text-end mono-figure">' + global.ChamaUI.formatKES(tx.amount) + '</td>' +
          '<td>' + global.ChamaUI.escapeHtml(tx.method) + '</td>' +
          '<td class="mono-figure">' + global.ChamaUI.escapeHtml(tx.reference) + '</td>' +
          '<td><span class="status-label ' + stClass + '">' + tx.status + '</span></td>' +
          '<td class="text-end">' + actions + '</td>' +
        '</tr>';
      }).join('');

      tbody.querySelectorAll('[data-view-receipt]').forEach(function (btn) {
        btn.addEventListener('click', function () {
          global.ChamaUI.openReceiptModal(btn.getAttribute('data-view-receipt'));
        });
      });
    }

    if (statusFilter) {
      statusFilter.addEventListener('change', renderRows);
    }
    renderRows();
  }

  function initMemberLoansPage() {
    if (!document.getElementById('memberLoansPage')) return;
    const user = global.ChamaUI.requireAuth(['MEMBER']);
    if (!user) return;

    function render() {
      const state = global.ChamaStore.loadState();
      populateSidebarUser(user, state);
      const summary = getMemberSummary(user, state);

      setText('loanSummaryBalance', global.ChamaUI.formatKES(summary.loanBalance));
      setText('loanSummaryNextDate', summary.activeLoan ? global.ChamaUI.formatDate(summary.activeLoan.nextRepaymentDate) : 'No active loan');
      setText('loanSummaryRepaid', global.ChamaUI.formatKES(summary.totalRepaid));

      const loansBody = document.getElementById('memberLoansListBody');
      if (loansBody) {
        loansBody.innerHTML = summary.myLoans.map(function (loan) {
          const stClass = loan.status === 'ACTIVE' || loan.status === 'COMPLETED'
            ? 'status-paid'
            : (loan.status === 'REJECTED' ? 'status-overdue' : 'status-pending');
          return '<tr>' +
            '<td class="mono-figure">' + loan.id + '</td>' +
            '<td>' + global.ChamaUI.escapeHtml(loan.purpose) + '</td>' +
            '<td class="text-end mono-figure">' + global.ChamaUI.formatKES(loan.principal) + '</td>' +
            '<td class="text-end mono-figure">' + global.ChamaUI.formatKES(loan.repaid) + '</td>' +
            '<td class="text-end mono-figure">' + global.ChamaUI.formatKES(loan.balance) + '</td>' +
            '<td class="mono-figure">' + global.ChamaUI.formatDate(loan.nextRepaymentDate) + '</td>' +
            '<td><span class="status-label ' + stClass + '">' + loan.status + '</span></td>' +
          '</tr>';
        }).join('');
      }

      const repBody = document.getElementById('memberRepaymentHistoryBody');
      if (repBody) {
        const allRepayments = [];
        summary.myLoans.forEach(function (l) {
          (l.repayments || []).forEach(function (r) {
            allRepayments.push({ loanId: l.id, date: r.date, amount: r.amount, reference: r.reference });
          });
        });
        repBody.innerHTML = allRepayments.length
          ? allRepayments.map(function (r) {
              return '<tr>' +
                '<td class="mono-figure">' + global.ChamaUI.formatDate(r.date) + '</td>' +
                '<td class="mono-figure">' + r.loanId + '</td>' +
                '<td class="mono-figure">' + r.reference + '</td>' +
                '<td class="text-end mono-figure">' + global.ChamaUI.formatKES(r.amount) + '</td>' +
              '</tr>';
            }).join('')
          : '<tr><td colspan="4" class="text-center py-3 text-chama-muted">No loan repayments recorded yet.</td></tr>';
      }
    }

    const loanForm = document.getElementById('loanApplicationForm');
    if (loanForm) {
      loanForm.addEventListener('submit', function (e) {
        e.preventDefault();
        const amount = Number(document.getElementById('loanAmountInput').value);
        const months = Number(document.getElementById('loanMonthsInput').value);
        const purpose = document.getElementById('loanPurposeInput').value;
        const alertEl = document.getElementById('loanAppAlert');

        if (amount < 1000) {
          alertEl.className = 'alert alert-danger small mb-3';
          alertEl.textContent = 'Minimum loan request is KES 1,000.';
          alertEl.classList.remove('d-none');
          return;
        }

        const res = global.ChamaStore.applyForLoan({
          userId: user.id,
          amount: amount,
          months: months,
          purpose: purpose
        });

        if (res.ok) {
          alertEl.className = 'alert alert-success small mb-3';
          alertEl.textContent = 'Loan application ' + res.loan.id + ' submitted for Chairperson & Treasurer review.';
          alertEl.classList.remove('d-none');
          loanForm.reset();
          render();
        }
      });
    }

    render();
  }

  function initMemberProfilePage() {
    if (!document.getElementById('memberProfilePage')) return;
    const user = global.ChamaUI.requireAuth(['MEMBER']);
    if (!user) return;

    function render() {
      const state = global.ChamaStore.loadState();
      const fresh = state.users.find(function (u) { return u.id === user.id; }) || user;
      populateSidebarUser(fresh, state);
      const summary = getMemberSummary(fresh, state);

      const photo = document.getElementById('profileAvatarImg');
      if (photo && fresh.avatar) photo.src = fresh.avatar;

      setText('profileDisplayName', fresh.fullName);
      setText('profileMemberNo', fresh.memberNo);
      setText('profileStatus', fresh.status);
      setText('profileJoinedDate', global.ChamaUI.formatDate(fresh.joinedDate));
      setText('profileSavingsTotal', global.ChamaUI.formatKES(fresh.savingsBalance));
      setText('profileLoanTotal', global.ChamaUI.formatKES(summary.loanBalance));

      document.getElementById('profileFullName').value = fresh.fullName;
      document.getElementById('profilePhone').value = fresh.phone;
      document.getElementById('profileEmail').value = fresh.email;
    }

    const editForm = document.getElementById('editProfileForm');
    if (editForm) {
      editForm.addEventListener('submit', function (e) {
        e.preventDefault();
        const res = global.ChamaStore.updateProfile(user.id, {
          fullName: document.getElementById('profileFullName').value,
          phone: document.getElementById('profilePhone').value,
          email: document.getElementById('profileEmail').value
        });
        const alertEl = document.getElementById('profileAlert');
        if (res.ok && alertEl) {
          alertEl.className = 'alert alert-success small mb-3';
          alertEl.textContent = 'Personal information updated in local prototype storage.';
          alertEl.classList.remove('d-none');
          render();
        }
      });
    }

    const pwForm = document.getElementById('changePasswordForm');
    if (pwForm) {
      pwForm.addEventListener('submit', function (e) {
        e.preventDefault();
        const currentPw = document.getElementById('currentPassword').value;
        const newPw = document.getElementById('newPassword').value;
        const confirmPw = document.getElementById('confirmNewPassword').value;
        const alertEl = document.getElementById('passwordAlert');

        if (newPw.length < 6 || newPw !== confirmPw) {
          alertEl.className = 'alert alert-danger small mb-3';
          alertEl.textContent = 'New passwords must match and be at least 6 characters.';
          alertEl.classList.remove('d-none');
          return;
        }

        const res = global.ChamaStore.changePassword(user.id, currentPw, newPw);
        if (!res.ok) {
          alertEl.className = 'alert alert-danger small mb-3';
          alertEl.textContent = res.message;
          alertEl.classList.remove('d-none');
          return;
        }
        alertEl.className = 'alert alert-success small mb-3';
        alertEl.textContent = 'Password updated successfully.';
        alertEl.classList.remove('d-none');
        pwForm.reset();
      });
    }

    render();
  }

  document.addEventListener('DOMContentLoaded', function () {
    initPendingPage();
    initChairpersonDashboard();
    initTreasurerDashboard();
    initSecretaryDashboard();
    initMemberDashboard();
    initChamaMembersPage();
    initPaymentHistoryPage();
    initMemberLoansPage();
    initMemberProfilePage();
  });
})(window);
