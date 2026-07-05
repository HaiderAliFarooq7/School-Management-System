package com.bfhs.parent.ui.screens.splash

import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.bfhs.parent.R
import com.bfhs.parent.ui.theme.BfhsColors
import com.bfhs.parent.ui.viewmodel.AuthViewModel
import kotlinx.coroutines.delay

private const val SPLASH_DURATION_MS = 2200L

/**
 * Splash — full-bleed radial gradient, glowing glass "BF" tile, 3-dot pulse loader.
 * Auto-advances after ~2.2s (or on tap) to Dashboard when a valid JWT exists,
 * otherwise to Login.
 */
@Composable
fun SplashScreen(
    onNavigateToLogin: () -> Unit,
    onNavigateToDashboard: () -> Unit,
    viewModel: AuthViewModel = hiltViewModel()
) {
    val isLoggedIn by viewModel.isLoggedIn.collectAsState()
    var timeElapsed by remember { mutableStateOf(false) }
    var navigated by remember { mutableStateOf(false) }

    LaunchedEffect(Unit) {
        delay(SPLASH_DURATION_MS)
        timeElapsed = true
    }

    fun advance() {
        val loggedIn = isLoggedIn ?: return // still reading DataStore
        if (!navigated) {
            navigated = true
            if (loggedIn) onNavigateToDashboard() else onNavigateToLogin()
        }
    }

    LaunchedEffect(timeElapsed, isLoggedIn) {
        if (timeElapsed) advance()
    }

    // Glow animation on the logo tile (splashGlow 2.4s ease-in-out infinite)
    val glow = rememberInfiniteTransition(label = "glow")
    val glowAlpha by glow.animateFloat(
        initialValue = 0.5f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(tween(1200), RepeatMode.Reverse),
        label = "glowAlpha"
    )

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(
                Brush.radialGradient(
                    0f to BfhsColors.SplashGradientCenter,
                    0.58f to BfhsColors.SplashGradientMid,
                    1f to BfhsColors.SplashGradientEdge,
                    center = Offset(0.3f, 0.2f),
                    radius = Float.POSITIVE_INFINITY
                )
            )
            .clickable(
                interactionSource = remember { MutableInteractionSource() },
                indication = null
            ) { advance() }
    ) {
        Column(
            modifier = Modifier.align(Alignment.Center),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(22.dp)
        ) {
            Box(
                modifier = Modifier
                    .size(104.dp)
                    .alpha(glowAlpha)
                    .background(BfhsColors.GlassFillStrong, RoundedCornerShape(32.dp))
                    .border(1.dp, BfhsColors.GlassBorderStrong, RoundedCornerShape(32.dp)),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    text = stringResource(R.string.logo_monogram),
                    color = BfhsColors.AccentGold,
                    fontSize = 34.sp,
                    fontWeight = androidx.compose.ui.text.font.FontWeight.SemiBold,
                    letterSpacing = 0.5.sp
                )
            }
            Column(
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(6.dp)
            ) {
                Text(
                    text = stringResource(R.string.app_name),
                    color = BfhsColors.TextPrimary,
                    style = MaterialTheme.typography.headlineMedium
                )
                Text(
                    text = stringResource(R.string.splash_tagline),
                    color = BfhsColors.TextSecondary,
                    style = MaterialTheme.typography.bodyLarge.copy(fontSize = 13.sp)
                )
            }
            PulsingDots(modifier = Modifier.padding(top = 18.dp))
        }
        Text(
            text = stringResource(R.string.splash_tap_to_continue),
            color = BfhsColors.TextHint,
            fontSize = 11.sp,
            modifier = Modifier
                .align(Alignment.BottomCenter)
                .padding(bottom = 36.dp)
        )
    }
}

@Composable
private fun PulsingDots(modifier: Modifier = Modifier) {
    val transition = rememberInfiniteTransition(label = "dots")
    val progress by transition.animateFloat(
        initialValue = 0f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(tween(1200, easing = LinearEasing)),
        label = "dotProgress"
    )
    Row(modifier = modifier, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        repeat(3) { index ->
            // Each dot pulses with a 0.2s stagger, matching the prototype's dotPulse keyframes.
            val phase = ((progress - index * 0.1667f + 1f) % 1f)
            val alpha = if (phase < 0.4f) 0.25f + (phase / 0.4f) * 0.75f
            else 1f - ((phase - 0.4f) / 0.6f) * 0.75f
            Box(
                modifier = Modifier
                    .size(7.dp)
                    .alpha(alpha.coerceIn(0.25f, 1f))
                    .background(BfhsColors.AccentGold, CircleShape)
            )
        }
    }
}
