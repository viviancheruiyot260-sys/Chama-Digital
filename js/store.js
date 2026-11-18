/**
 * Chama Digital — Client-Side State Store (localStorage Prototype)
 *
 * NOTE: This module simulates persistence in the browser using localStorage.
 * In production, replace these methods with API calls to a Django backend,
 * M-Pesa Daraja API (STK Push), Bank EFT reconciliation, SMS gateway, and Email service.
 */
(function (global) {
  'use strict';

  const STORAGE_KEY = 'chama_digital_state_v2';

  const DEFAULT_STATE = {
    chama: {
      name: 'Umoja Table Banking Chama',
      inviteCode: 'UMJ-2026',
      monthlyContribution: 12500,
      nextContributionDate: '2026-11-30',
      ussdCode: '*384*240#',
      paybill: '522522',
      bankName: 'Kenya Commercial Bank (KCB)',
      bankAccount: '1184-2093-5510'
    },
    currentUserId: null,
    users: [
      {
        id: 'usr_chair',
        fullName: 'Samuel Kamau',
        email: 'chairperson@chamadigital.co.ke',
        phone: '+254 711 223 344',
        nationalId: '24501190',
        password: 'password123',
        role: 'CHAIRPERSON',
        chamaName: 'Umoja Table Banking Chama',
        status: 'ACTIVE',
        memberNo: 'CHM-001',
        joinedDate: '2023-01-10',
        savingsBalance: 410000,
        monthlyTarget: 12500,
        avatar: 'images/avatar-treasurer-david.jpg'
      },
      {
        id: 'usr_treasurer',
        fullName: 'David Ochieng',
        email: 'treasurer@chamadigital.co.ke',
        phone: '+254 722 108 440',
        nationalId: '26190442',
        password: 'password123',
        role: 'TREASURER',
        chamaName: 'Umoja Table Banking Chama',
        status: 'ACTIVE',
        memberNo: 'CHM-002',
        joinedDate: '2023-01-10',
        savingsBalance: 385000,
        monthlyTarget: 12500,
        avatar: 'images/avatar-treasurer-david.jpg'
      },
      {
        id: 'usr_secretary',
        fullName: 'Grace Muthoni',
        email: 'secretary@chamadigital.co.ke',
        phone: '+254 723 991 100',
        nationalId: '27345811',
        password: 'password123',
        role: 'SECRETARY',
        chamaName: 'Umoja Table Banking Chama',
        status: 'ACTIVE',
        memberNo: 'CHM-003',
        joinedDate: '2023-02-04',
        savingsBalance: 340000,
        monthlyTarget: 12500,
        avatar: 'images/avatar-member-amina.jpg'
      },
      {
        id: 'usr_amina',
        fullName: 'Amina Wanjiku',
        email: 'amina@chamadigital.co.ke',
        phone: '+254 712 345 678',
        nationalId: '28904112',
        password: 'password123',
        role: 'MEMBER',
        chamaName: 'Umoja Table Banking Chama',
        status: 'ACTIVE',
        memberNo: 'CHM-018',
        joinedDate: '2024-01-15',
        savingsBalance: 312450,
        monthlyTarget: 12500,
        avatar: 'images/avatar-member-amina.jpg'
      },
      {
        id: 'usr_brian',
        fullName: 'Brian Kiprop',
        email: 'brian@chamadigital.co.ke',
        phone: '+254 718 334 455',
        nationalId: '29110234',
        password: 'password123',
        role: 'MEMBER',
        chamaName: 'Umoja Table Banking Chama',
        status: 'ACTIVE',
        memberNo: 'CHM-004',
        joinedDate: '2023-06-10',
        savingsBalance: 310000,
        monthlyTarget: 12500,
        avatar: 'images/avatar-treasurer-david.jpg'
      },
      {
        id: 'usr_peter',
        fullName: 'Peter Otieno',
        email: 'peter@chamadigital.co.ke',
        phone: '+254 725 881 200',
        nationalId: '30118902',
        password: 'password123',
        role: 'MEMBER',
        chamaName: 'Umoja Table Banking Chama',
        status: 'ACTIVE',
        memberNo: 'CHM-011',
        joinedDate: '2024-03-20',
        savingsBalance: 212500,
        monthlyTarget: 12500,
        avatar: 'images/avatar-treasurer-david.jpg'
      },
      {
        id: 'usr_faith',
        fullName: 'Faith Njeri Kamau',
        email: 'faith@example.co.ke',
        phone: '+254 712 884 190',
        nationalId: '29481022',
        password: 'password123',
        role: 'MEMBER',
        chamaName: 'Umoja Table Banking Chama',
        status: 'PENDING',
        memberNo: 'Pending',
        joinedDate: '2026-11-18',
        savingsBalance: 0,
        monthlyTarget: 12500,
        avatar: 'images/avatar-member-amina.jpg'
      },
      {
        id: 'usr_daniel',
        fullName: 'Daniel Kipchoge',
        email: 'daniel.k@example.co.ke',
        phone: '+254 720 443 211',
        nationalId: '31094518',
        password: 'password123',
        role: 'MEMBER',
        chamaName: 'Umoja Table Banking Chama',
        status: 'PENDING',
        memberNo: 'Pending',
        joinedDate: '2026-11-17',
        savingsBalance: 0,
        monthlyTarget: 12500,
        avatar: 'images/avatar-treasurer-david.jpg'
      }
    ],
    transactions: [
      {
        id: 'tx_105',
        receiptNo: 'RCT-2026-8841',
        userId: 'usr_amina',
        memberName: 'Amina Wanjiku',
        phone: '+254 712 345 678',
        email: 'amina@chamadigital.co.ke',
        month: '2026-10',
        monthLabel: 'October 2026',
        type: 'Monthly Contribution',
        method: 'M-Pesa STK Push',
        amount: 12500,
        reference: 'SI62B88P1M',
        date: '2026-10-15T10:18:00',
        status: 'Successful',
        emailNotified: true,
        smsNotified: true
      },
      {
        id: 'tx_104',
        receiptNo: 'RCT-2026-8790',
        userId: 'usr_amina',
        memberName: 'Amina Wanjiku',
        phone: '+254 712 345 678',
        email: 'amina@chamadigital.co.ke',
        month: '2026-11',
        monthLabel: 'Loan Installment (Nov)',
        type: 'Loan Repayment',
        method: 'Bank Transfer (EFT / PesaLink)',
        amount: 15000,
        reference: 'BNK79R42T8',
        date: '2026-11-05T14:22:00',
        status: 'Successful',
        emailNotified: true,
        smsNotified: true
      },
      {
        id: 'tx_103',
        receiptNo: 'RCT-2026-8612',
        userId: 'usr_amina',
        memberName: 'Amina Wanjiku',
        phone: '+254 712 345 678',
        email: 'amina@chamadigital.co.ke',
        month: '2026-09',
        monthLabel: 'September 2026',
        type: 'USSD Payment',
        method: 'USSD Payment',
        amount: 12500,
        reference: 'SH41D07K9X',
        date: '2026-09-14T09:05:00',
        status: 'Successful',
        emailNotified: true,
        smsNotified: true
      },
      {
        id: 'tx_102',
        receiptNo: 'RCT-2026-8835',
        userId: 'usr_brian',
        memberName: 'Brian Kiprop',
        phone: '+254 718 334 455',
        email: 'brian@chamadigital.co.ke',
        month: '2026-11',
        monthLabel: 'November 2026',
        type: 'Monthly Contribution',
        method: 'M-Pesa STK Push',
        amount: 12500,
        reference: 'SJ83M11Q4R',
        date: '2026-11-12T16:40:00',
        status: 'Successful',
        emailNotified: true,
        smsNotified: true
      },
      {
        id: 'tx_101',
        receiptNo: 'RCT-2026-8810',
        userId: 'usr_secretary',
        memberName: 'Grace Muthoni',
        phone: '+254 723 991 100',
        email: 'secretary@chamadigital.co.ke',
        month: '2026-11',
        monthLabel: 'November 2026',
        type: 'Monthly Contribution',
        method: 'Bank Deposit / Standing Order',
        amount: 12500,
        reference: 'BNK81P04N2',
        date: '2026-11-10T11:12:00',
        status: 'Successful',
        emailNotified: true,
        smsNotified: true
      }
    ],
    treasurerNotifications: [
      {
        id: 'notif_2',
        message: 'Brian Kiprop paid KES 12,500 for November 2026 via M-Pesa STK Push (Ref: SJ83M11Q4R).',
        date: '2026-11-12T16:40:00',
        unread: true
      },
      {
        id: 'notif_1',
        message: 'Grace Muthoni paid KES 12,500 for November 2026 via Bank Deposit / Standing Order (Ref: BNK81P04N2).',
        date: '2026-11-10T11:12:00',
        unread: false
      }
    ],
    loans: [
      {
        id: 'LN-2026-041',
        userId: 'usr_amina',
        memberName: 'Amina Wanjiku',
        purpose: 'Retail Inventory Expansion',
        principal: 120000,
        repaid: 75000,
        balance: 45000,
        interestRate: '1.5% / month',
        nextRepaymentDate: '2026-12-05',
        installmentAmount: 15000,
        status: 'ACTIVE',
        appliedDate: '2026-06-01',
        repayments: [
          { date: '2026-11-05', amount: 15000, reference: 'BNK79R42T8' },
          { date: '2026-10-05', amount: 15000, reference: 'SI55H19V3W' },
          { date: '2026-09-05', amount: 15000, reference: 'SH32K91A2B' },
          { date: '2026-08-05', amount: 15000, reference: 'SG19M44C8D' },
          { date: '2026-07-05', amount: 15000, reference: 'SF08P12E5F' }
        ]
      },
      {
        id: 'LN-2025-012',
        userId: 'usr_amina',
        memberName: 'Amina Wanjiku',
        purpose: 'School Fees Bridge Loan',
        principal: 60000,
        repaid: 60000,
        balance: 0,
        interestRate: '1.5% / month',
        nextRepaymentDate: 'Completed',
        installmentAmount: 15000,
        status: 'COMPLETED',
        appliedDate: '2025-01-20',
        repayments: []
      },
      {
        id: 'LN-2026-038',
        userId: 'usr_brian',
        memberName: 'Brian Kiprop',
        purpose: 'Agribusiness Greenhouse Setup',
        principal: 200000,
        repaid: 110400,
        balance: 89600,
        interestRate: '1.5% / month',
        nextRepaymentDate: '2026-12-12',
        installmentAmount: 18400,
        status: 'ACTIVE',
        appliedDate: '2026-05-10',
        repayments: []
      },
      {
        id: 'LN-2026-052',
        userId: 'usr_peter',
        memberName: 'Peter Otieno',
        purpose: 'Dairy Farming Equipment',
        principal: 80000,
        repaid: 0,
        balance: 80000,
        interestRate: '1.5% / month',
        nextRepaymentDate: 'Pending Approval',
        installmentAmount: 14000,
        status: 'PENDING',
        appliedDate: '2026-11-16',
        repayments: []
      }
    ],
    meetings: [
      {
        id: 'mtg_1',
        eventType: 'Meeting',
        title: 'Monthly Table-Banking & Loan Review Meeting',
        date: '2026-11-28',
        time: '10:00 AM EAT',
        venue: 'Umoja Community Hall, Nairobi',
        description: 'Review November contributions, verify bank reconciliations, and approve December merry-go-round rotation.',
        status: 'Scheduled',
        attendanceSummary: '18 of 24 RSVPs confirmed'
      },
      {
        id: 'mtg_2',
        eventType: 'Important Occasion',
        title: 'Annual General Meeting (AGM) & Dividend Payout Day',
        date: '2026-12-12',
        time: '09:30 AM EAT',
        venue: 'Sarova Panafric / Hybrid Zoom',
        description: 'Annual financial audit presentation, 2026 dividend distribution vote, and group celebration lunch.',
        status: 'Important Occasion',
        attendanceSummary: '21 of 24 RSVPs confirmed'
      },
      {
        id: 'mtg_3',
        eventType: 'Important Occasion',
        title: 'Kamulu Plot Investment Site Visit & Title Verification',
        date: '2026-12-19',
        time: '08:30 AM EAT',
        venue: 'Kamulu Phase 2, Kangundo Road',
        description: 'Joint chama land investment inspection with group surveyor and legal representative.',
        status: 'Important Occasion',
        attendanceSummary: '14 of 24 RSVPs confirmed'
      }
    ],
    announcements: [
      {
        id: 'ann_1',
        title: 'November Contribution Window Open Until 30 Nov',
        body: 'Members can settle November contributions via M-Pesa (STK Push / Paybill 522522), Bank Transfer (KCB 1184-2093-5510), or dial *384*240# for USSD.',
        author: 'David Ochieng (Treasurer)',
        date: '2026-11-10'
      },
      {
        id: 'ann_2',
        title: 'AGM & End-of-Year Dividend Preparation',
        body: 'Ensure all November dues are settled before 30 Nov 2026 so your dividend share is included in the AGM schedule on 12 Dec.',
        author: 'Grace Muthoni (Secretary)',
        date: '2026-11-08'
      },
      {
        id: 'ann_3',
        title: 'New Member Verification Guidelines',
        body: 'All newly registered members must complete National ID entry and await Chairperson approval before full portal access.',
        author: 'Samuel Kamau (Chairperson)',
        date: '2026-11-05'
      }
    ]
  };

  function clone(obj) {
    return JSON.parse(JSON.stringify(obj));
  }

  function loadState() {
    try {
      const raw = global.localStorage.getItem(STORAGE_KEY);
      if (!raw) {
        const initial = clone(DEFAULT_STATE);
        saveState(initial);
        return initial;
      }
      const parsed = JSON.parse(raw);
      if (!Array.isArray(parsed.treasurerNotifications)) {
        parsed.treasurerNotifications = clone(DEFAULT_STATE.treasurerNotifications);
      }
      return parsed;
    } catch (err) {
      return clone(DEFAULT_STATE);
    }
  }

  function saveState(state) {
    try {
      global.localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch (err) {
      console.warn('localStorage unavailable:', err);
    }
  }

  function getCurrentUser() {
    const state = loadState();
    if (!state.currentUserId) return null;
    return state.users.find(function (u) { return u.id === state.currentUserId; }) || null;
  }

  function setCurrentUser(userId) {
    const state = loadState();
    state.currentUserId = userId;
    saveState(state);
  }

  function logout() {
    setCurrentUser(null);
  }

  function authenticate(identifier, password) {
    const state = loadState();
    const norm = (identifier || '').trim().toLowerCase();
    const phoneNorm = norm.replace(/\s+/g, '');
    const user = state.users.find(function (u) {
      const uEmail = (u.email || '').toLowerCase();
      const uPhone = (u.phone || '').toLowerCase().replace(/\s+/g, '');
      return (uEmail === norm || uPhone === phoneNorm) && u.password === password;
    });
    if (!user) return { ok: false, reason: 'INVALID_CREDENTIALS' };
    if (user.status === 'PENDING') {
      state.currentUserId = user.id;
      saveState(state);
      return { ok: false, reason: 'PENDING_APPROVAL', user: user };
    }
    if (user.status === 'REJECTED') {
      return { ok: false, reason: 'REJECTED', user: user };
    }
    state.currentUserId = user.id;
    saveState(state);
    return { ok: true, user: user };
  }

  function registerMember(payload) {
    const state = loadState();
    const emailNorm = payload.email.trim().toLowerCase();
    const exists = state.users.some(function (u) { return u.email.toLowerCase() === emailNorm; });
    if (exists) {
      return { ok: false, message: 'An account with this email address already exists.' };
    }
    const newUser = {
      id: 'usr_' + Date.now(),
      fullName: payload.fullName.trim(),
      email: payload.email.trim(),
      phone: payload.phone.trim(),
      nationalId: payload.nationalId.trim(),
      inviteCode: payload.inviteCode.trim() || state.chama.inviteCode,
      chamaName: state.chama.name,
      password: payload.password,
      role: 'MEMBER',
      status: 'PENDING',
      memberNo: 'Pending',
      joinedDate: new Date().toISOString().slice(0, 10),
      savingsBalance: 0,
      monthlyTarget: state.chama.monthlyContribution,
      avatar: 'images/avatar-member-amina.jpg'
    };
    state.users.unshift(newUser);
    state.currentUserId = newUser.id;
    saveState(state);
    return { ok: true, user: newUser };
  }

  function registerOfficial(payload) {
    const state = loadState();
    const emailNorm = payload.email.trim().toLowerCase();
    const exists = state.users.some(function (u) { return u.email.toLowerCase() === emailNorm; });
    if (exists) {
      return { ok: false, message: 'An account with this email address already exists.' };
    }
    if (payload.chamaName && payload.chamaName.trim()) {
      state.chama.name = payload.chamaName.trim();
    }
    const roleUpper = (payload.role || 'TREASURER').toUpperCase();
    const newOfficial = {
      id: 'usr_' + Date.now(),
      fullName: payload.fullName.trim(),
      email: payload.email.trim(),
      phone: payload.phone.trim(),
      nationalId: 'OFFICIAL',
      chamaName: state.chama.name,
      password: payload.password,
      role: roleUpper,
      status: 'ACTIVE',
      memberNo: 'CHM-' + String(state.users.length + 1).padStart(3, '0'),
      joinedDate: new Date().toISOString().slice(0, 10),
      savingsBalance: 0,
      monthlyTarget: state.chama.monthlyContribution,
      avatar: roleUpper === 'SECRETARY' ? 'images/avatar-member-amina.jpg' : 'images/avatar-treasurer-david.jpg'
    };
    state.users.unshift(newOfficial);
    state.currentUserId = newOfficial.id;
    saveState(state);
    return { ok: true, user: newOfficial };
  }

  function setMemberStatus(userId, status) {
    const state = loadState();
    const target = state.users.find(function (u) { return u.id === userId; });
    if (!target) return null;
    target.status = status;
    if (status === 'ACTIVE' && target.memberNo === 'Pending') {
      const count = state.users.filter(function (u) { return u.status === 'ACTIVE'; }).length;
      target.memberNo = 'CHM-' + String(count + 18).padStart(3, '0');
    }
    saveState(state);
    return target;
  }

  function hasPaidMonth(userId, monthValue) {
    const state = loadState();
    return state.transactions.some(function (tx) {
      return tx.userId === userId &&
        tx.month === monthValue &&
        tx.type === 'Monthly Contribution' &&
        tx.status === 'Successful';
    });
  }

  function generatePaymentRef(method) {
    const prefix = (method || '').toLowerCase().indexOf('bank') !== -1 ? 'BNK' : 'SK';
    const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
    let out = prefix;
    for (let i = 0; i < 8; i++) {
      out += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return out;
  }

  /**
   * Simulates payment processing (M-Pesa & Bank methods), updates member/group balances,
   * and notifies the Treasurer.
   * Future Django + Daraja / Bank API integration point.
   */
  function recordPayment(payload) {
    const state = loadState();
    const user = state.users.find(function (u) { return u.id === payload.userId; });
    if (!user) return { ok: false, message: 'Member account not found.' };

    const refCode = (payload.customRef && payload.customRef.trim())
      ? payload.customRef.trim().toUpperCase()
      : generatePaymentRef(payload.method);

    const tx = {
      id: 'tx_' + Date.now(),
      receiptNo: 'RCT-2026-' + String(Math.floor(1000 + Math.random() * 9000)),
      userId: user.id,
      memberName: user.fullName,
      phone: payload.phone,
      email: user.email,
      month: payload.month,
      monthLabel: payload.monthLabel,
      type: payload.type,
      method: payload.method,
      amount: Number(payload.amount),
      reference: refCode,
      date: new Date().toISOString(),
      status: payload.simulatedOutcome || 'Successful',
      emailNotified: Boolean(payload.notifyEmail),
      smsNotified: Boolean(payload.notifySms)
    };

    state.transactions.unshift(tx);

    if (tx.status === 'Successful') {
      if (tx.type === 'Loan Repayment') {
        const activeLoan = state.loans.find(function (l) {
          return l.userId === user.id && l.status === 'ACTIVE';
        });
        if (activeLoan) {
          const payAmt = Math.min(tx.amount, activeLoan.balance);
          activeLoan.repaid += payAmt;
          activeLoan.balance -= payAmt;
          activeLoan.repayments.unshift({
            date: tx.date.slice(0, 10),
            amount: payAmt,
            reference: tx.reference
          });
          if (activeLoan.balance <= 0) {
            activeLoan.balance = 0;
            activeLoan.status = 'COMPLETED';
            activeLoan.nextRepaymentDate = 'Completed';
          }
        }
      } else {
        user.savingsBalance = Number(user.savingsBalance || 0) + tx.amount;
      }

      // Notify Treasurer immediately
      state.treasurerNotifications.unshift({
        id: 'notif_' + Date.now(),
        message: user.fullName + ' paid KES ' + Number(tx.amount).toLocaleString('en-KE') +
          ' (' + tx.type + ' · ' + tx.monthLabel + ') via ' + tx.method + ' (Ref: ' + tx.reference + ').',
        date: tx.date,
        unread: true
      });
    }

    saveState(state);
    return { ok: true, transaction: tx, user: user };
  }

  function markTreasurerNotificationsRead() {
    const state = loadState();
    state.treasurerNotifications.forEach(function (n) { n.unread = false; });
    saveState(state);
  }

  function applyForLoan(payload) {
    const state = loadState();
    const user = state.users.find(function (u) { return u.id === payload.userId; });
    if (!user) return { ok: false, message: 'Member not found.' };
    const principal = Number(payload.amount);
    const months = Number(payload.months) || 6;
    const newLoan = {
      id: 'LN-2026-' + String(Math.floor(100 + Math.random() * 899)),
      userId: user.id,
      memberName: user.fullName,
      purpose: payload.purpose.trim(),
      principal: principal,
      repaid: 0,
      balance: principal,
      interestRate: '1.5% / month',
      nextRepaymentDate: 'Pending Approval',
      installmentAmount: Math.ceil((principal * 1.09) / months),
      status: 'PENDING',
      appliedDate: new Date().toISOString().slice(0, 10),
      repayments: []
    };
    state.loans.unshift(newLoan);
    saveState(state);
    return { ok: true, loan: newLoan };
  }

  function setLoanStatus(loanId, status) {
    const state = loadState();
    const loan = state.loans.find(function (l) { return l.id === loanId; });
    if (!loan) return null;
    loan.status = status;
    if (status === 'ACTIVE') {
      const next = new Date();
      next.setDate(next.getDate() + 30);
      loan.nextRepaymentDate = next.toISOString().slice(0, 10);
    } else if (status === 'REJECTED') {
      loan.nextRepaymentDate = 'Declined';
    }
    saveState(state);
    return loan;
  }

  function addAnnouncement(payload) {
    const state = loadState();
    const item = {
      id: 'ann_' + Date.now(),
      title: payload.title.trim(),
      body: payload.body.trim(),
      author: payload.author,
      date: new Date().toISOString().slice(0, 10)
    };
    state.announcements.unshift(item);
    saveState(state);
    return item;
  }

  function addMeeting(payload) {
    const state = loadState();
    const eventType = payload.eventType || 'Meeting';
    const item = {
      id: 'mtg_' + Date.now(),
      eventType: eventType,
      title: payload.title.trim(),
      date: payload.date,
      time: payload.time.trim(),
      venue: payload.venue.trim(),
      description: (payload.description || '').trim() || 'Scheduled chama event.',
      status: eventType === 'Important Occasion' ? 'Important Occasion' : 'Scheduled',
      attendanceSummary: 'Open for member RSVP'
    };
    state.meetings.unshift(item);
    state.meetings.sort(function (a, b) {
      return String(a.date).localeCompare(String(b.date));
    });
    saveState(state);
    return item;
  }

  function updateProfile(userId, payload) {
    const state = loadState();
    const user = state.users.find(function (u) { return u.id === userId; });
    if (!user) return { ok: false, message: 'User not found.' };
    if (payload.fullName) user.fullName = payload.fullName.trim();
    if (payload.phone) user.phone = payload.phone.trim();
    if (payload.email) user.email = payload.email.trim();
    saveState(state);
    return { ok: true, user: user };
  }

  function changePassword(userId, currentPw, newPw) {
    const state = loadState();
    const user = state.users.find(function (u) { return u.id === userId; });
    if (!user) return { ok: false, message: 'User not found.' };
    if (user.password !== currentPw) {
      return { ok: false, message: 'Current password is incorrect.' };
    }
    user.password = newPw;
    saveState(state);
    return { ok: true };
  }

  function resetDemoData() {
    const initial = clone(DEFAULT_STATE);
    saveState(initial);
    return initial;
  }

  global.ChamaStore = {
    loadState: loadState,
    saveState: saveState,
    getCurrentUser: getCurrentUser,
    setCurrentUser: setCurrentUser,
    logout: logout,
    authenticate: authenticate,
    registerMember: registerMember,
    registerOfficial: registerOfficial,
    setMemberStatus: setMemberStatus,
    hasPaidMonth: hasPaidMonth,
    recordPayment: recordPayment,
    markTreasurerNotificationsRead: markTreasurerNotificationsRead,
    applyForLoan: applyForLoan,
    setLoanStatus: setLoanStatus,
    addAnnouncement: addAnnouncement,
    addMeeting: addMeeting,
    updateProfile: updateProfile,
    changePassword: changePassword,
    resetDemoData: resetDemoData
  };
})(window);
