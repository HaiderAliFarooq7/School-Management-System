from app.db.session import SessionLocal
from app.models.student import Student
from app.models.grade import Grade
from app.models.user import User
from app.models.role import Role
from app.models.fee_voucher import FeeVoucher
from app.models.extra_charge import ExtraCharge
from app.models.attendance import AttendanceRecord
from app.models.communication_provider import CommunicationProvider
from app.models.notification_template import NotificationTemplate
from app.models.notification_queue import NotificationQueue
from app.models.notification_log import NotificationLog
from app.models.school import School

db = SessionLocal()
print('students:', db.query(Student).count())
print('grades:', db.query(Grade).count())
print('users:', db.query(User).count())
print('roles:', [r.role_name for r in db.query(Role).all()])
print('vouchers:', db.query(FeeVoucher).count())
print('charges:', db.query(ExtraCharge).count())
print('attendance:', db.query(AttendanceRecord).count())
print('providers:', [(p.name, p.type, p.enabled) for p in db.query(CommunicationProvider).all()])
print('templates:', [(t.name, t.enabled) for t in db.query(NotificationTemplate).all()])
print('queue:', db.query(NotificationQueue).count())
print('logs:', db.query(NotificationLog).count())
print('school:', db.query(School).count())
for g in db.query(Grade).all():
    print(' grade:', g.grade_id, g.class_name, g.fee_amount)
for u in db.query(User).all():
    print(' user:', u.user_id, u.username, u.role_id, u.assigned_class_name, u.is_active)
db.close()
