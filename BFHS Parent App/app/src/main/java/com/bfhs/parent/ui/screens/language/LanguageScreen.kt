package com.bfhs.parent.ui.screens.language

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.CheckCircle
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.bfhs.parent.R
import com.bfhs.parent.ui.components.BackHeader
import com.bfhs.parent.ui.theme.BfhsColors
import com.bfhs.parent.ui.viewmodel.SettingsViewModel

/**
 * Language Selection — two selectable cards (English / اردو). The selected card
 * gets a gold border and a gold check-circle. Selection is persisted and applied
 * through Android's per-app locale API.
 */
@Composable
fun LanguageScreen(
    onBack: () -> Unit,
    viewModel: SettingsViewModel = hiltViewModel()
) {
    val language by viewModel.language.collectAsState()

    Column(modifier = Modifier.fillMaxSize()) {
        BackHeader(title = stringResource(R.string.settings_language), onBack = onBack)

        Column(
            verticalArrangement = Arrangement.spacedBy(12.dp),
            modifier = Modifier
                .fillMaxSize()
                .padding(horizontal = 16.dp, vertical = 20.dp)
        ) {
            LanguageCard(
                title = stringResource(R.string.language_english),
                subtitle = stringResource(R.string.language_english_desc),
                selected = language == "en",
                onClick = { viewModel.setLanguage("en") }
            )
            LanguageCard(
                title = stringResource(R.string.language_urdu),
                subtitle = stringResource(R.string.language_urdu_desc),
                selected = language == "ur",
                onClick = { viewModel.setLanguage("ur") }
            )
            Text(
                text = stringResource(R.string.language_footnote),
                color = BfhsColors.TextHint,
                fontSize = 11.5.sp,
                textAlign = TextAlign.Center,
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(top = 8.dp)
            )
        }
    }
}

@Composable
private fun LanguageCard(
    title: String,
    subtitle: String,
    selected: Boolean,
    onClick: () -> Unit
) {
    val shape = RoundedCornerShape(18.dp)
    Row(
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.SpaceBetween,
        modifier = Modifier
            .fillMaxWidth()
            .background(BfhsColors.GlassFill, shape)
            .border(
                width = 1.5.dp,
                color = if (selected) BfhsColors.AccentGold else BfhsColors.InactiveBorder,
                shape = shape
            )
            .clickable(onClick = onClick)
            .padding(18.dp)
    ) {
        Column {
            Text(
                text = title,
                color = BfhsColors.TextPrimary,
                fontSize = 15.sp,
                fontWeight = androidx.compose.ui.text.font.FontWeight.SemiBold
            )
            Text(
                text = subtitle,
                color = BfhsColors.TextSecondaryDim,
                style = MaterialTheme.typography.bodySmall
            )
        }
        if (selected) {
            Icon(
                Icons.Outlined.CheckCircle,
                contentDescription = null,
                tint = BfhsColors.AccentGold,
                modifier = Modifier.size(22.dp)
            )
        }
    }
}
