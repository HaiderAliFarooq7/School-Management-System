package com.bfhs.parent.ui.viewmodel

import androidx.appcompat.app.AppCompatDelegate
import androidx.core.os.LocaleListCompat
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.bfhs.parent.core.Resource
import com.bfhs.parent.data.datastore.SessionManager
import com.bfhs.parent.domain.models.Parent
import com.bfhs.parent.domain.models.SchoolProfile
import com.bfhs.parent.domain.repository.AuthRepository
import com.bfhs.parent.domain.repository.SchoolRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class SettingsViewModel @Inject constructor(
    private val authRepository: AuthRepository,
    private val schoolRepository: SchoolRepository,
    private val sessionManager: SessionManager
) : ViewModel() {

    val parent: StateFlow<Parent?> = authRepository.parent()
        .stateIn(viewModelScope, SharingStarted.Eagerly, null)

    val language: StateFlow<String> = sessionManager.language
        .stateIn(viewModelScope, SharingStarted.Eagerly, "en")

    private val _school = MutableStateFlow<Resource<SchoolProfile>>(Resource.Loading)
    val school: StateFlow<Resource<SchoolProfile>> = _school.asStateFlow()

    init {
        viewModelScope.launch {
            schoolRepository.schoolProfile().collect { _school.value = it }
        }
    }

    /** Persists the choice and applies it via Android's per-app locale API. */
    fun setLanguage(tag: String) {
        viewModelScope.launch {
            sessionManager.setLanguage(tag)
            AppCompatDelegate.setApplicationLocales(LocaleListCompat.forLanguageTags(tag))
        }
    }

    fun logout(onDone: () -> Unit) {
        viewModelScope.launch {
            authRepository.logout()
            onDone()
        }
    }
}
