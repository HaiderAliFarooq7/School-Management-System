package com.bfhs.parent.domain.models

enum class AttendanceStatus { PRESENT, ABSENT, LEAVE, UNKNOWN;

    companion object {
        fun from(raw: String?): AttendanceStatus = when (raw?.trim()?.lowercase()) {
            "present" -> PRESENT
            "absent" -> ABSENT
            "leave" -> LEAVE
            else -> UNKNOWN
        }
    }
}

enum class PaymentStatus { PAID, UNPAID;

    companion object {
        fun from(raw: String?): PaymentStatus =
            if (raw?.trim()?.equals("paid", ignoreCase = true) == true) PAID else UNPAID
    }
}

data class Parent(
    val name: String,
    val mobileNumber: String
)

data class Student(
    val id: String,
    val name: String,
    val registrationNumber: String,
    val className: String,
    val fatherName: String,
    val todayAttendance: AttendanceStatus,
    val remainingDues: Long,
    val monthlyAttendancePercent: Int
) {
    val initials: String
        get() = name.split(" ")
            .filter { it.isNotBlank() }
            .let { parts ->
                when {
                    parts.size >= 2 -> "${parts.first().first()}${parts.last().first()}"
                    parts.size == 1 -> parts.first().take(2)
                    else -> "?"
                }
            }.uppercase()
}

data class AttendanceRecord(
    val date: String,          // display form, e.g. "Thu, 2 Jul 2026"
    val status: AttendanceStatus
)

data class AttendanceSummary(
    val month: String,         // e.g. "July 2026"
    val presentCount: Int,
    val absentCount: Int,
    val leaveCount: Int,
    val overallPercent: Int,
    val records: List<AttendanceRecord>
)

data class MonthlyFee(
    val month: String,
    val amount: Long,
    val status: PaymentStatus,
    val dueDate: String?
)

data class FeeOverview(
    val current: MonthlyFee?,
    val history: List<MonthlyFee>
)

data class ExtraCharge(
    val id: String,
    val title: String,
    val amount: Long,
    val dateLabel: String,     // e.g. "Due 15 Jul 2026" / "Paid 3 Jun 2026"
    val status: PaymentStatus
)

enum class NotificationType { ABSENT, FEE_REMINDER, ANNOUNCEMENT;

    companion object {
        fun from(raw: String?): NotificationType = when (raw?.trim()?.lowercase()) {
            "absent", "attendance" -> ABSENT
            "fee", "fee_reminder" -> FEE_REMINDER
            else -> ANNOUNCEMENT
        }
    }
}

data class SchoolNotification(
    val id: String,
    val title: String,
    val body: String,
    val timeLabel: String,     // e.g. "9:14 AM" / "Yesterday"
    val unread: Boolean,
    val type: NotificationType,
    val studentId: String?
)

data class SchoolProfile(
    val name: String,
    val tagline: String,
    val principal: String,
    val established: String,
    val phone: String,
    val email: String,
    val address: String,
    val website: String,
    val about: String
)
