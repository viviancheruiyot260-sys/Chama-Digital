from datetime import date, timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import ChamaGroup, MembershipApprovalLog, User
from announcements.models import Announcement
from loans.models import Loan, LoanApplication, LoanRepayment
from meetings.models import AttendanceRecord, ChamaEvent
from notifications.models import TreasurerNotification
from payments.models import PaymentTransaction
from payments.services import finalize_verified_payment, notify_treasurer_of_transaction
from savings.models import SavingsAccount


class Command(BaseCommand):
    help = 'Seeds Chama Digital with realistic Kenyan table-banking sample data.'

    @transaction.atomic
    def handle(self, *args, **options):
        if ChamaGroup.objects.filter(invite_code='UMJ-2026').exists():
            self.stdout.write(self.style.WARNING('Sample chama data already exists. Skipping seed.'))
            return

        chama = ChamaGroup.objects.create(
            name='Umoja Table Banking Chama',
            invite_code='UMJ-2026',
            official_invite_code='UMOJA-OFFICIAL-2026',
            monthly_contribution=Decimal('12500.00'),
            next_contribution_date=date(2026, 11, 30),
            paybill_number='522522',
            bank_name='Kenya Commercial Bank (KCB)',
            bank_account='1184-2093-5510',
            ussd_code='*384*240#',
        )

        demo_pw = 'ChamaPass2026!'

        chair = User.objects.create_user(
            username='chairperson@chamadigital.co.ke',
            email='chairperson@chamadigital.co.ke',
            password=demo_pw,
            full_name='Samuel Kamau',
            phone_number='+254 711 223 344',
            national_id='24501190',
            chama=chama,
            role=User.Role.CHAIRPERSON,
            approval_status=User.ApprovalStatus.ACTIVE,
            member_number='CHM-001',
            default_avatar_path='images/avatar-treasurer-david.jpg',
            bio='Founding Chairperson focused on transparent table banking and member wealth.',
            approved_at=timezone.now(),
            is_staff=True,
        )

        treasurer = User.objects.create_user(
            username='treasurer@chamadigital.co.ke',
            email='treasurer@chamadigital.co.ke',
            password=demo_pw,
            full_name='David Ochieng',
            phone_number='+254 722 108 440',
            national_id='26190442',
            chama=chama,
            role=User.Role.TREASURER,
            approval_status=User.ApprovalStatus.ACTIVE,
            member_number='CHM-002',
            default_avatar_path='images/avatar-treasurer-david.jpg',
            bio='Group Treasurer overseeing monthly savings reconciliation, M-Pesa, and bank deposits.',
            approved_by=chair,
            approved_at=timezone.now(),
        )

        secretary = User.objects.create_user(
            username='secretary@chamadigital.co.ke',
            email='secretary@chamadigital.co.ke',
            password=demo_pw,
            full_name='Grace Muthoni',
            phone_number='+254 723 991 100',
            national_id='27345811',
            chama=chama,
            role=User.Role.SECRETARY,
            approval_status=User.ApprovalStatus.ACTIVE,
            member_number='CHM-003',
            default_avatar_path='images/avatar-member-amina.jpg',
            bio='Chama Secretary managing meeting minutes, attendance, and member communications.',
            approved_by=chair,
            approved_at=timezone.now(),
        )

        amina = User.objects.create_user(
            username='amina@chamadigital.co.ke',
            email='amina@chamadigital.co.ke',
            password=demo_pw,
            full_name='Amina Wanjiku',
            phone_number='+254 712 345 678',
            national_id='28904112',
            chama=chama,
            role=User.Role.MEMBER,
            approval_status=User.ApprovalStatus.ACTIVE,
            member_number='CHM-004',
            default_avatar_path='images/avatar-member-amina.jpg',
            bio='Agribusiness owner in Kiambu and proud table-banking member since 2024.',
            approved_by=chair,
            approved_at=timezone.now(),
        )

        brian = User.objects.create_user(
            username='brian@chamadigital.co.ke',
            email='brian@chamadigital.co.ke',
            password=demo_pw,
            full_name='Brian Kiprop',
            phone_number='+254 718 334 455',
            national_id='29110234',
            chama=chama,
            role=User.Role.MEMBER,
            approval_status=User.ApprovalStatus.ACTIVE,
            member_number='CHM-005',
            default_avatar_path='images/avatar-treasurer-david.jpg',
            bio='Logistics entrepreneur saving monthly for commercial vehicle expansion.',
            approved_by=chair,
            approved_at=timezone.now(),
        )

        faith = User.objects.create_user(
            username='faith@chamadigital.co.ke',
            email='faith@chamadigital.co.ke',
            password=demo_pw,
            full_name='Faith Njeri',
            phone_number='+254 719 440 221',
            national_id='31440981',
            chama=chama,
            role=User.Role.MEMBER,
            approval_status=User.ApprovalStatus.PENDING,
            default_avatar_path='images/avatar-member-amina.jpg',
            bio='Retail boutique owner applying to join Umoja Table Banking Chama.',
        )

        for u in (chair, treasurer, secretary, amina, brian, faith):
            SavingsAccount.objects.create(
                member=u,
                chama=chama,
                monthly_target=chama.monthly_contribution,
            )

        MembershipApprovalLog.objects.create(
            member=amina,
            reviewed_by=chair,
            decision=User.ApprovalStatus.ACTIVE,
            notes='Verified National ID and initial registration.',
        )

        # Seed verified contributions via transactional service
        tx1 = PaymentTransaction.objects.create(
            member=amina,
            chama=chama,
            contribution_month='2026-10',
            contribution_month_label='October 2026',
            amount=Decimal('12500.00'),
            payment_type=PaymentTransaction.PaymentType.MONTHLY_CONTRIBUTION,
            payment_method=PaymentTransaction.PaymentMethod.MPESA_STK,
            phone_number=amina.phone_number,
            external_reference='SK849201',
            status=PaymentTransaction.Status.PENDING_VERIFICATION,
            is_simulated=True,
        )
        finalize_verified_payment(tx1.pk, verifier=treasurer, notes='Initial seeded M-Pesa confirmation')

        tx2 = PaymentTransaction.objects.create(
            member=brian,
            chama=chama,
            contribution_month='2026-11',
            contribution_month_label='November 2026',
            amount=Decimal('12500.00'),
            payment_type=PaymentTransaction.PaymentType.MONTHLY_CONTRIBUTION,
            payment_method=PaymentTransaction.PaymentMethod.MPESA_PAYBILL,
            phone_number=brian.phone_number,
            external_reference='SK902311',
            status=PaymentTransaction.Status.PENDING_VERIFICATION,
            is_simulated=True,
        )
        finalize_verified_payment(tx2.pk, verifier=treasurer, notes='November Paybill contribution verified')

        # Seed a pending bank transfer for Treasurer verification demo
        pending_bank_tx = PaymentTransaction.objects.create(
            member=amina,
            chama=chama,
            contribution_month='2026-11',
            contribution_month_label='November 2026',
            amount=Decimal('12500.00'),
            payment_type=PaymentTransaction.PaymentType.MONTHLY_CONTRIBUTION,
            payment_method=PaymentTransaction.PaymentMethod.BANK_TRANSFER,
            phone_number=amina.phone_number,
            bank_name='Kenya Commercial Bank (KCB)',
            external_reference='KCB773019',
            status=PaymentTransaction.Status.PENDING_VERIFICATION,
            is_simulated=True,
        )
        notify_treasurer_of_transaction(pending_bank_tx, 'Awaiting Treasurer Bank Verification')

        # Seed Loan & Loan Application
        amina_app = LoanApplication.objects.create(
            member=amina,
            chama=chama,
            requested_amount=Decimal('60000.00'),
            repayment_months=6,
            purpose='Greenhouse drip irrigation & farm stock',
            status=LoanApplication.Status.APPROVED,
            reviewed_by=chair,
            reviewed_at=timezone.now() - timedelta(days=30),
        )
        amina_loan = Loan.objects.create(
            application=amina_app,
            loan_code='LN-2026-001',
            member=amina,
            chama=chama,
            principal_amount=Decimal('60000.00'),
            repayment_months=6,
            purpose='Greenhouse drip irrigation & farm stock',
            next_repayment_date=date(2026, 12, 5),
            status=Loan.Status.DISBURSED,
            disbursed_by=treasurer,
            disbursed_at=timezone.now() - timedelta(days=28),
        )
        LoanRepayment.objects.create(
            loan=amina_loan,
            amount=Decimal('15000.00'),
            reference='SK771022',
            recorded_by=treasurer,
        )

        LoanApplication.objects.create(
            member=brian,
            chama=chama,
            requested_amount=Decimal('45000.00'),
            repayment_months=6,
            purpose='Commercial delivery van service & tyres',
            status=LoanApplication.Status.PENDING,
        )

        # Seed Announcements
        Announcement.objects.create(
            chama=chama,
            author=secretary,
            title='November Contribution Deadline — 30 Nov 2026',
            category=Announcement.Category.CONTRIBUTION_REMINDER,
            body='Please submit your November 2026 contribution of KES 12,500 via M-Pesa Paybill 522522 or KCB Bank Transfer before 5:00 PM on 30 November 2026.',
        )
        Announcement.objects.create(
            chama=chama,
            author=chair,
            title='Annual Dividend & Audit Review Notice',
            category=Announcement.Category.IMPORTANT_NOTICE,
            body='Our end-of-year audit books are open for member inspection during the upcoming AGM. Bring your membership passbook or digital receipts.',
        )

        # Seed Meetings & Important Occasions
        m1 = ChamaEvent.objects.create(
            chama=chama,
            organizer=secretary,
            event_type=ChamaEvent.EventType.REGULAR_MEETING,
            title='Monthly Table-Banking Meeting',
            event_date=date(2026, 11, 28),
            event_time='10:00 AM EAT',
            venue='Umoja Community Hall, Nairobi',
            agenda='1. Opening prayer & roll call\n2. November savings reconciliation\n3. Loan approvals & table disbursement',
            description='Regular end-of-month table banking session for all approved members.',
        )
        ChamaEvent.objects.create(
            chama=chama,
            organizer=chair,
            event_type=ChamaEvent.EventType.AGM,
            title='Annual General Meeting & Dividend Payout Day',
            event_date=date(2026, 12, 12),
            event_time='9:30 AM EAT',
            venue='KICC Conference Room B, Nairobi',
            agenda='Annual financial report, dividend distribution, and 2027 investment vote.',
            description='Important end-of-year chama occasion. Smart casual attire.',
        )
        ChamaEvent.objects.create(
            chama=chama,
            organizer=secretary,
            event_type=ChamaEvent.EventType.CELEBRATION,
            title='End-of-Year Chama Thanksgiving & Member Birthdays',
            event_date=date(2026, 12, 19),
            event_time='1:00 PM EAT',
            venue='Karura Forest Picnic Grounds',
            agenda='Celebrating November & December member birthdays and group milestones.',
            description='Community celebration with family members welcome.',
        )

        AttendanceRecord.objects.create(event=m1, member=amina, attended=True, notes='Confirmed')
        AttendanceRecord.objects.create(event=m1, member=brian, attended=True, notes='Confirmed')

        self.stdout.write(self.style.SUCCESS('Seeded Umoja Table Banking Chama successfully!'))
