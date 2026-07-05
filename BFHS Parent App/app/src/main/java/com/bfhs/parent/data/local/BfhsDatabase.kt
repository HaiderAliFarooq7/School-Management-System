package com.bfhs.parent.data.local

import androidx.room.Database
import androidx.room.RoomDatabase

@Database(
    entities = [
        StudentEntity::class,
        AttendanceRecordEntity::class,
        AttendanceSummaryEntity::class,
        FeeEntity::class,
        ExtraChargeEntity::class,
        NotificationEntity::class,
        SchoolProfileEntity::class
    ],
    version = 1,
    exportSchema = false
)
abstract class BfhsDatabase : RoomDatabase() {
    abstract fun studentDao(): StudentDao
    abstract fun attendanceDao(): AttendanceDao
    abstract fun feeDao(): FeeDao
    abstract fun extraChargeDao(): ExtraChargeDao
    abstract fun notificationDao(): NotificationDao
    abstract fun schoolDao(): SchoolDao
}
