package com.bfhs.parent

import android.app.Application
import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.Context
import dagger.hilt.android.HiltAndroidApp

@HiltAndroidApp
class BfhsParentApp : Application() {

    override fun onCreate() {
        super.onCreate()
        createNotificationChannels()
    }

    private fun createNotificationChannels() {
        val manager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        val channels = listOf(
            NotificationChannel(
                CHANNEL_ATTENDANCE,
                getString(R.string.channel_attendance),
                NotificationManager.IMPORTANCE_HIGH
            ),
            NotificationChannel(
                CHANNEL_FEE,
                getString(R.string.channel_fee),
                NotificationManager.IMPORTANCE_HIGH
            ),
            NotificationChannel(
                CHANNEL_ANNOUNCEMENTS,
                getString(R.string.channel_announcements),
                NotificationManager.IMPORTANCE_DEFAULT
            )
        )
        channels.forEach(manager::createNotificationChannel)
    }

    companion object {
        const val CHANNEL_ATTENDANCE = "attendance_alerts"
        const val CHANNEL_FEE = "fee_reminders"
        const val CHANNEL_ANNOUNCEMENTS = "school_announcements"
    }
}
