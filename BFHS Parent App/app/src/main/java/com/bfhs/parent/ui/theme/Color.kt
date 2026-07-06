package com.bfhs.parent.ui.theme

import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color

/**
 * "Midnight Oxblood" design tokens — taken 1:1 from the design handoff.
 * Dark, immersive glassmorphism: deep oxblood/maroon base, frosted glass cards,
 * warm gold as the single accent.
 */
object BfhsColors {
    // Base surfaces
    val BackgroundBase = Color(0xFF180508)
    val DialogSurface = Color(0xFF2A0910)   // opaque dark maroon for dialogs

    // Gradient stops
    val HeaderGradientStart = Color(0xFF6E1B26)
    val HeaderGradientEnd = Color(0xFF3D0E14)
    val SplashGradientCenter = Color(0xFF7A2233)
    val SplashGradientMid = Color(0xFF3D0E14)
    val SplashGradientEdge = Color(0xFF1C0509)
    val LoginGradientTop = Color(0xFF5C1A26)
    val LoginGradientMid = Color(0xFF2A0910)
    val LoginGradientBottom = Color(0xFF1C0509)

    // Accent gold — CTAs, active states, money values, key numbers
    val AccentGold = Color(0xFFD9AE6B)
    val AccentGoldDark = Color(0xFFB98842)
    val AccentGoldChip = Color(0x29D9AE6B)     // rgba(217,174,107,0.16)
    val AccentGoldActive = Color(0x38D9AE6B)   // rgba(217,174,107,0.22)

    // Avatar / icon gradient end
    val AvatarGradientEnd = Color(0xFF93293A)

    // Glass
    val GlassFill = Color(0x0FFFFFFF)          // rgba(255,255,255,0.06)
    val GlassFillStrong = Color(0x14FFFFFF)    // rgba(255,255,255,0.08)
    val GlassBorder = Color(0x24FFFFFF)        // rgba(255,255,255,0.14)
    val GlassBorderStrong = Color(0x38FFFFFF)  // rgba(255,255,255,0.22)
    val GlassInnerTile = Color(0x0DFFFFFF)     // rgba(255,255,255,0.05)
    val FieldFill = Color(0x0FFFFFFF)          // rgba(255,255,255,0.06)
    val FieldBorder = Color(0x2EFFFFFF)        // rgba(255,255,255,0.18)
    val Divider = Color(0x14FFFFFF)            // rgba(255,255,255,0.08)
    val InactiveBorder = Color(0x1FFFFFFF)     // rgba(255,255,255,0.12)

    // Text
    val TextPrimary = Color(0xFFFFFFFF)
    val TextSecondary = Color(0x99FFFFFF)      // 0.6
    val TextSecondaryDim = Color(0x80FFFFFF)   // 0.5
    val TextTertiary = Color(0x66FFFFFF)       // 0.4
    val TextHint = Color(0x4DFFFFFF)           // 0.3
    val TextBody = Color(0xA6FFFFFF)           // 0.65
    val TextRow = Color(0xCCFFFFFF)            // 0.8
    val TextLabel = Color(0x73FFFFFF)          // 0.45

    // Status
    val Present = Color(0xFF1B8A5A)
    val PresentChip = Color(0x291B8A5A)        // rgba(27,138,90,0.16)
    val Absent = Color(0xFFB3261E)
    val AbsentChip = Color(0x2EB3261E)         // rgba(179,38,30,0.18)
    val Leave = Color(0xFFD9A441)
    val LeaveChip = Color(0x29D9A441)          // rgba(217,164,65,0.16)

    // Dark text used on top of the gold CTA button
    val OnAccent = Color(0xFF2A0910)

    // Reusable brushes
    val HeaderGradient = Brush.linearGradient(
        colors = listOf(HeaderGradientStart, HeaderGradientEnd)
    )
    val LoginGradient = Brush.verticalGradient(
        0f to LoginGradientTop,
        0.7f to LoginGradientMid,
        1f to LoginGradientBottom
    )
    val GoldButtonGradient = Brush.horizontalGradient(
        colors = listOf(AccentGold, AccentGoldDark)
    )
    val AvatarGradient = Brush.linearGradient(
        colors = listOf(AccentGold, AvatarGradientEnd)
    )
}
