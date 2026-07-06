package com.bfhs.parent.ui.screens.studentdetail

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.bfhs.parent.R
import com.bfhs.parent.core.Resource
import com.bfhs.parent.core.utils.Formatters
import com.bfhs.parent.domain.models.AttendanceStatus
import com.bfhs.parent.domain.models.AttendanceSummary
import com.bfhs.parent.domain.models.ExtraCharge
import com.bfhs.parent.domain.models.FeeOverview
import com.bfhs.parent.domain.models.MonthlyFee
import com.bfhs.parent.domain.models.PaymentStatus
import com.bfhs.parent.ui.components.GlassCard
import com.bfhs.parent.ui.components.GradientAvatar
import com.bfhs.parent.ui.components.LoadingBox
import com.bfhs.parent.ui.components.SectionLabel
import com.bfhs.parent.ui.components.StatusPill
import com.bfhs.parent.ui.theme.BfhsColors
import com.bfhs.parent.ui.theme.Dimens
import com.bfhs.parent.ui.viewmodel.StudentDetailViewModel
import java.time.LocalDate
import java.time.YearMonth
import java.time.format.DateTimeFormatter
import java.util.Locale

/**
 * Student Detail — one consolidated, read-only screen: a monthly attendance
 * calendar on top, then the total remaining dues, pending monthly fees, and
 * extra charges below. No sub-navigation — everything is here.
 */
@Composable
fun StudentDetailScreen(
    onBack: () -> Unit,
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

        Column(
            verticalArrangement = Arrangement.spacedBy(Dimens.CardGap),
            modifier = Modifier
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .padding(start = 16.dp, end = 16.dp, top = 4.dp, bottom = 28.dp)
        ) {
            // Header
            Column(
                horizontalAlignment = Alignment.CenterHorizontally,
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(bottom = 4.dp)
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

            // Attendance calendar
            SectionLabel(stringResource(R.string.detail_attendance), Modifier.padding(start = 4.dp, top = 4.dp))
            when (val a = attendance) {
                is Resource.Loading -> LoadingBox()
                is Resource.Error -> InfoNote(a.message)
                is Resource.Success -> AttendanceCalendarCard(a.data)
            }

            // Dues + fees + charges
            SectionLabel(stringResource(R.string.detail_fees_dues), Modifier.padding(start = 4.dp, top = 8.dp))
            DuesSummaryCard(student?.remainingDues ?: 0L)

            when (val f = fees) {
                is Resource.Loading -> LoadingBox()
                is Resource.Error -> InfoNote(f.message)
                is Resource.Success -> PendingFeesCard(f.data)
            }

            when (val c = charges) {
                is Resource.Loading -> LoadingBox()
                is Resource.Error -> InfoNote(c.message)
                is Resource.Success -> ExtraChargesCard(c.data)
            }
        }
    }
}

// --------------------------------------------------------------------------- //
// Attendance calendar
// --------------------------------------------------------------------------- //

@Composable
private fun AttendanceCalendarCard(summary: AttendanceSummary) {
    GlassCard(modifier = Modifier.fillMaxWidth(), contentPadding = androidx.compose.foundation.layout.PaddingValues(16.dp)) {
        Column {
            Text(
                text = summary.month,
                color = BfhsColors.TextPrimary,
                style = MaterialTheme.typography.titleSmall
            )
            Spacer(Modifier.height(12.dp))
            MonthGrid(summary)
            Spacer(Modifier.height(14.dp))
            HorizontalDivider(color = BfhsColors.Divider, thickness = 1.dp)
            Spacer(Modifier.height(12.dp))
            // Summary counts
            Row(
                horizontalArrangement = Arrangement.SpaceAround,
                modifier = Modifier.fillMaxWidth()
            ) {
                Stat(summary.presentCount.toString(), stringResource(R.string.status_present), BfhsColors.Present)
                Stat(summary.absentCount.toString(), stringResource(R.string.status_absent), BfhsColors.Absent)
                Stat(summary.leaveCount.toString(), stringResource(R.string.status_leave), BfhsColors.Leave)
                Stat("${summary.overallPercent}%", stringResource(R.string.attendance_overall), BfhsColors.AccentGold)
            }
        }
    }
}

private val WEEKDAYS = listOf("S", "M", "T", "W", "T", "F", "S")

@Composable
private fun MonthGrid(summary: AttendanceSummary) {
    // Parse the month ("July 2026") and map each day-of-month to its status.
    val yearMonth = rememberYearMonth(summary.month)
    if (yearMonth == null) {
        // Fallback: can't build a calendar, just list the records.
        Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
            summary.records.take(10).forEach { r ->
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    Text(r.date, color = BfhsColors.TextRow, fontSize = 13.sp)
                    Text(r.status.name, color = colorFor(r.status), fontSize = 12.sp)
                }
            }
        }
        return
    }

    val statusByDay = HashMap<Int, AttendanceStatus>()
    val dayFmt = DateTimeFormatter.ofPattern("EEE, d MMM yyyy", Locale.ENGLISH)
    summary.records.forEach { r ->
        runCatching { LocalDate.parse(r.date, dayFmt) }.getOrNull()?.let { d ->
            if (d.year == yearMonth.year && d.monthValue == yearMonth.monthValue) {
                statusByDay[d.dayOfMonth] = r.status
            }
        }
    }

    val daysInMonth = yearMonth.lengthOfMonth()
    // Sunday-first grid: leading blanks before day 1.
    val firstDow = LocalDate.of(yearMonth.year, yearMonth.monthValue, 1).dayOfWeek.value % 7
    val cells = ArrayList<Int?>()
    repeat(firstDow) { cells.add(null) }
    for (d in 1..daysInMonth) cells.add(d)
    while (cells.size % 7 != 0) cells.add(null)

    Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
        Row(Modifier.fillMaxWidth()) {
            WEEKDAYS.forEach { w ->
                Text(
                    w, color = BfhsColors.TextSecondaryDim, fontSize = 11.sp,
                    textAlign = TextAlign.Center, modifier = Modifier.weight(1f)
                )
            }
        }
        cells.chunked(7).forEach { week ->
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                week.forEach { day ->
                    DayCell(day, day?.let { statusByDay[it] }, Modifier.weight(1f))
                }
            }
        }
        Spacer(Modifier.height(2.dp))
        Row(horizontalArrangement = Arrangement.spacedBy(14.dp)) {
            LegendDot(stringResource(R.string.status_present), BfhsColors.Present)
            LegendDot(stringResource(R.string.status_absent), BfhsColors.Absent)
            LegendDot(stringResource(R.string.status_leave), BfhsColors.Leave)
        }
    }
}

@Composable
private fun DayCell(day: Int?, status: AttendanceStatus?, modifier: Modifier) {
    if (day == null) {
        Box(modifier.size(34.dp))
        return
    }
    val bg = when (status) {
        AttendanceStatus.PRESENT -> BfhsColors.PresentChip
        AttendanceStatus.ABSENT -> BfhsColors.AbsentChip
        AttendanceStatus.LEAVE -> BfhsColors.LeaveChip
        else -> BfhsColors.GlassInnerTile
    }
    val fg = when (status) {
        AttendanceStatus.PRESENT -> BfhsColors.Present
        AttendanceStatus.ABSENT -> BfhsColors.Absent
        AttendanceStatus.LEAVE -> BfhsColors.Leave
        else -> BfhsColors.TextSecondaryDim
    }
    Box(
        modifier = modifier
            .padding(vertical = 1.dp)
            .background(bg, RoundedCornerShape(10.dp))
            .padding(vertical = 8.dp),
        contentAlignment = Alignment.Center
    ) {
        Text(day.toString(), color = fg, fontSize = 12.5.sp, fontWeight = FontWeight.Medium)
    }
}

@Composable
private fun LegendDot(label: String, color: Color) {
    Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(4.dp)) {
        Box(Modifier.size(8.dp).background(color, CircleShape))
        Text(label, color = BfhsColors.TextSecondaryDim, fontSize = 10.5.sp)
    }
}

@Composable
private fun rememberYearMonth(month: String): YearMonth? =
    runCatching { YearMonth.parse(month, DateTimeFormatter.ofPattern("MMMM yyyy", Locale.ENGLISH)) }.getOrNull()

private fun colorFor(status: AttendanceStatus) = when (status) {
    AttendanceStatus.PRESENT -> BfhsColors.Present
    AttendanceStatus.ABSENT -> BfhsColors.Absent
    AttendanceStatus.LEAVE -> BfhsColors.Leave
    else -> BfhsColors.TextSecondaryDim
}

// --------------------------------------------------------------------------- //
// Fees & charges
// --------------------------------------------------------------------------- //

@Composable
private fun DuesSummaryCard(remainingDues: Long) {
    GlassCard(modifier = Modifier.fillMaxWidth(), contentPadding = androidx.compose.foundation.layout.PaddingValues(18.dp)) {
        Column {
            Text(
                text = stringResource(R.string.detail_total_dues).uppercase(),
                color = BfhsColors.TextLabel,
                style = MaterialTheme.typography.labelSmall
            )
            Spacer(Modifier.height(4.dp))
            Text(
                text = Formatters.rupees(remainingDues),
                color = BfhsColors.AccentGold,
                style = MaterialTheme.typography.displaySmall
            )
            Text(
                text = stringResource(R.string.fee_view_only),
                color = BfhsColors.TextHint,
                fontSize = 11.sp,
                modifier = Modifier.padding(top = 8.dp)
            )
        }
    }
}

@Composable
private fun PendingFeesCard(overview: FeeOverview) {
    val pending = buildList {
        overview.current?.let { if (it.status == PaymentStatus.UNPAID) add(it) }
        overview.history.forEach { if (it.status == PaymentStatus.UNPAID) add(it) }
    }
    GlassCard(modifier = Modifier.fillMaxWidth()) {
        Column {
            Text(
                text = stringResource(R.string.detail_monthly_fee),
                color = BfhsColors.TextPrimary,
                style = MaterialTheme.typography.titleSmall
            )
            Spacer(Modifier.height(8.dp))
            if (pending.isEmpty()) {
                Text(
                    text = stringResource(R.string.detail_fees_all_paid),
                    color = BfhsColors.Present,
                    style = MaterialTheme.typography.bodyMedium
                )
            } else {
                pending.forEachIndexed { i, fee ->
                    FeeRow(fee)
                    if (i < pending.size - 1) HorizontalDivider(color = BfhsColors.Divider, thickness = 1.dp)
                }
            }
        }
    }
}

@Composable
private fun FeeRow(fee: MonthlyFee) {
    Row(
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.SpaceBetween,
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 10.dp)
    ) {
        Column {
            Text(fee.month, color = BfhsColors.TextPrimary, fontSize = 13.5.sp, fontWeight = FontWeight.Medium)
            fee.dueDate?.let {
                Text(stringResource(R.string.fee_due, it), color = BfhsColors.TextSecondaryDim, fontSize = 11.sp)
            }
        }
        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            Text(Formatters.rupees(fee.amount), color = BfhsColors.AccentGold, fontSize = 14.sp, fontWeight = FontWeight.SemiBold)
            StatusPill(stringResource(R.string.status_unpaid), BfhsColors.Absent, BfhsColors.AbsentChip)
        }
    }
}

@Composable
private fun ExtraChargesCard(charges: List<ExtraCharge>) {
    // Only pending (unpaid) charges are shown — paid ones are hidden.
    val pending = charges.filter { it.status == PaymentStatus.UNPAID }
    GlassCard(modifier = Modifier.fillMaxWidth()) {
        Column {
            Text(
                text = stringResource(R.string.detail_extra_charges),
                color = BfhsColors.TextPrimary,
                style = MaterialTheme.typography.titleSmall
            )
            Spacer(Modifier.height(8.dp))
            if (pending.isEmpty()) {
                Text(
                    text = stringResource(R.string.detail_charges_none),
                    color = BfhsColors.TextSecondaryDim,
                    style = MaterialTheme.typography.bodyMedium
                )
            } else {
                pending.forEachIndexed { i, charge ->
                    ChargeRow(charge)
                    if (i < pending.size - 1) HorizontalDivider(color = BfhsColors.Divider, thickness = 1.dp)
                }
            }
        }
    }
}

@Composable
private fun ChargeRow(charge: ExtraCharge) {
    val unpaid = charge.status == PaymentStatus.UNPAID
    Row(
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.SpaceBetween,
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 10.dp)
    ) {
        Column(modifier = Modifier.weight(1f)) {
            Text(charge.title, color = BfhsColors.TextPrimary, fontSize = 13.5.sp, fontWeight = FontWeight.Medium)
            Text(charge.dateLabel, color = BfhsColors.TextSecondaryDim, fontSize = 11.sp)
        }
        Spacer(Modifier.width(8.dp))
        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            Text(Formatters.rupees(charge.amount), color = BfhsColors.AccentGold, fontSize = 14.sp, fontWeight = FontWeight.SemiBold)
            if (unpaid) {
                StatusPill(stringResource(R.string.status_unpaid), BfhsColors.Absent, BfhsColors.AbsentChip)
            } else {
                StatusPill(stringResource(R.string.status_paid), BfhsColors.Present, BfhsColors.PresentChip)
            }
        }
    }
}

// --------------------------------------------------------------------------- //

@Composable
private fun Stat(value: String, label: String, color: Color) {
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Text(value, color = color, fontSize = 20.sp, fontWeight = FontWeight.SemiBold)
        Text(label, color = BfhsColors.TextSecondaryDim, fontSize = 11.sp)
    }
}

@Composable
private fun InfoNote(message: String) {
    Text(
        text = message,
        color = BfhsColors.TextSecondaryDim,
        style = MaterialTheme.typography.bodyMedium,
        modifier = Modifier.padding(horizontal = 4.dp, vertical = 8.dp)
    )
}
