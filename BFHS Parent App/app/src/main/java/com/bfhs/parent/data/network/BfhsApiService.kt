package com.bfhs.parent.data.network

import com.bfhs.parent.data.network.dto.AttendanceResponseDto
import com.bfhs.parent.data.network.dto.ExtraChargeDto
import com.bfhs.parent.data.network.dto.FcmTokenRequestDto
import com.bfhs.parent.data.network.dto.FeeResponseDto
import com.bfhs.parent.data.network.dto.LoginRequestDto
import com.bfhs.parent.data.network.dto.LoginResponseDto
import com.bfhs.parent.data.network.dto.NotificationDto
import com.bfhs.parent.data.network.dto.SchoolProfileDto
import com.bfhs.parent.data.network.dto.StudentDto
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path

/**
 * Retrofit interface for the FastAPI multi-tenant School Management System.
 * Paths are relative to BuildConfig.BASE_URL (which ends in a slash) and map
 * one-to-one to the backend's parent routes under api/parent.
 */
interface BfhsApiService {

    @POST("api/parent/login")
    suspend fun login(@Body body: LoginRequestDto): LoginResponseDto

    @POST("api/parent/fcm-token")
    suspend fun registerFcmToken(@Body body: FcmTokenRequestDto)

    @GET("api/parent/students")
    suspend fun getStudents(): List<StudentDto>

    @GET("api/parent/students/{studentId}/attendance")
    suspend fun getAttendance(@Path("studentId") studentId: String): AttendanceResponseDto

    @GET("api/parent/students/{studentId}/fees")
    suspend fun getFees(@Path("studentId") studentId: String): FeeResponseDto

    @GET("api/parent/students/{studentId}/extra-charges")
    suspend fun getExtraCharges(@Path("studentId") studentId: String): List<ExtraChargeDto>

    @GET("api/parent/notifications")
    suspend fun getNotifications(): List<NotificationDto>

    @GET("api/parent/school")
    suspend fun getSchoolProfile(): SchoolProfileDto
}
