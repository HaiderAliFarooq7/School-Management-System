package com.bfhs.parent.ui.screens.charges

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
import com.bfhs.parent.ui.components.StatusPill
import com.bfhs.parent.ui.theme.BfhsColors
import com.bfhs.parent.ui.theme.Dimens
import com.bfhs.parent.ui.viewmodel.StudentDetailViewModel

/**
 * Extra Charges — stack of glass cards: title + status pill on top,
 * date + gold amount on the bottom row.
 */
@Composable
fun ExtraChargesScreen(
    onBack: () -> Unit,
    viewModel: StudentDetailViewModel = hiltViewModel()
) {
    val student by viewModel.student.collectAsState()
    val charges by viewModel.charges.collectAsState()

    Column(modifier = Modifier.fillMaxSize()) {
        BackHeader(title = stringResource(R.string.detail_extra_charges), onBack = onBack)

        when (val resource = charges) {
            is Resource.Loading -> LoadingBox()
            is Resource.Error -> ErrorBox(resource.message)
            is Resource.Success -> LazyColumn(
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
                items(resource.data, key = { it.id }) { charge ->
                    GlassCard(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(bottom = Dimens.CardGap)
                    ) {
                        Column {
                            Row(
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.SpaceBetween,
                                modifier = Modifier.fillMaxWidth()
                            ) {
                                Text(
                                    text = charge.title,
                                    color = BfhsColors.TextPrimary,
                                    style = MaterialTheme.typography.titleSmall
                                )
                                if (charge.status == PaymentStatus.UNPAID) {
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
                            Spacer(Modifier.height(8.dp))
                            Row(
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.SpaceBetween,
                                modifier = Modifier.fillMaxWidth()
                            ) {
                                Text(
                                    text = charge.dateLabel,
                                    color = BfhsColors.TextSecondaryDim,
                                    style = MaterialTheme.typography.bodySmall
                                )
                                Text(
                                    text = Formatters.rupees(charge.amount),
                                    color = BfhsColors.AccentGold,
                                    fontSize = 14.sp,
                                    fontWeight = androidx.compose.ui.text.font.FontWeight.SemiBold
                                )
                            }
                        }
                    }
                }
            }
        }
    }
}
