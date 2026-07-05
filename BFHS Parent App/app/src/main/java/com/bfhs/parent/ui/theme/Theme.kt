package com.bfhs.parent.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable

/**
 * Material 3 theme for the "Midnight Oxblood" design. The app is dark-only by design —
 * the same scheme is used regardless of the system setting.
 */
private val MidnightOxbloodScheme = darkColorScheme(
    primary = BfhsColors.AccentGold,
    onPrimary = BfhsColors.OnAccent,
    secondary = BfhsColors.AccentGoldDark,
    onSecondary = BfhsColors.OnAccent,
    background = BfhsColors.BackgroundBase,
    onBackground = BfhsColors.TextPrimary,
    surface = BfhsColors.BackgroundBase,
    onSurface = BfhsColors.TextPrimary,
    surfaceVariant = BfhsColors.GlassFill,
    onSurfaceVariant = BfhsColors.TextSecondary,
    outline = BfhsColors.GlassBorder,
    error = BfhsColors.Absent,
    onError = BfhsColors.TextPrimary
)

@Composable
fun BfhsParentTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit
) {
    MaterialTheme(
        colorScheme = MidnightOxbloodScheme,
        typography = BfhsTypography,
        content = content
    )
}
