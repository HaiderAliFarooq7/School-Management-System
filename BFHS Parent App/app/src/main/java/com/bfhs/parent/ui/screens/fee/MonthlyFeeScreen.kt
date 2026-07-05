package com.bfhs.parent.ui.screens.fee

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
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
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.bfhs.parent.R
import com.bfhs.parent.core.Resource
import com.bfhs.parent.core.utils.Formatters
import com.bfhs.parent.domain.models.PaymentStatus
import com.bfhs.parent.ui.components.BackHeader
import com.bfhs.parent.ui.components.ErrorBox
import com.bfhs.parent.ui.components.GlassCard
import com.bfhs.parent.ui.components.LoadingBox
import com.bfhs.parent.ui.components.SectionLabel
import com.bfhs.parent.ui.components.StatusPill
import com.bfhs.parent.ui.theme.BfhsColors
import com.bfhs.parent.ui.theme.Dimens
import com.bfhs.parent.ui.viewmodel.StudentDetailViewModel

/**
 * Monthly Fee — hero glass card (month + status pill, large gold amount, due date,
 * "view only" footer note) followed by the HISTORY list. No pay button, ever.
 */
@Composable
fun MonthlyFeeScreen(
    onBack: () -> Unit,
    viewModel: StudentDetailViewModel = hiltViewModel()
) {
    val student by viewModel.student.collectAsState()
    val fees by viewModel.fees.collectAsState()

    Column(modifier = Modifier.fillMaxSize()) {
        BackHeader(title = stringResource(R.string.detail_monthly_fee), onBack = onBack)

        when (val resource = fees) {
            is Resource.Loading -> LoadingBox()
            is Resource.Error -> ErrorBox(resource.message)
            is Resource.Success -> {
                val overview = resource.data
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
                            text = student?.name.orEmpty(),
                            color = BfhsColors.TextSecondaryDim,
                            style = MaterialTheme.typography.bodyMedium,
                            modifier = Modifier.padding(start = 2.dp, bottom = 14.dp)
                        )
                    }
                    overview.current?.let { current ->
                        item {
                            GlassCard(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .padding(bottom = 18.dp),
                                contentPadding = PaddingValues(20.dp)
                            ) {
                                Column {
                                    Row(
                                        verticalAlignment = Alignment.CenterVertically,
                                        horizontalArrangement = Arrangement.SpaceBetween,
                                        modifier = Modifier.fillMaxWidth()
                                    ) {
                                        Text(
                                            text = current.month,
                                            color = BfhsColors.TextSecondary,
                                            style = MaterialTheme.typography.labelMedium.copy(fontSize = 13.sp)
                                        )
                                        if (current.status == PaymentStatus.UNPAID) {
                                            StatusPill(
                                                text = stringResource(R.string.status_unpaid),
                                                color = BfhsColors.Absent,
                                                background = BfhsColors.AbsentChip
                                            )
                                        } else {
                                            StatusPill(
                                                text = stringResource(R.string.status_paid),
                                                color = BfhsColors.Present,
                                                background = BfhsColors.PresentChip
                                            )
                                        }
                                    }
                                    Text(
                                        text = Formatters.rupees(current.amount),
                                        color = BfhsColors.AccentGold,
                                        style = MaterialTheme.typography.displaySmall,
                                        modifier = Modifier.padding(top = 8.dp)
                                    )
                                    current.dueDate?.let { due ->
                                        Text(
                                            text = stringResource(R.string.fee_due, due),
                                            color = BfhsColors.TextSecondaryDim,
                                            style = MaterialTheme.typography.bodySmall,
                                            modifier = Modifier.padding(top = 4.dp)
                                        )
                                    }
                                    Spacer(Modifier.height(14.dp))
                                    HorizontalDivider(color = BfhsColors.Divider, thickness = 1.dp)
                                    Text(
                                        text = stringResource(R.string.fee_view_only),
                                        color = BfhsColors.TextHint,
                                        fontSize = 11.sp,
                                        modifier = Modifier.padding(top = 12.dp)
                                    )
                                }
                            }
                        }
                    }
                    item {
                        SectionLabel(
                            text = stringResource(R.string.fee_history),
                            modifier = Modifier.padding(start = 2.dp, bottom = 10.dp)
                        )
                    }
                    items(overview.history) { fee ->
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.SpaceBetween,
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(horizontal = 6.dp, vertical = 12.dp)
                        ) {
                            Column {
                                Text(
                                    text = fee.month,
                                    color = BfhsColors.TextPrimary,
                                    fontSize = 13.5.sp,
                                    fontWeight = androidx.compose.ui.text.font.FontWeight.Medium
                                )
                                Text(
                                    text = Formatters.rupees(fee.amount),
                                    color = BfhsColors.TextSecondaryDim,
                                    style = MaterialTheme.typography.bodySmall
                                )
                            }
                            if (fee.status == PaymentStatus.PAID) {
                                StatusPill(
                                    text = stringResource(R.string.status_paid),
                                    color = BfhsColors.Present,
                                    background = BfhsColors.PresentChip
                                )
                            } else {
                                StatusPill(
                                    text = stringResource(R.string.status_unpaid),
                                    color = BfhsColors.Absent,
                                    background = BfhsColors.AbsentChip
                                )
                            }
                        }
                        HorizontalDivider(color = BfhsColors.Divider, thickness = 1.dp)
                    }
                }
            }
        }
    }
}
