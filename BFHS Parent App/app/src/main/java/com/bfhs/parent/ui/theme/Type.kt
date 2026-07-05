package com.bfhs.parent.ui.theme

import androidx.compose.material3.Typography
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp

/**
 * Typography from the design handoff. Font: Roboto Flex — Android's system Roboto
 * (SansSerif) is the specified fallback; weights 400 / 500 / 600 map 1:1.
 */
private val Roboto = FontFamily.SansSerif

val BfhsTypography = Typography(
    // Splash / Login headline — 26sp / 600
    headlineMedium = TextStyle(
        fontFamily = Roboto,
        fontWeight = FontWeight.SemiBold,
        fontSize = 26.sp
    ),
    // Student detail name — 20sp / 600
    headlineSmall = TextStyle(
        fontFamily = Roboto,
        fontWeight = FontWeight.SemiBold,
        fontSize = 20.sp
    ),
    // Screen title (app bar) — 17sp / 600
    titleLarge = TextStyle(
        fontFamily = Roboto,
        fontWeight = FontWeight.SemiBold,
        fontSize = 17.sp
    ),
    // Card title / student name — 15.5sp / 600
    titleMedium = TextStyle(
        fontFamily = Roboto,
        fontWeight = FontWeight.SemiBold,
        fontSize = 15.5.sp
    ),
    // List row title — 14.5sp / 600
    titleSmall = TextStyle(
        fontFamily = Roboto,
        fontWeight = FontWeight.SemiBold,
        fontSize = 14.5.sp
    ),
    // Body / supporting text — 13.5sp / 400
    bodyLarge = TextStyle(
        fontFamily = Roboto,
        fontWeight = FontWeight.Normal,
        fontSize = 13.5.sp
    ),
    // Supporting text — 12.5sp / 400
    bodyMedium = TextStyle(
        fontFamily = Roboto,
        fontWeight = FontWeight.Normal,
        fontSize = 12.5.sp
    ),
    // Small supporting text — 12sp / 400
    bodySmall = TextStyle(
        fontFamily = Roboto,
        fontWeight = FontWeight.Normal,
        fontSize = 12.sp
    ),
    // Section label — 13sp / 600, uppercase, letter-spacing 0.4
    labelLarge = TextStyle(
        fontFamily = Roboto,
        fontWeight = FontWeight.SemiBold,
        fontSize = 13.sp,
        letterSpacing = 0.4.sp
    ),
    // Field label / pill text — 12sp / 500
    labelMedium = TextStyle(
        fontFamily = Roboto,
        fontWeight = FontWeight.Medium,
        fontSize = 12.sp
    ),
    // Tiny labels (mini-stat captions, nav labels, hints) — 10.5sp / 500
    labelSmall = TextStyle(
        fontFamily = Roboto,
        fontWeight = FontWeight.Medium,
        fontSize = 10.5.sp,
        letterSpacing = 0.3.sp
    ),
    // Big stat (fee amount) — 32sp / 600
    displaySmall = TextStyle(
        fontFamily = Roboto,
        fontWeight = FontWeight.SemiBold,
        fontSize = 32.sp
    )
)

// Note: attendance summary counts (22sp / 600) use BfhsTypography.headlineSmall
// with an explicit 22.sp override in AttendanceScreen for exact fidelity.
