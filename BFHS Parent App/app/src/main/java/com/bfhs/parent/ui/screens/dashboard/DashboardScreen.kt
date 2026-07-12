package com.bfhs.parent.ui.screens.dashboard

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
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Cancel
import androidx.compose.material.icons.outlined.CheckCircle
import androidx.compose.material.icons.outlined.ChevronRight
import androidx.compose.material.icons.outlined.Notifications
import androidx.compose.material.icons.outlined.RemoveCircleOutline
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.bfhs.parent.R
import com.bfhs.parent.core.Resource
import com.bfhs.parent.core.utils.Formatters
import com.bfhs.parent.domain.models.AttendanceStatus
import com.bfhs.parent.domain.models.Student
import com.bfhs.parent.ui.components.ErrorBox
import com.bfhs.parent.ui.components.GlassCard
import com.bfhs.parent.ui.components.GradientAvatar
import com.bfhs.parent.ui.components.LoadingBox
import com.bfhs.parent.ui.components.SectionLabel
import com.bfhs.parent.ui.theme.BfhsColors
import com.bfhs.parent.ui.theme.Dimens
import com.bfhs.parent.ui.viewmodel.DashboardViewModel

/**
 * Dashboard (Home tab) — gradient greeting header with the notification bell,
 * then "MY CHILDREN": one glass card per linked child with avatar, name,
 * class · S/O father, and the Today / Dues mini-stat tiles.
 */
@Composable
fun DashboardScreen(
    onStudentClick: (String) -> Unit,
    onBellClick: () -> Unit,
    viewModel: DashboardViewModel = hiltViewModel()
) {
    val students by viewModel.students.collectAsState()
    val parent by viewModel.parent.collectAsState()
    val hasUnread by viewModel.hasUnread.collectAsState()

    // Greeting shows the parent's real name — never the mobile number. If the
    // account has no name (or only digits), fall back to the child's father
    // name, then a generic label.
    val parentName = parent?.name?.trim().orEmpty()
    val greetingName = if (parentName.isNotEmpty() && parentName.any { it.isLetter() }) {
        parentName
    } else {
        (students as? Resource.Success)?.data?.firstOrNull()?.fatherName?.trim()
            ?.takeIf { it.isNotEmpty() }
            ?: stringResource(R.string.dashboard_default_parent)
    }

    Column(modifier = Modifier.fillMaxSize()) {
        // Gradient header
        Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween,
            modifier = Modifier
                .fillMaxWidth()
                .background(
                    BfhsColors.HeaderGradient,
                    RoundedCornerShape(bottomStart = 28.dp, bottomEnd = 28.dp)
                )
                .padding(start = 20.dp, end = 20.dp, top = 20.dp, bottom = 24.dp)
        ) {
            Column {
                Text(
                    text = stringResource(R.string.dashboard_greeting),
                    color = BfhsColors.TextSecondary,
                    style = MaterialTheme.typography.bodySmall
                )
                Text(
                    text = greetingName,
                    color = BfhsColors.TextPrimary,
                    fontSize = 19.sp,
                    fontWeight = androidx.compose.ui.text.font.FontWeight.SemiBold
                )
            }
            Box(
                modifier = Modifier
                    .size(42.dp)
                    .background(BfhsColors.GlassFillStrong, RoundedCornerShape(14.dp))
                    .clickable(onClick = onBellClick),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    Icons.Outlined.Notifications,
                    contentDescription = stringResource(R.string.nav_notices),
                    tint = BfhsColors.TextPrimary,
                    modifier = Modifier.size(22.dp)
                )
                if (hasUnread) {
                    Box(
                        modifier = Modifier
                            .align(Alignment.TopEnd)
                            .offset(x = (-9).dp, y = 8.dp)
                            .size(7.dp)
                            .background(BfhsColors.AccentGold, CircleShape)
                    )
                }
            }
        }

        LazyColumn(
            modifier = Modifier.fillMaxSize(),
            contentPadding = PaddingValues(
                start = Dimens.ScreenPaddingH,
                end = Dimens.ScreenPaddingH,
                top = 18.dp,
                bottom = Dimens.TabContentBottomPadding
            )
        ) {
            item {
                SectionLabel(
                    text = stringResource(R.string.dashboard_my_children),
                    modifier = Modifier.padding(start = 4.dp, top = 6.dp, bottom = 12.dp)
                )
            }
            when (val resource = students) {
                is Resource.Loading -> item { LoadingBox() }
                is Resource.Error -> item { ErrorBox(resource.message) }
                is Resource.Success -> items(resource.data, key = { it.id }) { student ->
                    StudentCard(student = student, onClick = { onStudentClick(student.id) })
                    Spacer(Modifier.height(Dimens.CardGapLarge))
                }
            }
        }
    }
}

@Composable
private fun StudentCard(student: Student, onClick: () -> Unit) {
    GlassCard(
        modifier = Modifier.fillMaxWidth(),
        contentPadding = PaddingValues(18.dp),
        onClick = onClick
    ) {
        Column {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(Dimens.RowGap)
            ) {
                GradientAvatar(initials = student.initials)
                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        text = student.name,
                        color = BfhsColors.TextPrimary,
                        style = MaterialTheme.typography.titleMedium
                    )
                    Text(
                        text = "${student.className} · S/O ${student.fatherName}",
                        color = BfhsColors.TextSecondary,
                        style = MaterialTheme.typography.bodyMedium
                    )
                }
                Icon(
                    Icons.Outlined.ChevronRight,
                    contentDescription = null,
                    tint = BfhsColors.TextHint,
                    modifier = Modifier.size(20.dp)
                )
            }
            Row(
                horizontalArrangement = Arrangement.spacedBy(Dimens.RowGap),
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(top = Dimens.RowGap)
            ) {
                // Today's attendance mini-stat
                MiniStatTile(
                    label = stringResource(R.string.dashboard_today),
                    modifier = Modifier.weight(1f)
                ) {
                    val (icon, color, text) = when (student.todayAttendance) {
                        AttendanceStatus.PRESENT -> Triple(
                            Icons.Outlined.CheckCircle, BfhsColors.Present,
                            stringResource(R.string.status_present)
                        )
                        AttendanceStatus.ABSENT -> Triple(
                            Icons.Outlined.Cancel, BfhsColors.Absent,
                            stringResource(R.string.status_absent)
                        )
                        AttendanceStatus.LEAVE -> Triple(
                            Icons.Outlined.RemoveCircleOutline, BfhsColors.Leave,
                            stringResource(R.string.status_leave)
                        )
                        AttendanceStatus.UNKNOWN -> Triple(
                            Icons.Outlined.RemoveCircleOutline, BfhsColors.TextSecondaryDim, "—"
                        )
                    }
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(5.dp)
                    ) {
                        Icon(icon, contentDescription = null, tint = color, modifier = Modifier.size(15.dp))
                        Text(
                            text = text,
                            color = color,
                            fontSize = 13.sp,
                            fontWeight = androidx.compose.ui.text.font.FontWeight.SemiBold
                        )
                    }
                }
                // Remaining dues mini-stat
                MiniStatTile(
                    label = stringResource(R.string.dashboard_dues),
                    modifier = Modifier.weight(1f)
                ) {
                    Text(
                        text = Formatters.rupees(student.remainingDues),
                        color = BfhsColors.AccentGold,
                        fontSize = 13.sp,
                        fontWeight = androidx.compose.ui.text.font.FontWeight.SemiBold
                    )
                }
            }
        }
    }
}

@Composable
private fun MiniStatTile(
    label: String,
    modifier: Modifier = Modifier,
    content: @Composable () -> Unit
) {
    Column(
        modifier = modifier
            .background(BfhsColors.GlassInnerTile, RoundedCornerShape(14.dp))
            .padding(horizontal = 12.dp, vertical = 10.dp)
    ) {
        Text(
            text = label.uppercase(),
            color = BfhsColors.TextLabel,
            style = MaterialTheme.typography.labelSmall
        )
        Spacer(Modifier.height(3.dp))
        content()
    }
}
