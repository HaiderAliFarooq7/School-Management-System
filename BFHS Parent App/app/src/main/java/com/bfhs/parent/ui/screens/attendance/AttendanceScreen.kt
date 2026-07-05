package com.bfhs.parent.ui.screens.attendance

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.HorizontalDivider
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
import com.bfhs.parent.domain.models.AttendanceStatus
import com.bfhs.parent.ui.components.BackHeader
import com.bfhs.parent.ui.components.ErrorBox
import com.bfhs.parent.ui.components.GlassCard
import com.bfhs.parent.ui.components.LoadingBox
import com.bfhs.parent.ui.components.StatusPill
import com.bfhs.parent.ui.theme.BfhsColors
import com.bfhs.parent.ui.theme.Dimens
import com.bfhs.parent.ui.viewmodel.StudentDetailViewModel

/**
 * Attendance — summary glass card with 4 stat columns (Present / Absent / Leave /
 * Overall %), then a plain divided list of dated rows with status pills.
 */
@Composable
fun AttendanceScreen(
    onBack: () -> Unit,
    viewModel: StudentDetailViewModel = hiltViewModel()
) {
    val student by viewModel.student.collectAsState()
    val attendance by viewModel.attendance.collectAsState()

    Column(modifier = Modifier.fillMaxSize()) {
        BackHeader(title = stringResource(R.string.detail_attendance), onBack = onBack)

        when (val resource = attendance) {
            is Resource.Loading -> LoadingBox()
            is Resource.Error -> ErrorBox(resource.message)
            is Resource.Success -> {
                val summary = resource.data
                LazyColumn(
                    contentPadding = PaddingValues(
                        start = Dimens.ScreenPaddingH,
                        end = Dimens.ScreenPaddingH,
                        top = 14.dp,
                        bottom = 24.dp
                    )
                ) {
                    item {
                        Text(
                            text = "${student?.name.orEmpty()} · ${summary.month}",
                            color = BfhsColors.TextSecondaryDim,
                            style = MaterialTheme.typography.bodyMedium,
                            modifier = Modifier.padding(start = 2.dp, bottom = 14.dp)
                        )
                        GlassCard(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(bottom = 16.dp),
                            contentPadding = PaddingValues(18.dp)
                        ) {
                            Row(
                                horizontalArrangement = Arrangement.SpaceAround,
                                modifier = Modifier.fillMaxWidth()
                            ) {
                                StatColumn(summary.presentCount.toString(), stringResource(R.string.status_present), BfhsColors.Present)
                                StatColumn(summary.absentCount.toString(), stringResource(R.string.status_absent), BfhsColors.Absent)
                                StatColumn(summary.leaveCount.toString(), stringResource(R.string.status_leave), BfhsColors.Leave)
                                StatColumn("${summary.overallPercent}%", stringResource(R.string.attendance_overall), BfhsColors.AccentGold)
                            }
                        }
                    }
                    items(summary.records) { record ->
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.SpaceBetween,
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(horizontal = 6.dp, vertical = 12.dp)
                        ) {
                            Text(
                                text = record.date,
                                color = BfhsColors.TextRow,
                                fontSize = 13.5.sp
                            )
                            val (label, color, bg) = when (record.status) {
                                AttendanceStatus.PRESENT -> Triple(stringResource(R.string.status_present), BfhsColors.Present, BfhsColors.PresentChip)
                                AttendanceStatus.ABSENT -> Triple(stringResource(R.string.status_absent), BfhsColors.Absent, BfhsColors.AbsentChip)
                                AttendanceStatus.LEAVE -> Triple(stringResource(R.string.status_leave), BfhsColors.Leave, BfhsColors.LeaveChip)
                                AttendanceStatus.UNKNOWN -> Triple("—", BfhsColors.TextSecondaryDim, BfhsColors.GlassInnerTile)
                            }
                            StatusPill(text = label, color = color, background = bg)
                        }
                        HorizontalDivider(color = BfhsColors.Divider, thickness = 1.dp)
                    }
                }
            }
        }
    }
}

@Composable
private fun StatColumn(value: String, label: String, color: Color) {
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Text(
            text = value,
            color = color,
            fontSize = 22.sp,
            fontWeight = FontWeight.SemiBold,
            textAlign = TextAlign.Center
        )
        Text(
            text = label,
            color = BfhsColors.TextSecondaryDim,
            fontSize = 11.sp,
            textAlign = TextAlign.Center
        )
    }
}
