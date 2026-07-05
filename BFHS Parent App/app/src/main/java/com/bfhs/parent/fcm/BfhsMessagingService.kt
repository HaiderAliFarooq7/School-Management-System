package com.bfhs.parent.fcm

import android.app.PendingIntent
import android.content.Intent
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import androidx.core.content.PermissionChecker
import com.bfhs.parent.BfhsParentApp
import com.bfhs.parent.MainActivity
import com.bfhs.parent.R
import com.bfhs.parent.domain.repository.AuthRepository
import com.google.firebase.messaging.FirebaseMessagingService
import com.google.firebase.messaging.RemoteMessage
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.launch
import javax.inject.Inject

/**
 * Handles FCM messages for the three supported notification types:
 *  - "absent"       → opens the student's Attendance screen
 *  - "fee_reminder" → opens the student's Monthly Fee screen
 *  - "announcement" → opens the Notifications tab
 *
 * Expected data payload keys: "type", "title", "body", optional "student_id".
 */
@AndroidEntryPoint
class BfhsMessagingService : FirebaseMessagingService() {

    @Inject
    lateinit var authRepository: AuthRepository

    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    override fun onNewToken(token: String) {
        scope.launch { authRepository.registerFcmToken(token) }
    }

    override fun onMessageReceived(message: RemoteMessage) {
        val data = message.data
        val type = data["type"] ?: "announcement"
        val title = data["title"] ?: message.notification?.title ?: getString(R.string.app_name)
        val body = data["body"] ?: message.notification?.body ?: ""
        val studentId = data["student_id"]

        val channelId = when (type) {
            "absent", "attendance" -> BfhsParentApp.CHANNEL_ATTENDANCE
            "fee", "fee_reminder" -> BfhsParentApp.CHANNEL_FEE
            else -> BfhsParentApp.CHANNEL_ANNOUNCEMENTS
        }

        val intent = Intent(this, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
            putExtra(MainActivity.EXTRA_NOTIFICATION_TYPE, type)
            studentId?.let { putExtra(MainActivity.EXTRA_STUDENT_ID, it) }
        }
        val pendingIntent = PendingIntent.getActivity(
            this,
            System.currentTimeMillis().toInt(),
            intent,
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
        )

        val notification = NotificationCompat.Builder(this, channelId)
            .setSmallIcon(R.drawable.ic_notification)
            .setContentTitle(title)
            .setContentText(body)
            .setStyle(NotificationCompat.BigTextStyle().bigText(body))
            .setAutoCancel(true)
            .setContentIntent(pendingIntent)
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .build()

        val canPost = PermissionChecker.checkSelfPermission(
            this, android.Manifest.permission.POST_NOTIFICATIONS
        ) == PermissionChecker.PERMISSION_GRANTED || android.os.Build.VERSION.SDK_INT < 33

        if (canPost) {
            NotificationManagerCompat.from(this)
                .notify(System.currentTimeMillis().toInt(), notification)
        }
    }

    override fun onDestroy() {
        scope.cancel()
        super.onDestroy()
    }
}
