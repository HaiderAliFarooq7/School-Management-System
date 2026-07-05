package com.bfhs.parent.ui.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.bfhs.parent.core.Resource
import com.bfhs.parent.domain.models.Parent
import com.bfhs.parent.domain.models.Student
import com.bfhs.parent.domain.repository.AuthRepository
import com.bfhs.parent.domain.repository.NotificationRepository
import com.bfhs.parent.domain.repository.StudentRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class DashboardViewModel @Inject constructor(
    private val studentRepository: StudentRepository,
    private val authRepository: AuthRepository,
    notificationRepository: NotificationRepository
) : ViewModel() {

    private val _students = MutableStateFlow<Resource<List<Student>>>(Resource.Loading)
    val students: StateFlow<Resource<List<Student>>> = _students.asStateFlow()

    val parent: StateFlow<Parent?> = authRepository.parent()
        .stateIn(viewModelScope, SharingStarted.Eagerly, null)

    val hasUnread: StateFlow<Boolean> = notificationRepository.hasUnread()
        .stateIn(viewModelScope, SharingStarted.Eagerly, false)

    init {
        refresh()
        // Ensure this device's FCM token is registered with the backend now that
        // the parent is signed in (covers both fresh login and auto-login) — the
        // token minted at startup couldn't register before authentication.
        viewModelScope.launch { authRepository.registerCurrentDevice() }
    }

    fun refresh() {
        viewModelScope.launch {
            studentRepository.students().collect { _students.value = it }
        }
    }
}
