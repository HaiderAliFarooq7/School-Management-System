package com.bfhs.parent.data.local

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Transaction
import kotlinx.coroutines.flow.Flow

@Dao
interface StudentDao {
    @Query("SELECT * FROM students")
    fun observeAll(): Flow<List<StudentEntity>>

    @Query("SELECT * FROM students WHERE id = :id")
    fun observeById(id: String): Flow<StudentEntity?>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertAll(students: List<StudentEntity>)

    @Query("DELETE FROM students")
    suspend fun clear()

    @Transaction
    suspend fun replaceAll(students: List<StudentEntity>) {
        clear()
        insertAll(students)
    }
}

@Dao
interface AttendanceDao {
    @Query("SELECT * FROM attendance_summaries WHERE studentId = :studentId")
    fun observeSummary(studentId: String): Flow<AttendanceSummaryEntity?>

    @Query("SELECT * FROM attendance_records WHERE studentId = :studentId")
    fun observeRecords(studentId: String): Flow<List<AttendanceRecordEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertSummary(summary: AttendanceSummaryEntity)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertRecords(records: List<AttendanceRecordEntity>)

    @Query("DELETE FROM attendance_records WHERE studentId = :studentId")
    suspend fun clearRecords(studentId: String)

    @Transaction
    suspend fun replaceFor(studentId: String, summary: AttendanceSummaryEntity, records: List<AttendanceRecordEntity>) {
        clearRecords(studentId)
        insertSummary(summary)
        insertRecords(records)
    }
}

@Dao
interface FeeDao {
    @Query("SELECT * FROM fees WHERE studentId = :studentId")
    fun observeFor(studentId: String): Flow<List<FeeEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertAll(fees: List<FeeEntity>)

    @Query("DELETE FROM fees WHERE studentId = :studentId")
    suspend fun clearFor(studentId: String)

    @Transaction
    suspend fun replaceFor(studentId: String, fees: List<FeeEntity>) {
        clearFor(studentId)
        insertAll(fees)
    }
}

@Dao
interface ExtraChargeDao {
    @Query("SELECT * FROM extra_charges WHERE studentId = :studentId")
    fun observeFor(studentId: String): Flow<List<ExtraChargeEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertAll(charges: List<ExtraChargeEntity>)

    @Query("DELETE FROM extra_charges WHERE studentId = :studentId")
    suspend fun clearFor(studentId: String)

    @Transaction
    suspend fun replaceFor(studentId: String, charges: List<ExtraChargeEntity>) {
        clearFor(studentId)
        insertAll(charges)
    }
}

@Dao
interface NotificationDao {
    @Query("SELECT * FROM notifications")
    fun observeAll(): Flow<List<NotificationEntity>>

    @Query("SELECT COUNT(*) FROM notifications WHERE unread = 1")
    fun observeUnreadCount(): Flow<Int>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertAll(notifications: List<NotificationEntity>)

    @Query("UPDATE notifications SET unread = 0")
    suspend fun markAllRead()

    @Query("DELETE FROM notifications")
    suspend fun clear()

    @Transaction
    suspend fun replaceAll(notifications: List<NotificationEntity>) {
        clear()
        insertAll(notifications)
    }
}

@Dao
interface SchoolDao {
    @Query("SELECT * FROM school_profile WHERE id = 1")
    fun observe(): Flow<SchoolProfileEntity?>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(profile: SchoolProfileEntity)
}
