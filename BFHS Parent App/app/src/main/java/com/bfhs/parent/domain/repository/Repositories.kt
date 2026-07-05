package com.bfhs.parent.domain.repository

import com.bfhs.parent.core.Resource
import com.bfhs.parent.domain.models.AttendanceSummary
import com.bfhs.parent.domain.models.ExtraCharge
import com.bfhs.parent.domain.models.FeeOverview
import com.bfhs.parent.domain.models.Parent
import com.bfhs.parent.domain.models.SchoolNotification
import com.bfhs.parent.domain.models.SchoolProfile
import com.bfhs.parent.domain.models.Student
import kotlinx.coroutines.flow.Flow

interface AuthRepository {
    suspend fun login(mobileNumber: String, password: String): Resource<Parent>
    suspend fun logout()
    fun isLoggedIn(): Flow<Boolean>
    fun parent(): Flow<Parent?>
    suspend fun registerFcmToken(token: String)

    /** Fetches this device's current FCM token and registers it with the
     * backend for the signed-in parent. Best-effort; safe to call repeatedly. */
    suspend fun registerCurrentDevice()
}

interface StudentRepository {
    /** Emits cached data first (offline support), then refreshed API data. */
    fun students(): Flow<Resource<List<Student>>>
    fun student(studentId: String): Flow<Student?>
    fun attendance(studentId: String): Flow<Resource<AttendanceSummary>>
    fun fees(studentId: String): Flow<Resource<FeeOverview>>
    fun extraCharges(studentId: String): Flow<Resource<List<ExtraCharge>>>
}

interface NotificationRepository {
    fun notifications(): Flow<Resource<List<SchoolNotification>>>
    suspend fun markAllRead()
    fun hasUnread(): Flow<Boolean>
}

interface SchoolRepository {
    fun schoolProfile(): Flow<Resource<SchoolProfile>>
}
