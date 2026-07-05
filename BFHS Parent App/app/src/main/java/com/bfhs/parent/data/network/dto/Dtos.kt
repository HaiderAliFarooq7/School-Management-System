package com.bfhs.parent.data.network.dto

import com.google.gson.annotations.SerializedName

// ---------- Auth ----------

data class LoginRequestDto(
    @SerializedName("mobile_number") val mobileNumber: String,
    @SerializedName("password") val password: String
)

data class LoginResponseDto(
    @SerializedName("access_token") val accessToken: String,
    @SerializedName("token_type") val tokenType: String?,
    @SerializedName("parent_name") val parentName: String?,
    @SerializedName("mobile_number") val mobileNumber: String?
)

data class FcmTokenRequestDto(
    @SerializedName("fcm_token") val fcmToken: String
)

// ---------- Students ----------

data class StudentDto(
    @SerializedName("id") val id: String,
    @SerializedName("name") val name: String,
    @SerializedName("registration_number") val registrationNumber: String?,
    @SerializedName("class_name") val className: String?,
    @SerializedName("father_name") val fatherName: String?,
    @SerializedName("today_attendance") val todayAttendance: String?,
    @SerializedName("remaining_dues") val remainingDues: Long?,
    @SerializedName("monthly_attendance_percent") val monthlyAttendancePercent: Int?
)

// ---------- Attendance ----------

data class AttendanceRecordDto(
    @SerializedName("date") val date: String,
    @SerializedName("status") val status: String
)

data class AttendanceResponseDto(
    @SerializedName("month") val month: String?,
    @SerializedName("present_count") val presentCount: Int?,
    @SerializedName("absent_count") val absentCount: Int?,
    @SerializedName("leave_count") val leaveCount: Int?,
    @SerializedName("overall_percent") val overallPercent: Int?,
    @SerializedName("records") val records: List<AttendanceRecordDto>?
)

// ---------- Fees ----------

data class MonthlyFeeDto(
    @SerializedName("month") val month: String,
    @SerializedName("amount") val amount: Long,
    @SerializedName("status") val status: String?,
    @SerializedName("due_date") val dueDate: String?
)

data class FeeResponseDto(
    @SerializedName("current") val current: MonthlyFeeDto?,
    @SerializedName("history") val history: List<MonthlyFeeDto>?
)

// ---------- Extra charges ----------

data class ExtraChargeDto(
    @SerializedName("id") val id: String,
    @SerializedName("title") val title: String,
    @SerializedName("amount") val amount: Long,
    @SerializedName("date_label") val dateLabel: String?,
    @SerializedName("status") val status: String?
)

// ---------- Notifications ----------

data class NotificationDto(
    @SerializedName("id") val id: String,
    @SerializedName("title") val title: String,
    @SerializedName("body") val body: String?,
    @SerializedName("time_label") val timeLabel: String?,
    @SerializedName("unread") val unread: Boolean?,
    @SerializedName("type") val type: String?,
    @SerializedName("student_id") val studentId: String?
)

// ---------- School ----------

data class SchoolProfileDto(
    @SerializedName("name") val name: String,
    @SerializedName("tagline") val tagline: String?,
    @SerializedName("principal") val principal: String?,
    @SerializedName("established") val established: String?,
    @SerializedName("phone") val phone: String?,
    @SerializedName("email") val email: String?,
    @SerializedName("address") val address: String?,
    @SerializedName("website") val website: String?,
    @SerializedName("about") val about: String?
)
