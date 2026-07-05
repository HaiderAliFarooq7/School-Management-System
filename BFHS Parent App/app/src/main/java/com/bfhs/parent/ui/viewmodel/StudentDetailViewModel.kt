package com.bfhs.parent.ui.viewmodel

import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.bfhs.parent.core.Resource
import com.bfhs.parent.domain.models.AttendanceSummary
import com.bfhs.parent.domain.models.ExtraCharge
import com.bfhs.parent.domain.models.FeeOverview
import com.bfhs.parent.domain.models.Student
import com.bfhs.parent.domain.repository.StudentRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import javax.inject.Inject

/**
 * Shared by Student Detail, Attendance, Monthly Fee and Extra Charges screens —
 * each screen instance is scoped to the studentId from its navigation route.
 */
@HiltViewModel
class StudentDetailViewModel @Inject constructor(
    savedStateHandle: SavedStateHandle,
    private val studentRepository: StudentRepository
) : ViewModel() {

    val studentId: String = savedStateHandle["studentId"] ?: ""

    val student: StateFlow<Student?> = studentRepository.student(studentId)
        .stateIn(viewModelScope, SharingStarted.Eagerly, null)

    private val _attendance = MutableStateFlow<Resource<AttendanceSummary>>(Resource.Loading)
    val attendance: StateFlow<Resource<AttendanceSummary>> = _attendance.asStateFlow()

    private val _fees = MutableStateFlow<Resource<FeeOverview>>(Resource.Loading)
    val fees: StateFlow<Resource<FeeOverview>> = _fees.asStateFlow()

    private val _charges = MutableStateFlow<Resource<List<ExtraCharge>>>(Resource.Loading)
    val charges: StateFlow<Resource<List<ExtraCharge>>> = _charges.asStateFlow()

    init {
        if (studentId.isNotBlank()) {
            viewModelScope.launch {
                studentRepository.attendance(studentId).collect { _attendance.value = it }
            }
            viewModelScope.launch {
                studentRepository.fees(studentId).collect { _fees.value = it }
            }
            viewModelScope.launch {
                studentRepository.extraCharges(studentId).collect { _charges.value = it }
            }
        }
    }
}
