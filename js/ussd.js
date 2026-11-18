/**
 * Chama Digital — Interactive USSD Simulator (*384*240#)
 * Frontend demonstration only. Production connects to a telecom USSD gateway.
 */
(function (global) {
  'use strict';

  function initUssdSimulator(containerId) {
    const root = document.getElementById(containerId);
    if (!root) return;

    const screenEl = root.querySelector('[data-ussd-screen]');
    const inputEl = root.querySelector('[data-ussd-input]');
    const sendBtn = root.querySelector('[data-ussd-send]');
    const resetBtn = root.querySelector('[data-ussd-reset]');
    const quickButtons = root.querySelectorAll('[data-ussd-choice]');

    let currentStep = 'MAIN';

    function getMemberContext() {
      const state = global.ChamaStore.loadState();
      const current = global.ChamaStore.getCurrentUser();
      const member = (current && current.role === 'MEMBER' && current.status === 'ACTIVE')
        ? current
        : state.users.find(function (u) { return u.id === 'usr_amina'; }) || state.users[0];
      const activeLoan = state.loans.find(function (l) {
        return l.userId === member.id && l.status === 'ACTIVE';
      });
      const txs = state.transactions.filter(function (t) { return t.userId === member.id; }).slice(0, 3);
      return { state: state, member: member, activeLoan: activeLoan, txs: txs };
    }

    function showMainMenu() {
      currentStep = 'MAIN';
      if (screenEl) {
        screenEl.textContent = [
          'Welcome to Chama Digital',
          '1. Check Savings',
          '2. Check Loan Balance',
          '3. Make Contribution',
          '4. Payment History',
          '5. Exit'
        ].join('\n');
      }
      if (inputEl) inputEl.value = '';
    }

    function handleChoice(choiceRaw) {
      const choice = String(choiceRaw || '').trim();
      const ctx = getMemberContext();

      if (currentStep === 'CONFIRM_CONTRIBUTION') {
        if (choice === '1') {
          const res = global.ChamaStore.recordPayment({
            userId: ctx.member.id,
            phone: ctx.member.phone,
            month: '2026-11',
            monthLabel: 'November 2026 (USSD)',
            type: 'Monthly Contribution',
            method: 'USSD Payment',
            amount: ctx.state.chama.monthlyContribution,
            simulatedOutcome: 'Successful',
            notifyEmail: true,
            notifySms: true
          });
          currentStep = 'RESULT';
          if (res.ok) {
            screenEl.textContent = [
              'Contribution Confirmed!',
              'Amount: ' + global.ChamaUI.formatKES(res.transaction.amount),
              'Ref: ' + res.transaction.reference,
              'New Savings: ' + global.ChamaUI.formatKES(res.user.savingsBalance),
              'SMS receipt dispatched (Demo).',
              '0. Back to Main Menu'
            ].join('\n');
          }
          return;
        }
        showMainMenu();
        return;
      }

      if (choice === '0') {
        showMainMenu();
        return;
      }

      switch (choice) {
        case '1':
          currentStep = 'RESULT';
          screenEl.textContent = [
            'Savings Summary (' + ctx.member.fullName + ')',
            'Total Savings: ' + global.ChamaUI.formatKES(ctx.member.savingsBalance),
            'Monthly Target: ' + global.ChamaUI.formatKES(ctx.state.chama.monthlyContribution),
            'Next Due Date: ' + global.ChamaUI.formatDate(ctx.state.chama.nextContributionDate),
            '0. Back to Main Menu'
          ].join('\n');
          break;
        case '2':
          currentStep = 'RESULT';
          screenEl.textContent = ctx.activeLoan
            ? [
                'Loan Account: ' + ctx.activeLoan.id,
                'Outstanding: ' + global.ChamaUI.formatKES(ctx.activeLoan.balance),
                'Next Installment: ' + global.ChamaUI.formatKES(ctx.activeLoan.installmentAmount),
                'Next Due Date: ' + global.ChamaUI.formatDate(ctx.activeLoan.nextRepaymentDate),
                '0. Back to Main Menu'
              ].join('\n')
            : 'No active outstanding loans.\n0. Back to Main Menu';
          break;
        case '3':
          currentStep = 'CONFIRM_CONTRIBUTION';
          screenEl.textContent = [
            'Make Contribution via M-Pesa',
            'Group: ' + ctx.state.chama.name,
            'Amount: ' + global.ChamaUI.formatKES(ctx.state.chama.monthlyContribution),
            'Phone: ' + ctx.member.phone,
            '1. Confirm & Simulate M-Pesa Prompt',
            '0. Cancel'
          ].join('\n');
          break;
        case '4':
          currentStep = 'RESULT';
          if (ctx.txs.length === 0) {
            screenEl.textContent = 'No recent transactions found.\n0. Back to Main Menu';
          } else {
            const lines = ['Recent Payments:'];
            ctx.txs.forEach(function (t, i) {
              lines.push((i + 1) + '. ' + t.monthLabel + ' - ' + global.ChamaUI.formatKES(t.amount) + ' (' + t.reference + ')');
            });
            lines.push('0. Back to Main Menu');
            screenEl.textContent = lines.join('\n');
          }
          break;
        case '5':
          currentStep = 'EXITED';
          screenEl.textContent = 'Thank you for using Chama Digital.\nDial *384*240# anytime without internet.\n\nPress Reset to start a new session.';
          break;
        default:
          showMainMenu();
          break;
      }
      if (inputEl) inputEl.value = '';
    }

    quickButtons.forEach(function (btn) {
      btn.addEventListener('click', function () {
        handleChoice(btn.getAttribute('data-ussd-choice'));
      });
    });

    if (sendBtn && inputEl) {
      sendBtn.addEventListener('click', function () {
        handleChoice(inputEl.value);
      });
      inputEl.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') {
          e.preventDefault();
          handleChoice(inputEl.value);
        }
      });
    }

    if (resetBtn) {
      resetBtn.addEventListener('click', showMainMenu);
    }

    showMainMenu();
  }

  document.addEventListener('DOMContentLoaded', function () {
    initUssdSimulator('ussdSimulatorHome');
    initUssdSimulator('ussdSimulatorMember');
  });
})(window);
