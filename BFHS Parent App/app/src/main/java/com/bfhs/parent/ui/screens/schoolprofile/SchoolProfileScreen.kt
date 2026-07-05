package com.bfhs.parent.ui.screens.schoolprofile

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.CalendarMonth
import androidx.compose.material.icons.outlined.Call
import androidx.compose.material.icons.outlined.LocationOn
import androidx.compose.material.icons.outlined.MailOutline
import androidx.compose.material.icons.outlined.Person
import androidx.compose.material.icons.outlined.School
import androidx.compose.material3.HorizontalDivider
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
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.bfhs.parent.R
import com.bfhs.parent.core.Resource
import com.bfhs.parent.ui.components.BackHeader
import com.bfhs.parent.ui.components.ErrorBox
import com.bfhs.parent.ui.components.GlassCard
import com.bfhs.parent.ui.components.GradientIconTile
import com.bfhs.parent.ui.components.LoadingBox
import com.bfhs.parent.ui.theme.BfhsColors
import com.bfhs.parent.ui.theme.Dimens
import com.bfhs.parent.ui.viewmodel.SettingsViewModel

/**
 * School Profile — centered icon tile + name + tagline header, then a single
 * glass card of info rows: Principal, Established, Phone, Email, Address.
 */
@Composable
fun SchoolProfileScreen(
    onBack: () -> Unit,
    viewModel: SettingsViewModel = hiltViewModel()
) {
    val school by viewModel.school.collectAsState()

    Column(modifier = Modifier.fillMaxSize()) {
        BackHeader(title = stringResource(R.string.settings_school_profile), onBack = onBack)

        when (val resource = school) {
            is Resource.Loading -> LoadingBox()
            is Resource.Error -> ErrorBox(resource.message)
            is Resource.Success -> {
                val profile = resource.data
                Column(
                    modifier = Modifier
                        .fillMaxSize()
                        .verticalScroll(rememberScrollState())
                        .padding(start = 16.dp, end = 16.dp, top = 12.dp, bottom = 24.dp)
                ) {
                    Column(
                        horizontalAlignment = Alignment.CenterHorizontally,
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(bottom = 20.dp)
                    ) {
                        GradientIconTile(
                            Icons.Outlined.School,
                            size = 72.dp,
                            corner = 22.dp,
                            iconSize = 32.dp
                        )
                        Text(
                            text = profile.name,
                            color = BfhsColors.TextPrimary,
                            fontSize = 18.sp,
                            fontWeight = androidx.compose.ui.text.font.FontWeight.SemiBold,
                            modifier = Modifier.padding(top = 12.dp)
                        )
                        Text(
                            text = profile.tagline,
                            color = BfhsColors.TextSecondaryDim,
                            style = MaterialTheme.typography.bodyMedium,
                            modifier = Modifier.padding(top = 2.dp)
                        )
                    }
                    GlassCard(
                        modifier = Modifier.fillMaxWidth(),
                        contentPadding = PaddingValues(horizontal = 4.dp, vertical = 6.dp)
                    ) {
                        Column {
                            InfoRow(Icons.Outlined.Person, stringResource(R.string.school_principal), profile.principal)
                            HorizontalDivider(color = BfhsColors.Divider, thickness = 1.dp)
                            InfoRow(Icons.Outlined.CalendarMonth, stringResource(R.string.school_established), profile.established)
                            HorizontalDivider(color = BfhsColors.Divider, thickness = 1.dp)
                            InfoRow(Icons.Outlined.Call, stringResource(R.string.school_phone), profile.phone)
                            HorizontalDivider(color = BfhsColors.Divider, thickness = 1.dp)
                            InfoRow(Icons.Outlined.MailOutline, stringResource(R.string.school_email), profile.email)
                            HorizontalDivider(color = BfhsColors.Divider, thickness = 1.dp)
                            InfoRow(Icons.Outlined.LocationOn, stringResource(R.string.school_address), profile.address)
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun InfoRow(icon: ImageVector, label: String, value: String) {
    Row(
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(Dimens.RowGap),
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 14.dp, vertical = 12.dp)
    ) {
        Icon(icon, contentDescription = null, tint = BfhsColors.AccentGold, modifier = Modifier.size(19.dp))
        Column {
            Text(text = label, color = BfhsColors.TextLabel, fontSize = 11.sp)
            Text(
                text = value,
                color = BfhsColors.TextPrimary,
                fontSize = 13.5.sp,
                fontWeight = androidx.compose.ui.text.font.FontWeight.Medium
            )
        }
    }
}
