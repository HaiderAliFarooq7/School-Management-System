package com.bfhs.parent.ui.screens.studentdetail

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.outlined.ChevronRight
import androidx.compose.material.icons.outlined.EventAvailable
import androidx.compose.material.icons.outlined.Payments
import androidx.compose.material.icons.outlined.ReceiptLong
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.bfhs.parent.R
import com.bfhs.parent.core.Resource
import com.bfhs.parent.core.utils.Formatters
import com.bfhs.parent.domain.models.AttendanceStatus
import com.bfhs.parent.domain.models.PaymentStatus
import com.bfhs.parent.ui.components.GlassCard
import com.bfhs.parent.ui.components.GoldIconChip
import com.bfhs.parent.ui.components.GradientAvatar
import com.bfhs.parent.ui.theme.BfhsColors
import com.bfhs.parent.ui.theme.Dimens
import com.bfhs.parent.ui.viewmodel.StudentDetailViewModel

/**
 * Student Detail — centered avatar/name header, then three glass quick-access rows
 * (Attendance / Monthly Fee / Extra Charges) and the "coming soon" footer note.
 */
@Composable
fun StudentDetailScreen(
    onBack: () -> Unit,
    onAttendance: (String) -> Unit,
    onFee: (String) -> Unit,
    onCharges: (String) -> Unit,
    viewModel: StudentDetailViewModel = hiltViewModel()
) {
    val student by viewModel.student.collectAsState()
    val attendance by viewModel.attendance.collectAsState()
    val fees by viewModel.fees.collectAsState()
    val charges by viewModel.charges.collectAsState()

    Column(modifier = Modifier.fillMaxSize()) {
        Icon(
            imageVector = Icons.AutoMirrored.Filled.ArrowBack,
            contentDescription = null,
            tint = BfhsColors.TextPrimary,
            modifier = Modifier
                .padding(start = 16.dp, top = 16.dp)
                .size(22.dp)
                .clickable(onClick = onBack)
        )

        // Centered header
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            modifier = Modifier
                .fillMaxWidth()
                .padding(start = 20.dp, end = 20.dp, top = 8.dp, bottom = 20.dp)
        ) {
            GradientAvatar(
                initials = student?.initials ?: "",
                size = Dimens.AvatarLargeSize,
                corner = Dimens.AvatarLargeCorner,
                fontSize = 26.sp
            )
            Text(
                text = student?.name.orEmpty(),
                color = BfhsColors.TextPrimary,
                style = MaterialTheme.typography.headlineSmall,
                modifier = Modifier.padding(top = 12.dp)
            )
            Text(
                text = student?.let {
                    "${it.className} · ${stringResource(R.string.detail_father)}: ${it.fatherName}"
                }.orEmpty(),
                color = BfhsColors.TextSecondary,
                style = MaterialTheme.typography.bodyLarge.copy(fontSize = 13.sp),
                modifier = Modifier.padding(top = 2.dp)
            )
        }

        Column(
            verticalArrangement = Arrangement.spacedBy(Dimens.CardGap),
            modifier = Modifier
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .padding(start = 16.dp, end = 16.dp, top = 4.dp, bottom = 24.dp)
        ) {
            val attendanceSupport = when (val a = attendance) {
                is Resource.Success -> {
                    val today = when (student?.todayAttendance) {
                        AttendanceStatus.PRESENT -> stringResource(R.string.detail_present_today)
                        AttendanceStatus.ABSENT -> stringResource(R.string.detail_absent_today)
                        AttendanceStatus.LEAVE -> stringResource(R.string.detail_leave_today)
                        else -> ""
                    }
                    val percent = stringResource(R.string.detail_percent_this_month, a.data.overallPercent)
                    if (today.isNotEmpty()) "$today · $percent" else percent
                }
                else -> stringResource(R.string.detail_view_daily_record)
            }
            DetailRow(
                icon = Icons.Outlined.EventAvailable,
                title = stringResource(R.string.detail_attendance),
                support = attendanceSupport,
                onClick = { onAttendance(viewModel.studentId) }
            )

            val feeSupport = when (val f = fees) {
                is Resource.Success -> f.data.current?.let { current ->
                    if (current.status == PaymentStatus.UNPAID) {
                        stringResource(
                            R.string.detail_fee_due,
                            Formatters.rupees(current.amount),
                            current.month
                        )
                    } else {
                        stringResource(R.string.detail_fee_paid, current.month)
                    }
                } ?: stringResource(R.string.detail_view_fee)
                else -> stringResource(R.string.detail_view_fee)
            }
            DetailRow(
                icon = Icons.Outlined.Payments,
                title = stringResource(R.string.detail_monthly_fee),
                support = feeSupport,
                onClick = { onFee(viewModel.studentId) }
            )

            val chargesSupport = when (val c = charges) {
                is Resource.Success -> {
                    val pending = c.data.filter { it.status == PaymentStatus.UNPAID }
                    if (pending.isNotEmpty()) {
                        stringResource(
                            R.string.detail_charges_pending,
                            pending.size,
                            Formatters.rupees(pending.sumOf { it.amount })
                        )
                    } else {
                        stringResource(R.string.detail_charges_none)
                    }
                }
                else -> stringResource(R.string.detail_view_charges)
            }
            DetailRow(
                icon = Icons.Outlined.ReceiptLong,
                title = stringResource(R.string.detail_extra_charges),
                support = chargesSupport,
                onClick = { onCharges(viewModel.studentId) }
            )

            Text(
                text = stringResource(R.string.detail_coming_soon),
                color = BfhsColors.TextHint,
                fontSize = 11.sp,
                textAlign = TextAlign.Center,
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(top = 8.dp)
            )
        }
    }
}

@Composable
private fun DetailRow(
    icon: ImageVector,
    title: String,
    support: String,
    onClick: () -> Unit
) {
    GlassCard(modifier = Modifier.fillMaxWidth(), onClick = onClick) {
        Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(Dimens.RowGap)
        ) {
            GoldIconChip(icon)
            Column(modifier = Modifier.weight(1f)) {
                Text(text = title, color = BfhsColors.TextPrimary, style = MaterialTheme.typography.titleSmall)
                Text(text = support, color = BfhsColors.TextSecondaryDim, style = MaterialTheme.typography.bodySmall)
            }
            Icon(
                Icons.Outlined.ChevronRight,
                contentDescription = null,
                tint = BfhsColors.TextHint,
                modifier = Modifier.size(20.dp)
            )
        }
    }
}
