package com.bfhs.parent.ui.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.bfhs.parent.core.Resource
import com.bfhs.parent.domain.models.SchoolNotification
import com.bfhs.parent.domain.repository.NotificationRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class NotificationsViewModel @Inject constructor(
    private val notificationRepository: NotificationRepository
) : ViewModel() {

    private val _notifications =
        MutableStateFlow<Resource<List<SchoolNotification>>>(Resource.Loading)
    val notifications: StateFlow<Resource<List<SchoolNotification>>> = _notifications.asStateFlow()

    init {
        refresh()
    }

    fun refresh() {
        viewModelScope.launch {
            notificationRepository.notifications().collect { _notifications.value = it }
        }
    }

    fun markAllRead() {
        viewModelScope.launch { notificationRepository.markAllRead() }
    }
}
