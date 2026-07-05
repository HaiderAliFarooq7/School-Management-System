package com.bfhs.parent.data.repository

import com.bfhs.parent.data.local.AttendanceRecordEntity
import com.bfhs.parent.data.local.AttendanceSummaryEntity
import com.bfhs.parent.data.local.ExtraChargeEntity
import com.bfhs.parent.data.local.FeeEntity
import com.bfhs.parent.data.local.NotificationEntity
import com.bfhs.parent.data.local.SchoolProfileEntity
import com.bfhs.parent.data.local.StudentEntity
import com.bfhs.parent.data.network.dto.AttendanceResponseDto
import com.bfhs.parent.data.network.dto.ExtraChargeDto
import com.bfhs.parent.data.network.dto.MonthlyFeeDto
import com.bfhs.parent.data.network.dto.NotificationDto
import com.bfhs.parent.data.network.dto.SchoolProfileDto
import com.bfhs.parent.data.network.dto.StudentDto
import com.bfhs.parent.domain.models.AttendanceRecord
import com.bfhs.parent.domain.models.AttendanceStatus
import com.bfhs.parent.domain.models.AttendanceSummary
import com.bfhs.parent.domain.models.ExtraCharge
import com.bfhs.parent.domain.models.MonthlyFee
import com.bfhs.parent.domain.models.NotificationType
import com.bfhs.parent.domain.models.PaymentStatus
import com.bfhs.parent.domain.models.SchoolNotification
import com.bfhs.parent.domain.models.SchoolProfile
import com.bfhs.parent.domain.models.Student

// ---------- DTO -> Entity ----------

fun StudentDto.toEntity() = StudentEntity(
    id = id,
    name = name,
    registrationNumber = registrationNumber.orEmpty(),
    className = className.orEmpty(),
    fatherName = fatherName.orEmpty(),
    todayAttendance = todayAttendance.orEmpty(),
    remainingDues = remainingDues ?: 0L,
    monthlyAttendancePercent = monthlyAttendancePercent ?: 0
)

fun AttendanceResponseDto.toSummaryEntity(studentId: String) = AttendanceSummaryEntity(
    studentId = studentId,
    month = month.orEmpty(),
    presentCount = presentCount ?: 0,
    absentCount = absentCount ?: 0,
    leaveCount = leaveCount ?: 0,
    overallPercent = overallPercent ?: 0
)

fun AttendanceResponseDto.toRecordEntities(studentId: String) =
    records.orEmpty().map { AttendanceRecordEntity(studentId, it.date, it.status) }

fun MonthlyFeeDto.toEntity(studentId: String, isCurrent: Boolean) = FeeEntity(
    studentId = studentId,
    month = month,
    amount = amount,
    status = status.orEmpty(),
    dueDate = dueDate,
    isCurrent = isCurrent
)

fun ExtraChargeDto.toEntity(studentId: String) = ExtraChargeEntity(
    id = id,
    studentId = studentId,
    title = title,
    amount = amount,
    dateLabel = dateLabel.orEmpty(),
    status = status.orEmpty()
)

fun NotificationDto.toEntity() = NotificationEntity(
    id = id,
    title = title,
    body = body.orEmpty(),
    timeLabel = timeLabel.orEmpty(),
    unread = unread ?: false,
    type = type.orEmpty(),
    studentId = studentId
)

fun SchoolProfileDto.toEntity() = SchoolProfileEntity(
    name = name,
    tagline = tagline.orEmpty(),
    principal = principal.orEmpty(),
    established = established.orEmpty(),
    phone = phone.orEmpty(),
    email = email.orEmpty(),
    address = address.orEmpty(),
    website = website.orEmpty(),
    about = about.orEmpty()
)

// ---------- Entity -> Domain ----------

fun StudentEntity.toDomain() = Student(
    id = id,
    name = name,
    registrationNumber = registrationNumber,
    className = className,
    fatherName = fatherName,
    todayAttendance = AttendanceStatus.from(todayAttendance),
    remainingDues = remainingDues,
    monthlyAttendancePercent = monthlyAttendancePercent
)

fun AttendanceSummaryEntity.toDomain(records: List<AttendanceRecordEntity>) = AttendanceSummary(
    month = month,
    presentCount = presentCount,
    absentCount = absentCount,
    leaveCount = leaveCount,
    overallPercent = overallPercent,
    records = records.map { AttendanceRecord(it.date, AttendanceStatus.from(it.status)) }
)

fun FeeEntity.toDomain() = MonthlyFee(
    month = month,
    amount = amount,
    status = PaymentStatus.from(status),
    dueDate = dueDate
)

fun ExtraChargeEntity.toDomain() = ExtraCharge(
    id = id,
    title = title,
    amount = amount,
    dateLabel = dateLabel,
    status = PaymentStatus.from(status)
)

fun NotificationEntity.toDomain() = SchoolNotification(
    id = id,
    title = title,
    body = body,
    timeLabel = timeLabel,
    unread = unread,
    type = NotificationType.from(type),
    studentId = studentId
)

fun SchoolProfileEntity.toDomain() = SchoolProfile(
    name = name,
    tagline = tagline,
    principal = principal,
    established = established,
    phone = phone,
    email = email,
    address = address,
    website = website,
    about = about
)
