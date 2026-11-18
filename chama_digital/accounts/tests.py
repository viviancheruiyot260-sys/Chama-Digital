from datetime import date
from decimal import Decimal
from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import ChamaGroup, User
from loans.models import LoanApplication
from notifications.models import TreasurerNotification
from payments.models import PaymentTransaction, Receipt
from savings.models import SavingsAccount


class ChamaDigitalWorkflowTests(TestCase):
    def setUp(self):
        self.chama = ChamaGroup.objects.create(
            name='Umoja Test Chama',
            invite_code='TST-2026',
            official_invite_code='TST-OFF-2026',
            monthly_contribution=Decimal('10000.00'),
            next_contribution_date=date(2026, 11, 30),
        )
        self.other_chama = ChamaGroup.objects.create(
            name='Other Chama',
            invite_code='OTH-2026',
            official_invite_code='OTH-OFF-2026',
        )
        self.pw = 'StrongPass2026!'
        self.chair = User.objects.create_user(
            username='chair@test.co.ke',
            email='chair@test.co.ke',
            password=self.pw,
            full_name='Chair Test',
            phone_number='+254700000001',
            chama=self.chama,
            role=User.Role.CHAIRPERSON,
            approval_status=User.ApprovalStatus.ACTIVE,
            member_number='CHM-001',
        )
        self.treasurer = User.objects.create_user(
            username='treasurer@test.co.ke',
            email='treasurer@test.co.ke',
            password=self.pw,
            full_name='Treasurer Test',
            phone_number='+254700000002',
            chama=self.chama,
            role=User.Role.TREASURER,
            approval_status=User.ApprovalStatus.ACTIVE,
            member_number='CHM-002',
        )
        self.member = User.objects.create_user(
            username='member@test.co.ke',
            email='member@test.co.ke',
            password=self.pw,
            full_name='Member Test',
            phone_number='+254700000003',
            chama=self.chama,
            role=User.Role.MEMBER,
            approval_status=User.ApprovalStatus.ACTIVE,
            member_number='CHM-003',
        )
        SavingsAccount.objects.create(member=self.member, chama=self.chama, monthly_target=Decimal('10000.00'))

    def test_pending_member_cannot_access_member_dashboard_until_approved(self):
        c = Client()
        resp = c.post(reverse('accounts:register') + '?tab=member', {
            'registration_type': 'member',
            'full_name': 'Pending Alice',
            'email': 'alice@test.co.ke',
            'phone_number': '+254700000099',
            'national_id': '30001122',
            'chama_invite_code': 'TST-2026',
            'password': self.pw,
            'confirm_password': self.pw,
        })
        self.assertRedirects(resp, reverse('accounts:pending_approval'))
        alice = User.objects.get(email='alice@test.co.ke')
        self.assertEqual(alice.approval_status, User.ApprovalStatus.PENDING)

        # Blocked from member dashboard while pending
        dash_resp = c.get(reverse('savings:member_dashboard'))
        self.assertRedirects(dash_resp, reverse('accounts:pending_approval'))

        # Chairperson approves Alice
        c.force_login(self.chair)
        c.post(reverse('members:review_application', args=[alice.pk]), {'decision': 'approve'})
        alice.refresh_from_db()
        self.assertEqual(alice.approval_status, User.ApprovalStatus.ACTIVE)
        self.assertTrue(alice.member_number.startswith('CHM-'))

        c.force_login(alice)
        self.assertEqual(c.get(reverse('savings:member_dashboard')).status_code, 200)

    def test_official_registration_requires_valid_code(self):
        c = Client()
        resp = c.post(reverse('accounts:register') + '?tab=official', {
            'registration_type': 'official',
            'full_name': 'Fake Chair',
            'email': 'fake@test.co.ke',
            'phone_number': '+254700000055',
            'chama_name': 'Umoja Test Chama',
            'role': User.Role.CHAIRPERSON,
            'official_code': 'WRONG-CODE',
            'password': self.pw,
            'confirm_password': self.pw,
        })
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(User.objects.filter(email='fake@test.co.ke').exists())

    def test_mpesa_and_bank_payment_verification_and_pdf_receipt(self):
        c = Client()
        c.force_login(self.member)

        # Simulated M-Pesa confirmation updates savings + receipt + treasurer notification
        resp = c.post(reverse('payments:make_payment') + '?method=mpesa', {
            'channel_group': 'mpesa',
            'contribution_month': '2026-10',
            'amount': '10000.00',
            'phone_number': '+254700000003',
            'payment_method': PaymentTransaction.PaymentMethod.MPESA_STK,
            'payment_type': PaymentTransaction.PaymentType.MONTHLY_CONTRIBUTION,
            'simulated_outcome': 'SUCCESSFUL',
            'notify_email': True,
            'notify_sms': True,
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(self.member.savings_account.total_savings, Decimal('10000.00'))
        self.assertEqual(TreasurerNotification.objects.filter(chama=self.chama).count(), 1)
        receipt = Receipt.objects.get()
        pdf_resp = c.get(reverse('payments:receipt_pdf', args=[receipt.pk]))
        self.assertEqual(pdf_resp.status_code, 200)
        self.assertEqual(pdf_resp['Content-Type'], 'application/pdf')
        self.assertTrue(pdf_resp.content.startswith(b'%PDF'))

        # Bank payment stays PENDING_VERIFICATION without changing savings until Treasurer verifies
        c.post(reverse('payments:make_payment') + '?method=bank', {
            'channel_group': 'bank',
            'contribution_month': '2026-11',
            'amount': '10000.00',
            'bank_name': 'Kenya Commercial Bank (KCB)',
            'payment_method': PaymentTransaction.PaymentMethod.BANK_TRANSFER,
            'external_reference': 'KCB123456',
            'payment_type': PaymentTransaction.PaymentType.MONTHLY_CONTRIBUTION,
        })
        bank_tx = PaymentTransaction.objects.get(external_reference='KCB123456')
        self.assertEqual(bank_tx.status, PaymentTransaction.Status.PENDING_VERIFICATION)
        self.assertEqual(self.member.savings_account.total_savings, Decimal('10000.00'))

        # Member cannot access Treasurer dashboard
        self.assertEqual(c.get(reverse('payments:treasurer_dashboard')).status_code, 302)

        # Treasurer verifies bank payment -> savings becomes 20000.00
        c.force_login(self.treasurer)
        c.post(reverse('payments:verify_payment', args=[bank_tx.pk]), {'decision': 'verify'})
        bank_tx.refresh_from_db()
        self.assertEqual(bank_tx.status, PaymentTransaction.Status.SUCCESSFUL)
        self.assertEqual(self.member.savings_account.total_savings, Decimal('20000.00'))

    def test_cross_chama_isolation_in_directory(self):
        outsider = User.objects.create_user(
            username='outsider@test.co.ke',
            email='outsider@test.co.ke',
            password=self.pw,
            full_name='Outsider Member',
            phone_number='+254700000088',
            chama=self.other_chama,
            role=User.Role.MEMBER,
            approval_status=User.ApprovalStatus.ACTIVE,
            member_number='OTH-001',
        )
        c = Client()
        c.force_login(self.member)
        resp = c.get(reverse('members:public_profile', args=[outsider.pk]))
        self.assertEqual(resp.status_code, 404)

    def test_loan_eligibility_based_on_savings(self):
        from loans.services import calculate_loan_eligibility
        from savings.models import Contribution

        c = Client()
        c.force_login(self.member)

        # With KES 0 verified savings, member is not eligible and cannot apply
        elig_zero = calculate_loan_eligibility(self.member)
        self.assertFalse(elig_zero['is_eligible'])
        self.assertEqual(elig_zero['max_loan_limit'], Decimal('0.00'))

        dash_zero = c.get(reverse('savings:member_dashboard'))
        self.assertContains(dash_zero, 'Not Yet Eligible')

        bad_resp = c.post(reverse('loans:member_loans'), {
            'requested_amount': '5000.00',
            'repayment_months': '6',
            'purpose': 'Inventory stock',
        })
        self.assertEqual(bad_resp.status_code, 200)
        self.assertEqual(LoanApplication.objects.filter(member=self.member).count(), 0)

        # Add KES 10,000 verified savings -> 3x max limit = KES 30,000
        Contribution.objects.create(
            member=self.member,
            chama=self.chama,
            month='2026-11',
            month_label='November 2026',
            amount=Decimal('10000.00'),
        )
        elig_funded = calculate_loan_eligibility(self.member)
        self.assertTrue(elig_funded['is_eligible'])
        self.assertEqual(elig_funded['max_loan_limit'], Decimal('30000.00'))
        self.assertEqual(elig_funded['remaining_apply_capacity'], Decimal('30000.00'))

        loans_page = c.get(reverse('loans:member_loans'))
        self.assertContains(loans_page, 'Eligible for Loan')
        self.assertContains(loans_page, '30,000.00')

        # Requesting above 3x limit is rejected
        over_resp = c.post(reverse('loans:member_loans'), {
            'requested_amount': '35000.00',
            'repayment_months': '6',
            'purpose': 'Too large',
        })
        self.assertEqual(over_resp.status_code, 200)
        self.assertEqual(LoanApplication.objects.filter(member=self.member).count(), 0)

        # Requesting within 3x limit succeeds and lowers remaining capacity
        ok_resp = c.post(reverse('loans:member_loans'), {
            'requested_amount': '25000.00',
            'repayment_months': '6',
            'purpose': 'Farm input purchase',
        })
        self.assertEqual(ok_resp.status_code, 302)
        self.assertEqual(LoanApplication.objects.filter(member=self.member).count(), 1)
        elig_after = calculate_loan_eligibility(self.member)
        self.assertEqual(elig_after['remaining_apply_capacity'], Decimal('5000.00'))

