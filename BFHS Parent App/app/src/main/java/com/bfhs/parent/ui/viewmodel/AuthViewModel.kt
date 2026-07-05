package com.bfhs.parent.ui.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.bfhs.parent.core.Resource
import com.bfhs.parent.data.datastore.SessionManager
import com.bfhs.parent.domain.repository.AuthRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

data class LoginUiState(
    val mobileNumber: String = "",
    val password: String = "",
    val passwordVisible: Boolean = false,
    val isLoading: Boolean = false,
    val error: String? = null,
    val loginSucceeded: Boolean = false
)

@HiltViewModel
class AuthViewModel @Inject constructor(
    private val authRepository: AuthRepository,
    sessionManager: SessionManager
) : ViewModel() {

    private val _uiState = MutableStateFlow(LoginUiState())
    val uiState: StateFlow<LoginUiState> = _uiState.asStateFlow()

    /** null while reading DataStore; then true/false — drives auto-login from Splash. */
    val isLoggedIn: StateFlow<Boolean?> = authRepository.isLoggedIn()
        .stateIn(viewModelScope, SharingStarted.Eagerly, null)

    val parent = authRepository.parent()
        .stateIn(viewModelScope, SharingStarted.Eagerly, null)

    val language: StateFlow<String> = sessionManager.language
        .stateIn(viewModelScope, SharingStarted.Eagerly, "en")

    fun onMobileChanged(value: String) = _uiState.update { it.copy(mobileNumber = value, error = null) }
    fun onPasswordChanged(value: String) = _uiState.update { it.copy(password = value, error = null) }
    fun togglePasswordVisibility() = _uiState.update { it.copy(passwordVisible = !it.passwordVisible) }
    fun consumeLoginSuccess() = _uiState.update { it.copy(loginSucceeded = false) }

    fun login() {
        val state = _uiState.value
        if (state.mobileNumber.isBlank() || state.password.isBlank()) {
            _uiState.update { it.copy(error = "Enter your mobile number and password") }
            return
        }
        _uiState.update { it.copy(isLoading = true, error = null) }
        viewModelScope.launch {
            when (val result = authRepository.login(state.mobileNumber.trim(), state.password)) {
                is Resource.Success -> _uiState.update {
                    it.copy(isLoading = false, loginSucceeded = true, password = "")
                }
                is Resource.Error -> _uiState.update {
                    it.copy(isLoading = false, error = result.message)
                }
                else -> Unit
            }
        }
    }

    fun logout() {
        viewModelScope.launch { authRepository.logout() }
    }
}
