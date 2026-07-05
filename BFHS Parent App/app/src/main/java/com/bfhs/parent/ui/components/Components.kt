package com.bfhs.parent.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.bfhs.parent.ui.theme.BfhsColors
import com.bfhs.parent.ui.theme.Dimens

/**
 * Frosted glass card — translucent white fill + 1dp light border on the dark base,
 * per the "Midnight Oxblood" glassmorphism tokens.
 */
@Composable
fun GlassCard(
    modifier: Modifier = Modifier,
    corner: Dp = Dimens.CardCorner,
    fill: Color = BfhsColors.GlassFill,
    border: Color = BfhsColors.GlassBorder,
    contentPadding: PaddingValues = PaddingValues(Dimens.CardPadding),
    onClick: (() -> Unit)? = null,
    content: @Composable () -> Unit
) {
    val shape = RoundedCornerShape(corner)
    Box(
        modifier = modifier
            .background(fill, shape)
            .border(1.dp, border, shape)
            .let { if (onClick != null) it.clickable(onClick = onClick) else it }
            .padding(contentPadding)
    ) {
        content()
    }
}

/** Fully-rounded status pill: colored text on a tinted chip background. */
@Composable
fun StatusPill(text: String, color: Color, background: Color) {
    Text(
        text = text,
        color = color,
        style = MaterialTheme.typography.labelMedium.copy(fontSize = 11.5.sp),
        fontWeight = androidx.compose.ui.text.font.FontWeight.SemiBold,
        modifier = Modifier
            .background(background, RoundedCornerShape(100.dp))
            .padding(horizontal = 12.dp, vertical = 4.dp)
    )
}

/** Gold→maroon gradient avatar tile with the student's 2-letter monogram. */
@Composable
fun GradientAvatar(
    initials: String,
    size: Dp = Dimens.AvatarSize,
    corner: Dp = Dimens.AvatarCorner,
    fontSize: androidx.compose.ui.unit.TextUnit = 16.sp
) {
    Box(
        modifier = Modifier
            .size(size)
            .background(BfhsColors.AvatarGradient, RoundedCornerShape(corner)),
        contentAlignment = Alignment.Center
    ) {
        Text(
            text = initials,
            color = BfhsColors.TextPrimary,
            fontSize = fontSize,
            fontWeight = androidx.compose.ui.text.font.FontWeight.SemiBold
        )
    }
}

/** Gold→maroon gradient tile holding an icon (school glyph, person, etc.). */
@Composable
fun GradientIconTile(
    icon: ImageVector,
    size: Dp = Dimens.IconChipSize,
    corner: Dp = Dimens.IconChipCorner,
    iconSize: Dp = 22.dp,
    circular: Boolean = false
) {
    Box(
        modifier = Modifier
            .size(size)
            .background(
                BfhsColors.AvatarGradient,
                if (circular) CircleShape else RoundedCornerShape(corner)
            ),
        contentAlignment = Alignment.Center
    ) {
        Icon(icon, contentDescription = null, tint = BfhsColors.TextPrimary, modifier = Modifier.size(iconSize))
    }
}

/** Gold-tinted square chip holding a gold icon — used on list rows. */
@Composable
fun GoldIconChip(icon: ImageVector) {
    Box(
        modifier = Modifier
            .size(Dimens.IconChipSize)
            .background(BfhsColors.AccentGoldChip, RoundedCornerShape(Dimens.IconChipCorner)),
        contentAlignment = Alignment.Center
    ) {
        Icon(icon, contentDescription = null, tint = BfhsColors.AccentGold, modifier = Modifier.size(22.dp))
    }
}

/** Primary CTA — gold gradient, dark text, 52dp tall, 16dp corner. */
@Composable
fun GoldButton(
    text: String,
    modifier: Modifier = Modifier,
    isLoading: Boolean = false,
    onClick: () -> Unit
) {
    Box(
        modifier = modifier
            .fillMaxWidth()
            .height(Dimens.ButtonHeight)
            .background(BfhsColors.GoldButtonGradient, RoundedCornerShape(Dimens.ButtonCorner))
            .clickable(enabled = !isLoading, onClick = onClick),
        contentAlignment = Alignment.Center
    ) {
        if (isLoading) {
            CircularProgressIndicator(
                color = BfhsColors.OnAccent,
                strokeWidth = 2.5.dp,
                modifier = Modifier.size(22.dp)
            )
        } else {
            Text(
                text = text,
                color = BfhsColors.OnAccent,
                fontSize = 15.sp,
                fontWeight = androidx.compose.ui.text.font.FontWeight.SemiBold,
                letterSpacing = 0.2.sp
            )
        }
    }
}

/** Uppercase section label, e.g. "MY CHILDREN" / "HISTORY". */
@Composable
fun SectionLabel(text: String, modifier: Modifier = Modifier) {
    Text(
        text = text.uppercase(),
        color = BfhsColors.TextSecondaryDim,
        style = MaterialTheme.typography.labelLarge,
        modifier = modifier
    )
}

/** Back arrow + screen title header used on all pushed (non-tab) screens. */
@Composable
fun BackHeader(title: String, onBack: () -> Unit) {
    Row(
        verticalAlignment = Alignment.CenterVertically,
        modifier = Modifier
            .fillMaxWidth()
            .padding(start = Dimens.ScreenPaddingH, end = Dimens.ScreenPaddingH, top = 16.dp, bottom = 4.dp)
    ) {
        Icon(
            imageVector = Icons.AutoMirrored.Filled.ArrowBack,
            contentDescription = null,
            tint = BfhsColors.TextPrimary,
            modifier = Modifier
                .size(22.dp)
                .clickable(onClick = onBack)
        )
        Text(
            text = title,
            color = BfhsColors.TextPrimary,
            style = MaterialTheme.typography.titleLarge,
            modifier = Modifier.padding(start = Dimens.RowGap)
        )
    }
}

/** Centered loading state. */
@Composable
fun LoadingBox(modifier: Modifier = Modifier) {
    Box(modifier = modifier.fillMaxWidth().padding(40.dp), contentAlignment = Alignment.Center) {
        CircularProgressIndicator(color = BfhsColors.AccentGold, strokeWidth = 3.dp)
    }
}

/** Centered error text. */
@Composable
fun ErrorBox(message: String, modifier: Modifier = Modifier) {
    Column(
        modifier = modifier.fillMaxWidth().padding(40.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(
            text = message,
            color = BfhsColors.TextSecondary,
            style = MaterialTheme.typography.bodyLarge,
            textAlign = TextAlign.Center
        )
    }
}
