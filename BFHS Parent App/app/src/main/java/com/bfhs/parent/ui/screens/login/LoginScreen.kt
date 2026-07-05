package com.bfhs.parent.ui.screens.login

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Call
import androidx.compose.material.icons.outlined.Lock
import androidx.compose.material.icons.outlined.Visibility
import androidx.compose.material.icons.outlined.VisibilityOff
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.bfhs.parent.R
import com.bfhs.parent.ui.components.GoldButton
import com.bfhs.parent.ui.theme.BfhsColors
import com.bfhs.parent.ui.theme.Dimens
import com.bfhs.parent.ui.viewmodel.AuthViewModel

/**
 * Login — gradient background, logo chip + "Welcome back" headline, one large
 * glass card with mobile + password fields and the gold Log In CTA.
 */
@Composable
fun LoginScreen(
    onLoginSuccess: () -> Unit,
    viewModel: AuthViewModel = hiltViewModel()
) {
    val state by viewModel.uiState.collectAsState()

    LaunchedEffect(state.loginSucceeded) {
        if (state.loginSucceeded) {
            viewModel.consumeLoginSuccess()
            onLoginSuccess()
        }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(BfhsColors.LoginGradient)
    ) {
        // Header
        Column(modifier = Modifier.padding(start = 28.dp, end = 28.dp, top = 36.dp)) {
            Box(
                modifier = Modifier
                    .size(56.dp)
                    .background(BfhsColors.GlassFillStrong, RoundedCornerShape(18.dp))
                    .border(1.dp, BfhsColors.GlassBorderStrong, RoundedCornerShape(18.dp)),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    text = stringResource(R.string.logo_monogram),
                    color = BfhsColors.AccentGold,
                    fontSize = 18.sp,
                    fontWeight = androidx.compose.ui.text.font.FontWeight.SemiBold
                )
            }
            Spacer(Modifier.height(20.dp))
            Text(
                text = stringResource(R.string.login_welcome),
                color = BfhsColors.TextPrimary,
                style = MaterialTheme.typography.headlineMedium
            )
            Text(
                text = stringResource(R.string.login_subtitle),
                color = BfhsColors.TextSecondary,
                style = MaterialTheme.typography.bodyLarge.copy(fontSize = 13.sp),
                modifier = Modifier.padding(top = 4.dp)
            )
        }

        // Glass form card
        Column(
            modifier = Modifier
                .padding(start = 20.dp, end = 20.dp, top = 24.dp, bottom = 20.dp)
                .fillMaxWidth()
                .background(BfhsColors.GlassFill, RoundedCornerShape(Dimens.CardCornerHero))
                .border(1.dp, BfhsColors.GlassBorder, RoundedCornerShape(Dimens.CardCornerHero))
                .padding(Dimens.CardPaddingLarge)
                .verticalScroll(rememberScrollState()),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            LoginField(
                label = stringResource(R.string.login_mobile_label),
                value = state.mobileNumber,
                onValueChange = viewModel::onMobileChanged,
                placeholder = stringResource(R.string.login_mobile_hint),
                leadingIcon = Icons.Outlined.Call,
                keyboardType = KeyboardType.Phone
            )
            LoginField(
                label = stringResource(R.string.login_password_label),
                value = state.password,
                onValueChange = viewModel::onPasswordChanged,
                placeholder = "••••••••",
                leadingIcon = Icons.Outlined.Lock,
                keyboardType = KeyboardType.Password,
                isPassword = true,
                passwordVisible = state.passwordVisible,
                onToggleVisibility = viewModel::togglePasswordVisibility
            )

            Text(
                text = stringResource(R.string.login_forgot_password),
                color = BfhsColors.AccentGold,
                style = MaterialTheme.typography.labelMedium,
                modifier = Modifier.align(Alignment.End)
            )

            state.error?.let { error ->
                Text(
                    text = error,
                    color = BfhsColors.Absent,
                    style = MaterialTheme.typography.bodyMedium
                )
            }

            GoldButton(
                text = stringResource(R.string.login_button),
                isLoading = state.isLoading,
                modifier = Modifier.padding(top = 6.dp),
                onClick = viewModel::login
            )

            Text(
                text = stringResource(R.string.login_help),
                color = BfhsColors.TextTertiary,
                fontSize = 11.5.sp,
                textAlign = TextAlign.Center,
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(top = 4.dp)
            )
        }
    }
}

@Composable
private fun LoginField(
    label: String,
    value: String,
    onValueChange: (String) -> Unit,
    placeholder: String,
    leadingIcon: ImageVector,
    keyboardType: KeyboardType,
    isPassword: Boolean = false,
    passwordVisible: Boolean = false,
    onToggleVisibility: (() -> Unit)? = null
) {
    Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
        Text(text = label, color = BfhsColors.TextSecondary, style = MaterialTheme.typography.labelMedium)
        Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(10.dp),
            modifier = Modifier
                .fillMaxWidth()
                .background(BfhsColors.FieldFill, RoundedCornerShape(Dimens.FieldCorner))
                .border(1.dp, BfhsColors.FieldBorder, RoundedCornerShape(Dimens.FieldCorner))
                .padding(horizontal = 14.dp, vertical = 12.dp)
        ) {
            Icon(
                leadingIcon,
                contentDescription = null,
                tint = BfhsColors.TextSecondaryDim,
                modifier = Modifier.size(20.dp)
            )
            Box(modifier = Modifier.weight(1f)) {
                if (value.isEmpty()) {
                    Text(
                        text = placeholder,
                        color = BfhsColors.TextHint,
                        fontSize = 15.sp
                    )
                }
                BasicTextField(
                    value = value,
                    onValueChange = onValueChange,
                    singleLine = true,
                    textStyle = TextStyle(color = BfhsColors.TextPrimary, fontSize = 15.sp),
                    cursorBrush = SolidColor(BfhsColors.AccentGold),
                    keyboardOptions = KeyboardOptions(keyboardType = keyboardType),
                    visualTransformation = if (isPassword && !passwordVisible) {
                        PasswordVisualTransformation()
                    } else {
                        VisualTransformation.None
                    },
                    modifier = Modifier.fillMaxWidth()
                )
            }
            if (isPassword && onToggleVisibility != null) {
                Icon(
                    imageVector = if (passwordVisible) Icons.Outlined.Visibility else Icons.Outlined.VisibilityOff,
                    contentDescription = null,
                    tint = BfhsColors.TextTertiary,
                    modifier = Modifier
                        .size(18.dp)
                        .clickable(onClick = onToggleVisibility)
                )
            }
        }
    }
}
