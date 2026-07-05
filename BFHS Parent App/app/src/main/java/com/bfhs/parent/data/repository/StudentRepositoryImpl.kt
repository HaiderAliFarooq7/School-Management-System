package com.bfhs.parent.data.repository

import com.bfhs.parent.core.Resource
import com.bfhs.parent.data.local.AttendanceDao
import com.bfhs.parent.data.local.ExtraChargeDao
import com.bfhs.parent.data.local.FeeDao
import com.bfhs.parent.data.local.StudentDao
import com.bfhs.parent.data.network.BfhsApiService
import com.bfhs.parent.domain.models.AttendanceSummary
import com.bfhs.parent.domain.models.ExtraCharge
import com.bfhs.parent.domain.models.FeeOverview
import com.bfhs.parent.domain.models.Student
import com.bfhs.parent.domain.repository.StudentRepository
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.map
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Offline-first: every read emits the Room cache immediately, then tries the network,
 * persists fresh data to Room and re-emits. If the network fails, the cache (when
 * present) keeps the app usable offline.
 */
@Singleton
class StudentRepositoryImpl @Inject constructor(
    private val api: BfhsApiService,
    private val studentDao: StudentDao,
    private val attendanceDao: AttendanceDao,
    private val feeDao: FeeDao,
    private val extraChargeDao: ExtraChargeDao
) : StudentRepository {

    override fun students(): Flow<Resource<List<Student>>> = flow {
        emit(Resource.Loading)
        val cached = studentDao.observeAll().first().map { it.toDomain() }
        if (cached.isNotEmpty()) emit(Resource.Success(cached, fromCache = true))
        try {
            val fresh = api.getStudents()
            studentDao.replaceAll(fresh.map { it.toEntity() })
            emit(Resource.Success(studentDao.observeAll().first().map { it.toDomain() }))
        } catch (e: Exception) {
            if (cached.isEmpty()) emit(Resource.Error(e.userMessage()))
            // else: keep showing cache silently (offline mode)
        }
    }

    override fun student(studentId: String): Flow<Student?> =
        studentDao.observeById(studentId).map { it?.toDomain() }

    override fun attendance(studentId: String): Flow<Resource<AttendanceSummary>> = flow {
        emit(Resource.Loading)
        val cachedSummary = attendanceDao.observeSummary(studentId).first()
        val cachedRecords = attendanceDao.observeRecords(studentId).first()
        if (cachedSummary != null) {
            emit(Resource.Success(cachedSummary.toDomain(cachedRecords), fromCache = true))
        }
        try {
            val fresh = api.getAttendance(studentId)
            attendanceDao.replaceFor(
                studentId,
                fresh.toSummaryEntity(studentId),
                fresh.toRecordEntities(studentId)
            )
            val summary = attendanceDao.observeSummary(studentId).first()
            val records = attendanceDao.observeRecords(studentId).first()
            if (summary != null) emit(Resource.Success(summary.toDomain(records)))
        } catch (e: Exception) {
            if (cachedSummary == null) emit(Resource.Error(e.userMessage()))
        }
    }

    override fun fees(studentId: String): Flow<Resource<FeeOverview>> = flow {
        emit(Resource.Loading)
        val cached = feeDao.observeFor(studentId).first()
        if (cached.isNotEmpty()) emit(Resource.Success(cached.toOverview(), fromCache = true))
        try {
            val fresh = api.getFees(studentId)
            val entities = buildList {
                fresh.current?.let { add(it.toEntity(studentId, isCurrent = true)) }
                fresh.history.orEmpty().forEach { add(it.toEntity(studentId, isCurrent = false)) }
            }
            feeDao.replaceFor(studentId, entities)
            emit(Resource.Success(feeDao.observeFor(studentId).first().toOverview()))
        } catch (e: Exception) {
            if (cached.isEmpty()) emit(Resource.Error(e.userMessage()))
        }
    }

    override fun extraCharges(studentId: String): Flow<Resource<List<ExtraCharge>>> = flow {
        emit(Resource.Loading)
        val cached = extraChargeDao.observeFor(studentId).first().map { it.toDomain() }
        if (cached.isNotEmpty()) emit(Resource.Success(cached, fromCache = true))
        try {
            val fresh = api.getExtraCharges(studentId)
            extraChargeDao.replaceFor(studentId, fresh.map { it.toEntity(studentId) })
            emit(Resource.Success(extraChargeDao.observeFor(studentId).first().map { it.toDomain() }))
        } catch (e: Exception) {
            if (cached.isEmpty()) emit(Resource.Error(e.userMessage()))
        }
    }

    private fun List<com.bfhs.parent.data.local.FeeEntity>.toOverview() = FeeOverview(
        current = firstOrNull { it.isCurrent }?.toDomain(),
        history = filter { !it.isCurrent }.map { it.toDomain() }
    )
}
