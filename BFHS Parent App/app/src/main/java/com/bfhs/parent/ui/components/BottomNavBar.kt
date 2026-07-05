package com.bfhs.parent.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Home
import androidx.compose.material.icons.outlined.Notifications
import androidx.compose.material.icons.outlined.Settings
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.bfhs.parent.R
import com.bfhs.parent.ui.theme.BfhsColors
import com.bfhs.parent.ui.theme.Dimens

enum class BottomTab { HOME, NOTICES, SETTINGS }

/**
 * Floating glass pill bottom nav — only shown on the three tab-root screens.
 * Active tab: gold icon + gold-tinted pill chip behind the icon.
 */
@Composable
fun BfhsBottomNavBar(
    current: BottomTab,
    onTabSelected: (BottomTab) -> Unit,
    modifier: Modifier = Modifier
) {
    val shape = RoundedCornerShape(Dimens.BottomNavCorner)
    Row(
        modifier = modifier
            .padding(horizontal = Dimens.BottomNavMarginH)
            .padding(bottom = Dimens.BottomNavMarginB)
            .fillMaxWidth()
            .height(Dimens.BottomNavHeight)
            .background(BfhsColors.GlassFillStrong, shape)
            .border(1.dp, Color(0x29FFFFFF), shape),
        horizontalArrangement = Arrangement.SpaceAround,
        verticalAlignment = Alignment.CenterVertically
    ) {
        NavItem(Icons.Outlined.Home, stringResource(R.string.nav_home), current == BottomTab.HOME) {
            onTabSelected(BottomTab.HOME)
        }
        NavItem(Icons.Outlined.Notifications, stringResource(R.string.nav_notices), current == BottomTab.NOTICES) {
            onTabSelected(BottomTab.NOTICES)
        }
        NavItem(Icons.Outlined.Settings, stringResource(R.string.nav_settings), current == BottomTab.SETTINGS) {
            onTabSelected(BottomTab.SETTINGS)
        }
    }
}

@Composable
private fun NavItem(
    icon: ImageVector,
    label: String,
    active: Boolean,
    onClick: () -> Unit
) {
    val tint = if (active) BfhsColors.AccentGold else BfhsColors.TextSecondaryDim
    Column(
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(2.dp),
        modifier = Modifier.clickable(onClick = onClick)
    ) {
        Box(
            modifier = Modifier
                .width(44.dp)
                .height(26.dp)
                .background(
                    if (active) BfhsColors.AccentGoldActive else Color.Transparent,
                    RoundedCornerShape(14.dp)
                ),
            contentAlignment = Alignment.Center
        ) {
            Icon(icon, contentDescription = label, tint = tint, modifier = Modifier.size(19.dp))
        }
        Text(text = label, color = tint, style = MaterialTheme.typography.labelSmall)
    }
}
