package com.bfhs.parent.ui.navigation

object Routes {
    const val SPLASH = "splash"
    const val LOGIN = "login"
    const val DASHBOARD = "dashboard"
    const val NOTIFICATIONS = "notifications"
    const val SETTINGS = "settings"
    const val STUDENT_DETAIL = "student/{studentId}"
    const val ATTENDANCE = "attendance/{studentId}"
    const val FEE = "fee/{studentId}"
    const val CHARGES = "charges/{studentId}"
    const val SCHOOL_PROFILE = "school_profile"
    const val LANGUAGE = "language"
    const val ABOUT = "about"

    fun studentDetail(studentId: String) = "student/$studentId"
    fun attendance(studentId: String) = "attendance/$studentId"
    fun fee(studentId: String) = "fee/$studentId"
    fun charges(studentId: String) = "charges/$studentId"
}
