package com.bfhs.parent.ui.screens.settings

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
import androidx.compose.material.icons.automirrored.outlined.Logout
import androidx.compose.material.icons.outlined.ChevronRight
import androidx.compose.material.icons.outlined.Info
import androidx.compose.material.icons.outlined.Language
import androidx.compose.material.icons.outlined.Person
import androidx.compose.material.icons.outlined.School
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.bfhs.parent.R
import com.bfhs.parent.ui.components.GlassCard
import com.bfhs.parent.ui.components.GradientIconTile
import com.bfhs.parent.ui.theme.BfhsColors
import com.bfhs.parent.ui.theme.Dimens
import com.bfhs.parent.ui.viewmodel.SettingsViewModel

/**
 * Settings (tab root) — account summary row, then School Profile / Language /
 * About School glass rows, and a separated red Log Out row.
 */
@Composable
fun SettingsScreen(
    onSchoolProfile: () -> Unit,
    onLanguage: () -> Unit,
    onAbout: () -> Unit,
    onLoggedOut: () -> Unit,
    viewModel: SettingsViewModel = hiltViewModel()
) {
    val parent by viewModel.parent.collectAsState()
    val language by viewModel.language.collectAsState()

    Column(modifier = Modifier.fillMaxSize()) {
        Text(
            text = stringResource(R.string.settings_title),
            color = BfhsColors.TextPrimary,
            fontSize = 20.sp,
            fontWeight = androidx.compose.ui.text.font.FontWeight.SemiBold,
            modifier = Modifier.padding(start = 20.dp, end = 20.dp, top = 18.dp, bottom = 14.dp)
        )
        Column(
            verticalArrangement = Arrangement.spacedBy(10.dp),
            modifier = Modifier
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .padding(
                    start = Dimens.ScreenPaddingH,
                    end = Dimens.ScreenPaddingH,
                    top = 6.dp,
                    bottom = Dimens.TabContentBottomPadding
                )
        ) {
            // Account summary (non-interactive)
            GlassCard(modifier = Modifier.fillMaxWidth()) {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(Dimens.RowGap)
                ) {
                    GradientIconTile(Icons.Outlined.Person)
                    Column {
                        Text(
                            text = parent?.name.orEmpty(),
                            color = BfhsColors.TextPrimary,
                            style = MaterialTheme.typography.titleSmall
                        )
                        Text(
                            text = parent?.mobileNumber.orEmpty(),
                            color = BfhsColors.TextSecondaryDim,
                            style = MaterialTheme.typography.bodySmall
                        )
                    }
                }
            }

            SettingsRow(
                icon = Icons.Outlined.School,
                label = stringResource(R.string.settings_school_profile),
                onClick = onSchoolProfile
            )
            SettingsRow(
                icon = Icons.Outlined.Language,
                label = stringResource(R.string.settings_language),
                trailing = if (language == "ur") stringResource(R.string.language_urdu_short)
                else stringResource(R.string.language_english),
                onClick = onLanguage
            )
            SettingsRow(
                icon = Icons.Outlined.Info,
                label = stringResource(R.string.settings_about_school),
                onClick = onAbout
            )

            // Log Out — red, visually separated
            GlassCard(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(top = 8.dp),
                onClick = { viewModel.logout(onLoggedOut) }
            ) {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(Dimens.RowGap)
                ) {
                    Icon(
                        Icons.AutoMirrored.Outlined.Logout,
                        contentDescription = null,
                        tint = BfhsColors.Absent,
                        modifier = Modifier.size(22.dp)
                    )
                    Text(
                        text = stringResource(R.string.settings_logout),
                        color = BfhsColors.Absent,
                        fontSize = 14.5.sp,
                        fontWeight = androidx.compose.ui.text.font.FontWeight.Medium
                    )
                }
            }
        }
    }
}

@Composable
private fun SettingsRow(
    icon: ImageVector,
    label: String,
    trailing: String? = null,
    onClick: () -> Unit
) {
    GlassCard(modifier = Modifier.fillMaxWidth(), onClick = onClick) {
        Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(Dimens.RowGap)
        ) {
            Icon(icon, contentDescription = null, tint = BfhsColors.AccentGold, modifier = Modifier.size(22.dp))
            Text(
                text = label,
                color = BfhsColors.TextPrimary,
                fontSize = 14.5.sp,
                fontWeight = androidx.compose.ui.text.font.FontWeight.Medium,
                modifier = Modifier.weight(1f)
            )
            trailing?.let {
                Text(text = it, color = BfhsColors.TextTertiary, style = MaterialTheme.typography.bodyMedium)
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
