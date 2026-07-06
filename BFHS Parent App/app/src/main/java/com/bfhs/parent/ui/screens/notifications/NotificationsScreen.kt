package com.bfhs.parent.ui.screens.notifications

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.School
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.bfhs.parent.R
import com.bfhs.parent.core.Resource
import com.bfhs.parent.domain.models.SchoolNotification
import com.bfhs.parent.ui.components.ErrorBox
import com.bfhs.parent.ui.components.LoadingBox
import com.bfhs.parent.ui.theme.BfhsColors
import com.bfhs.parent.ui.theme.Dimens
import com.bfhs.parent.ui.viewmodel.NotificationsViewModel

/**
 * Notifications (Notices tab) — WhatsApp-style flat list on the dark background:
 * circular gradient school-glyph avatar, title + time, one-line preview, and a
 * small gold unread dot on the right when unread. No glass cards here by design.
 */
@Composable
fun NotificationsScreen(
    viewModel: NotificationsViewModel = hiltViewModel()
) {
    val notifications by viewModel.notifications.collectAsState()
    var opened by remember { mutableStateOf<SchoolNotification?>(null) }

    // Opening the tab marks everything read (clears the dashboard bell dot).
    LaunchedEffect(notifications) {
        if (notifications is Resource.Success) viewModel.markAllRead()
    }

    opened?.let { n ->
        NotificationDialog(notification = n, onDismiss = { opened = null })
    }

    Column(modifier = Modifier.fillMaxSize()) {
        Text(
            text = stringResource(R.string.notifications_title),
            color = BfhsColors.TextPrimary,
            fontSize = 20.sp,
            fontWeight = androidx.compose.ui.text.font.FontWeight.SemiBold,
            modifier = Modifier.padding(start = 20.dp, end = 20.dp, top = 18.dp, bottom = 14.dp)
        )
        HorizontalDivider(color = BfhsColors.Divider, thickness = 1.dp)

        when (val resource = notifications) {
            is Resource.Loading -> LoadingBox()
            is Resource.Error -> ErrorBox(resource.message)
            is Resource.Success -> LazyColumn(
                contentPadding = PaddingValues(
                    start = 8.dp,
                    end = 8.dp,
                    top = 6.dp,
                    bottom = Dimens.TabContentBottomPadding
                )
            ) {
                items(resource.data, key = { it.id }) { notification ->
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(Dimens.RowGap),
                        modifier = Modifier
                            .fillMaxWidth()
                            .clickable { opened = notification }
                            .padding(horizontal = 12.dp, vertical = 12.dp)
                    ) {
                        Box(
                            modifier = Modifier
                                .size(44.dp)
                                .background(BfhsColors.AvatarGradient, CircleShape),
                            contentAlignment = Alignment.Center
                        ) {
                            Icon(
                                Icons.Outlined.School,
                                contentDescription = null,
                                tint = BfhsColors.TextPrimary,
                                modifier = Modifier.size(20.dp)
                            )
                        }
                        Column(modifier = Modifier.weight(1f)) {
                            Row(
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.SpaceBetween,
                                modifier = Modifier.fillMaxWidth()
                            ) {
                                Text(
                                    text = notification.title,
                                    color = BfhsColors.TextPrimary,
                                    fontSize = 14.sp,
                                    fontWeight = androidx.compose.ui.text.font.FontWeight.SemiBold,
                                    maxLines = 1,
                                    overflow = TextOverflow.Ellipsis,
                                    modifier = Modifier.weight(1f, fill = false)
                                )
                                Text(
                                    text = notification.timeLabel,
                                    color = BfhsColors.TextTertiary,
                                    fontSize = 11.sp
                                )
                            }
                            Text(
                                text = notification.body,
                                color = BfhsColors.TextSecondary,
                                style = MaterialTheme.typography.bodyMedium,
                                maxLines = 2,
                                overflow = TextOverflow.Ellipsis,
                                modifier = Modifier.padding(top = 2.dp)
                            )
                        }
                        if (notification.unread) {
                            Box(
                                modifier = Modifier
                                    .size(8.dp)
                                    .background(BfhsColors.AccentGold, CircleShape)
                            )
                        }
                    }
                }
            }
        }
    }
}

/** Full-message reader — opens when a notification row is tapped. */
@Composable
private fun NotificationDialog(notification: SchoolNotification, onDismiss: () -> Unit) {
    AlertDialog(
        onDismissRequest = onDismiss,
        confirmButton = {
            TextButton(onClick = onDismiss) {
                Text(stringResource(R.string.action_close), color = BfhsColors.AccentGold)
            }
        },
        containerColor = BfhsColors.DialogSurface,
        title = { Text(notification.title, color = BfhsColors.TextPrimary) },
        text = {
            Column {
                Text(
                    text = notification.timeLabel,
                    color = BfhsColors.TextTertiary,
                    fontSize = 11.sp
                )
                Spacer(Modifier.height(10.dp))
                Text(
                    text = notification.body,
                    color = BfhsColors.TextSecondary,
                    style = MaterialTheme.typography.bodyLarge
                )
            }
        }
    )
}
