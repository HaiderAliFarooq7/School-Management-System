package com.bfhs.parent.data.local

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "students")
data class StudentEntity(
    @PrimaryKey val id: String,
    val name: String,
    val registrationNumber: String,
    val className: String,
    val fatherName: String,
    val todayAttendance: String,
    val remainingDues: Long,
    val monthlyAttendancePercent: Int
)

@Entity(tableName = "attendance_records", primaryKeys = ["studentId", "date"])
data class AttendanceRecordEntity(
    val studentId: String,
    val date: String,
    val status: String
)

@Entity(tableName = "attendance_summaries")
data class AttendanceSummaryEntity(
    @PrimaryKey val studentId: String,
    val month: String,
    val presentCount: Int,
    val absentCount: Int,
    val leaveCount: Int,
    val overallPercent: Int
)

@Entity(tableName = "fees", primaryKeys = ["studentId", "month"])
data class FeeEntity(
    val studentId: String,
    val month: String,
    val amount: Long,
    val status: String,
    val dueDate: String?,
    val isCurrent: Boolean
)

@Entity(tableName = "extra_charges")
data class ExtraChargeEntity(
    @PrimaryKey val id: String,
    val studentId: String,
    val title: String,
    val amount: Long,
    val dateLabel: String,
    val status: String
)

@Entity(tableName = "notifications")
data class NotificationEntity(
    @PrimaryKey val id: String,
    val title: String,
    val body: String,
    val timeLabel: String,
    val unread: Boolean,
    val type: String,
    val studentId: String?
)

@Entity(tableName = "school_profile")
data class SchoolProfileEntity(
    @PrimaryKey val id: Int = 1,
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
