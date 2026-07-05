package com.bfhs.parent

import android.Manifest
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import com.bfhs.parent.ui.navigation.BfhsNavGraph
import com.bfhs.parent.ui.theme.BfhsParentTheme
import dagger.hilt.android.AndroidEntryPoint

@AndroidEntryPoint
class MainActivity : AppCompatActivity() {

    // Result is ignored: FCM still delivers if denied, the system just won't
    // show a heads-up notification. Registered before the activity starts.
    private val requestNotificationPermission =
        registerForActivityResult(ActivityResultContracts.RequestPermission()) { }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        maybeRequestNotificationPermission()

        // FCM deep-link extras ("type" + optional "student_id") routed into the nav graph.
        val notificationType = intent.getStringExtra(EXTRA_NOTIFICATION_TYPE)
        val studentId = intent.getStringExtra(EXTRA_STUDENT_ID)

        setContent {
            BfhsParentTheme {
                BfhsNavGraph(
                    notificationType = notificationType,
                    notificationStudentId = studentId
                )
            }
        }
    }

    /** On Android 13+ (API 33) notifications are hidden until the user grants
     * POST_NOTIFICATIONS at runtime — the manifest declaration alone isn't
     * enough. Ask once on launch if not already granted. */
    private fun maybeRequestNotificationPermission() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            val granted = ContextCompat.checkSelfPermission(
                this, Manifest.permission.POST_NOTIFICATIONS
            ) == PackageManager.PERMISSION_GRANTED
            if (!granted) {
                requestNotificationPermission.launch(Manifest.permission.POST_NOTIFICATIONS)
            }
        }
    }

    companion object {
        const val EXTRA_NOTIFICATION_TYPE = "type"
        const val EXTRA_STUDENT_ID = "student_id"
    }
}
